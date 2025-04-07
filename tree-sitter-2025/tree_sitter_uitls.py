from tree_sitter._binding import Node

from tree_enums import NodeKeys


def calc_unique_key(name,start,end):
    """给节点信息添加id属性"""
    unique_id = f"{name}|{start},{end}"
    return unique_id


def extract_node_text_infos(root_node, query, total_node_field, need_node_field='name'):
    """获取节点的名称和起始行信息 返回字典格式"""
    infos = []
    for match in query.matches(root_node):
        match_dict = match[1]
        if total_node_field in match_dict:
            total_node = match_dict[total_node_field][0]
            if total_node:
                # 通过 child_by_field_name 提取命名空间名称
                need_node = total_node.child_by_field_name(need_node_field)
                need_text = need_node.text.decode('utf8')
                # 计算一个唯一键
                start_point = total_node.start_point[0]
                end_point = total_node.end_point[0]
                unique_id = calc_unique_key(need_text, start_point, end_point)
                node_info = {
                    NodeKeys.UNIQ_ID.value: unique_id,
                    NodeKeys.NODE_NAME.value: need_text,
                    NodeKeys.START_LINE.value: start_point,
                    NodeKeys.END_LINE.value: end_point,
                }
                infos.append(node_info)
    return infos


def find_first_child_by_field(node:Node, field_name_or_type:str) -> Node:
    """获取节点指定字段名或字段类型的 第一个值"""
    find_child = node.child_by_field_name(field_name_or_type)
    if not find_child:
        find_child = next((n for n in node.children if n.type == field_name_or_type), None)
    return find_child

def find_children_by_field(node:Node, field_name_or_type:str) -> Node:
    """获取节点指定字段名或字段类型的 所有值"""
    children = node.children_by_field_name(field_name_or_type)
    if not children:
        children = [child for child in node.children if child.type == field_name_or_type]
    return children