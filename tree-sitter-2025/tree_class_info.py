from typing import List, Dict, Any

from init_tree_sitter import init_php_parser
from libs_com.file_io import read_file_bytes
from libs_com.utils_json import print_json
from tree_const import *
from tree_enums import MethodType, PHPVisibility, PHPModifier


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
            body: (declaration_list)? @namespace_body
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
            (visibility_modifier)? @property_visibility
            (static_modifier)? @is_static
            (readonly_modifier)? @is_readonly
            (property_element
                name: (variable_name) @property_name
                (
                    "="
                    (_) @property_value
                )?
            )+
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
    current_namespace = None
    namespace_stack = []  # 添加命名空间栈
    
    for pattern_index, match_dict in class_info_matches:
        # 添加调试信息
        print("Pattern match type:", [key for key in match_dict.keys()])
        
        # 获取命名空间信息
        if 'namespace_name' in match_dict:
            current_namespace = match_dict['namespace_name'][0].text.decode('utf-8')
            print("Found namespace:", current_namespace)
            
            # 检查是否有命名空间体
            if 'namespace_body' in match_dict and match_dict['namespace_body'][0]:
                # 大括号语法
                namespace_stack.append(current_namespace)
            continue
            
        # 处理类信息时使用当前命名空间
        if 'class_name' in match_dict:
            # 如果命名空间栈非空，使用栈顶命名空间
            active_namespace = namespace_stack[-1] if namespace_stack else current_namespace
            current_class = process_class_interface_info(match_dict, active_namespace)
            if current_class:
                class_infos.append(current_class)
                print("Added class:", current_class[CLASS_NAME], "in namespace:", active_namespace)
        
        # 处理方法和属性
        if current_class:
            if 'method_name' in match_dict:
                process_method_info(match_dict, current_class, file_functions)
                print("Added method:", match_dict['method_name'][0].text.decode('utf-8'))
            
            if 'property_name' in match_dict:
                process_property_info(match_dict, current_class)
                print("Added property:", match_dict['property_name'][0].text.decode('utf-8'))
        
    return class_infos


def process_class_interface_info(match_dict, current_namespace):
    # 添加调试信息
    print("Processing class/interface info:", match_dict.keys())
    extends_info = match_dict['extends'][0].text.decode('utf-8') if 'extends' in match_dict else None

    if 'class_name' in match_dict:
        class_info = match_dict['class_name'][0]
        class_body = match_dict['class_body'][0]  # 获取类体节点
        # 获取类的可见性
        visibility = PHPVisibility.PUBLIC.value  # 默认可见性
        if 'class_visibility' in match_dict and match_dict['class_visibility'][0]:
            visibility = match_dict['class_visibility'][0].text.decode('utf-8')

        # 获取类的修饰符
        class_modifiers = []
        if 'is_abstract_class' in match_dict and match_dict['is_abstract_class'][0]:
            class_modifiers.append(PHPModifier.ABSTRACT.value)
        if 'is_final_class' in match_dict and match_dict['is_final_class'][0]:
            class_modifiers.append(PHPModifier.FINAL.value)

        return {
            CLASS_NAME: class_info.text.decode('utf-8'),
            CLASS_NAMESPACE: current_namespace if current_namespace else "",
            CLASS_VISIBILITY: visibility,
            CLASS_MODIFIERS: class_modifiers,
            CLASS_START_LINE: class_info.start_point[0] + 1,
            CLASS_END_LINE: class_body.end_point[0] + 1,  # 使用类体的结束行号
            CLASS_EXTENDS: [{extends_info: None}] if extends_info else [{None: None}],  # 修改这里
            CLASS_INTERFACES: [{None: None}],  # 修改这里
            CLASS_METHODS: [],
            CLASS_PROPERTIES: [],
        }

    elif 'interface_name' in match_dict:
        interface_info = match_dict['interface_name'][0]
        return {
            CLASS_NAME: interface_info.text.decode('utf-8'),
            CLASS_NAMESPACE: current_namespace,
            CLASS_VISIBILITY: 'public',
            CLASS_MODIFIERS: [PHPModifier.INTERFACE.value],
            CLASS_START_LINE: interface_info.start_point[0] + 1,
            CLASS_END_LINE: interface_info.end_point[0] + 1,
            CLASS_EXTENDS: [{extends_info: None}] if extends_info else [{None: None}],  # 修改这里
            CLASS_INTERFACES: [{None: None}],  # 修改这里
            CLASS_PROPERTIES: [],
            CLASS_METHODS: [],
        }

    return None

def process_method_info(match_dict, current_class, file_functions):
    if not (current_class and 'method_name' in match_dict):
        return
        
    method_info = match_dict['method_name'][0]
    method_body = match_dict['method_body'][0] if 'method_body' in match_dict else method_info
    method_name = method_info.text.decode('utf-8')
    
    # 获取方法可见性和修饰符
    visibility = PHPVisibility.PUBLIC.value
    if 'method_visibility' in match_dict and match_dict['method_visibility'][0]:
        visibility = match_dict['method_visibility'][0].text.decode('utf-8')
    
    method_modifiers = []
    if 'is_static_method' in match_dict and match_dict['is_static_method'][0]:
        method_modifiers.append(PHPModifier.STATIC.value)
    if 'is_abstract_method' in match_dict and match_dict['is_abstract_method'][0]:
        method_modifiers.append(PHPModifier.ABSTRACT.value)
    if 'is_final_method' in match_dict and match_dict['is_final_method'][0]:
        method_modifiers.append(PHPModifier.FINAL.value)

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
        METHOD_OBJECT: current_class[CLASS_NAME],
        METHOD_FULL_NAME: f"{current_class[CLASS_NAME]}->{method_name}",
        METHOD_RETURN_TYPE: return_type,
        METHOD_RETURN_VALUE: return_type,
        METHOD_PARAMETERS: [],
        CALLED_METHODS: []
    }
    
    # 处理方法参数
    if 'method_params' in match_dict:
        params_node = match_dict['method_params'][0]
        seen_params = set()
        for child in params_node.children:
            if child.type == 'simple_parameter':
                param_name = None
                param_type = None
                param_value = None
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
                            PARAMETER_VALUE: param_value
                        }
                        current_method[METHOD_PARAMETERS].append(method_param_type)
    
    # 处理方法体中的函数调用
    if 'method_body' in match_dict:
        body_node = match_dict['method_body'][0]
        seen_called_functions = set()
        process_method_body_node(body_node, seen_called_functions, file_functions, current_method, current_class)
    
    current_class[CLASS_METHODS].append(current_method)

def process_property_info(match_dict, current_class):
    if not (current_class and 'property_name' in match_dict):
        return
        
    property_visibility = match_dict.get('property_visibility', [None])[0]
    visibility = property_visibility.text.decode('utf-8') if property_visibility else PHPVisibility.PUBLIC.value
    
    is_static = 'is_static' in match_dict and match_dict['is_static'][0] is not None
    is_readonly = 'is_readonly' in match_dict and match_dict['is_readonly'][0] is not None

    property_info = match_dict['property_name'][0]
    property_modifiers = []
    if is_static:
        property_modifiers.append(PHPModifier.STATIC.value)
    if is_readonly:
        property_modifiers.append(PHPModifier.READONLY.value)

    current_property = {
        PROPERTY_NAME: property_info.text.decode('utf-8'),
        PROPERTY_LINE: property_info.start_point[0] + 1,
        PROPERTY_TYPE: None,
        PROPERTY_VISIBILITY: visibility,
        PROPERTY_MODIFIERS: property_modifiers,
        PROPERTY_INITIAL_VALUE: None
    }

    if 'property_value' in match_dict and match_dict['property_value'][0]:
        property_value = match_dict['property_value'][0]
        print("Debug - Property value node:", {
            'type': property_value.type,
            'text': property_value.text.decode('utf-8'),
            'start_point': property_value.start_point,
            'end_point': property_value.end_point,
            'children_types': [child.type for child in property_value.children]
        })
        
        if property_value.type == 'integer':
            print("Debug - Processing integer value")
            current_property[PROPERTY_INITIAL_VALUE] = int(property_value.text.decode('utf-8'))
            current_property[PROPERTY_TYPE] = 'integer'
        elif property_value.type == 'string':
            print("Debug - Processing string value")
            value = property_value.text.decode('utf-8').strip('"\'')
            current_property[PROPERTY_INITIAL_VALUE] = value
            current_property[PROPERTY_TYPE] = 'string'
        elif property_value.type == 'float':
            print("Debug - Processing float value")
            current_property[PROPERTY_INITIAL_VALUE] = float(property_value.text.decode('utf-8'))
            current_property[PROPERTY_TYPE] = 'float'
        elif property_value.type == 'null':
            print("Debug - Processing null value")
            current_property[PROPERTY_INITIAL_VALUE] = None
            current_property[PROPERTY_TYPE] = 'null'
        elif property_value.type == 'boolean':
            print("Debug - Processing boolean value")
            value = property_value.text.decode('utf-8').lower()
            current_property[PROPERTY_INITIAL_VALUE] = value == 'true'
            current_property[PROPERTY_TYPE] = 'boolean'
        else:
            print("Debug - Processing unknown type:", property_value.type)
            current_property[PROPERTY_INITIAL_VALUE] = property_value.text.decode('utf-8')
            current_property[PROPERTY_TYPE] = property_value.type
    else:
        print("Debug - No property value found in match_dict")

    print("Debug - Final property:", current_property)
    current_class[CLASS_PROPERTIES].append(current_property)

def process_method_body_node(node, seen_called_functions, file_functions, current_method, current_class):
    if node.type == 'function_call_expression':
        func_node = node.child_by_field_name('function')
        if func_node:
            func_name = func_node.text.decode('utf-8')
            call_key = f"{func_name}:{node.start_point[0]}"
            if call_key not in seen_called_functions:
                seen_called_functions.add(call_key)
                # 修改函数类型判断逻辑
                func_type = MethodType.CUSTOM_METHOD.value
                if func_name in PHP_BUILTIN_FUNCTIONS:
                    func_type = MethodType.BUILTIN_METHOD.value
                elif func_name in file_functions:
                    func_type = MethodType.LOCAL_METHOD.value
                elif func_name.startswith('$'):
                    func_type = MethodType.DYNAMIC_METHOD.value

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
                METHOD_TYPE: MethodType.CLASS_METHOD.value,
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
    php_file = r"php_demo\multi_namespace.php"
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
