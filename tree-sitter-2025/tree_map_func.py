from tree_func_utils import read_file_to_parse


def analyze_func_relation(parsed_infos):
    return None


if __name__ == '__main__':
    # Import required modules
    from libs_com.file_io import read_file_bytes
    from tree_class_info import analyze_class_infos
    from tree_const import METHOD_INFOS, CLASS_INFOS
    from tree_func_info import analyze_direct_method_infos
    from init_tree_sitter import init_php_parser
    from libs_com.utils_json import print_json
    from libs_com.files_filter import get_php_files

    # Initialize PHP parser
    PARSER, LANGUAGE = init_php_parser()
    
    # Set test directory
    project_path = r"php_demo/func_call_demo"
    project_path = r"php_demo/class_call_demo"
    php_files = get_php_files(project_path)
    parsed_infos = {}
    for abspath_path in php_files:
        php_file_tree = read_file_to_parse(PARSER, abspath_path)
        print(f"read_file_to_parse:->{abspath_path}")
        # 分析函数信息
        method_infos = analyze_direct_method_infos(php_file_tree, LANGUAGE)
        print(f"function_info:->{method_infos}")
        # 分析类信息（在常量分析之后添加）
        class_infos = analyze_class_infos(php_file_tree, LANGUAGE)
        print(f"class_info:->{class_infos}")
        # 修改总结结果信息
        parsed_infos[abspath_path] = {METHOD_INFOS: method_infos, CLASS_INFOS: class_infos}
    print_json(parsed_infos)

    # Dictionary to store parsed information
    analyzed_infos = analyze_func_relation(parsed_infos)
    print_json(analyzed_infos)