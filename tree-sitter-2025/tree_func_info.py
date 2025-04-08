from tree_func_utils import query_global_methods_info_old
from tree_func_utils_global_define import query_global_methods_define_infos, query_classes_define_infos, \
    query_created_class_object_infos, get_node_infos_names_ranges
from tree_func_utils_global_code import has_global_code, query_global_code_called_methods


def analyze_direct_method_infos(tree, language):
    """获取所有函数信息，包括函数内部和非函数部分"""
    # 获取所有本地函数名称和代码范围
    global_methods_define_infos = query_global_methods_define_infos(language, tree.root_node)
    gb_methods_names,gb_methods_ranges = get_node_infos_names_ranges(global_methods_define_infos)
    print(f"global_methods_define_infos:{global_methods_define_infos}")
    # 获取所有类定义的代码行范围，以排除类方法 本文件不处理类方法
    classes_define_infos = query_classes_define_infos(language, tree.root_node)
    classes_names, classes_ranges = get_node_infos_names_ranges(classes_define_infos)
    print(f"classes_define_infos:{classes_define_infos}")
    # 获取文件中所有类的初始化信息
    object_class_infos = query_created_class_object_infos(language, tree.root_node)
    print(f"object_class_infos:{object_class_infos}")
    exit()
    # 获取文件中的所有函数信息
    methods_info = query_global_methods_info_old(language, tree.root_node, classes_ranges, classes_names,
                                                 gb_methods_names, object_class_infos)
    # 处理文件级别的函数调用
    if has_global_code(tree.root_node, classes_ranges, gb_methods_ranges):
        non_function_info = query_global_code_called_methods(language, tree.root_node, classes_names, classes_ranges,
                                                             gb_methods_names, gb_methods_ranges, object_class_infos)
        if non_function_info:
            methods_info.append(non_function_info)
    return methods_info


if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.utils_json import print_json
    from tree_sitter_uitls import read_file_to_parse

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/class.php"
    php_file_tree = read_file_to_parse(PARSER, php_file)
    code = analyze_direct_method_infos(php_file_tree, LANGUAGE)
    print_json(code)
