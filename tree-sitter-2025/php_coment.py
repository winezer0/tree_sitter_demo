def remove_comment_nodes(language, root_node):
    """移除所有注释信息"""
    # 匹配所有 comment 节点
    query = language.query("""(comment) @comment_node""")
    # 执行查询，获取所有匹配的注释节点
    matches = query.matches(root_node)
    # 提取所有注释节点，并按照起始字节排序（从后往前处理，避免索引偏移）
    comment_nodes = []
    for match in matches:
        match_dict = match[1]  # 获取捕获组字典
        if 'comment_node' in match_dict:
            comment_nodes.extend(match_dict['comment_node'])

    # 按照起始字节排序注释节点
    comment_nodes = sorted(comment_nodes, key=lambda node: node.start_byte, reverse=True)

    # 替换注释为空字符串
    code_bytes = root_node.text
    for comment_node in comment_nodes:
        start_byte = comment_node.start_byte
        end_byte = comment_node.end_byte
        # 替换注释为空字符串（保留换行符以保持格式）
        replacement = b'\n' * code_bytes[start_byte:end_byte].count(b'\n')
        code_bytes = code_bytes[:start_byte] + replacement + code_bytes[end_byte:]
    # 进行编码
    code_string = code_bytes.decode("utf8")
    # 清理多余的空白行
    code_string = remove_blank_lines(code_string)
    return code_string


def remove_blank_lines(code_string):
    """ 删除字符串中的所有空白行（包括仅包含空格或制表符的行）。 """
    # 按行分割代码
    lines = code_string.splitlines()
    # 过滤掉空白行（包括仅包含空格或制表符的行）
    non_blank_lines = [line for line in lines if line.strip()]
    # 将非空白行重新组合为一个字符串
    cleaned_code = "\n".join(non_blank_lines)
    return cleaned_code

if __name__ == '__main__':
    # 解析tree
    from tree_sitter_uitls import init_php_parser, read_file_to_root
    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/comment_demo/comment.php"
    root_node = read_file_to_root(PARSER, php_file)
    print(root_node)
    modified_code = remove_comment_nodes(LANGUAGE, root_node)
    # 输出修改后的代码
    print(modified_code)
