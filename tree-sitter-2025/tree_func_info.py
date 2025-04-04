from tree_func_info_check import query_classes_define_names_ranges, has_not_function_content, \
    query_not_method_called_methods, query_general_methods_define_names_ranges, \
    query_general_methods_info


def analyze_direct_method_infos(tree, language):
    """获取所有函数信息，包括函数内部和非函数部分"""
    # 获取所有本地函数名称和代码范围
    gb_methods_names,gb_methods_ranges = query_general_methods_define_names_ranges(tree, language)
    
    # 获取所有类定义的代码行范围，以排除类方法 本文件不处理类方法
    classes_names, classes_ranges = query_classes_define_names_ranges(tree, language)

    # 获取文件中的所有函数信息
    methods_info = query_general_methods_info(tree, language, classes_ranges, classes_names, gb_methods_names)

    # 处理文件级别的函数调用
    if has_not_function_content(tree, classes_ranges, gb_methods_ranges):
        non_function_info = query_not_method_called_methods(tree, language, classes_names, classes_ranges, gb_methods_names, gb_methods_ranges)
        if non_function_info:
            methods_info.append(non_function_info)
    return methods_info


if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.utils_json import print_json
    from tree_func_utils import read_file_to_parse

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/class_call_demo/use_class.php"
    php_file_tree = read_file_to_parse(PARSER, php_file)
    code = analyze_direct_method_infos(php_file_tree, LANGUAGE)
    print_json(code)


