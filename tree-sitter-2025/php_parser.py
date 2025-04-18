import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from libs_com.file_path import get_root_dir, get_relative_path, file_is_empty, path_is_exist
from libs_com.files_filter import get_php_files
from libs_com.utils_hash import get_path_hash
from libs_com.utils_json import dump_json
from libs_com.utils_process import print_progress
from tree_php.php_parser_args import parse_php_parser_args
from tree_php.php_class_info import analyze_class_infos
from tree_php.php_enums import FileInfoKeys, ClassKeys
from tree_php.php_func_info import analyze_direct_method_infos
from tree_php.php_map_relation import analyze_methods_relation
from tree_uitls.tree_sitter_uitls import init_php_parser, read_file_to_root
from tree_php.php_variable_info import analyze_variable_infos
from tree_php.php_dependent_utils import analyse_dependent_infos


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
        # 解析出基础依赖信息用于函数调用呢
        dependent_infos = analyse_dependent_infos(language, root_node)

        # 分析函数信息
        method_infos = analyze_direct_method_infos(parser, language, root_node, dependent_infos)
        # 分析类信息（在常量分析之后添加）
        class_infos = analyze_class_infos(language, root_node, dependent_infos)
        # 分析变量和常量信息 目前没有使用
        variables_infos = analyze_variable_infos(parser, language, root_node, dependent_infos)

        # 结果信息
        parsed_info = {
            FileInfoKeys.METHOD_INFOS.value: method_infos,
            FileInfoKeys.CLASS_INFOS.value: class_infos,
            FileInfoKeys.VARIABLE_INFOS.value: variables_infos,
            FileInfoKeys.DEPEND_INFOS.value: dependent_infos,
        }

        if relative_path is None:
            relative_path = abspath_path
        return relative_path, parsed_info

    def parse_php_files_threads(self, php_files, workers=None):
        parse_infos = {}
        # 使用多线程解析文件
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # 提交任务到线程池
            start_time = time.time()
            futures = [executor.submit(
                self.parse_php_file,file, self.PARSER, self.LANGUAGE, get_relative_path(file, self.project_root))
                       for file in php_files]
            for index, future in enumerate(as_completed(futures), start=1):
                relative_path, parsed_info = future.result()
                print_progress(index, len(php_files), start_time)
                if parsed_info:
                    parse_infos[relative_path] = parsed_info
        return parse_infos

    def parse_php_files_single(self, php_files):
        parse_infos = {}
        start_time = time.time()
        for index, file in enumerate(php_files, start=1):
            relative_path, parsed_info = self.parse_php_file(file,self.PARSER, self.LANGUAGE, get_relative_path(file, self.project_root))
            print_progress(index, len(php_files), start_time)
            if parsed_info:
                parse_infos[relative_path] = parsed_info
        return parse_infos


    def analyse(self, save_cache=True, workers=None):
        """运行PHP解析器"""
        #  加载已存在的解析结果
        if file_is_empty(self.parsed_cache):
            start_time = time.time()
            php_files = get_php_files(self.project_path)
            if workers == 1:
                parsed_infos = self.parse_php_files_single(php_files)
            else:
                parsed_infos = self.parse_php_files_threads(php_files, workers=workers)
            print(f"\n代码结构初步解析完成  用时:{time.time() - start_time:.1f} 秒")
            if save_cache:
                dump_json(self.parsed_cache, parsed_infos, encoding='utf-8', indent=2, mode="w+")
        else:
            print(f"\n加载缓存分析结果文件:->{self.parsed_cache}")
            parsed_infos = json.load(open(self.parsed_cache, "r", encoding="utf-8"))

        # 补充函数调用信息
        start_time = time.time()
        analyze_infos = analyze_methods_relation(parsed_infos)
        print(f"\n补充函数调用信息完成 用时: {time.time() - start_time:.1f} 秒")
        return analyze_infos


if __name__ == '__main__':
    args = parse_php_parser_args()

    project_path = args.project_path
    if not project_path or not path_is_exist(project_path):
        print("[!] 请输入有效的项目路径!!!!")
        exit()

    project_name = args.project_name
    workers = args.workers
    save_cache = args.save_cache

    # project_name = "default_project"
    # project_path = r"C:\phps\WWW\TestCode\EcShopBenTengAppSample"
    php_parser = PHPParser(project_name=project_name, project_path=project_path)
    parsed_infos = php_parser.analyse(save_cache=save_cache, workers=workers)

    # 定义要处理的信息类型
    info_types = {
        'variable': FileInfoKeys.VARIABLE_INFOS.value,
        'depend': FileInfoKeys.DEPEND_INFOS.value,
        'method': FileInfoKeys.METHOD_INFOS.value,
        'class': FileInfoKeys.CLASS_INFOS.value
    }

    # 定义要处理的信息类型
    info_types = [
        FileInfoKeys.VARIABLE_INFOS.value,
        FileInfoKeys.DEPEND_INFOS.value,
        FileInfoKeys.METHOD_INFOS.value,
        FileInfoKeys.CLASS_INFOS.value,
    ]

    # 按类型处理并保存，避免一次性存储所有数据
    for info_type in info_types:
        curr_type_infos = {}
        for relative_path, parsed_info in parsed_infos.items():
            curr_file_infos = parsed_info.get(info_type, None)
            # 当获取方法信息时 进行额外处理
            if info_type == FileInfoKeys.METHOD_INFOS.value:
                # 当获取方法信息时，往信息中补充类方法信息
                for class_info in parsed_info.get(FileInfoKeys.CLASS_INFOS.value, []):
                    class_method_infos = class_info.get(ClassKeys.METHODS.value, [])
                    curr_file_infos.extend(class_method_infos)

            if curr_file_infos:
                curr_type_infos[relative_path] = curr_file_infos

        # 立即写入文件并释放内存
        output_file = f"{args.output}.{info_type}.json" if args.output else f"{project_name}.parsed.{info_type}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(curr_type_infos, f, ensure_ascii=False, indent=2)
        del curr_type_infos  # 显式释放内存（可选）

