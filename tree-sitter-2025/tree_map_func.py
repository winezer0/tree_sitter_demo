from tree_const import METHOD_INFOS, CLASS_INFOS, CLASS_METHODS, CODE_FILE, METHOD_FULL_NAME, CALLED_BY
from collections import defaultdict

def format_path(path:str):
    return path.replace('\\', '/').replace('//', '/')


def build_method_map(parsed_infos:dict):
    # 1、整理出所有文件函数
    all_method_infos = []
    for file_path, parsed_info in parsed_infos.items():
        # 1.1、获取文件方法
        direct_method_infos = parsed_info.get(METHOD_INFOS)
        all_method_infos.extend(direct_method_infos)
        # 1.2、获取类方法
        for class_info in parsed_info.get(CLASS_INFOS):
            class_method_infos = class_info.get(CLASS_METHODS)
            all_method_infos.extend(class_method_infos)

        # 2、为所有的方法补充CODE_FILE标志和CALLED_BY信息,表名函数来源文件
        for method_info in all_method_infos:
            method_info[CODE_FILE] = format_path(file_path)
            method_info[CALLED_BY] = []
            
    # 2、创建 方法名和方法信息字典 ｛方法名称:[方法信息,方法信息]｝
    method_name_info_map = defaultdict(list)  # 默认值为列表
    for method_info in all_method_infos:
        method_full_name = method_info.get(METHOD_FULL_NAME)
        method_name_info_map[method_full_name].append(method_info)  # 直接追加，无需初始化
    return method_name_info_map


def replenish_method_call_relation(method_name_info_map):
    """分析补充函数之间的调用关系""" # TODO 分析补充函数之间的调用关系
    return []

def analyze_func_relation(parsed_infos:dict):
    """整理出所有文件的函数关系"""
    # 整理出函数名和函数信息的映射关系
    method_name_info_map = build_method_map(parsed_infos)
    # 分析补充函数之间的调用关系
    method_name_info_map = replenish_method_call_relation(method_name_info_map)
    return method_name_info_map

if __name__ == '__main__':
    # Import required modules
    from tree_class_info import analyze_class_infos
    from tree_func_info import analyze_direct_method_infos
    from init_tree_sitter import init_php_parser
    from libs_com.utils_json import print_json
    from libs_com.files_filter import get_php_files
    from tree_func_utils import read_file_to_parse

    # Initialize PHP parser
    PARSER, LANGUAGE = init_php_parser()
    
    # Set test directory
    project_path = r"php_demo/func_call_demo"
    project_path = r"php_demo/class_call_demo"
    php_files = get_php_files(project_path)
    parsed_infos = {}
    for abspath_path in php_files:
        php_file_tree = read_file_to_parse(PARSER, abspath_path)
        # 分析函数信息
        method_infos = analyze_direct_method_infos(php_file_tree, LANGUAGE)
        # 分析类信息（在常量分析之后添加）
        class_infos = analyze_class_infos(php_file_tree, LANGUAGE)

        # 修改总结结果信息
        parsed_infos[abspath_path] = {METHOD_INFOS: method_infos, CLASS_INFOS: class_infos}
    # print(f"parsed_infos:======================")
    # print_json(parsed_infos)
    # print(f"parsed_infos:======================")
    # Dictionary to store parsed information
    analyzed_infos = analyze_func_relation(parsed_infos)
