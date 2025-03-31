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
    
    # 定义超全局变量列表
    SUPERGLOBALS = ['$_GET', '$_POST', '$_REQUEST', '$_SESSION', 
                    '$_COOKIE', '$_SERVER', '$_FILES', '$_ENV', '$GLOBALS']
    
    # 查询变量声明和使用
    query = language.query("""
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
        
        (static_variable_declaration
            (variable_name) @static_var
        )
        
        (global_declaration
            (variable_name) @global_var
        )
        
        (member_access_expression
            (variable_name) @array_name
            (name) @key_name
        )
        
        (subscript_expression
            (variable_name) @array_name
            (_) @key_name
        )
    """)
    
    matches = query.matches(tree.root_node)
    current_function = None
    processed_vars = set()
    
    for match in matches:
        pattern_index, match_dict = match
        
        # 更新当前函数上下文
        if 'function_name' in match_dict:
            current_function = match_dict['function_name'][0].text.decode('utf-8')
            
        for capture_name, nodes in match_dict.items():
            if capture_name not in ['assigned_var', 'static_var', 'global_var', 'array_name']:
                continue
                
            node = nodes[0]
            var_name = node.text.decode('utf-8')
            var_key = f"{var_name}:{current_function}"
            
            if var_key in processed_vars:
                continue
                
            # 处理超全局变量
            if var_name in SUPERGLOBALS:
                key_name = None
                if 'key_name' in match_dict:
                    key_node = match_dict['key_name'][0]
                    key_name = key_node.text.decode('utf-8')
                
                variables.append({
                    'type': 'superglobal',
                    'variable': var_name,
                    'key': key_name,
                    'line': node.start_point[0] + 1,
                    'function': current_function,
                    'value': None
                })
                processed_vars.add(var_key)
                continue
            
            # 确定变量类型
            var_type = 'local'
            current_node = node
            while current_node and current_node.type != 'function_definition':
                if current_node.type == 'static_variable_declaration':
                    var_type = 'static'
                    break
                if current_node.type == 'global_declaration':
                    var_type = 'global'
                    break
                current_node = current_node.parent
            
            if not current_node or current_node.type != 'function_definition':
                var_type = 'file_level'
            
            # 获取变量值
            value = None
            if 'var_value' in match_dict:
                value = format_value(match_dict['var_value'][0].text.decode('utf-8'))
            
            variables.append({
                'type': var_type,
                'variable': var_name,
                'line': node.start_point[0] + 1,
                'function': current_function,
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