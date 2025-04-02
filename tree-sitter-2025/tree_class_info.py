from typing import List, Dict, Any

from init_tree_sitter import init_php_parser
from libs_com.file_io import read_file_bytes
from libs_com.utils_json import print_json
from tree_const import *


def analyze_class_infos(tree, language) -> List[Dict[str, Any]]:
    """提取所有类定义信息"""
    # 获取所有本地函数名称
    file_functions = get_file_funcs(tree, language)

    class_infos = []
    class_info_query = language.query("""
        (class_declaration
            name: (name) @class_name
            (base_clause (name) @extends)? @base_clause
            body: (declaration_list) @class_body
        )
        
        (interface_declaration
            name: (name) @interface_name
            (base_clause (name) @extends)? @base_clause
            body: (declaration_list) @interface_body
        )
        
        (namespace_definition
            name: (namespace_name) @namespace_name
        )
        
        (method_declaration
            (visibility_modifier)? @method_visibility
            (static_modifier)? @is_static_method
            name: (name) @method_name
            parameters: (formal_parameters) @method_params
            body: (compound_statement) @method_body
        )

        (property_declaration
            (visibility_modifier) @property_visibility
            (static_modifier)? @is_static
            (property_element
                name: (variable_name) @property_name
                value: (_)? @property_value
            )
        )

        ; 修改函数调用匹配
        ((function_call_expression
            function: (name) @function_call
            arguments: (arguments) @function_args
        ) @function_call_expr
        (#not-eq? @function_call "echo"))

        ; 修改方法调用匹配
        (member_call_expression
            object: (_) @object
            name: (name) @method_call
            arguments: (arguments) @method_args
        ) @method_call_expr
    """)
    class_info_matches = class_info_query.matches(tree.root_node)

    # 修改函数调用解析部分
    current_class = None
    current_method = None
    for pattern_index, match_dict in class_info_matches:
        # 修改类信息提取部分
        extends_info = match_dict['extends'][0].text.decode('utf-8') if 'extends' in match_dict else None
        if 'class_name' in match_dict:
            class_info = match_dict['class_name'][0]
            current_class = {
                CLASS_EXTENDS: extends_info,
                CLASS_DEPENDS: set(),  # 初始化依赖集合
                CLASS_PROPS: [],  # 确保包含 properties 字段
                CLASS_METHODS: [],

                CLASS_NAME: class_info.text.decode('utf-8'),
                CLASS_START_LINE: class_info.start_point[0] + 1,
                CLASS_END_LINE: class_info.end_point[0] + 1,
                CLASS_TYPE: TYPE_CLASS
            }
            class_infos.append(current_class)
            
        elif 'interface_name' in match_dict:
            interface_info = match_dict['interface_name'][0]
            current_interface = {
                CLASS_DEPENDS: set(),  # 初始化依赖集合
                CLASS_PROPS: [],  # 确保包含 properties 字段
                CLASS_METHODS: [],
                CLASS_EXTENDS: extends_info,
                CLASS_NAME: interface_info.text.decode('utf-8'),
                CLASS_START_LINE: interface_info.start_point[0] + 1,
                CLASS_END_LINE: interface_info.end_point[0] + 1,
                CLASS_TYPE: TYPE_INTERFACE,
            }
            class_infos.append(current_interface)
            
        elif 'namespace_name' in match_dict:
            namespace_info = match_dict['namespace_name'][0]
            current_namespace = {
                CLASS_DEPENDS: set(),  # 初始化依赖集合
                CLASS_PROPS: [],  # 确保包含 properties 字段
                CLASS_METHODS: [],
                CLASS_EXTENDS: extends_info,

                CLASS_NAME: namespace_info.text.decode('utf-8'),
                CLASS_START_LINE: namespace_info.start_point[0] + 1,
                CLASS_END_LINE: namespace_info.end_point[0] + 1,
                CLASS_TYPE: TYPE_NAMESPACE,
            }
            class_infos.append(current_namespace)

        elif current_class and 'method_name' in match_dict:
            method_info = match_dict['method_name'][0]
            method_name = method_info.text.decode('utf-8')

            visibility = match_dict.get('method_visibility', [None])[0]
            visibility = visibility.text.decode('utf-8') if visibility else 'public'
            
            is_static = 'is_static_method' in match_dict and match_dict['is_static_method'][0] is not None

            current_method = {
                METHOD_NAME: method_name,
                METHOD_START_LINE: method_info.start_point[0] + 1,
                METHOD_END_LINE: method_info.end_point[0] + 1,
                METHOD_VISIBILITY: visibility,
                METHOD_IS_STATIC: is_static,
                METHOD_PARAMS: [],
                CALLED_METHODS: []
            }
            
            # 修改方法参数解析部分
            if 'method_params' in match_dict:
                params_node = match_dict['method_params'][0]
                seen_params = set()  # 用于去重
                for child in params_node.children:
                    if child.type == 'simple_parameter':
                        param_name = None
                        param_type = None
                        for param_child in child.children:
                            if param_child.type == 'variable_name':
                                param_name = param_child.text.decode('utf-8')
                            elif param_child.type in ['primitive_type', 'name']:
                                param_type = param_child.text.decode('utf-8')
                            if param_name and param_name not in seen_params:
                                seen_params.add(param_name)
                                method_param_type = {
                                    PARAM_NAME: param_name,
                                    PARAM_TYPE: param_type
                                }
                                current_method[METHOD_PARAMS].append(method_param_type)
            
            # 处理方法体中的函数调用
            if 'method_body' in match_dict:
                body_node = match_dict['method_body'][0]
                seen_called_functions = set()
                process_method_body_node(body_node, seen_called_functions, file_functions, current_method, current_class)
            
            current_class[CLASS_METHODS].append(current_method)
            
        elif current_class and 'property_name' in match_dict:
            visibility = match_dict.get('property_visibility', [None])[0]
            visibility = visibility.text.decode('utf-8') if visibility else 'public'

            is_static = 'is_static' in match_dict and match_dict['is_static'][0] is not None

            property_info = match_dict['property_name'][0]
            cuurent_property = {
                PROP_NAME: property_info.text.decode('utf-8'),
                PROP_LINE: property_info.start_point[0] + 1,
                PROPERTY_VISIBILITY: visibility,
                PROP_IS_STATIC: is_static,
                PROP_VALUE: None,
            }

            if 'property_value' in match_dict and match_dict['property_value'][0]:
                property_value = match_dict['property_value'][0]
                if property_value.type == 'integer':
                    cuurent_property[PROP_VALUE] = int(property_value.text.decode('utf-8'))
                else:
                    cuurent_property[PROP_VALUE] = property_value.text.decode('utf-8')
            
            current_class[CLASS_PROPS].append(cuurent_property)

    # 将依赖集合转换为列表
    for class_info in class_infos:
        class_info[CLASS_DEPENDS] = [{METHOD_NAME: func_name, METHOD_TYPE: func_type} for func_name, func_type in class_info[
            CLASS_DEPENDS]]
    
    return class_infos


def process_method_body_node(node, seen_called_functions, file_functions, current_method, current_class):
    if node.type == 'function_call_expression':
        func_node = node.child_by_field_name('function')
        if func_node:
            func_name = func_node.text.decode('utf-8')
            call_key = f"{func_name}:{node.start_point[0]}"
            if call_key not in seen_called_functions:
                seen_called_functions.add(call_key)
                # 修改函数类型判断逻辑
                func_type = CUSTOM_METHOD  # 默认为自定义函数
                if func_name in PHP_BUILTIN_FUNCTIONS:
                    func_type = BUILTIN_METHOD  # PHP内置函数
                elif func_name in file_functions:
                    func_type = LOCAL_METHOD  # 本地定义的函数
                elif func_name.startswith('$'):
                    func_type = DYNAMIC_METHOD  # 动态函数调用

                # 只记录非内置函数的调用
                if func_type != BUILTIN_METHOD:
                    call_info = {
                        METHOD_NAME: func_name,
                        METHOD_START_LINE: node.start_point[0] + 1,
                        METHOD_END_LINE: node.end_point[0] + 1,
                        METHOD_TYPE: func_type,
                    }
                    current_method[CALLED_METHODS].append(call_info)
                    current_class[CLASS_DEPENDS].add((func_name, func_type))
    elif node.type == 'member_call_expression':
        print("已进入 member_call_expression, 该方法还需要进行测试!!!")
        object_node = node.child_by_field_name('object')
        name_node = node.child_by_field_name('name')
        if object_node and name_node:
            object_name = object_node.text.decode('utf-8')
            method_name = name_node.text.decode('utf-8')
            # method_info = match_dict['method_name'][0] # 原来用的是这个,但是好像重复了,需要遇到以后再进行测试
            method_info = name_node
            call_info = {
                METHOD_FULL_NAME: f"{object_name}->{method_name}",
                METHOD_OBJECT: object_name,
                METHOD_NAME: method_name,
                METHOD_START_LINE: method_info.start_point[0] + 1,
                METHOD_END_LINE: method_info.end_point[0] + 1,
                METHOD_TYPE: OBJECT_METHOD,
            }
            current_method[CALLED_METHODS].append(call_info)

    for children in node.children:
        process_method_body_node(children, seen_called_functions, file_functions, current_method, current_class)


def get_file_funcs(tree, language):
    # 获取所有本地函数名称
    file_functions = set()
    function_query = language.query("""
        (function_definition
            name: (name) @function.name
        )
    """)
    for match in function_query.matches(tree.root_node):
        if 'function.name' in match[1]:
            name_node = match[1]['function.name'][0]
            if name_node:
                file_functions.add(name_node.text.decode('utf8'))

    return file_functions

if __name__ == '__main__':
    php_file = r"php_demo\class.php"
    # php_file = r"php_demo\extends.php"
    # php_file = r"php_demo\interface.php"
    PARSER, LANGUAGE = init_php_parser()
    php_file_bytes = read_file_bytes(php_file)
    php_file_tree = PARSER.parse(php_file_bytes)
    # print(php_file_tree.root_node)
    classes = analyze_class_infos(php_file_tree, LANGUAGE)
    for class_info in classes:
        print("=" * 50)
        print_json(class_info)
        print("=" * 50)
