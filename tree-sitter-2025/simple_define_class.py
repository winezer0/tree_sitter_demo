from typing import Tuple

from tree_sitter_uitls import extract_define_node_simple_infos


def query_gb_classes_define_infos(language, tree_node) -> Tuple[set[str], set[Tuple[int, int]]]:
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

    class_define_infos = extract_define_node_simple_infos(tree_node, class_def_query, 'class.def', need_node_field='name')
    return class_define_infos
