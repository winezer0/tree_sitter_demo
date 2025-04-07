from typing import Tuple

from tree_sitter._binding import Node

from tree_enums import MethodKeys, NodeKeys
from tree_sitter_uitls import extract_node_text_infos, find_first_child_by_field, get_node_text, get_node_filed_text


def query_global_methods_define_infos(language, root_node) -> Tuple[set, set[Tuple[int, int]]]:
    """ 获取所有本地普通函数（全局函数）的名称及其范围。"""
    # 定义查询语句
    function_query = language.query("""
        (function_definition
            name: (name) @function.name
        ) @function.def
    """)

    function_define_infos = extract_node_text_infos(root_node, function_query, 'function.def', need_node_field='name')
    return function_define_infos


def query_classes_define_infos(language, root_node) -> Tuple[set[str], set[Tuple[int, int]]]:
    """获取所有类定义的类名及其代码行范围。 """
    # 定义查询语句，匹配类型定义
    class_def_query = language.query("""
        ;匹配普通|抽象|final类定义信息
        (class_declaration
            name: (name) @class.name
        ) @class.def

        ;匹配接口类定义信息
        (interface_declaration
            name: (name) @class.name
        ) @class.def
    """)

    class_define_infos = extract_node_text_infos(root_node, class_def_query, 'class.def', need_node_field='name')
    return class_define_infos


def query_node_created_class_object_infos(language: object, tree_node: Node) -> list[dict]:
    """获取节点中中所有创建的类对象和名称关系"""
    # 定义查询语句
    new_object_query = language.query("""
        ; 查询对象方法创建 同时获取返回值
        (assignment_expression
            left: (variable_name) @left_variable
            right: (
                (object_creation_expression
                   (name) @new_class_name
                   (arguments) @constructor_args
                ) @new_expr
            )
        ) @assignment_expr
    """)

    # 存储结果的列表
    object_class_dicts = []
    # 遍历匹配结果
    for match in new_object_query.matches(tree_node):
        match_dict = match[1]

        # 提取 assignment_expr 节点
        if 'assignment_expr' in match_dict:
            assignment_expr_node = match_dict['assignment_expr'][0]
            start_line = assignment_expr_node.start_point[0]
            end_line = assignment_expr_node.end_point[0]

            # 初始化变量
            # 使用 child_by_field_name 提取左侧变量名
            left_node = find_first_child_by_field(assignment_expr_node, 'left')
            object_name = get_node_text(left_node)

            # 使用 child_by_field_name 提取右侧表达式
            right_expr_node = find_first_child_by_field(assignment_expr_node, 'right')
            if right_expr_node and right_expr_node.type == 'object_creation_expression':
                class_name = get_node_filed_text(right_expr_node, 'name')
                if class_name and object_name:
                    object_info = {
                        MethodKeys.OBJECT.value: object_name,
                        MethodKeys.CLASS.value: class_name,
                        MethodKeys.START_LINE.value: start_line,
                        MethodKeys.END_LINE.value: end_line,
                    }
                    object_class_dicts.append(object_info)
    return object_class_dicts


def get_node_infos_names_ranges(node_infos: dict) -> Tuple[set[str], set[Tuple[int, int]]]:
    """从提取的节点名称|起始行信息中获取 节点名称和范围元组"""
    node_names = set()
    node_ranges = set()
    for node_info in node_infos:
        node_names.add(node_info.get(NodeKeys.NODE_NAME.value))
        node_ranges.add((node_info.get(NodeKeys.START_LINE.value), node_info.get(NodeKeys.END_LINE.value)))
    return node_names, node_ranges
