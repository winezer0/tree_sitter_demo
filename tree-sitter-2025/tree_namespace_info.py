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
