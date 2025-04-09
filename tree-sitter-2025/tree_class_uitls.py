from tree_sitter_uitls import extract_node_text_infos


def query_namespace_define_infos(language, root_node):
    """获取所有本地命名空间的定义 返回node字典格式"""
    namespace_define_query = language.query("""
    ;匹配命名空间定义信息
    (namespace_definition
        name: (namespace_name) @namespace_name
    ) @namespace.def
    """)
    namespace_infos = extract_node_text_infos(root_node, namespace_define_query, 'namespace.def', need_node_field='name')
    return namespace_infos


def is_static_method(modifiers):
    if modifiers and 'static' in modifiers:
        return True
    return False


def get_method_fullname(method_name, class_name, object_name, is_static):
    concat = "::" if is_static else "->"
    if class_name:
        fullname = f"{class_name}{concat}{method_name}"
    elif object_name:
        fullname = f"{object_name}{concat}{method_name}"
    else:
        fullname = f"{method_name}"
    return fullname
