from tree_creat_object import query_gb_object_creation_infos
from tree_define_class import query_gb_classes_define_infos
from tree_define_method import query_gb_methods_define_infos
from tree_define_namespace import analyse_namespace_define_infos
from tree_func_utils import query_global_methods_info, parse_global_code_called_methods
from tree_sitter_uitls import trans_node_infos_names_ranges


def analyze_direct_method_infos(parser, language, root_node,
                                gb_namespace_infos=None, global_methods_define_infos=None, classes_define_infos=None):
    """获取所有函数信息，包括函数内部和非函数部分 """
    # 获取所有命名空间信息
    if gb_namespace_infos is None:
        gb_namespace_infos =analyse_namespace_define_infos(language, root_node)

    if global_methods_define_infos is None or classes_define_infos is None:
        # 获取所有本地函数名称和代码范围
        global_methods_define_infos = query_gb_methods_define_infos(language, root_node)
        # print(f"global_methods_define_infos:{global_methods_define_infos}")
        # 获取所有类定义的代码行范围，以排除类方法 本文件不处理类方法
        classes_define_infos = query_gb_classes_define_infos(language, root_node)
        # print(f"classes_define_infos:{classes_define_infos}")

    gb_methods_names,gb_methods_ranges = trans_node_infos_names_ranges(global_methods_define_infos)
    gb_classes_names, gb_classes_ranges = trans_node_infos_names_ranges(classes_define_infos)

    # 获取文件中所有类的初始化信息
    gb_object_class_infos = query_gb_object_creation_infos(language, root_node)
    # print(f"object_class_infos:{gb_object_class_infos}")

    # 获取文件中的所有函数信息
    methods_info = query_global_methods_info(language, root_node, gb_classes_names, gb_methods_names,
                                             gb_object_class_infos, gb_namespace_infos)
    # 处理文件级别的函数调用
    global_code_info = parse_global_code_called_methods(parser, language, root_node,
                                                        gb_classes_names, gb_classes_ranges,
                                                        gb_methods_names, gb_methods_ranges,
                                                        gb_object_class_infos)
    if global_code_info:
        methods_info.append(global_code_info)
    return methods_info


if __name__ == '__main__':
    # 解析tree
    from tree_sitter_uitls import init_php_parser, read_file_to_root
    from libs_com.utils_json import print_json

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/class.php"
    php_file = "php_demo/full_demo/index.php"
    root_node = read_file_to_root(PARSER, php_file)
    direct_method_infos = analyze_direct_method_infos(PARSER, LANGUAGE, root_node)
    print_json(direct_method_infos)
