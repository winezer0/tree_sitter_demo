from collections import defaultdict

from tree_enums import ClassKeys, FileInfoKeys, MethodKeys


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
        methods = class_info.get(ClassKeys.METHODS.value, {})
        if method_name in methods:
            possible_class_info.append(class_info)
    return possible_class_info


def build_method_map(parsed_infos:dict):
    # 1、整理出所有文件函数
    all_method_infos = []
    for file_path, parsed_info in parsed_infos.items():
        # 1.1、获取文件方法
        direct_method_infos = parsed_info.get(FileInfoKeys.METHOD_INFOS.value)
        all_method_infos.extend(direct_method_infos)
        # 1.2、获取类方法
        for class_info in parsed_info.get(FileInfoKeys.CLASS_INFOS.value):
            class_method_infos = class_info.get(ClassKeys.METHODS.value)
            all_method_infos.extend(class_method_infos)

        # 2、为所有的方法补充 额外信息
        for method_info in all_method_infos:
            method_info[MethodKeys.FILE.value] = format_path(file_path)   # 填充文件路径信息
            method_info[MethodKeys.CALLED_MAY.value] = []                   # CALLED_BY_METHODS 预填充调用的信息
            method_info[MethodKeys.CALLED_BY_MAY.value] = []                 # CALLED_BY_METHODS 预填充被调用的信息

    # 2、创建 方法名和方法信息字典 ｛方法名称:[方法信息,方法信息]｝
    method_name_info_map = defaultdict(list)  # 默认值为列表 无需初始化
    for method_info in all_method_infos:
        method_full_name = method_info.get(MethodKeys.FULLNAME.value)
        method_name_info_map[method_full_name].append(method_info)
    return method_name_info_map


def format_path(path:str):
    return path.replace('\\', '/').replace('//', '/')
