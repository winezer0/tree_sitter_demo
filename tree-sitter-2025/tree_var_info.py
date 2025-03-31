
def get_global_variable_declarations(tree, language):
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
    captures = query.captures(tree.root_node)
    current_function = None

    for node, capture_name in captures:
        if capture_name == 'function_name':
            current_function = node.text.decode('utf-8')
        if capture_name == 'global_var':
            var_name = node.text.decode('utf-8')
            global_vars.append({
                'function': current_function,
                'variable': var_name,
                'line': node.start_point[0] + 1,
                # 'column': node.start_point[1]
            })
    return global_vars


def get_global_variable_usages(tree, language):
    """获取PHP文件中的全局变量使用"""
    global_usages = []
    query = language.query("""
        (variable_name) @var_usage
    """)
    captures = query.captures(tree.root_node)
    for node, _ in captures:
        var_name = node.text.decode('utf-8')
        if var_name.startswith('$') and var_name not in global_usages:
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
                    # 'column': node.start_point[1]
                })
    return global_usages


def get_file_level_globals(tree, language):
    """获取PHP文件级别的全局变量声明（函数外的全局变量）"""
    file_globals = []
    query = language.query("""
        (program
            (global_declaration
                (variable_name) @global_var) @global_decl
        )
    """)
    captures = query.captures(tree.root_node)

    for node, capture_name in captures:
        if capture_name == 'global_var':
            # 检查是否在函数定义之外
            parent = node.parent
            while parent:
                if parent.type == 'function_definition':
                    break
                parent = parent.parent

            if not parent:  # 如果没有找到函数定义作为父节点，说明是文件级别的
                file_globals.append({
                    'variable': node.text.decode('utf-8'),
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

    captures = query.captures(tree.root_node)
    for node, _ in captures:
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
                file_vars.append({
                    'variable': var_name.text.decode('utf-8'),
                    'value': var_value.text.decode('utf-8') if var_value else None,
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

    captures = query.captures(tree.root_node)
    current_var = None

    for node, capture_name in captures:
        if capture_name == 'array_name':
            var_name = node.text.decode('utf-8')
            if var_name in ['$_REQUEST', '$_GET', '$_POST', '$_SESSION', '$_COOKIE', '$_SERVER']:
                current_var = var_name
        elif capture_name == 'key_name' and current_var:
            key_name = node.text.decode('utf-8').strip("'\"")
            superglobal_usages.append({
                'variable': current_var,
                'key': key_name,
                'line': node.start_point[0] + 1,
                'full_expression': node.parent.text.decode('utf-8')
            })
            current_var = None

    return superglobal_usages

