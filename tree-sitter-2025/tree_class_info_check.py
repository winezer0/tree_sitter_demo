from tree_enums import NodeKeys
from tree_sitter_uitls import extract_node_infos


def find_nearest_namespace(class_line, namespaces_infos, start_line_key=NodeKeys.START_LINE.value):
    """ 根据目标行号查找最近的命名空间名称（命名空间开始行号必须小于等于目标行号）"""
    if not namespaces_infos:
        return None  # 如果命名空间列表为空，直接返回 None

    # 筛选出所有行号小于等于目标行号的命名空间
    valid_namespaces = [ns for ns in namespaces_infos if ns[start_line_key] <= class_line]
    if not valid_namespaces:
        return None  # 如果没有符合条件的命名空间，返回 None
    # 找到行号最大的命名空间（即最接近目标行号的命名空间）
    nearest_namespace = max(valid_namespaces, key=lambda ns: ns[NodeKeys.START_LINE.value])
    return nearest_namespace[start_line_key]


def query_namespace_define_infos(tree, language):
    """获取所有本地命名空间的定义 返回node字典格式"""
    namespace_define_query = language.query("""
    ;匹配命名空间定义信息
    (namespace_definition
        name: (namespace_name) @namespace_name
    ) @namespace.def
    """)
    namespace_infos = extract_node_infos(tree.root_node, namespace_define_query, 'namespace.def', need_node_field='name')
    return namespace_infos
