import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from tree_define_namespace import analyse_namespace_define_infos
from tree_sitter_uitls import init_php_parser, read_file_to_root
from libs_com.file_io import read_file_bytes
from libs_com.file_path import get_root_dir, get_relative_path, file_is_empty
from libs_com.files_filter import get_php_files
from libs_com.utils_hash import get_path_hash
from libs_com.utils_json import dump_json
from libs_com.utils_process import print_progress
# 首先添加导入
from tree_class_info import analyze_class_infos
from tree_variable_info import analyze_variable_infos, parse_constants_node
from tree_enums import FileInfoKeys
from tree_func_info import analyze_direct_method_infos
from tree_import_info import analyze_import_infos
from tree_map_relation import analyze_methods_relation


class PHPParser:
    def __init__(self, project_name, project_path):
        # 初始化解析器
        self.PARSER, self.LANGUAGE = init_php_parser()
        self.project_path = project_path
        self.project_root = get_root_dir(project_path)
        self.parsed_cache = f"{project_name}.{get_path_hash(project_path)}.parse.cache"

    @staticmethod
    def parse_php_file(abspath_path, parser, language, relative_path=None):
        # 解析tree
        root_node = read_file_to_root(parser, abspath_path)

        # 分析函数信息
        method_infos = analyze_direct_method_infos(parser, language, root_node)
        # 分析类信息（在常量分析之后添加）
        class_infos = analyze_class_infos(language, root_node)

        # 分析依赖信息和分析导入信息 可用于方法范围限定
        import_infos = analyze_import_infos(language, root_node)
        namespace_infos = analyse_namespace_define_infos(language, root_node)

        # 分析变量和常量信息 目前没有使用
        variables_infos = analyze_variable_infos(parser, language, root_node)

        # 修改总结结果信息
        parsed_info = {
            FileInfoKeys.METHOD_INFOS.value: method_infos,
            FileInfoKeys.CLASS_INFOS.value: class_infos,
            FileInfoKeys.IMPORT_INFOS.value: import_infos,
            FileInfoKeys.NAMESPACE_INFOS.value: namespace_infos,
            FileInfoKeys.VARIABLE_INFOS.value: variables_infos,
        }
        if relative_path is None:
            relative_path = abspath_path
        return relative_path, parsed_info

    def parse_php_files(self, php_files, workers=None):
        parse_infos = {}
        # 使用多线程解析文件
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # 提交任务到线程池
            start_time = time.time()
            futures = [executor.submit(
                self.parse_php_file,file, self.PARSER, self.LANGUAGE, get_relative_path(file, self.project_root))
                       for file in php_files
                       ]
            for index, future in enumerate(as_completed(futures), start=1):
                relative_path, parsed_info = future.result()
                print_progress(index, len(php_files), start_time)
                if parsed_info:
                    parse_infos[relative_path] = parsed_info
        return parse_infos

    def analyse(self, save_cache=True):
        """运行PHP解析器"""
        #  加载已存在的解析结果
        if file_is_empty(self.parsed_cache):
            start_time = time.time()
            php_files = get_php_files(self.project_path)
            parsed_infos = self.parse_php_files(php_files)
            print(f"代码结构初步解析完成  用时:{time.time() - start_time:.1f} 秒")
            # 补充函数调用信息
            start_time = time.time()
            parsed_infos = analyze_methods_relation(parsed_infos)
            print(f"补充函数调用信息完成 用时: {time.time() - start_time:.1f} 秒")

            if save_cache:
                dump_json(self.parsed_cache, parsed_infos, encoding='utf-8', indent=2, mode="w+")
        else:
            print(f"加载缓存分析结果文件:->{self.parsed_cache}")
            parsed_infos = json.load(open(self.parsed_cache, "r", encoding="utf-8"))
        return parsed_infos

if __name__ == '__main__':
    php_parser =  PHPParser(project_name="default_project", project_path=r"php_demo/class_call_demo")
    php_parser.analyse()
