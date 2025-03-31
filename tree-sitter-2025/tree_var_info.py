def format_value(value):
    """格式化提取的值，去除引号等处理"""
    if not value:
        return None
    # 去除字符串的引号
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value

def get_global_variable_declare(tree, language):
    """获取PHP文件中的全局变量声明"""
    global_vars = []
    query = language.query("""
        (function_definition
            name: (name) @function_name
            body: (compound_statement 
                (global_declaration
                    (variable_name) @global_var)
            )
        )
    """)
    
    # 修复：使用 matches() 替代 captures()
    matches = query.matches(tree.root_node)
    current_function = None

    for match in matches:
        pattern_index, match_dict = match
        if 'function_name' in match_dict:
            current_function = match_dict['function_name'][0].text.decode('utf-8')
        if 'global_var' in match_dict:
            node = match_dict['global_var'][0]
            var_name = node.text.decode('utf-8')
            global_vars.append({
                'function': current_function,
                'variable': var_name,
                'line': node.start_point[0] + 1,
            })
    return global_vars

def get_global_variable_usages(tree, language):
    """获取PHP文件中的全局变量使用"""
    global_usages = []
    query = language.query("""
        (variable_name) @var_usage
    """)
    
    # 修复：使用 matches() 替代 captures()
    matches = query.matches(tree.root_node)
    seen_vars = set()  # 用于跟踪已经处理过的变量

    for match in matches:
        pattern_index, match_dict = match
        if 'var_usage' in match_dict:
            node = match_dict['var_usage'][0]
            var_name = node.text.decode('utf-8')
            if var_name.startswith('$') and var_name not in seen_vars:
                # 检查变量是否在全局声明中
                parent = node.parent
                while parent:
                    if parent.type == 'global_declaration':
                        break
                    parent = parent.parent
                if parent and parent.type == 'global_declaration':
                    global_usages.append({
                        'name': var_name,
                        'line': node.start_point[0] + 1,
                    })
                    seen_vars.add(var_name)
    return global_usages

def get_file_level_globals(tree, language):
    """获取PHP文件级别的全局变量声明（函数外的全局变量）"""
    file_globals = []
    query = language.query("""
        (program 
            (expression_statement 
                (assignment_expression
                    left: (variable_name) @var_name
                    right: (_) @var_value
                )
            )
        )
    """)
    
    matches = query.matches(tree.root_node)

    for match in matches:
        pattern_index, match_dict = match
        if 'var_name' in match_dict:
            node = match_dict['var_name'][0]
            # 检查是否在函数定义之外
            parent = node.parent
            while parent:
                if parent.type == 'function_definition':
                    break
                parent = parent.parent

            if not parent:  # 如果没有找到函数定义作为父节点，说明是文件级别的
                var_name = node.text.decode('utf-8')
                var_value = None
                if 'var_value' in match_dict:
                    var_value = format_value(match_dict['var_value'][0].text.decode('utf-8'))
                
                file_globals.append({
                    'variable': var_name,
                    'value': var_value,
                    'line': node.start_point[0] + 1
                })

    return file_globals

def get_file_level_variables(tree, language):
    """获取PHP文件级别直接定义的变量"""
    file_vars = []
    query = language.query("""
        (program
            (expression_statement
                (assignment_expression) @assignment
            )
        )
    """)

    # 修复：使用 matches() 替代 captures()
    matches = query.matches(tree.root_node)

    for match in matches:
        pattern_index, match_dict = match
        if 'assignment' in match_dict:
            node = match_dict['assignment'][0]
            # 检查是否在函数定义之外
            parent = node.parent
            while parent:
                if parent.type == 'function_definition':
                    break
                parent = parent.parent

            if not parent:  # 如果不在函数内
                var_name = node.child_by_field_name('left')
                var_value = node.child_by_field_name('right')
                if var_name and var_name.type == 'variable_name':
                    value = var_value.text.decode('utf-8') if var_value else None
                    file_vars.append({
                        'variable': var_name.text.decode('utf-8'),
                        'value': format_value(value),
                        'line': node.start_point[0] + 1
                    })

    return file_vars

def get_super_global_usages(tree, language):
    """获取PHP超全局变量的使用情况"""
    superglobal_usages = []
    query = language.query("""
        (subscript_expression
            (variable_name) @array_name
            (string) @key_name
        ) @access
        (member_access_expression
            (variable_name) @array_name
            (name) @key_name
        ) @access
    """)

    # 修复：使用 matches() 替代 captures()
    matches = query.matches(tree.root_node)
    current_var = None

    for match in matches:
        pattern_index, match_dict = match
        if 'array_name' in match_dict:
            var_name = match_dict['array_name'][0].text.decode('utf-8')
            if var_name in ['$_REQUEST', '$_GET', '$_POST', '$_SESSION', '$_COOKIE', '$_SERVER']:
                current_var = var_name
                if 'key_name' in match_dict:
                    key_name = format_value(match_dict['key_name'][0].text.decode('utf-8'))
                    node = match_dict['access'][0]
                    superglobal_usages.append({
                        'variable': current_var,
                        'key': key_name,
                        'line': node.start_point[0] + 1,
                        'full_expression': node.text.decode('utf-8')
                    })

    return superglobal_usages

if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.file_io import read_file_bytes

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/var_globals.php"
    php_file_bytes = read_file_bytes(php_file)
    print(f"read_file_bytes:->{php_file}")
    php_file_tree = PARSER.parse(php_file_bytes)
    # code = get_global_variable_declare(php_file_tree, LANGUAGE)
    # print(f"get_global_variable_declare:{code}")
    # code = get_global_variable_usages(php_file_tree, LANGUAGE)
    # print(f"get_global_variable_usages:{code}")
    # code = get_file_level_globals(php_file_tree, LANGUAGE)
    # print(f"get_file_level_globals:{code}")

    # code = get_file_level_variables(php_file_tree, LANGUAGE)
    # print(f"get_file_level_variables:{code}")

    code = get_super_global_usages(php_file_tree, LANGUAGE)
    print(f"get_super_global_usages:{code}")