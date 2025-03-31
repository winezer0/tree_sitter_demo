
def get_non_function_code(tree, language):
    """获取所有不在函数内的PHP代码"""
    # 获取所有函数定义的范围
    function_ranges = []
    query = language.query("""
        (function_definition) @function
    """)

    captures = query.captures(tree.root_node)
    for node, _ in captures:
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