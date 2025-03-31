from typing import List, Dict, Any

# 常量定义
SUPERGLOBALS = [
    '$_GET', '$_POST', '$_REQUEST', '$_SESSION', 
    '$_COOKIE', '$_SERVER', '$_FILES', '$_ENV', '$GLOBALS'
]

def format_value(value: str) -> str:
    """格式化提取的值，去除引号等处理"""
    if not value:
        return None
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value

def determine_variable_type(node, global_vars) -> str:
    """确定变量类型"""
    var_name = node.text.decode('utf-8')
    
    if var_name in SUPERGLOBALS:
        return 'superglobal'
    
    current_node = node
    while current_node:
        if current_node.type == 'static_variable_declaration':
            return 'static'
        elif current_node.type == 'global_declaration':
            return 'global'
        elif current_node.type == 'function_definition':
            if var_name in global_vars:
                return 'global'
            if node.parent and node.parent.type == 'assignment_expression':
                right_node = node.parent.child_by_field_name('right')
                if right_node and right_node.type == 'subscript_expression':
                    array_name = right_node.child_by_field_name('array')
                    if array_name and array_name.text.decode('utf-8') in SUPERGLOBALS:
                        return 'local'
            return 'local'
        current_node = current_node.parent
    
    return 'global'

def create_variable_info(node, current_function, match_dict, global_vars) -> Dict[str, Any]:
    """创建变量信息字典"""
    var_name = node.text.decode('utf-8')
    
    var_info = {
        'variable': var_name,
        'line': node.start_point[0] + 1,
        'function': current_function
    }
    
    var_type = determine_variable_type(node, global_vars)
    var_info['type'] = var_type
    
    if var_type == 'static' and 'static_value' in match_dict:
        var_info['value'] = format_value(match_dict['static_value'][0].text.decode('utf-8'))
    elif var_type in ['global', 'file_level']:
        if 'var_value' in match_dict:
            value_node = match_dict['var_value'][0]
            var_info['value'] = format_value(value_node.text.decode('utf-8'))
        elif var_name in global_vars:
            var_info['value'] = global_vars[var_name]
        else:
            var_info['value'] = None
    elif 'var_value' in match_dict:
        value_node = match_dict['var_value'][0]
        if value_node.type == 'subscript_expression':
            array_name = value_node.child_by_field_name('array')
            if array_name and array_name.text.decode('utf-8') in SUPERGLOBALS:
                var_info['type'] = 'local'
        var_info['value'] = format_value(value_node.text.decode('utf-8'))
    else:
        var_info['value'] = None
        
    return var_info

def analyze_php_variables(tree, language) -> Dict[str, List[Dict[str, Any]]]:
    """分析PHP文件中的所有变量"""
    query = language.query("""
        ; 函数定义
        (function_definition
            name: (name) @function_name
            body: (compound_statement) @function_body
        ) @function
        
        ; 变量赋值
        [
            (expression_statement
                (assignment_expression
                    left: (variable_name) @assigned_var
                    right: (_) @var_value
                )
            )
            (global_declaration
                (variable_name) @global_var
            )
        ]
        
        ; 静态变量声明
        (static_variable_declaration
            (variable_name) @static_var
            value: (_) @static_value
        )
        
        ; 全局变量声明和使用
        [
            (global_declaration
                (variable_name) @global_var
            )
            (assignment_expression
                left: (variable_name) @global_var_assign
                right: (_) @global_var_value
            )
        ]
        
        ; 超全局变量访问
        (subscript_expression
            (variable_name) @array_name
            (_) @key_name
        )
    """)

    matches = query.matches(tree.root_node)
    processed_vars = set()
    global_vars = {}
    all_variables = []
    function_context = {}
    current_function = None

    # 先处理文件级变量和全局声明
    global_vars = {}  # 初始化全局变量字典
    function_context = {}  # 移到这里以便全局使用
    
    # 第一遍扫描：收集所有函数定义和全局变量
    for match in matches:
        pattern_index, match_dict = match
        
        # 记录函数定义
        if 'function_name' in match_dict and 'function' in match_dict:
            func_name = match_dict['function_name'][0].text.decode('utf-8')
            function_node = match_dict['function'][0]
            function_context[func_name] = {
                'start': function_node.start_point[0],
                'end': function_node.end_point[0]
            }
        
        # 记录全局变量声明和赋值
        for capture_name, nodes in match_dict.items():
            if capture_name in ['assigned_var', 'global_var']:
                node = nodes[0]
                var_name = node.text.decode('utf-8')
                node_line = node.start_point[0]
                
                # 确定当前函数上下文
                current_function = None
                for func_name, context in function_context.items():
                    if context['start'] <= node_line <= context['end']:
                        current_function = func_name
                        break
                
                # 处理全局变量
                # 修改全局变量处理逻辑
                if current_function is None or capture_name == 'global_var':
                    if 'var_value' in match_dict:
                        value_node = match_dict['var_value'][0]
                        # 确保值正确解析
                        value = format_value(value_node.text.decode('utf-8'))
                        if value is not None:
                            global_vars[var_name] = value
                    elif capture_name == 'global_var' and var_name not in global_vars:
                        global_vars[var_name] = None
                
                # 只处理文件级变量和全局声明
                if current_function is None or capture_name == 'global_var':
                    var_key = f"{var_name}:{current_function}"
                    if var_key not in processed_vars:
                        var_info = create_variable_info(node, current_function, match_dict, global_vars)
                        if var_info:
                            all_variables.append(var_info)
                            processed_vars.add(var_key)
    
    # 重置函数上下文
    current_function = None
    
    # 处理其他变量
    function_context = {}  # 用于存储函数上下文信息
    
    for match in matches:
        pattern_index, match_dict = match
        
        # 更新函数上下文
        if 'function_name' in match_dict and 'function' in match_dict:
            current_function = match_dict['function_name'][0].text.decode('utf-8')
            function_node = match_dict['function'][0]
            function_context[current_function] = {
                'start': function_node.start_point[0],
                'end': function_node.end_point[0]
            }
        
        for capture_name, nodes in match_dict.items():
            if capture_name in ['assigned_var', 'static_var', 'array_name']:
                node = nodes[0]
                node_line = node.start_point[0]
                
                # 确定当前函数上下文
                current_function = None
                for func_name, context in function_context.items():
                    if context['start'] <= node_line <= context['end']:
                        current_function = func_name
                        break
                
                var_name = node.text.decode('utf-8')
                
                # 处理超全局变量使用
                if capture_name == 'array_name' and var_name in SUPERGLOBALS:
                    var_key = f"{var_name}:{current_function}"
                    if var_key not in processed_vars:
                        # 获取访问的键名
                        key_name = None
                        if 'key_name' in match_dict:
                            key_node = match_dict['key_name'][0]
                            key_name = key_node.text.decode('utf-8')
                        
                        all_variables.append({
                            'type': 'superglobal',
                            'variable': var_name,
                            'key': key_name,
                            'line': node.start_point[0] + 1,
                            'function': current_function,
                            'value': None
                        })
                        processed_vars.add(var_key)
                        continue
                
                # 处理其他变量
                var_key = f"{var_name}:{current_function}"
                if var_key not in processed_vars:
                    var_info = create_variable_info(node, current_function, match_dict, global_vars)
                    if var_info:
                        all_variables.append(var_info)
                        processed_vars.add(var_key)

    # 处理变量并返回结果
    var_dict = {
        'local': {},
        'static': {},
        'superglobal': {},
        'global': {}
    }

    for var in all_variables:
        var_name = var['variable']
        var_type = var['type']
        
        if var_type == 'superglobal':
            var_key = f"{var_name}:{var.get('key', '')}"
            if var_key not in var_dict['superglobal']:
                var_dict['superglobal'][var_key] = var
        elif var_type == 'static':
            var_key = f"{var_name}:{var['function']}"
            if var_key not in var_dict['static'] or var.get('value') is not None:
                var_dict['static'][var_key] = var
        elif var_type == 'local':
            var_key = f"{var_name}:{var['function']}"
            var_dict['local'][var_key] = var
        elif var_type in ['global', 'file_level']:
            var_key = var_name
            existing_var = var_dict['global'].get(var_key)
            if not existing_var or var.get('value') is not None:
                var['type'] = 'global'
                var['function'] = None
                var_dict['global'][var_key] = var

    return {
        'local': list(var_dict['local'].values()),
        'static': list(var_dict['static'].values()),
        'superglobal': list(var_dict['superglobal'].values()),
        'global': sorted(list(var_dict['global'].values()), key=lambda x: x['line'])
    }

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
    from init_tree_sitter import init_php_parser
    from libs_com.file_io import read_file_bytes

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo\var_globals.php"
    php_file_bytes = read_file_bytes(php_file)
    php_file_tree = PARSER.parse(php_file_bytes)

    # 分析所有变量
    variables = analyze_php_variables(php_file_tree, LANGUAGE)
    
    print_variable_info(variables['local'], "局部变量")
    print_variable_info(variables['global'], "全局变量")
    print_variable_info(variables['static'], "静态变量")
    print_variable_info(variables['superglobal'], "超全局变量")