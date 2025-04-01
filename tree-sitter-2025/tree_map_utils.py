from tree_class_info import CLASS_NAME, CLASS_METHODS, METHOD_NAME, METHOD_IS_STATIC, METHOD_VISIBILITY, \
    METHOD_START_LINE, METHOD_END_LINE, METHOD_PARAMS, CLASS_TYPE, CLASS_PROPS
from tree_const import FUNCTIONS, CLASS_INFO, FUNCTION, CLASS_METHOD, FUNC_TYPE, php_magic_methods
from tree_func_info import FUNC_NAME, FUNC_PARAMS, FUNC_START_LINE, FUNC_END_LINE

CALLS = 'calls'
CALLED_BY = 'called_by'
CODE_FILE = 'code_file'


def init_calls_value(parsed_infos):
    # 初始化调用关系字段
    if parsed_infos:
        for _, parsed_info in parsed_infos.items():
            for function_info in parsed_info.get(FUNCTIONS, []):
                if CALLS not in function_info:
                    function_info[CALLS] = []
                if CALLED_BY not in function_info:
                    function_info[CALLED_BY] = []

            for class_info in parsed_info.get(CLASS_INFO, []):
                for function_info in class_info.get(CLASS_METHODS, []):
                    if CALLS not in function_info:
                        function_info[CALLS] = []
                    if CALLED_BY not in function_info:
                        function_info[CALLED_BY] = []
    return parsed_infos


def build_function_map(parsed_infos):
    """建立函数和类方法名到文件位置的映射 func -> list 格式""" 
    function_map = {}
    # 第一遍：建立基本映射
    for file_path, file_info in parsed_infos.items():
        # 记录普通函数的 函数名->函数信息关系
        for func_info in file_info.get(FUNCTIONS):
            func_name = func_info[FUNC_NAME]

            if func_name not in function_map:
                function_map[func_name] = []

            func_dict = {
                FUNC_TYPE: FUNCTION,
                CODE_FILE: file_path,
                FUNC_PARAMS: func_info.get(FUNC_PARAMS),
                FUNC_START_LINE: func_info.get(FUNC_START_LINE),
                FUNC_END_LINE: func_info.get(FUNC_END_LINE)
            }
            function_map[func_name].append(func_dict)

        print("开始建立类函数的映射...")
        for class_info in file_info.get(CLASS_INFO):
            class_name = class_info.get(CLASS_NAME)
            # 记录类的方法
            for method in class_info.get(CLASS_METHODS):
                method_name = method.get(METHOD_NAME)
                full_method_name = f"{class_name}::{method_name}"

                # 记录到函数映射
                if full_method_name not in function_map:
                    function_map[full_method_name] = []

                full_method_info = {
                    CODE_FILE: file_path,
                    CLASS_NAME: class_name,
                    METHOD_NAME: method_name,
                    FUNC_TYPE: CLASS_METHOD,
                    METHOD_IS_STATIC: method.get(METHOD_IS_STATIC),
                    METHOD_VISIBILITY: method.get(METHOD_VISIBILITY),
                    METHOD_PARAMS: method.get(METHOD_PARAMS),
                    METHOD_START_LINE: method.get(METHOD_START_LINE),
                    METHOD_END_LINE: method.get(METHOD_END_LINE),
                }
                function_map[full_method_name].append(full_method_info)

    return function_map


def build_classes_map(parsed_infos):
    """建立函数和类方法名到文件位置的映射 class_name-> {class_name:class_dict}格式"""
    class_map = {}

    for file_path, file_info in parsed_infos.items():
        print("开始建立类信息的映射...")
        for class_info in file_info.get(CLASS_INFO):
            class_name = class_info.get(CLASS_NAME)
            class_dict = {
                CLASS_NAME: class_info.get(CLASS_NAME),
                CODE_FILE: file_path,
                CLASS_TYPE: class_info.get(CLASS_TYPE),
                CLASS_PROPS: class_info.get(CLASS_PROPS),
                CLASS_METHODS: {},
            }
            class_map[class_name] = class_dict

            for method in class_info.get(CLASS_METHODS):
                method_name = method[METHOD_NAME]
                class_map[class_name][CLASS_METHODS][method_name] = method
    return class_map


def is_php_magic_method(method_name):
    """检查给定的方法名是否是 PHP 的内置魔术方法。 """
    return method_name in php_magic_methods


def find_class_infos_by_method(method_name, class_map):
    """
    根据方法名找到包含该方法的类信息。

    :param method_name: 要查找的方法名，例如 'classMethod'。
    :param class_map: 类映射字典，包含类及其方法信息。
    :return: 包含该方法的类信息， [{'file': 'MyClass.php', 'type': 'class', 'methods': {'classMethod':....]
    """
    possible_class_info = []
    for class_name, class_info in class_map.items():
        # 检查 methods 字段是否存在，并且是否包含指定的方法名
        methods = class_info.get(CLASS_METHODS, {})
        if method_name in methods:
            possible_class_info.append(class_info)
    return possible_class_info
