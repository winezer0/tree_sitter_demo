from typing import List, Dict, Any

from tree_class_utils import parse_class_define_info, query_namespace_define_infos
from tree_func_utils_global_define import query_gb_methods_define_infos, query_gb_classes_define_infos, \
    get_node_infos_names_ranges
from tree_sitter_uitls import read_file_to_parse

def analyze_class_infos(tree, language) -> List[Dict[str, Any]]:
    """提取所有类定义信息"""
    root_node = tree.root_node
    # 获取所有本地函数名称
    gb_methods_define_infos = query_gb_methods_define_infos(language, root_node)
    gb_methods_names,gb_methods_ranges=get_node_infos_names_ranges(gb_methods_define_infos)
    print(f"gb_methods_names:{gb_methods_names}")
    # 获取所有类定义的代码行范围，以排除类方法 本文件不处理类方法
    classes_define_infos = query_gb_classes_define_infos(language, root_node)
    gb_classes_names, gb_classes_ranges= get_node_infos_names_ranges(classes_define_infos)
    print(f"gb_classes_names:{gb_classes_names}")
    # gb_classes_names:{'InterfaceImplementation', 'MyAbstractClass', 'ConcreteClass', 'MyInterface', 'MyClass'}
    # 获取所有命名空间信息
    namespaces_infos = query_namespace_define_infos(language, root_node)
    print(namespaces_infos)
    # [{'NAME': 'App\\Namespace1', 'START': 7, 'END': 41, 'UNIQ': 'App\\Namespace1|7,41'},

    TREE_SITTER_CLASS_DEFINE_QUERY = """
        ;匹配类定义信息 含abstract类和final类
        (class_declaration) @class.def
        ;匹配接口定义
        (interface_declaration) @class.def
    """
    class_info_query = language.query(TREE_SITTER_CLASS_DEFINE_QUERY)
    class_info_matches = class_info_query.matches(root_node)

    # 函数调用解析部分
    class_infos = []
    for pattern_index, match_dict in class_info_matches:
        # 添加调试信息
        print(f"{pattern_index}/{len(class_info_matches)} Pattern match type:", [key for key in match_dict.keys()])
        # 一次性解析类信息
        class_def_mark = 'class.def'  # 语法中表示类定义
        inter_def_mark = 'interface.def' # 语法中表示接口定义
        if class_def_mark in match_dict or inter_def_mark in match_dict:
            # 处理类信息时使用当前命名空间 # 如果命名空间栈非空，使用栈顶命名空间
            is_interface = inter_def_mark in match_dict
            class_node = match_dict[inter_def_mark][0] if is_interface else match_dict[class_def_mark][0]
            class_info = parse_class_define_info(language, class_node, is_interface, namespaces_infos)
            class_infos.append(class_info)
    return class_infos


if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.utils_json import print_json

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/class2.php"
    php_file_tree = read_file_to_parse(PARSER, php_file)
    code = analyze_class_infos(php_file_tree, LANGUAGE)
    print_json(code)


