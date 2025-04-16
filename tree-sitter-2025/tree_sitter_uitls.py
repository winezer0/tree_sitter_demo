import hashlib
from typing import List

import tree_sitter_php
from tree_sitter import Language, Parser

from tree_sitter._binding import Node

from libs_com.file_io import read_file_bytes
from tree_enums import NodeKeys


def custom_format_path(path:str):
    return path.replace('\\', '/').replace('//', '/')

def get_strs_hash(*args):
    # 计算传入的任意个字符串的MD5哈希值，并返回前8个字符。
    if not args:
        raise ValueError("至少需要提供一个字符串参数")
    # 将所有字符串连接成一个单一的字符串
    concatenated_string = '|'.join(str(arg) for arg in args)
    # 计算并返回哈希值的前8个字符
    hash_object = hashlib.md5(concatenated_string.encode('utf-8'))
    return hash_object.hexdigest()[:8]

def find_first_child_by_field(node:Node, field_name_or_type:str) -> Node:
    """获取节点指定字段名或字段类型的 第一个值"""
    if node is None:
        return None
    find_child = node.child_by_field_name(field_name_or_type)
    if not find_child:
        find_child = next((n for n in node.children if n.type == field_name_or_type), None)
    return find_child


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
                start_point = total_node.start_point[0]
                end_point = total_node.end_point[0]
                node_info = {
                    NodeKeys.NAME.value: need_text,
                    NodeKeys.END_LINE.value: end_point,
                    NodeKeys.START_LINE.value: start_point,
                    # NodeKeys.UNIQ_ID.value: get_strs_hash(need_text, start_point, end_point),
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
    if not node:
        return None
    if node.type in ['string','encapsed_string']:
        find_text = get_node_filed_text(node, "string_content")
    elif node.type == 'array_creation_expression':
        # 解析数组内容
        array_elements = []
        for element in node.children:
            if element.type == 'array_element_initializer':
                element_value = get_node_text(element.child(0))
                array_elements.append(element_value)
        find_text = array_elements
    else:
        find_text = node.text.decode('utf-8')
    return find_text


def get_node_type(node):
    """获取节点的文本值"""
    find_type = node.type if node else None
    return find_type


def find_nearest_line_info(object_line, object_class_infos, start_key):
    """根据目标行号查找最近的类对象创建信息名称（类对象创建的开始行号必须小于等于目标行号）"""
    if not object_class_infos:
        return None  # 如果命名空间列表为空，直接返回 None

    # 筛选出所有行号小于等于目标行号的命名空间
    valid_infos = [x for x in object_class_infos if x[start_key] <= object_line]
    if not valid_infos:
        return None  # 如果没有符合条件的命名空间，返回 None
    # 找到行号最大的命名空间信息（即最接近目标行号的命名空间）
    nearest_class = max(valid_infos, key=lambda ns: ns[start_key])
    return nearest_class


def init_php_parser():
    """
    初始化 tree-sitter PHP 解析器
    tree_sitter>0.21.3 （test on 0.24.0 0.23.2）
    """
    PHP_LANGUAGE = Language(tree_sitter_php.language_php())
    php_parser = Parser(PHP_LANGUAGE)
    return php_parser, PHP_LANGUAGE


def read_file_to_parse(parser, php_file: str):
    """解析PHP文件"""
    php_bytes = read_file_bytes(php_file)
    return parser.parse(php_bytes)

def read_file_to_root(parser, php_file: str):
    """解析PHP文件"""
    php_bytes = read_file_bytes(php_file)
    return parser.parse(php_bytes).root_node

def load_str_to_parse(parser, php_code: str):
    """将字符串形式的 PHP 代码解析为语法树"""
    if not isinstance(php_code, str):
        return None
    # 将字符串转换为字节流（Tree-sitter 需要字节流作为输入）
    php_bytes = bytes(php_code, 'utf-8')
    # 使用解析器解析字节流
    return parser.parse(php_bytes)


def find_children_by_field(node:Node, field_name_or_type:str) -> List[Node]:
    """获取节点指定字段名或字段类型的 所有值"""
    if node is None:
        return []
    children = node.children_by_field_name(field_name_or_type)
    if not children:
        children = [child for child in node.children if child.type == field_name_or_type]
    return children
