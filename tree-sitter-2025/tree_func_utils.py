def get_function_by_line(tree, language, line_number):
    """获取指定行号所在的函数信息"""
    query = language.query("""
        (function_definition
            name: (name) @function_name
            parameters: (formal_parameters) @params
            body: (compound_statement) @body
        ) @function
    """)

    matches = query.matches(tree.root_node)
    for match in matches:
        pattern_index, match_dict = match
        if 'function' in match_dict:
            # 修复：match_dict['function'] 返回的是列表，取第一个元素
            node = match_dict['function'][0]  # 获取第一个匹配的节点
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1

            if start_line <= line_number <= end_line:
                function_info = {
                    'name': node.child_by_field_name('name').text.decode('utf-8'),
                    'start_line': start_line,
                    'end_line': end_line,
                    'code_line': line_number,
                    'parameters': []
                }

                # 获取参数信息
                params_node = node.child_by_field_name('parameters')
                if params_node:
                    for param in params_node.children:
                        if param.type == 'parameter':
                            param_info = {
                                'name': '',
                                'type': None
                            }
                            # 获取参数类型
                            type_node = param.child_by_field_name('type')
                            if type_node:
                                param_info['type'] = type_node.text.decode('utf-8')
                            # 获取参数名
                            name_node = param.child_by_field_name('name')
                            if name_node:
                                param_info['name'] = name_node.text.decode('utf-8')
                            function_info['parameters'].append(param_info)

                return function_info

    return None


def get_function_code(tree, language, function_name):
    """获取指定函数名的代码内容"""
    query = language.query("""
        (function_definition
            name: (name) @function_name
            body: (compound_statement) @body
        ) @function
    """)

    # 修复：使用 matches() 替代 captures()
    matches = query.matches(tree.root_node)
    for match in matches:
        pattern_index, match_dict = match
        if 'function_name' in match_dict:
            node = match_dict['function_name'][0]
            if node.text.decode('utf-8') == function_name:
                function_node = node.parent
                # 获取函数的完整文本内容
                return {
                    'name': function_name,
                    'code': function_node.text.decode('utf-8'),
                    'start_line': function_node.start_point[0] + 1,
                    'end_line': function_node.end_point[0] + 1
                }
    return None


def get_non_function_code(tree, language):
    """获取所有不在函数内的PHP代码"""
    # 获取所有函数定义的范围
    function_ranges = []
    query = language.query("""
        (function_definition) @function
    """)

    # 修复：使用 matches() 替代 captures()
    matches = query.matches(tree.root_node)
    for match in matches:
        pattern_index, match_dict = match
        if 'function' in match_dict:
            node = match_dict['function'][0]
            function_ranges.append((node.start_point[0], node.end_point[0]))

    # 读取原始代码行
    source_lines = tree.root_node.text.decode('utf-8').split('\n')
    non_function_code = []

    # 遍历每一行，检查是否在函数范围内
    for line_num, line in enumerate(source_lines):
        in_function = False
        for start, end in function_ranges:
            if start <= line_num <= end:
                in_function = True
                break

        if not in_function:
            non_function_code.append({
                'line_number': line_num + 1,
                'code': line
            })

    return {
        'code_blocks': non_function_code,
        'start_line': non_function_code[0]['line_number'] if non_function_code else None,
        'end_line': non_function_code[-1]['line_number'] if non_function_code else None,
        'total_lines': len(non_function_code)
    }
    
if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.file_io import read_file_bytes

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo\no_func.php"
    php_file_bytes = read_file_bytes(php_file)
    print(f"read_file_bytes:->{php_file}")
    php_file_tree = PARSER.parse(php_file_bytes)
    code = get_function_by_line(php_file_tree, LANGUAGE, 5)
    code = get_function_code(php_file_tree, LANGUAGE, "back_action")
    code =  get_non_function_code(php_file_tree, LANGUAGE)
    print(code)