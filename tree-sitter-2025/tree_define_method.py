from typing import Tuple

from tree_sitter_uitls import extract_define_node_simple_infos


def query_gb_methods_define_infos(language, tree_node) -> Tuple[set, set[Tuple[int, int]]]:
    """ 获取所有本地普通函数（全局函数）的名称及其范围。"""
    # 定义查询语句
    function_query = language.query("""
        (function_definition
            name: (name) @function.name
        ) @function.def
    """)

    function_define_infos = extract_define_node_simple_infos(tree_node, function_query, 'function.def', need_node_field='name')
    return function_define_infos

if __name__ == '__main__':
    # 解析tree
    from tree_sitter_uitls import init_php_parser, read_file_to_root
    from libs_com.utils_json import print_json

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/class.php"
    root_node = read_file_to_root(PARSER, php_file)
    namespace_infos = query_gb_methods_define_infos(LANGUAGE, root_node)
    print_json(namespace_infos)