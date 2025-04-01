from typing import List, Dict, Any

from init_tree_sitter import init_php_parser
from libs_com.file_io import read_file_bytes
from libs_com.utils_json import print_json
from tree_const import BUILTIN_METHOD, CALLED_FUNCTIONS, CUSTOM_METHOD, LOCAL_METHOD, DYNAMIC_METHOD, \
    FUNC_TYPE, OBJECT_METHOD, PHP_BUILTIN_FUNCTIONS

CLASS_TYPE = 'class_type'
CLASS_PROPERTIES = 'class_properties'
CLASS_METHODS = 'class_methods'
CLASS_DEPENDENCIES = 'class_dependencies'
CLASS_EXTENDS = 'class_extends'
TYPE_CLASS = 'type_class'
TYPE_INTERFACE = 'type_interface'
TYPE_NAMESPACE = 'type_namespace'

METHOD_IS_STATIC = 'method_is_static'
METHOD_VISIBILITY = 'method_visibility'
METHOD_PARAMETERS = 'method_parameters'

PROPERTY_VISIBILITY = 'property_visibility'
PROPERTY_IS_STATIC = 'property_is_static'

CLASS_NAME = 'class_name'
CLASS_LINE = 'class_line'
METHOD_NAME = 'method_name'
METHOD_LINE = 'method_line'
METHOD_FULL_NAME = 'method_full_name'
METHOD_OBJECT_NAME = 'method_object_name'

PARAM_NAME = 'param_name'
PARAM_TYPE = 'param_type'

PROPERTY_NAME = 'property_name'
PROPERTY_VALUE = 'property_value'
PROPERTY_LINE = 'property_line'

FUNCTION_NAME = 'function_name'
FUNCTION_LINE = 'function_line'


def extract_class_info(tree, language) -> List[Dict[str, Any]]:
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
            current_class = {
                CLASS_EXTENDS: extends_info,
                CLASS_DEPENDENCIES: set(),  # 初始化依赖集合
                CLASS_PROPERTIES: [],  # 确保包含 properties 字段
                CLASS_METHODS: [],

                CLASS_NAME: match_dict['class_name'][0].text.decode('utf-8'),
                CLASS_LINE: match_dict['class_name'][0].start_point[0] + 1,
                CLASS_TYPE: TYPE_CLASS
            }
            class_infos.append(current_class)
            
        elif 'interface_name' in match_dict:
            current_interface = {
                CLASS_DEPENDENCIES: set(),  # 初始化依赖集合
                CLASS_PROPERTIES: [],  # 确保包含 properties 字段
                CLASS_METHODS: [],
                CLASS_EXTENDS: extends_info,
                CLASS_NAME: match_dict['interface_name'][0].text.decode('utf-8'),
                CLASS_LINE: match_dict['interface_name'][0].start_point[0] + 1,
                CLASS_TYPE: TYPE_INTERFACE,
            }
            class_infos.append(current_interface)
            
        elif 'namespace_name' in match_dict:
            namespace = {
                CLASS_DEPENDENCIES: set(),  # 初始化依赖集合
                CLASS_PROPERTIES: [],  # 确保包含 properties 字段
                CLASS_METHODS: [],
                CLASS_EXTENDS: extends_info,

                CLASS_NAME: match_dict['namespace_name'][0].text.decode('utf-8'),
                CLASS_LINE: match_dict['namespace_name'][0].start_point[0] + 1,
                CLASS_TYPE: TYPE_NAMESPACE,
            }
            class_infos.append(namespace)

        elif current_class and 'method_name' in match_dict:
            method_name = match_dict['method_name'][0].text.decode('utf-8')
            visibility = match_dict.get('method_visibility', [None])[0]
            visibility = visibility.text.decode('utf-8') if visibility else 'public'
            
            is_static = 'is_static_method' in match_dict and match_dict['is_static_method'][0] is not None

            current_method = {
                METHOD_NAME: method_name,
                METHOD_LINE: match_dict['method_name'][0].start_point[0] + 1,
                METHOD_VISIBILITY: visibility,
                METHOD_IS_STATIC: is_static,
                METHOD_PARAMETERS: [],
                CALLED_FUNCTIONS: []
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
                                current_method[METHOD_PARAMETERS].append(method_param_type)
            
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

            property_info = {
                PROPERTY_NAME: match_dict['property_name'][0].text.decode('utf-8'),
                PROPERTY_LINE: match_dict['property_name'][0].start_point[0] + 1,
                PROPERTY_VISIBILITY: visibility,
                PROPERTY_IS_STATIC: is_static,
                PROPERTY_VALUE: None,
            }

            if 'property_value' in match_dict and match_dict['property_value'][0]:
                property_value = match_dict['property_value'][0]
                if property_value.type == 'integer':
                    property_info[PROPERTY_VALUE] = int(property_value.text.decode('utf-8'))
                else:
                    property_info[PROPERTY_VALUE] = property_value.text.decode('utf-8')
            
            current_class[CLASS_PROPERTIES].append(property_info)

    # 将依赖集合转换为列表
    for class_info in class_infos:
        class_info[CLASS_DEPENDENCIES] = [{FUNCTION_NAME: func_name, FUNC_TYPE: func_type} for func_name, func_type in class_info[CLASS_DEPENDENCIES]]
    
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
                        FUNCTION_NAME: func_name,
                        FUNCTION_LINE: node.start_point[0] + 1,
                        FUNC_TYPE: func_type,
                    }
                    current_method[CALLED_FUNCTIONS].append(call_info)
                    current_class[CLASS_DEPENDENCIES].add((func_name, func_type))
    elif node.type == 'member_call_expression':
        object_node = node.child_by_field_name('object')
        name_node = node.child_by_field_name('name')
        if object_node and name_node:
            object_name = object_node.text.decode('utf-8')
            method_name = name_node.text.decode('utf-8')
            call_info = {
                METHOD_FULL_NAME: f"{object_name}->{method_name}",
                METHOD_OBJECT_NAME: object_name,
                METHOD_NAME: method_name,
                METHOD_LINE: node.start_point[0] + 1,
                FUNC_TYPE: OBJECT_METHOD,
            }
            current_method[CALLED_FUNCTIONS].append(call_info)

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

# 修改打印函数以显示调用信息
def print_class_info(class_infos: List[Dict[str, Any]]):
    """打印类信息"""
    for class_info in class_infos:
        print(f"\n类名: {class_info[CLASS_NAME]}")
        print(f"  定义行号: {class_info[CLASS_LINE]}")

        if class_info[CLASS_DEPENDENCIES]:
            print("\n  依赖函数:")
            for dep in class_info[CLASS_DEPENDENCIES]:
                print(f"    - {dep}")

        print("\n  属性:")
        for prop in class_info[CLASS_PROPERTIES]:
            print(f"    {prop[PROPERTY_NAME]}")
            print(f"      可见性: {prop[PROPERTY_VISIBILITY]}")
            print(f"      静态: {prop[PROPERTY_IS_STATIC]}")
            print(f"      行号: {prop[PROPERTY_LINE]}")
            if 'value' in prop:
                print(f"      默认值: {prop[PROPERTY_VALUE]}")

        print("\n  方法:")
        for method in class_info[CLASS_METHODS]:
            print(f"    {method[METHOD_NAME]}")
            print(f"      可见性: {method[METHOD_VISIBILITY]}")
            print(f"      静态: {method[METHOD_IS_STATIC]}")
            print(f"      行号: {method[METHOD_LINE]}")
            if method[METHOD_PARAMETERS]:
                params_str = ', '.join([f"{param[PARAM_NAME]}" +
                                        (f": {param[PARAM_TYPE]}" if param[PARAM_TYPE] else '')
                                        for param in method[METHOD_PARAMETERS]])
                print(f"      参数: {params_str}")
            if method[CALLED_FUNCTIONS]:
                print("      调用:")
                for call in method[CALLED_FUNCTIONS]:
                    print(f"           CALLED_FUNCTION:{call}")

if __name__ == '__main__':
    php_file = r"php_demo\class.php"
    # php_file = r"php_demo\extends.php"
    # php_file = r"php_demo\interface.php"
    PARSER, LANGUAGE = init_php_parser()
    php_file_bytes = read_file_bytes(php_file)
    php_file_tree = PARSER.parse(php_file_bytes)
    # print(php_file_tree.root_node)
    classes = extract_class_info(php_file_tree, LANGUAGE)
    for class_info in classes:
        print("=" * 50)
        print_json(class_info)
        print("=" * 50)
    print_class_info(classes)