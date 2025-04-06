from tree_sitter._binding import Node

from tree_enums import NodeKeys


def node_info_add_unique_key(node_info: dict, name_key=NodeKeys.NODE_NAME.value):
    """给节点信息添加id属性"""
    name = node_info.get(name_key)
    start = node_info.get(NodeKeys.START_LINE.value, -1)
    end = node_info.get(NodeKeys.END_LINE.value, -1)
    unique_id = f"{name}|{start},{end}"
    node_info[NodeKeys.UNIQ_ID.value] = unique_id
    return node_info


def do_query_node_infos(tree, query, node_def_mark, node_name_mark='name'):
    """获取所有本地命名空间的定义 返回node字典格式"""
    infos = []
    for match in query.matches(tree.root_node):
        match_dict = match[1]
        if node_def_mark in match_dict:
            def_node = match_dict[node_def_mark][0]
            if def_node:
                # 通过 child_by_field_name 提取命名空间名称
                name_node = def_node.child_by_field_name(node_name_mark)
                name_text = name_node.text.decode('utf8')
                node_info = {
                    NodeKeys.NODE_NAME.value: name_text,
                    NodeKeys.START_LINE.value: def_node.start_point[0],
                    NodeKeys.END_LINE.value: def_node.end_point[0],
                }
                node_info = node_info_add_unique_key(node_info)
                infos.append(node_info)
    return infos


def find_child_by_field(node:Node, field_name_or_type:str) -> Node:
    """获取节点指定字段名或字段类型的 第一个值"""
    find_child = node.child_by_field_name(field_name_or_type)
    if not find_child:
        find_child = next((n for n in node.children if n.type == field_name_or_type), None)
    return find_child

def find_children_by_field(node:Node, field_name_or_type:str) -> Node:
    """获取节点指定字段名或字段类型的 所有个值"""
    children = node.children_by_field_name(field_name_or_type)
    if not children:
        children = [child for child in node.children if child.type == field_name_or_type]
    return children