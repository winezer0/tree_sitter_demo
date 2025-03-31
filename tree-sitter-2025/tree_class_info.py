from typing import List, Dict, Any
from init_tree_sitter import init_php_parser
from libs_com.file_io import read_file_bytes

def extract_class_info(tree, language) -> List[Dict[str, Any]]:
    """提取所有类定义信息"""
    classes = []
    
    # 扩展查询语法，添加函数调用匹配
    query = language.query("""
        (class_declaration
            name: (name) @class_name
            body: (declaration_list) @class_body
        )
        
        (property_declaration
            (visibility_modifier) @property_visibility
            (static_modifier)? @is_static
            (property_element
                name: (variable_name) @property_name
                value: (_)? @property_value
            )
        )
        
        (method_declaration
            (visibility_modifier)? @method_visibility
            (static_modifier)? @is_static_method
            name: (name) @method_name
            parameters: (formal_parameters) @method_params
            body: (compound_statement) @method_body
        )

        (function_call_expression
            function: (name) @called_function
            arguments: (arguments) @call_args
        )

        (member_call_expression
            object: (_) @object
            name: (name) @method_call
            arguments: (arguments) @method_args
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
                'dependencies': []  # 添加依赖列表
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
                'calls': []  # 添加函数调用列表
            }
            
            # 解析方法参数
            if 'method_params' in match_dict:
                params_node = match_dict['method_params'][0]
                current_method['parameters'] = [
                    param.text.decode('utf-8')
                    for param in params_node.children
                    if param.type == 'parameter'
                ]
            
            current_class['methods'].append(current_method)
            
        # 处理函数调用
        elif current_method and 'called_function' in match_dict:
            func_name = match_dict['called_function'][0].text.decode('utf-8')
            current_method['calls'].append({
                'type': 'function',
                'name': func_name,
                'line': match_dict['called_function'][0].start_point[0] + 1
            })
            current_class['dependencies'].append(func_name)
            
        # 处理方法调用
        elif current_method and 'method_call' in match_dict:
            method_name = match_dict['method_call'][0].text.decode('utf-8')
            object_node = match_dict['object'][0]
            object_text = object_node.text.decode('utf-8')
            
            current_method['calls'].append({
                'type': 'method',
                'object': object_text,
                'name': method_name,
                'line': match_dict['method_call'][0].start_point[0] + 1
            })
            
        # 处理类属性保持不变...
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
            
        # 处理类方法
        elif current_class and 'method_name' in match_dict:
            visibility = match_dict.get('method_visibility', [None])[0]
            visibility = visibility.text.decode('utf-8') if visibility else 'public'
            
            is_static = 'is_static_method' in match_dict and match_dict['is_static_method'][0] is not None
            
            method_info = {
                'name': match_dict['method_name'][0].text.decode('utf-8'),
                'visibility': visibility,
                'static': is_static,
                'line': match_dict['method_name'][0].start_point[0] + 1
            }
            
            # 解析方法参数
            if 'method_params' in match_dict:
                params_node = match_dict['method_params'][0]
                method_info['parameters'] = [
                    param.text.decode('utf-8')
                    for param in params_node.children
                    if param.type == 'parameter'
                ]
            
            current_class['methods'].append(method_info)
    
    # 去重依赖列表
    for class_info in classes:
        class_info['dependencies'] = list(set(class_info['dependencies']))
    
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
            if 'parameters' in method:
                print(f"      参数: {', '.join(method['parameters'])}")
            if method['calls']:
                print("      调用:")
                for call in method['calls']:
                    if call['type'] == 'function':
                        print(f"        - 函数: {call['name']} (行 {call['line']})")
                    else:
                        print(f"        - 方法: {call['object']}->{call['name']} (行 {call['line']})")

def analyze_php_classes(php_file: str) -> List[Dict[str, Any]]:
    """分析PHP文件中的类定义"""
    PARSER, LANGUAGE = init_php_parser()
    php_file_bytes = read_file_bytes(php_file)
    php_file_tree = PARSER.parse(php_file_bytes)
    
    return extract_class_info(php_file_tree, LANGUAGE)

def print_class_info(classes: List[Dict[str, Any]]):
    """打印类信息"""
    for class_info in classes:
        print(f"\n类名: {class_info['name']}")
        print(f"  定义行号: {class_info['line']}")
        
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
            if 'parameters' in method:
                print(f"      参数: {', '.join(method['parameters'])}")

if __name__ == '__main__':
    php_file = r"php_demo\class.php"
    classes = analyze_php_classes(php_file)
    print_class_info(classes)