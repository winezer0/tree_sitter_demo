from tree_sitter_uitls import extract_define_node_simple_infos


def query_namespace_define_infos(language, root_node):
    """获取所有本地命名空间的定义 返回node字典格式"""
    namespace_define_query = language.query("""
    ;匹配命名空间定义信息
    (namespace_definition
        name: (namespace_name) @namespace_name
    ) @namespace.def
    """)
    namespace_infos = extract_define_node_simple_infos(root_node, namespace_define_query, 'namespace.def', need_node_field='name')
    return namespace_infos




if __name__ == '__main__':
    # 解析tree
    from tree_sitter_uitls import init_php_parser, read_file_to_root
    from libs_com.utils_json import print_json

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/class.php"
    root_node = read_file_to_root(PARSER, php_file)
    namespace_infos = query_namespace_define_infos(LANGUAGE, root_node)
    print_json(namespace_infos)

