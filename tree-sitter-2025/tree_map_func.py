from collections import defaultdict
from ftplib import all_errors

from tree_const import *


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

        # 2、为所有的方法补充 额外信息
        for method_info in all_method_infos:
            method_info[METHOD_FILE] = format_path(file_path)   # 填充文件路径信息
            method_info[CALLED_BY_METHODS] = []                 # CALLED_BY_METHODS 预填充被调用的未知

    # 2、创建 方法名和方法信息字典 ｛方法名称:[方法信息,方法信息]｝
    method_name_info_map = defaultdict(list)  # 默认值为列表 无需初始化
    for method_info in all_method_infos:
        method_full_name = method_info.get(METHOD_FULL_NAME)
        method_name_info_map[method_full_name].append(method_info)
    return method_name_info_map


def rev_find_local_method(called_method, method_name_info_map):
    # 先查找同名函数 然后通过文件名过滤
    method_name = called_method.get(METHOD_NAME)
    if method_name is None:
        print(f"严重错误!!! 发现异常的本地方法:{called_method}")
        return None

    possible_methods = method_name_info_map.get(method_name)
    if not possible_methods:
        print(f"严重错误!!! 未发现同名的本地方法:{called_method}")
        return None

    if len(possible_methods) > 1:
        # 存在多个同名方法需要继续查找 常见于java重载、php单文件多类 一般都是构造函数才会重复
        # 在php中还可以通过方法参数数量进行判断
        # 通过文件名进行筛选
        possible_methods =  [x.get(METHOD_FILE) == called_method[METHOD_FILE] for x in possible_methods]
        # 通过函数参数数量进行筛选
        possible_methods =  [len(x.get(METHOD_PARAMETERS)) >= len(called_method[METHOD_PARAMETERS]) for x in possible_methods]

    return possible_methods



def repair_called_methods(method_name_info_map):
    """补充CALLED_METHODS的详细信息"""
    for method_full_name, method_infos in method_name_info_map.items():
        for method_info in method_infos:
            method_file = method_info.get(METHOD_FILE)
            for called_method in method_info.get(CALLED_METHODS):
                if called_method.get(METHOD_TYPE) == LOCAL_METHOD:
                    # 如果是本地方法 说明是被当前文件调用的,更新 METHOD_FILE 为 method_file
                    called_method[METHOD_FILE] = method_file
                    # TODO 需要从建立的所有函数映射表中反查获取方法数据 并更新
                    find_infos = rev_find_local_method(method_name_info_map, called_method)

                elif called_method.get(METHOD_TYPE) in [BUILTIN_METHOD]:  #
                    # 如果是内置方法 说明数据保存了 内置方法函数,应该忽略掉
                    called_method[METHOD_FILE] = method_file
                    # TODO 需要获取方法数据 并更新
                elif called_method.get(METHOD_TYPE) in [CUSTOM_METHOD, DYNAMIC_METHOD]:
                    # 如果是自定义方法 还需要从别的文件进行查找 动态方法还不一定能查到
                    called_method[METHOD_FILE] = "Need Find File"
                    # TODO 需要获取方法数据 并更新
                elif called_method.get(METHOD_TYPE) in [CLASS_METHOD, CONSTRUCTOR]:
                    called_method[METHOD_FILE] = "Need Find Class"
                else:
                    print(f"发现未预期的被调用方法类型!!! 需要进行分析:{called_method}")
                    exit()
                print_json(called_method)
    return None


def padding_method_call_relation(method_name_info_map):
    """分析补充函数之间的调用关系""" # TODO 分析补充函数之间的调用关系
    method_name_info_map = repair_called_methods(method_name_info_map)
    print_json(method_name_info_map)
    return []

def analyze_func_relation(parsed_infos:dict):
    """整理出所有文件的函数关系"""
    # 整理出函数名和函数信息的映射关系
    method_name_info_map = build_method_map(parsed_infos)
    # 分析补充函数之间的调用关系
    method_name_info_map = padding_method_call_relation(method_name_info_map)
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
