from typing import List, Dict, Any
from init_tree_sitter import init_php_parser
from libs_com.file_io import read_file_bytes

def extract_class_info(tree, language) -> List[Dict[str, Any]]:
    """提取所有类定义信息"""
    classes = []
    
    # 修改查询语法，简化参数匹配
    query = language.query("""
        (class_declaration
            name: (name) @class_name
            body: (declaration_list) @class_body
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

        ; 添加 echo 语句中的函数调用匹配
        (echo_statement
            (function_call_expression
                function: (name) @echo_function_call
                arguments: (arguments) @echo_function_args
            )
        )
    """)
    
    matches = query.matches(tree.root_node)
    current_class = None
    current_method = None
    
    for match in matches:
        pattern_index, match_dict = match
        
        # 处理类定义
        if 'class_name' in match_dict:
            current_class = {
                'name': match_dict['class_name'][0].text.decode('utf-8'),
                'line': match_dict['class_name'][0].start_point[0] + 1,
                'properties': [],
                'methods': [],
                'dependencies': set()  # 使用集合避免重复
            }
            classes.append(current_class)
            
        # 处理类方法
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
                'calls': []
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
                                    'type': param_type
                                })
            
            # 修改函数调用解析部分
            if 'method_body' in match_dict:
                body_node = match_dict['method_body'][0]
                seen_calls = set()  # 用于去重
                def process_node(node):
                    if node.type == 'function_call_expression':
                        func_node = node.child_by_field_name('function')
                        if func_node:
                            func_name = func_node.text.decode('utf-8')
                            call_key = f"{func_name}:{node.start_point[0]}"
                            if func_name != 'echo' and call_key not in seen_calls:
                                seen_calls.add(call_key)
                                current_method['calls'].append({
                                    'type': 'function',
                                    'name': func_name,
                                    'line': node.start_point[0] + 1
                                })
                                current_class['dependencies'].add(func_name)
                    elif node.type == 'member_call_expression':
                        object_node = node.child_by_field_name('object')
                        name_node = node.child_by_field_name('name')
                        if object_node and name_node:
                            current_method['calls'].append({
                                'type': 'method',
                                'object': object_node.text.decode('utf-8'),
                                'name': name_node.text.decode('utf-8'),
                                'line': node.start_point[0] + 1
                            })
                    elif node.type == 'echo_statement':
                        for child in node.children:
                            if child.type == 'function_call_expression':
                                process_node(child)
                    
                    for child in node.children:
                        process_node(child)
                
                process_node(body_node)
            
            current_class['methods'].append(current_method)
            
        # 处理类属性（保持不变）...
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
                property_info['value'] = match_dict['property_value'][0].text.decode('utf-8')
            
            current_class['properties'].append(property_info)
            pass
    
    # 将依赖集合转换为列表
    for class_info in classes:
        class_info['dependencies'] = list(class_info['dependencies'])
    
    return classes



# 修改打印函数以显示调用信息
def print_class_info(classes: List[Dict[str, Any]]):
    """打印类信息"""
    for class_info in classes:
        print(f"\n类名: {class_info['name']}")
        print(f"  定义行号: {class_info['line']}")

        if class_info['dependencies']:
            print("\n  依赖函数:")
            for dep in class_info['dependencies']:
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
            if method['calls']:
                print("      调用:")
                for call in method['calls']:
                    if call['type'] == 'function':
                        print(f"        - 函数: {call['name']} (行 {call['line']})")
                    else:
                        print(f"        - 方法: {call['object']}->{call['name']} (行 {call['line']})")


if __name__ == '__main__':
    php_file = r"php_demo\class.php"
    PARSER, LANGUAGE = init_php_parser()
    php_file_bytes = read_file_bytes(php_file)
    php_file_tree = PARSER.parse(php_file_bytes)
    # print(php_file_tree.root_node)
    classes = extract_class_info(php_file_tree, LANGUAGE)
    print(classes)
    # print_class_info(classes)