from libs_com.utils_json import print_json
from tree_const import METHOD_NAME, METHOD_START_LINE, METHOD_END_LINE, PARAMETER_TYPE, PARAMETER_NAME, \
    METHOD_PARAMETERS


def get_function_by_line(php_file, parser, language, line_number):
    """获取指定行号所在的函数信息"""
    php_bytes = read_file_bytes(php_file)
    php_tree = parser.parse(php_bytes)

    query = language.query("""
        (function_definition
            name: (name) @function_name
            parameters: (formal_parameters) @params
            body: (compound_statement) @body
        ) @function
    """)

    matches = query.matches(php_tree.root_node)
    for match in matches:
        pattern_index, match_dict = match
        if 'function' in match_dict:
            # 修复：match_dict['function'] 返回的是列表，取第一个元素
            node = match_dict['function'][0]  # 获取第一个匹配的节点
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1

            if start_line <= line_number <= end_line:
                function_info = {
                    METHOD_NAME: node.child_by_field_name('name').text.decode('utf-8'),
                    METHOD_START_LINE: start_line,
                    METHOD_END_LINE: end_line,
                    METHOD_PARAMETERS: [],
                    'code_line': line_number,
                }

                # 获取参数信息
                params_node = node.child_by_field_name('parameters')
                if params_node:
                    for param in params_node.children:
                        if param.type == 'parameter':
                            param_info = {
                                PARAMETER_NAME: '',
                                PARAMETER_TYPE: None
                            }
                            # 获取参数类型
                            type_node = param.child_by_field_name('type')
                            if type_node:
                                param_info[PARAMETER_TYPE] = type_node.text.decode('utf-8')
                            # 获取参数名
                            name_node = param.child_by_field_name('name')
                            if name_node:
                                param_info[PARAMETER_NAME] = name_node.text.decode('utf-8')
                            function_info[METHOD_PARAMETERS].append(param_info)

                return function_info

    return None


def get_function_code(php_file, parser, language, function_name):
    """获取指定函数名的代码内容"""
    php_bytes = read_file_bytes(php_file)
    php_tree = parser.parse(php_bytes)

    query = language.query("""
        (function_definition
            name: (name) @function_name
            body: (compound_statement) @body
        ) @function
    """)

    # 修复：使用 matches() 替代 captures()
    matches = query.matches(php_tree.root_node)
    for match in matches:
        pattern_index, match_dict = match
        if 'function_name' in match_dict:
            node = match_dict['function_name'][0]
            if node.text.decode('utf-8') == function_name:
                function_node = node.parent
                # 获取函数的完整文本内容
                return {
                    METHOD_NAME: function_name,
                    METHOD_START_LINE: function_node.start_point[0] + 1,
                    METHOD_END_LINE: function_node.end_point[0] + 1,
                    'code': function_node.text.decode('utf-8'),
                }
    return None


def get_not_in_func_code(php_file, parser, language):
    """获取所有不在函数内的PHP代码"""
    php_bytes = read_file_bytes(php_file)
    php_tree = parser.parse(php_bytes)

    # 获取所有函数定义的范围
    function_ranges = []
    query = language.query("""
        (function_definition) @function
    """)

    # 修复：使用 matches() 替代 captures()
    matches = query.matches(php_tree.root_node)
    for match in matches:
        pattern_index, match_dict = match
        if 'function' in match_dict:
            node = match_dict['function'][0]
            function_ranges.append((node.start_point[0], node.end_point[0]))

    # 读取原始代码行
    source_lines = php_tree.root_node.text.decode('utf-8').split('\n')
    non_function_code = []

    # 遍历每一行，检查是否在函数范围内
    for line_num, line in enumerate(source_lines):
        in_function = False
        for start, end in function_ranges:
            if start <= line_num <= end:
                in_function = True
                break

        if not in_function:
            code_line_info = {
                'line_number': line_num + 1,
                'code': line
            }
            non_function_code.append(code_line_info)

    return {
        METHOD_START_LINE: non_function_code[0]['line_number'] if non_function_code else None,
        METHOD_END_LINE: non_function_code[-1]['line_number'] if non_function_code else None,
        'total_lines': len(non_function_code),
        'code_blocks': non_function_code,
    }
    
if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.file_io import read_file_bytes
    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/function_none.php"
    # print(f"read_file_bytes:->{php_file}")
    code = get_function_by_line(php_file, PARSER, LANGUAGE, 5)
    print_json(code)
    print(f"=" * 50)
    code = get_function_code(php_file, PARSER, LANGUAGE, "back_action")
    print_json(code)
    print(f"=" * 50)
    code =  get_not_in_func_code(php_file, PARSER, LANGUAGE)
    print_json(code)
    print(f"=" * 50)
