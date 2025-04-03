from tree_const import CLASS_METHODS


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
