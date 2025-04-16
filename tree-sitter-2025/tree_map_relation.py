from tree_enums import FileInfoKeys
from tree_import_info import analyze_import_infos
from tree_map_called import fix_parsed_infos_called_info, build_method_info_map
from libs_com.utils_json import print_json
from tree_map_basic import fix_parsed_infos_basic_info


def analyze_methods_relation(parsed_infos:dict):
    """整理出所有文件的函数关系"""
    # 为原始信息进行进行基本的信息补充
    parsed_infos = fix_parsed_infos_basic_info(parsed_infos)
    # 进一步补充被调用函数的信息
    # 获取常用的对应关系映射
    method_info_map = build_method_info_map(parsed_infos)
    parsed_infos = fix_parsed_infos_called_info(parsed_infos, method_info_map)
    print("===============================")
    print_json(parsed_infos)
    print("===============================")
    return parsed_infos

if __name__ == '__main__':
    # Import required modules
    from tree_class_info import analyze_class_infos
    from tree_func_info import analyze_direct_method_infos
    from tree_sitter_uitls import init_php_parser, read_file_to_root, custom_format_path
    from libs_com.files_filter import get_php_files

    # Initialize PHP parser
    PARSER, LANGUAGE = init_php_parser()
    
    # Set test directory
    project_path = r"php_demo/func_call_demo"
    project_path = r"php_demo/class_call_demo"
    php_files = get_php_files(project_path)
    parsed_infos = {}
    for abspath_path in php_files:
        abspath_path =  custom_format_path(abspath_path)
        root_node = read_file_to_root(PARSER, abspath_path)
        # 分析函数信息
        method_infos = analyze_direct_method_infos(PARSER, LANGUAGE, root_node)
        # print_json(method_infos)
        # 分析类信息（在常量分析之后添加）
        class_infos = analyze_class_infos(LANGUAGE, root_node)
        # print_json(class_infos)
        import_infos = analyze_import_infos(LANGUAGE, root_node)
        # print_json(import_infos)

        # 修改总结结果信息
        parsed_infos[abspath_path] = {
            FileInfoKeys.METHOD_INFOS.value: method_infos,
            FileInfoKeys.CLASS_INFOS.value: class_infos,
            FileInfoKeys.IMPORT_INFOS.value: import_infos
        }

    # 修复并解析新的数据
    analyzed_infos = analyze_methods_relation(parsed_infos)
