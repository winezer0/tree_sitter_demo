from tree_const import PHP_MAGIC_METHODS, PHP_BUILTIN_FUNCTIONS
from tree_enums import MethodType, MethodKeys


def guess_method_type(method_name, method_is_native, is_class_method):
    """根据被调用的函数完整信息猜测函数名"""
    if is_class_method:
        method_type = MethodType.CLASS.value
        # 判断方法是否是php类的内置构造方法
        if method_name == '__construct':
            method_type = MethodType.CONSTRUCT.value
        # 判断方法是否是php类的内置魔术方法
        elif method_name in PHP_MAGIC_METHODS and method_is_native is False:
            method_type = MethodType.BUILTIN.value
    else:
        method_type = MethodType.GENERAL.value
        # 判断方法是否是php内置方法
        if method_name in PHP_BUILTIN_FUNCTIONS and method_is_native is False:
            method_type = MethodType.BUILTIN.value
        # 判断方法是否时动态调用方法
        elif method_name.startswith("$"):
            method_type = MethodType.DYNAMIC.value
    return method_type


def guess_called_object_is_native(object_name, object_line, classes_names, object_class_infos):
    """从本文件中初始化类信息字典分析对象属于哪个类"""
    # [{'METHOD_OBJECT': '$myClass', 'METHOD_CLASS': 'MyClass', 'METHOD_START_LINE': 5},,,]
    if object_name in classes_names:
        return True, object_name

    # 通过对象名称 初次筛选获取命中的类信息
    filtered_infos_1 = []
    for object_class_info in object_class_infos:
        if object_name == object_class_info.get(MethodKeys.OBJECT.value):
            filtered_infos_1.append(object_class_info)

    # 使用初始化对象的代码位置来进行来进行筛选 因为对象构造方法的定义一般都在对象调用方法之前
    filtered_infos_2 = []
    # 从类中类的创建在类的调用之前的选项
    for obj_cls_info in filtered_infos_1:
        if int(obj_cls_info.get(MethodKeys.START_LINE.value)) <= int(object_line):
            filtered_infos_2.append(obj_cls_info)

    if len(filtered_infos_2)==1:
        # 刚好找到1个,直接进行返回即可
        class_name = filtered_infos_1[0].get(MethodKeys.CLASS.value)
        return True,class_name
    elif len(filtered_infos_2)>1:
        # 如果两个构造方法创建的时间小于方法调用,就用其中start_line最大的那个
        obj_cls_info = max(filtered_infos_2, key=lambda x: x.get(MethodKeys.START_LINE.value))
        class_name = obj_cls_info.get(MethodKeys.CLASS.value)
        return True,class_name
    else:
        # 如果一个都没发现,说明应该不是
        return False,None


