from tree_const import PHP_MAGIC_METHODS, PHP_BUILTIN_FUNCTIONS
from tree_enums import MethodType, MethodKeys


def guess_method_type(method_name, is_native_method_or_class, is_class_method):
    """根据被调用的函数完整信息猜测函数名"""
    if is_class_method:
        method_type = MethodType.CLASS.value
        # 判断方法是否是php类的内置构造方法
        if method_name == '__construct':
            method_type = MethodType.CONSTRUCT.value
        # 判断方法是否是php类的内置魔术方法
        elif method_name in PHP_MAGIC_METHODS and is_native_method_or_class is False:
            method_type = MethodType.BUILTIN.value
    else:
        method_type = MethodType.GENERAL.value
        # 判断方法是否是php内置方法
        if method_name in PHP_BUILTIN_FUNCTIONS and is_native_method_or_class is False:
            method_type = MethodType.BUILTIN.value
        # 判断方法是否时动态调用方法
        elif method_name.startswith("$"):
            method_type = MethodType.DYNAMIC.value
    return method_type


def find_nearest_class_info(object_line, object_class_infos):
    nearest_class = find_nearest_info_by_line(object_line, object_class_infos, start_key=MethodKeys.START_LINE.value)
    return nearest_class


def guess_called_object_is_native(object_name, object_line, gb_classes_names, gb_object_class_infos):
    """从本文件中初始化类信息字典分析对象属于哪个类"""
    # [{'METHOD_OBJECT': '$myClass', 'METHOD_CLASS': 'MyClass', 'METHOD_START_LINE': 5},,,]
    if object_name in gb_classes_names:
        return True, object_name

    # 通过对象名称 初次筛选获取命中的类信息
    filtered_object_infos = [info for info in gb_object_class_infos if info.get(MethodKeys.OBJECT.value, None) == object_name]
    if filtered_object_infos:
        # 进一步筛选最近的类创建信息
        nearest_class_info = find_nearest_class_info(object_line, filtered_object_infos)
        print(f"nearest_class_info:{nearest_class_info}")
        return True, nearest_class_info[MethodKeys.CLASS.value]
    return False,None


def find_nearest_info_by_line(object_line, object_class_infos, start_key):
    """根据目标行号查找最近的类对象创建信息名称（类对象创建的开始行号必须小于等于目标行号）"""
    if not object_class_infos:
        return None  # 如果命名空间列表为空，直接返回 None

    # 筛选出所有行号小于等于目标行号的命名空间
    valid_infos = [x for x in object_class_infos if x[start_key] <= object_line]
    if not valid_infos:
        return None  # 如果没有符合条件的命名空间，返回 None
    # 找到行号最大的命名空间信息（即最接近目标行号的命名空间）
    nearest_class = max(valid_infos, key=lambda ns: ns[start_key])
    return nearest_class