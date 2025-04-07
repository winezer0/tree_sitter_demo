from tree_enums import ClassKeys
from tree_func_utils import query_node_created_class_object_infos, query_global_methods_define_infos, \
    query_classes_define_infos, query_global_methods_info_old, TREE_SITTER_PHP_METHOD_CALLED_STAT, \
    create_method_result_dict
from guess import has_global_code, get_node_infos_names_ranges, line_in_methods_or_classes_ranges, \
    guess_called_object_is_native


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
    object_class_infos = query_node_created_class_object_infos(language, tree.root_node)
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


def query_global_code_called_methods(language, root_node, classes_names, classes_ranges, gb_methods_names,
                                     gb_methods_ranges, object_class_infos):
    """查询全部代码调用的函数信息 并且只保留其中不属于函数和类的部分"""
    queried = language.query(TREE_SITTER_PHP_METHOD_CALLED_STAT)

    nf_called_infos = []

    # 处理对象方法调用
    for match in queried.matches(root_node):
        match_dict = match[1]
        if 'member.call' in match_dict or 'static.call' in match_dict:
            # 根据静态方法和普通对象方法的语法查询结果关键字进行判断是否是静态方法
            is_static_call = 'static.call' in match_dict
            method_node = match_dict['static.call'][0] if is_static_call else match_dict['member.call'][0]
            start_line = method_node.start_point[0]

            if not line_in_methods_or_classes_ranges(start_line, gb_methods_ranges, classes_ranges):
                method_name = match_dict['method.name'][0].text.decode('utf-8')
                object_node = match_dict['method.object'][0]
                args_node = match_dict.get('method.args', [None])[0]

                object_name = object_node.text.decode('utf-8')
                object_line = object_node.start_point[0]
                class_is_native, class_name = guess_called_object_is_native(object_name, object_line, classes_names, object_class_infos)

                nf_called_info = res_called_object_method(
                    object_node, method_node, args_node, method_name, class_is_native, is_static_call, class_name)
                nf_called_infos.append(nf_called_info)

    # 处理对象创建
    for match in queried.matches(root_node):
        match_dict = match[1]
        if 'new_class_name' in match_dict:
            class_node = match_dict['new_class_name'][0]
            start_line = class_node.start_point[0]

            class_name = class_node.text.decode('utf-8')
            class_is_native = class_name in classes_names  # 构造方法 可以直接判断

            if not line_in_methods_or_classes_ranges(start_line, gb_methods_ranges, classes_ranges):
                args_node = match_dict.get('constructor_args', [None])[0]
                nf_called_info = res_called_construct_method(class_node, args_node, class_is_native)
                nf_called_infos.append(nf_called_info)

    # 处理普通函数调用
    for match in queried.matches(root_node):
        match_dict = match[1]
        if 'function_call' in match_dict:
            func_node = match_dict['function_call'][0]
            start_line = func_node.start_point[0]

            if not line_in_methods_or_classes_ranges(start_line, gb_methods_ranges, classes_ranges):
                func_name = func_node.text.decode('utf-8')
                args_node = match_dict.get('function_args', [None])[0]

                # 分析函数类型
                method_is_native = func_name in gb_methods_names
                nf_called_info = res_called_general_method(func_node, func_name, args_node, method_is_native)
                nf_called_infos.append(nf_called_info)

    # 判断函数是否有内容, 有的话进行结果返回
    if nf_called_infos:
        nf_name_txt = ClassKeys.NOT_IN_METHOD.value
        nf_start_line = root_node.start_point[0]
        nf_end_line = root_node.end_point[0]
        nf_method_info = create_method_result_dict(nf_name_txt, nf_start_line, nf_end_line, None, None, None, nf_called_infos, None)
        return nf_method_info
    return None
