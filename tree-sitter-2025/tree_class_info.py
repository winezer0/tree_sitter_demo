from ftplib import all_errors
from sre_parse import TYPE_FLAGS
from typing import List, Dict, Any, TYPE_CHECKING
from init_tree_sitter import init_php_parser
from libs_com.file_io import read_file_bytes
from tree_const import BUILTIN_METHOD, CALLED_FUNCTIONS, CLASSES
from tree_func_info import PHP_BUILTIN_FUNCTIONS

CLASS_TYPE = 'type'
CLASS_PROPERTIES = 'properties'
CLASS_METHODS = 'methods'
CLASS_DEPENDENCIES = 'dependencies'
CLASS_EXTENDS = 'extends'
TYPE_CLASS = 'class'
TYPE_INTERFACE = 'interface'
TYPE_NAMESPACE = 'namespace'


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

    # 修改函数调用解析部分
    class_info_matches = class_info_query.matches(tree.root_node)
    current_class = None
    current_method = None

    for pattern_index, match_dict in class_info_matches:
        # 修改类信息提取部分
        if 'class_name' in match_dict:
            current_class = {
                'name': match_dict['class_name'][0].text.decode('utf-8'),
                'line': match_dict['class_name'][0].start_point[0] + 1,
                CLASS_PROPERTIES: [],  # 确保包含 properties 字段
                CLASS_METHODS: [],
                CLASS_DEPENDENCIES: set(),  # 初始化依赖集合
                CLASS_EXTENDS: match_dict['extends'][0].text.decode('utf-8') if 'extends' in match_dict else None,
                CLASS_TYPE: TYPE_CLASS
            }
            class_infos.append(current_class)
            
        elif 'interface_name' in match_dict:
            current_interface = {
                'name': match_dict['interface_name'][0].text.decode('utf-8'),
                'line': match_dict['interface_name'][0].start_point[0] + 1,
                CLASS_PROPERTIES: [],  # 确保包含 properties 字段
                CLASS_METHODS: [],
                CLASS_DEPENDENCIES: set(),  # 初始化依赖集合
                CLASS_EXTENDS: match_dict['extends'][0].text.decode('utf-8') if 'extends' in match_dict else None,
                CLASS_TYPE: TYPE_INTERFACE
            }
            class_infos.append(current_interface)
            
        elif 'namespace_name' in match_dict:
            namespace = {
                'name': match_dict['namespace_name'][0].text.decode('utf-8'),
                'line': match_dict['namespace_name'][0].start_point[0] + 1,
                CLASS_DEPENDENCIES: set(),  # 添加依赖集合
                CLASS_PROPERTIES: [],       # 添加属性字段
                CLASS_METHODS: [],          # 添加方法字段
                CLASS_TYPE: TYPE_NAMESPACE
            }
            class_infos.append(namespace)
            
        elif current_class and 'method_name' in match_dict:
            method_name = match_dict['method_name'][0].text.decode('utf-8')
            visibility = match_dict.get('method_visibility', [None])[0]
            visibility = visibility.text.decode('utf-8') if visibility else 'public'
            
            is_static = 'is_static_method' in match_dict and match_dict['is_static_method'][0] is not None
            
            current_method = {
                'name': method_name,
                'visibility': visibility,
                'static': is_static,
                'line': match_dict['method_name'][0].start_point[0] + 1,
                'parameters': [],
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
                                current_method['parameters'].append({
                                    'name': param_name,
                                    CLASS_TYPE: param_type
                                })
            
            # 处理方法体中的函数调用
            if 'method_body' in match_dict:
                body_node = match_dict['method_body'][0]
                seen_called_functions = set()
                
                def process_node(node):
                    if node.type == 'function_call_expression':
                        func_node = node.child_by_field_name('function')
                        if func_node:
                            func_name = func_node.text.decode('utf-8')
                            call_key = f"{func_name}:{node.start_point[0]}"
                            if func_name != 'echo' and call_key not in seen_called_functions:
                                seen_called_functions.add(call_key)
                                # 修改函数类型判断逻辑
                                func_type = 'custom'  # 默认为自定义函数
                                if func_name in PHP_BUILTIN_FUNCTIONS:
                                    func_type = BUILTIN_METHOD  # PHP内置函数
                                elif func_name in file_functions:
                                    func_type = 'local'    # 本地定义的函数
                                elif func_name.startswith('$'):
                                    func_type = 'dynamic'  # 动态函数调用
                                
                                # 只记录非内置函数的调用
                                if func_type != 'builtin':
                                    call_info = {
                                        'name': func_name,
                                        CLASS_TYPE: func_type,
                                        'call_type': 'function',
                                        'line': node.start_point[0] + 1
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
                                'name': f"{object_name}->{method_name}",
                                CLASS_TYPE: 'object_method',
                                'object': object_name,
                                'method': method_name,
                                'call_type': 'method',
                                'line': node.start_point[0] + 1
                            }
                            current_method[CALLED_FUNCTIONS].append(call_info)
                    
                    for child in node.children:
                        process_node(child)
                
                process_node(body_node)
            
            current_class[CLASS_METHODS].append(current_method)
            
        elif current_class and 'property_name' in match_dict:
            visibility = match_dict.get('property_visibility', [None])[0]
            visibility = visibility.text.decode('utf-8') if visibility else 'public'
            
            is_static = 'is_static' in match_dict and match_dict['is_static'][0] is not None
            
            property_info = {
                'name': match_dict['property_name'][0].text.decode('utf-8'),
                'visibility': visibility,
                'static': is_static,
                'line': match_dict['property_name'][0].start_point[0] + 1
            }
            
            if 'property_value' in match_dict and match_dict['property_value'][0]:
                property_value = match_dict['property_value'][0]
                if property_value.type == 'integer':
                    property_info['value'] = int(property_value.text.decode('utf-8'))
                else:
                    property_info['value'] = property_value.text.decode('utf-8')
            
            current_class[CLASS_PROPERTIES].append(property_info)

    # 将依赖集合转换为列表
    for class_info in class_infos:
        class_info[CLASS_DEPENDENCIES] = [{'name': name, CLASS_TYPE: dep_type} for name, dep_type in class_info[CLASS_DEPENDENCIES]]
    
    return class_infos


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
def print_class_info(classes: List[Dict[str, Any]]):
    """打印类信息"""
    for class_info in classes:
        print(f"\n类名: {class_info['name']}")
        print(f"  定义行号: {class_info['line']}")

        if class_info[CLASS_DEPENDENCIES]:
            print("\n  依赖函数:")
            for dep in class_info[CLASS_DEPENDENCIES]:
                print(f"    - {dep}")

        print("\n  属性:")
        for prop in class_info['properties']:
            print(f"    {prop['name']}")
            print(f"      可见性: {prop['visibility']}")
            print(f"      静态: {prop['static']}")
            print(f"      行号: {prop['line']}")
            if 'value' in prop:
                print(f"      默认值: {prop['value']}")

        print("\n  方法:")
        for method in class_info['methods']:
            print(f"    {method['name']}")
            print(f"      可见性: {method['visibility']}")
            print(f"      静态: {method['static']}")
            print(f"      行号: {method['line']}")
            if method['parameters']:
                params_str = ', '.join([
                    f"{param['name']}" + (f": {param['type']}" if param['type'] else '')
                    for param in method['parameters']
                ])
                print(f"      参数: {params_str}")
            if method[CALLED_FUNCTIONS]:
                print("      调用:")
                for call in method[CALLED_FUNCTIONS]:
                    if call['type'] == 'function':
                        print(f"        - 函数: {call['name']} (行 {call['line']})")
                    elif call['type'] == 'object_method':
                        print(f"        - 方法: {call['object']}->{call['method']} (行 {call['line']})")
                    else:
                        print(f"        - 调用: {call.get('name', '未知')} (行 {call['line']})")


if __name__ == '__main__':
    # php_file = r"php_demo\class.php"
    php_file = r"php_demo\extends.php"
    # php_file = r"php_demo\interface.php"
    PARSER, LANGUAGE = init_php_parser()
    php_file_bytes = read_file_bytes(php_file)
    php_file_tree = PARSER.parse(php_file_bytes)
    # print(php_file_tree.root_node)
    classes = extract_class_info(php_file_tree, LANGUAGE)
    print(classes)
    print_class_info(classes)