from typing import List

from tree_sitter._binding import Node

from libs_com.file_io import read_file_bytes
from tree_enums import NodeKeys


def calc_unique_key(*args):
    """根据传入的任意数量的参数生成唯一的键。"""
    unique_id = "|".join(map(str, args))
    return unique_id

def find_first_child_by_field(node:Node, field_name_or_type:str) -> Node:
    """获取节点指定字段名或字段类型的 第一个值"""
    find_child = node.child_by_field_name(field_name_or_type)
    if not find_child:
        find_child = next((n for n in node.children if n.type == field_name_or_type), None)
    return find_child

def find_children_by_field(node:Node, field_name_or_type:str) -> List[Node]:
    """获取节点指定字段名或字段类型的 所有值"""
    children = node.children_by_field_name(field_name_or_type)
    if not children:
        children = [child for child in node.children if child.type == field_name_or_type]
    return children

def extract_node_text_infos(root_node, query, total_node_field, need_node_field='name'):
    """获取节点的名称和起始行信息 返回字典格式"""
    infos = []
    for match in query.matches(root_node):
        match_dict = match[1]
        if total_node_field in match_dict:
            total_node = match_dict[total_node_field][0]
            if total_node:
                # 通过 child_by_field_name 提取命名空间名称
                need_node = find_first_child_by_field(total_node, need_node_field)
                need_text = need_node.text.decode('utf8')
                # 计算一个唯一键
                start_point = total_node.start_point[0]
                end_point = total_node.end_point[0]
                unique_id = calc_unique_key(need_text, start_point, end_point)
                node_info = {
                    NodeKeys.NODE_NAME.value: need_text,
                    NodeKeys.END_LINE.value: end_point,
                    NodeKeys.START_LINE.value: start_point,
                    NodeKeys.UNIQ_ID.value: unique_id,
                }
                infos.append(node_info)
    return infos


def get_node_filed_text(node, field_name_or_type):
    """获取节点的指定子节点的指定名称or类型对应的文本值"""
    find_node = find_first_child_by_field(node, field_name_or_type)
    find_text = find_node.text.decode('utf-8') if find_node else None
    return find_text


def get_node_text(node):
    """获取节点的文本值"""
    find_text = node.text.decode('utf-8') if node else None
    return find_text

def get_node_type(node):
    """获取节点的文本值"""
    find_type = node.type if node else None
    return find_type

def read_file_to_parse(parser, php_file: str):
    """解析PHP文件"""
    php_bytes = read_file_bytes(php_file)
    return parser.parse(php_bytes)
