from typing import List, Dict, Any
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from libs_com.file_io import read_file_bytes
from libs_com.file_path import get_root_dir, get_relative_path, file_is_empty
from libs_com.files_filter import get_php_files
from libs_com.utils_hash import get_path_hash
from libs_com.utils_json import dump_json
from libs_com.utils_process import print_progress
from init_tree_sitter import init_php_parser
from tree_const import METHOD_INFOS, IMPORT_INFOS, VARIABLE_INFOS, CONSTANT_INFOS, CLASS_INFOS
from tree_func_info import analyze_direct_method_infos
from tree_func_map import analyze_func_relation
from tree_imports_info import get_import_info
from tree_var_analyzer import analyze_php_variables
from tree_const_info import analyze_php_constants
# 首先添加导入
from tree_class_info import analyze_class_infos


class PHPParser:
    def __init__(self, project_name, project_path, build_mode=True):
        # 初始化解析器
        self.PARSER, self.LANGUAGE = init_php_parser()
        self.project_path = project_path
        self.project_root = get_root_dir(project_path)
        self.relation_cache = f"{project_name}.{get_path_hash(project_path)}.parse.cache"

    def parse_php_file(self, php_file):
        # 获取相对路径
        relative_path = get_relative_path(php_file, self.project_root)
        parsed_info = None
        # 解析tree
        php_file_bytes = read_file_bytes(php_file)
        print(f"read_file_bytes:->{relative_path}")
        php_file_tree = self.PARSER.parse(php_file_bytes)
        # print(f"php_file_tree:->{php_file_tree.root_node}")
        
        # 分析依赖信息
        import_info = get_import_info(php_file_tree, self.LANGUAGE)
        print(f"import_info:->{import_info}")
        
        # 分析函数信息
        method_infos = analyze_direct_method_infos(php_file_tree, self.LANGUAGE)
        print(f"function_info:->{method_infos}")
        
        # 分析变量信息
        variables_infos = analyze_php_variables(php_file_tree, self.LANGUAGE)
        print(f"variables_info:->{variables_infos}")
        
        # 分析常量信息
        constants_infos = analyze_php_constants(php_file_tree, self.LANGUAGE)
        print(f"constants_info:->{constants_infos}")
        
        # 分析类信息（在常量分析之后添加）
        class_infos = analyze_class_infos(php_file_tree, self.LANGUAGE)
        print(f"class_info:->{class_infos}")
        
        # 修改总结结果信息
        parsed_info = {
            METHOD_INFOS: method_infos,
            IMPORT_INFOS: import_info,
            VARIABLE_INFOS: variables_infos,
            CONSTANT_INFOS: constants_infos,
            CLASS_INFOS: class_infos,
        }
        return relative_path, parsed_info

    def parse_php_files(self, php_files, workers=None):
        parse_infos = {}
        # 使用多线程解析文件
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # 提交任务到线程池
            start_time = time.time()
            futures = [executor.submit(self.parse_php_file, file) for file in php_files]
            for index, future in enumerate(as_completed(futures), start=1):
                relative_path, parsed_info = future.result()
                print_progress(index, len(php_files), start_time)
                if parsed_info:
                    parse_infos[relative_path] = parsed_info
        return parse_infos

    def analyse(self, save_cache=True):
        """运行PHP解析器"""
        start_time = time.time()
        #  加载已存在的解析结果
        if file_is_empty(self.relation_cache):
            php_files = get_php_files(self.project_path)
            parsed_infos = self.parse_php_files(php_files)
            print(f"代码结构初步解析完成:->{time.time() - start_time:.1f} 秒")
        else:
            print(f"加载缓存分析结果文件:->{self.relation_cache}")
            parsed_infos = json.load(open(self.relation_cache, "r", encoding="utf-8"))
        # 分析函数调用关系
        relation_info = analyze_func_relation(parsed_infos)
        print(f"函数调用关系分析完成 总用时: {time.time() - start_time:.1f} 秒")
        if save_cache:
            dump_json(self.relation_cache, relation_info, encoding='utf-8', indent=2, mode="w+")
        return relation_info
