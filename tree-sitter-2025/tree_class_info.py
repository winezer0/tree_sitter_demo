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
            (visibility_modifier)? @class_visibility
            (abstract_modifier)? @is_abstract_class
            (final_modifier)? @is_final_class
            name: (name) @class_name
            (base_clause (name) @extends)? @base_clause
            body: (declaration_list) @class_body
        )
        
        (namespace_definition
            name: (namespace_name) @namespace_name
        )
        
        (method_declaration
            (visibility_modifier)? @method_visibility
            (static_modifier)? @is_static_method
            (abstract_modifier)? @is_abstract_method
            (final_modifier)? @is_final_method
            name: (name) @method_name
            parameters: (formal_parameters) @method_params
            return_type: (_)? @method_return_type
            body: (compound_statement) @method_body
        )

        (property_declaration
            (visibility_modifier) @property_visibility
            (static_modifier)? @is_static
            (readonly_modifier)? @is_readonly
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
    current_namespace = None  # 当前命名空间
    
    for pattern_index, match_dict in class_info_matches:
        # 修改类信息提取部分
        extends_info = match_dict['extends'][0].text.decode('utf-8') if 'extends' in match_dict else None
        
        if 'namespace_name' in match_dict:
            current_namespace = match_dict['namespace_name'][0].text.decode('utf-8')
            continue
            
        if 'class_name' in match_dict:
            class_info = match_dict['class_name'][0]
            
            # 获取类的可见性
            visibility = 'public'  # 默认可见性
            if 'class_visibility' in match_dict and match_dict['class_visibility'][0]:
                visibility = match_dict['class_visibility'][0].text.decode('utf-8')
            
            # 获取类的修饰符
            class_modifiers = []
            if 'is_abstract_class' in match_dict and match_dict['is_abstract_class'][0]:
                class_modifiers.append('abstract')
            if 'is_final_class' in match_dict and match_dict['is_final_class'][0]:
                class_modifiers.append('final')
                
            current_class = {
                CLASS_NAME: class_info.text.decode('utf-8'),
                CLASS_NAMESPACE: current_namespace if current_namespace else "",
                CLASS_VISIBILITY: visibility,
                CLASS_MODIFIERS: class_modifiers,
                CLASS_START_LINE: class_info.start_point[0] + 1,
                CLASS_END_LINE: class_info.end_point[0] + 1,
                CLASS_EXTENDS: [{extends_info: None}] if extends_info else [],  # 修改为数组对象格式
                CLASS_INTERFACES: [],
                CLASS_METHODS: [],
                CLASS_PROPERTIES: [],
            }
            class_infos.append(current_class)
            
        elif 'interface_name' in match_dict:
            interface_info = match_dict['interface_name'][0]
            current_class = {
                CLASS_NAME: interface_info.text.decode('utf-8'),
                CLASS_NAMESPACE: current_namespace,
                CLASS_VISIBILITY: 'public',
                CLASS_MODIFIERS: ['interface'],
                CLASS_START_LINE: interface_info.start_point[0] + 1,
                CLASS_END_LINE: interface_info.end_point[0] + 1,
                CLASS_EXTENDS: {extends_info: None} if extends_info else None,
                CLASS_INTERFACES: [],
                CLASS_PROPERTIES: [],
                CLASS_METHODS: [],
            }
            class_infos.append(current_class)

        elif 'interface_name' in match_dict:
            interface_info = match_dict['interface_name'][0]
            current_interface = {
                CLASS_PROPERTIES: [],  # 确保包含 properties 字段
                CLASS_METHODS: [],
                CLASS_EXTENDS: extends_info,
                CLASS_NAME: interface_info.text.decode('utf-8'),
                CLASS_START_LINE: interface_info.start_point[0] + 1,
                CLASS_END_LINE: interface_info.end_point[0] + 1,
            }
            class_infos.append(current_interface)
            
        elif 'namespace_name' in match_dict:
            namespace_info = match_dict['namespace_name'][0]
            current_namespace = {
                CLASS_PROPERTIES: [],  # 确保包含 properties 字段
                CLASS_METHODS: [],
                CLASS_EXTENDS: extends_info,
                CLASS_NAME: namespace_info.text.decode('utf-8'),
                CLASS_START_LINE: namespace_info.start_point[0] + 1,
                CLASS_END_LINE: namespace_info.end_point[0] + 1,
            }
            class_infos.append(current_namespace)

        elif current_class and 'method_name' in match_dict:
            method_info = match_dict['method_name'][0]
            method_body = match_dict['method_body'][0] if 'method_body' in match_dict else method_info
            method_name = method_info.text.decode('utf-8')
            
            # 获取方法可见性
            visibility = 'public'  # 默认可见性
            if 'method_visibility' in match_dict and match_dict['method_visibility'][0]:
                visibility = match_dict['method_visibility'][0].text.decode('utf-8')
            
            # 获取方法修饰符
            method_modifiers = []
            
            # 检查静态方法
            if 'is_static_method' in match_dict and match_dict['is_static_method'][0]:
                method_modifiers.append("static")
                
            # 检查抽象方法
            if 'is_abstract_method' in match_dict and match_dict['is_abstract_method'][0]:
                method_modifiers.append("abstract")
                
            # 检查final方法
            if 'is_final_method' in match_dict and match_dict['is_final_method'][0]:
                method_modifiers.append("final")
 
            # 获取返回值类型
            return_type = None
            if 'method_return_type' in match_dict and match_dict['method_return_type'][0]:
                return_type = match_dict['method_return_type'][0].text.decode('utf-8')
            
            current_method = {
                METHOD_NAME: method_name,
                METHOD_START_LINE: method_info.start_point[0] + 1,
                METHOD_END_LINE: method_body.end_point[0] + 1,
                METHOD_VISIBILITY: visibility,
                METHOD_MODIFIERS: method_modifiers,
                METHOD_OBJECT: current_class[CLASS_NAME],  # 添加方法所属类
                METHOD_FULL_NAME: f"{current_class[CLASS_NAME]}->{method_name}",  # 添加完整方法名
                METHOD_RETURN_TYPE: return_type,
                METHOD_RETURN_VALUE: return_type,  # 暂时与return_type相同
                METHOD_PARAMETERS: [],
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
                        param_value = None  # 添加参数值
                        for param_child in child.children:
                            if param_child.type == 'variable_name':
                                param_name = param_child.text.decode('utf-8')
                            elif param_child.type in ['primitive_type', 'name']:
                                param_type = param_child.text.decode('utf-8')
                            elif param_child.type == 'default_value':
                                param_value = param_child.text.decode('utf-8')
                            
                            if param_name and param_name not in seen_params:
                                seen_params.add(param_name)
                                method_param_type = {
                                    PARAMETER_NAME: param_name,
                                    PARAMETER_TYPE: param_type,
                                    PARAMETER_DEFAULT: None,
                                    PARAMETER_VALUE: param_value  # 添加参数值字段
                                }
                                current_method[METHOD_PARAMETERS].append(method_param_type)
            
            # 处理方法体中的函数调用
            if 'method_body' in match_dict:
                body_node = match_dict['method_body'][0]
                seen_called_functions = set()
                process_method_body_node(body_node, seen_called_functions, file_functions, current_method, current_class)
            
            current_class[CLASS_METHODS].append(current_method)
            
        elif current_class and 'property_name' in match_dict:
            # 获取属性可见性
            property_visibility = match_dict.get('property_visibility', [None])[0]
            visibility = property_visibility.text.decode('utf-8') if property_visibility else 'public'
            
            # 获取属性修饰符
            is_static = 'is_static' in match_dict and match_dict['is_static'][0] is not None
            is_readonly = 'is_readonly' in match_dict and match_dict['is_readonly'][0] is not None

            property_info = match_dict['property_name'][0]
            # 获取属性修饰符
            property_modifiers = []
            if is_static:
                property_modifiers.append("static")
            if is_readonly:
                property_modifiers.append("readonly")
            current_property = {
                PROPERTY_NAME: property_info.text.decode('utf-8'),
                PROPERTY_LINE: property_info.start_point[0] + 1,
                PROPERTY_TYPE: None,  # 添加属性类型字段
                PROPERTY_VISIBILITY: visibility,
                PROPERTY_MODIFIERS: property_modifiers,
                PROPERTY_INITIAL_VALUE: None
            }

            if 'property_value' in match_dict and match_dict['property_value'][0]:
                property_value = match_dict['property_value'][0]
                if property_value.type == 'integer':
                    current_property[PROPERTY_INITIAL_VALUE] = int(property_value.text.decode('utf-8'))
                    current_property[PROPERTY_TYPE] = 'integer'  # 设置属性类型
                else:
                    current_property[PROPERTY_INITIAL_VALUE] = property_value.text.decode('utf-8')
                    current_property[PROPERTY_TYPE] = property_value.type  # 设置属性类型
            
            current_class[CLASS_PROPERTIES].append(current_property)

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
                func_type = CUSTOM_METHOD
                if func_name in PHP_BUILTIN_FUNCTIONS:
                    func_type = BUILTIN_METHOD
                elif func_name in file_functions:
                    func_type = LOCAL_METHOD
                elif func_name.startswith('$'):
                    func_type = DYNAMIC_METHOD

                # 处理参数
                args_node = node.child_by_field_name('arguments')
                call_params = []
                if args_node:
                    param_index = 0
                    for arg in args_node.children:
                        # 跳过括号和逗号
                        if arg.type not in [',', '(', ')']:
                            arg_value = arg.text.decode('utf-8')
                            # 检查是否有显式的参数名指定
                            param_name = None
                            if arg.type == 'named_argument':
                                name_node = arg.child_by_field_name('name')
                                if name_node:
                                    param_name = name_node.text.decode('utf-8')
                                value_node = arg.child_by_field_name('value')
                                if value_node:
                                    arg_value = value_node.text.decode('utf-8')
                            
                            # 处理参数值，去掉字符串的引号
                            if arg_value.startswith('"') and arg_value.endswith('"'):
                                arg_value = arg_value[1:-1]
                            elif arg_value.startswith("'") and arg_value.endswith("'"):
                                arg_value = arg_value[1:-1]
                            
                            call_params.append({
                                PARAMETER_NAME: param_name if param_name else f"$arg{param_index}",
                                PARAMETER_TYPE: None,
                                PARAMETER_DEFAULT: None,
                                PARAMETER_VALUE: arg_value
                            })
                            param_index += 1
                call_info = {
                    METHOD_NAME: func_name,
                    METHOD_START_LINE: node.start_point[0] + 1,
                    METHOD_END_LINE: node.end_point[0] + 1,
                    METHOD_OBJECT: None,  # 函数调用没有对象
                    METHOD_FULL_NAME: func_name,
                    METHOD_TYPE: func_type,
                    METHOD_MODIFIERS: [],
                    METHOD_RETURN_TYPE: None,
                    METHOD_RETURN_VALUE: None,
                    METHOD_PARAMETERS: call_params
                }
                current_method[CALLED_METHODS].append(call_info)

    elif node.type == 'member_call_expression':
        object_node = node.child_by_field_name('object')
        name_node = node.child_by_field_name('name')
        if object_node and name_node:
            object_name = object_node.text.decode('utf-8')
            method_name = name_node.text.decode('utf-8')
            
            # 处理参数
            args_node = node.child_by_field_name('arguments')
            call_params = []
            if args_node:
                for arg in args_node.children:
                    # 跳过括号和逗号
                    if arg.type not in [',', '(', ')']:
                        arg_value = arg.text.decode('utf-8')
                        call_params.append({
                            PARAMETER_NAME: arg_value,
                            PARAMETER_TYPE: None,
                            PARAMETER_DEFAULT: None,
                            PARAMETER_VALUE: arg_value
                        })

            call_info = {
                METHOD_OBJECT: object_name,
                METHOD_NAME: method_name,
                METHOD_FULL_NAME: f"{object_name}->{method_name}",
                METHOD_START_LINE: name_node.start_point[0] + 1,
                METHOD_END_LINE: name_node.end_point[0] + 1,
                METHOD_TYPE: CLASS_METHOD,
                METHOD_MODIFIERS: [],
                METHOD_RETURN_TYPE: None,
                METHOD_RETURN_VALUE: None,
                METHOD_PARAMETERS: call_params
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
