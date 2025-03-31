from typing import List, Dict, Any
from init_tree_sitter import init_php_parser
from libs_com.file_io import read_file_bytes

def format_value(value: str) -> Any:
    """格式化提取的值，去除引号等处理"""
    if not value:
        return None
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value

def extract_variables(tree, language) -> List[Dict[str, Any]]:
    """提取所有变量声明和使用"""
    variables = []
    
    # 添加类相关的查询
    query = language.query("""
        ; 添加成员访问表达式的匹配
        (member_access_expression
            object: (variable_name) @object_var
            name: (name) @member_name
        )

        ; 添加文件级变量赋值匹配
        (program
            (expression_statement
                (assignment_expression
                    left: (variable_name) @file_var
                    right: (_) @file_var_value
                )
            )
        )

        ; 保持原有的查询
        (class_declaration
            name: (name) @class_name
            body: (declaration_list) @class_body
        ) @class

        (property_declaration
            (visibility_modifier)? @property_visibility
            (static_modifier)? @is_static
            (property_element
                name: (variable_name) @property_name
                value: (_)? @property_value
            )
        )

        (method_declaration
            name: (name) @method_name
            body: (compound_statement) @method_body
        ) @method

        ; 原有的变量查询部分保持不变
        (function_definition
            name: (name) @function_name
            body: (compound_statement) @function_body
        ) @function
        
        (expression_statement
            (assignment_expression
                left: (variable_name) @assigned_var
                right: (_) @var_value
            )
        )
    """)
    
    matches = query.matches(tree.root_node)
    current_class = None
    current_method = None
    current_function = None
    processed_vars = set()
    
    for match in matches:
        pattern_index, match_dict = match
        
        # 处理文件级变量
        if 'file_var' in match_dict:
            node = match_dict['file_var'][0]
            var_name = node.text.decode('utf-8')
            value = None
            if 'file_var_value' in match_dict:
                value = format_value(match_dict['file_var_value'][0].text.decode('utf-8'))
            
            variables.append({
                'type': 'file_level',
                'variable': var_name,
                'line': node.start_point[0] + 1,
                'context': None,
                'value': value
            })
            continue

        # 更新类上下文
        if 'class_name' in match_dict:
            current_class = match_dict['class_name'][0].text.decode('utf-8')
            current_method = None
        
        # 更新方法上下文
        elif 'method_name' in match_dict:
            current_method = match_dict['method_name'][0].text.decode('utf-8')
            current_function = None
        
        # 更新函数上下文
        elif 'function_name' in match_dict:
            current_function = match_dict['function_name'][0].text.decode('utf-8')
            current_class = None
            current_method = None
        
        for capture_name, nodes in match_dict.items():
            if capture_name not in ['assigned_var', 'property_name']:
                continue
            
            node = nodes[0]
            var_name = node.text.decode('utf-8')
            
            # 特殊处理 $this
            if var_name == '$this' and current_class and current_method:
                continue  # 跳过 $this 的记录
            
            # 先确定变量类型和上下文
            if current_class:
                if capture_name == 'property_name':
                    var_type = 'class_property'
                    context = current_class
                elif current_method:
                    var_type = 'method_local'
                    context = f"{current_class}::{current_method}"
                else:
                    var_type = 'class_level'
                    context = current_class
            elif current_function:
                var_type = 'local'
                context = current_function
            else:
                var_type = 'file_level'
                context = None
            
            # 修改变量去重逻辑
            def get_var_key(var_name, var_type, context):
                return f"{var_name}:{var_type}:{context}"
            
            # 在处理变量时
            var_key = get_var_key(var_name, var_type, context)
            if var_key in processed_vars:
                continue
            
            # 获取变量值
            value = None
            if 'var_value' in match_dict:
                value = format_value(match_dict['var_value'][0].text.decode('utf-8'))
            
            variables.append({
                'type': var_type,
                'variable': var_name,
                'line': node.start_point[0] + 1,
                'context': context,
                'value': value
            })
            processed_vars.add(var_key)
    
    return variables

def analyze_php_variables(tree, language) -> Dict[str, List[Dict[str, Any]]]:
    """分析PHP文件中的所有变量"""
    variables = extract_variables(tree, language)
    
    # 按类型分组
    result = {
        'local': [],
        'static': [],
        'superglobal': [],
        'global': []
    }
    
    for var in variables:
        var_type = var['type']
        if var_type == 'file_level':
            result['global'].append(var)
        else:
            result[var_type].append(var)
    
    return result

def print_variable_info(var_list: List[Dict], title: str):
    """打印变量信息"""
    print(f"\n{title}:")
    for var in var_list:
        print("  变量:", var['variable'])
        print("    行号:", var['line'])
        print("    函数:", var['function'] or '文件级别')
        print("    类型:", var['type'])
        if 'key' in var:
            print("    键名:", var['key'])
        print("    值:", var['value'])
        print()

if __name__ == '__main__':
    php_file = r"php_demo\back.php"
    PARSER, LANGUAGE = init_php_parser()
    php_file_bytes = read_file_bytes(php_file)
    php_file_tree = PARSER.parse(php_file_bytes)
    variables = analyze_php_variables(php_file_tree, LANGUAGE)
    
    print_variable_info(variables['local'], "局部变量")
    print_variable_info(variables['global'], "全局变量")
    print_variable_info(variables['static'], "静态变量")
    print_variable_info(variables['superglobal'], "超全局变量")