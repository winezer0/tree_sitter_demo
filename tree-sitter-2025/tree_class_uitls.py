from tree_sitter._binding import Node

from tree_enums import NodeKeys, PropertyKeys
from tree_func_utils_sub_parse import get_node_modifiers
from tree_sitter_uitls import extract_node_text_infos, find_first_child_by_field, get_node_filed_text, \
    find_children_by_field


def query_namespace_define_infos(tree, language):
    """获取所有本地命名空间的定义 返回node字典格式"""
    namespace_define_query = language.query("""
    ;匹配命名空间定义信息
    (namespace_definition
        name: (namespace_name) @namespace_name
    ) @namespace.def
    """)
    namespace_infos = extract_node_text_infos(tree.root_node, namespace_define_query, 'namespace.def', need_node_field='name')
    return namespace_infos


def find_nearest_namespace(class_line, namespaces_infos):
    """根据目标行号查找最近的命名空间名称（命名空间开始行号必须小于等于目标行号）"""
    if not namespaces_infos:
        return None  # 如果命名空间列表为空，直接返回 None

    # 筛选出所有行号小于等于目标行号的命名空间
    valid_namespaces = [x for x in namespaces_infos if x[NodeKeys.START_LINE.value] <= class_line]
    if not valid_namespaces:
        return None  # 如果没有符合条件的命名空间，返回 None
    # 找到行号最大的命名空间信息（即最接近目标行号的命名空间）
    nearest_namespace = max(valid_namespaces, key=lambda ns: ns[NodeKeys.START_LINE.value])
    return nearest_namespace[NodeKeys.START_LINE.value]


def parse_class_properties_node(class_node):
    """获取类节内部的属性定义信息"""
    def parse_class_property_node(property_node: Node) -> dict:
        """解析单个属性声明节点的信息。 """
        # property_node:(property_declaration (visibility_modifier) (static_modifier)
        # (property_element name: (variable_name (name)) default_value: (encapsed_string (string_content))))
        # 初始化属性信息
        # 获取属性元素节点
        property_element_node = find_first_child_by_field(property_node, 'property_element')
        property_info = {
            PropertyKeys.NAME.value: get_node_filed_text(property_element_node, 'name'),
            PropertyKeys.DEFAULT.value: get_node_filed_text(property_element_node, 'default_value'),

            PropertyKeys.START_LINE.value: property_node.start_point[0],
            PropertyKeys.END_LINE.value: property_node.end_point[0],

            PropertyKeys.VISIBILITY.value: get_node_filed_text(property_node, 'visibility_modifier'),
            PropertyKeys.TYPE.value: get_node_filed_text(property_node, 'primitive_type'),
            PropertyKeys.MODIFIERS.value: get_node_modifiers(property_node),
        }
        # 添加行属性
        return property_info

    # 存储返回结果
    properties = []
    # 获取请求体部分
    body_node = find_first_child_by_field(class_node, "body")
    if body_node:
        props_nodes = find_children_by_field(body_node, 'property_declaration')
        properties = [parse_class_property_node(prop_node) for prop_node in props_nodes]
    return properties
