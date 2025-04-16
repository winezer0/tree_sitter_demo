from tree_enums import ClassKeys, MethodKeys, FileInfoKeys
from tree_sitter_uitls import get_strs_hash, custom_format_path


def fix_method_infos_uniq_id(method_infos: list[dict], file_path: str):
    """为方法信息填充ID数据等"""

    def calc_method_uniq_id(method_info: dict):
        m_file = method_info.get(MethodKeys.FILE.value)
        m_class = method_info.get(MethodKeys.METHOD_CLASS.value)
        m_name = method_info.get(MethodKeys.NAME.value)
        m_start = method_info.get(MethodKeys.START.value)
        m_end = method_info.get(MethodKeys.END.value)
        uniq_id = get_strs_hash(f"{m_file}|{m_class}|{m_name}|{m_start}|{m_end}")
        uniq_id = f"method_{uniq_id}"
        return uniq_id

    # 循环进行信息补充
    for index, method_info in enumerate(method_infos):
        # 修复方法信息的文件路径
        method_info[MethodKeys.FILE.value] = file_path
        # 修复方法信息的唯一标识符逻辑
        method_info[MethodKeys.UNIQ_ID.value] = calc_method_uniq_id(method_info)
        # 把更新保存到原数据中
        method_infos[index] = method_info
    return method_infos


def fix_class_infos_uniq_id(class_infos: list[dict], file_path: str):
    """为生成的类信息补充数据"""

    def calc_class_uniq_id(class_info: dict):
        c_file = class_info.get(ClassKeys.FILE.value)
        c_namespace = class_info.get(ClassKeys.NAMESPACE.value)
        c_name = class_info.get(ClassKeys.NAME.value)
        c_start = class_info.get(ClassKeys.START.value)
        c_end = class_info.get(ClassKeys.END.value)
        uniq_id = get_strs_hash(f"{c_file}|{c_namespace}|{c_name}|{c_start}|{c_end}")
        uniq_id = f"class_{uniq_id}"
        return uniq_id

    for index, class_info in enumerate(class_infos):
        # 修复方法信息的文件路径
        class_info[ClassKeys.FILE.value] = file_path
        # 修复方法信息的唯一标识符逻辑
        class_info[ClassKeys.UNIQ_ID.value] = calc_class_uniq_id(class_info)
        class_infos[index] = class_info
    return class_infos


def fix_called_method_file_by_native(called_method_infos: list[dict], file_path: str):
    # 循环进行信息补充
    for index, called_method_info in enumerate(called_method_infos):
        # 如果是本地方法的话 就设置文件路径
        if called_method_info.get(MethodKeys.IS_NATIVE.value, False):
            called_method_info[MethodKeys.FILE.value] = file_path
            called_method_infos[index] = called_method_info
    return called_method_infos




def fix_parsed_infos_basic_info(parsed_infos:dict):
    """修复函数和类的UNIQ和FILE信息"""
    for file_path, parsed_info in parsed_infos.items():
        # 格式化路径
        file_path = custom_format_path(file_path)

        # 填充 类信息中ID和路径信息
        class_infos = parsed_info.get(FileInfoKeys.CLASS_INFOS.value, [])
        parsed_info[FileInfoKeys.CLASS_INFOS.value] = fix_class_infos_uniq_id(class_infos, file_path)

        # 填充 全局代码中的方法信息
        global_method_infos = parsed_info.get(FileInfoKeys.METHOD_INFOS.value, [])
        parsed_info[FileInfoKeys.METHOD_INFOS.value] = fix_method_infos_uniq_id(global_method_infos, file_path)

        # 填充 类信息中的方法信息
        class_infos = parsed_info.get(FileInfoKeys.CLASS_INFOS.value, [])
        for class_info in class_infos:
            class_method_infos = class_info.get(ClassKeys.METHODS.value, [])
            class_info[ClassKeys.METHODS.value] = fix_method_infos_uniq_id(class_method_infos, file_path)

        # 填充 called_methods 中的部分已知信息
        global_method_infos = parsed_info.get(FileInfoKeys.METHOD_INFOS.value, [])
        for global_method_info in global_method_infos:
            # 获取调用方法信息 并逐个进行修改
            called_method_infos = global_method_info.get(MethodKeys.CALLED.value, [])
            global_method_info[MethodKeys.CALLED.value] = fix_called_method_file_by_native(called_method_infos, file_path)

        # 填充 class 中的 called_methods 中的部分已知信息
        class_infos = parsed_info.get(FileInfoKeys.CLASS_INFOS.value, [])
        for class_info in class_infos:
            class_method_infos = class_info.get(ClassKeys.METHODS.value, [])
            for class_method_info in class_method_infos:
                called_method_infos = class_method_info.get(MethodKeys.CALLED.value, [])
                class_method_info[MethodKeys.CALLED.value] = fix_called_method_file_by_native(called_method_infos, file_path)

    return parsed_infos
