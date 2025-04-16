from collections import defaultdict

from tree_enums import ClassKeys, MethodKeys, MethodType, PHPVisibility, FileInfoKeys, ImportKey, ImportType
from tree_map_build import *

GLOBAL_METHOD_ID_METHOD_INFO_MAP = "GLOBAL_METHOD_ID_METHOD_INFO_MAP"
GLOBAL_METHOD_NAME_METHOD_IDS_MAP = "GLOBAL_METHOD_NAME_METHOD_IDS_MAP"

CLASS_ID_CLASS_INFO_MAP = "CLASS_ID_CLASS_INFO_MAP"
CLASS_NAME_CLASS_IDS_MAP = "CLASS_NAME_CLASS_IDS_MAP"
CLASS_METHOD_NAME_CLASS_IDS_MAP = "CLASS_METHOD_NAME_CLASS_IDS_MAP"
CLASS_METHOD_FULLNAME_CLASS_IDS_MAP = "CLASS_METHOD_FULLNAME_CLASS_IDS_MAP"


def build_method_info_map(parsed_infos:dict):

    # 1、整理出所有文件中的全局函数信息|类信息
    all_global_methods = get_all_global_methods(parsed_infos)
    all_class_infos = get_all_class_infos(parsed_infos)
    # all_class_methods = get_parsed_infos_all_class_methods(parsed_infos)

    method_info_map = {
        # 全局方法id->方法详情 的对应关系
        GLOBAL_METHOD_ID_METHOD_INFO_MAP: build_method_id_method_info_map(all_global_methods),
        # 全局方法名称->方法id 的对应关系
        GLOBAL_METHOD_NAME_METHOD_IDS_MAP: build_method_name_method_ids_map(all_global_methods),

        # 类ID -> 类详情 的对应关系
        CLASS_ID_CLASS_INFO_MAP: build_class_id_class_info_map(all_class_infos),
        # 类方法名 -> 类IDs 的对应关系
        CLASS_METHOD_NAME_CLASS_IDS_MAP :build_class_method_name_class_ids_map(all_class_infos),
        # 类完整方法名 -> 类 IDs 的对应关系
        CLASS_METHOD_FULLNAME_CLASS_IDS_MAP: build_class_method_fullname_class_ids_map(all_class_infos),
        # 类名称 -> 类IDs 的对应关系
        CLASS_NAME_CLASS_IDS_MAP: build_class_name_class_ids_map(all_class_infos),
    }

    return method_info_map


def filter_methods_by_visibility(possible_method_infos):
    """通过类方法的可访问性进行一次过滤"""
    filtered_method_infos = []
    for possible_method_info in possible_method_infos:
        # 如果没有 visibility 表示是 public 类型
        method_visibility = possible_method_info.get(MethodKeys.VISIBILITY.value, PHPVisibility.PUBLIC.value)
        if PHPVisibility.PRIVATE.value != method_visibility:
            filtered_method_infos.append(possible_method_info)

    print(f"通过类方法可访问性筛选出可能的方法信息:[{len(possible_method_infos)}]个")
    return filtered_method_infos


def filter_methods_by_params_num(called_method_info, possible_method_infos):
    """通过对比参数数量信息过滤可能的方法"""
    # TODO 通过默认值进行优化参数过滤
    filtered_method_infos = []
    for possible_method_info in possible_method_infos:
        if len(possible_method_info[MethodKeys.PARAMS.value]) >= len(called_method_info[MethodKeys.PARAMS.value]):
            filtered_method_infos.append(possible_method_info)

    method_name = called_method_info.get(MethodKeys.NAME.value)
    print(f"基于参数信息筛选[{method_name}]对应方法:[{len(filtered_method_infos)}]个")

    return filtered_method_infos


def filter_methods_by_native_file(called_method_info, possible_method_infos):
    """根据是否是本地方法文件来进行筛选"""
    filtered_method_infos = []
    # 查找其中文件名和 called_method_info 中的文件名相同的对象
    native_file = called_method_info.get(MethodKeys.FILE.value, None)
    for possible_method_info in possible_method_infos:
        possible_file = possible_method_info.get(MethodKeys.FILE.value, None)
        if native_file and possible_file and possible_file == native_file:
            filtered_method_infos.append(possible_method_info)

    called_method_name = called_method_info.get(MethodKeys.NAME.value)
    print(f"基于Native信息 找到[{called_method_name}]对应方法:[{len(filtered_method_infos)}]个 -> File: [{native_file}]")
    return filtered_method_infos


def find_possible_global_methods(called_method_info: dict, method_info_map: dict):
    """查找多个uniq中最有可能的方法"""
    global_method_id_method_info_map = method_info_map.get(GLOBAL_METHOD_ID_METHOD_INFO_MAP)
    global_method_name_method_ids_map = method_info_map.get(GLOBAL_METHOD_NAME_METHOD_IDS_MAP)

    # 获取被调用类的信息
    method_name = called_method_info.get(MethodKeys.NAME.value)
    # 通过方法名称查找可能的全局方法信息
    possible_method_ids = global_method_name_method_ids_map.get(method_name, [])
    print(f"通过方法名[{method_name}]找到可能的全局方法:[{len(possible_method_ids)}]个")

    # 获取 ids 对应的方法详情数据
    possible_method_infos = [global_method_id_method_info_map.get(mid) for mid in possible_method_ids]

    # 通过本地方法标志进行初次筛选
    if called_method_info.get(MethodKeys.IS_NATIVE.value, False):
        possible_method_infos = filter_methods_by_native_file(called_method_info, possible_method_infos)

    # 通过参数数量再一次进行过滤 对于java等语言可以通过参数类型进行过滤
    possible_method_infos = filter_methods_by_params_num(called_method_info, possible_method_infos)

    # TODO 可以通过导入信息和命名命名空间进一步补充筛选
    return possible_method_infos


def find_possible_class_methods(called_method_info: dict, method_info_map: dict):
    class_id_class_info_map = method_info_map.get(CLASS_ID_CLASS_INFO_MAP)

    class_name_class_ids_map = method_info_map.get(CLASS_NAME_CLASS_IDS_MAP)
    clss_method_name_class_ids_map = method_info_map.get(CLASS_METHOD_NAME_CLASS_IDS_MAP)
    clss_method_fullname_class_ids_map = method_info_map.get(CLASS_METHOD_FULLNAME_CLASS_IDS_MAP)

    called_method_fullname = called_method_info.get(MethodKeys.FULLNAME.value)
    called_method_class_name = called_method_info.get(MethodKeys.CLASS.value)

    possible_class_ids = []
    # 1、直接通过完整的方法直接查找可能的类信息
    if not possible_class_ids:
        possible_class_ids = clss_method_fullname_class_ids_map.get(called_method_fullname, [])
        print(f"通过完整方法名[{called_method_fullname}]找到可能的class:[{len(possible_class_ids)}个]")

    # 2、通过类名进行查找可能的类信息
    if not possible_class_ids:
        possible_class_ids = class_name_class_ids_map.get(called_method_class_name, [])
        print(f"通过完整类名[{called_method_class_name}]找到可能的class:[{len(possible_class_ids)}]个")

    # 3、通过不完整的方法名查找可能的对象名
    if not possible_class_ids:
        possible_class_ids = clss_method_name_class_ids_map.get(called_method_class_name, [])
        print(f"通过不完整方法名[{called_method_fullname}]找到可能的class:[{len(possible_class_ids)}]个")

    if not possible_class_ids:
        print(f"所有类信息中都没有找到可能的类方法:[{called_method_fullname}] 请检查!!!")
        return []

    # 获取 ids 对应的方法详情数据
    possible_class_infos = [class_id_class_info_map.get(cid) for cid in possible_class_ids]

    # 如果是本地方法 就通过方法对应的文件信息进行初次筛选
    method_is_native = called_method_info.get(MethodKeys.IS_NATIVE.value, False)
    if method_is_native:
        possible_class_infos = filter_class_by_native_file(called_method_info, possible_class_infos)

    # 从可能的class中获取方法信息
    possible_method_infos = get_class_methods_by_method_name(called_method_info, possible_class_infos)

    # 通过参数数量再一次进行过滤 对于java等语言可以通过参数类型进行过滤
    possible_method_infos = filter_methods_by_params_num(called_method_info, possible_method_infos)

    # 如果不是本地方法 还可以通过 Class方法的可访问性再次进行过滤
    if not method_is_native:
        possible_method_infos = filter_methods_by_visibility(possible_method_infos)

    # TODO 如果是构造函数应该进行额外处理
    # TODO 通过导入信息|命名空间信息可以进一步查找可能的对象方法 暂未实现命名空间信息 需要在解析时进行实现
    return possible_method_infos


def get_class_methods_by_method_name(called_method_info, possible_class_infos):
    """通过被调用的方法名 从可能的类信息中提取方法信息"""
    called_method_name  = called_method_info.get(MethodKeys.NAME.value)
    called_method_fullname  = called_method_info.get(MethodKeys.FULLNAME.value)

    possible_method_infos = []
    for possible_class_info in possible_class_infos:
        method_infos = possible_class_info.get(ClassKeys.METHODS.value, [])
        for method_info in method_infos:
            method_name = method_info[MethodKeys.NAME.value]
            method_fullname = method_info[MethodKeys.FULLNAME.value]
            if method_fullname == called_method_fullname or method_name == called_method_name:
                possible_method_infos.append(method_info)
    print(f"通过被调用方法名筛选[{called_method_fullname}]可能的方法信息:[{len(possible_method_infos)}]个")
    return possible_method_infos


def filter_class_by_native_file(called_method_info, possible_class_infos):
    """通过本地方法属性进行calss过滤"""
    filtered_class_infos = []
    native_file = called_method_info[MethodKeys.FILE.value]
    for possible_class_info in possible_class_infos:
        possible_file = possible_class_info[ClassKeys.FILE.value]
        if native_file and possible_file and possible_file == native_file:
            filtered_class_infos.append(possible_class_info)

    called_method_fullname = called_method_info.get(MethodKeys.FULLNAME.value)
    print(f"基于Native信息 找到[{called_method_fullname}]对应方法: {len(filtered_class_infos)}个 -> File:[{native_file}]")
    return filtered_class_infos

def find_possible_called_methods(called_method_info, method_info_map: dict):
    called_method_fullname = called_method_info.get(MethodKeys.FULLNAME.value)
    called_method_name = called_method_info.get(MethodKeys.NAME.value)
    called_method_type = called_method_info.get(MethodKeys.METHOD_TYPE.value)
    print(f"called method fullname:{called_method_fullname} -> method_type:{called_method_type}")

    # 存储可能的方法信息
    possible_methods = []

    # BUILTIN = "BUILTIN_METHOD"      # PHP内置方法
    if called_method_type in [MethodType.BUILTIN.value]:
        print("被调用的方法是内置方法,无需进行文件信息查询!!!")

    # DYNAMIC = "DYNAMIC_METHOD"      # 动态方法 （使用变量作为函数名）
    elif called_method_type in [MethodType.DYNAMIC.value]:
        print(f"被调用的方法 {called_method_name} 是动态方法 需要结合变量赋值进行动态分析 暂时放弃查询!!!")

    # GENERAL = "GENERAL_METHOD"      # 自定义的普通方法
    elif called_method_type in [MethodType.GENERAL.value]:
        print(f"被调用的方法[{called_method_name}]是全局方法 开始进行查找可能的源信息")
        possible_methods = find_possible_global_methods(called_method_info, method_info_map)
        print(f"最终查找到全局方法[{called_method_fullname}]可能的原始方法 共[{len(possible_methods)}]个")

    # 开始查找类方法 CONSTRUCT MAGIC CLASS
    elif called_method_type in [MethodType.CONSTRUCT.value, MethodType.MAGIC_METHOD.value, MethodType.CLASS_METHOD.value]:
        print(f"被调用的方法[{called_method_name}]是类的方法 开始进行查找可能的源信息")
        possible_methods = find_possible_class_methods(called_method_info, method_info_map)
        print(f"查找到类的方法[{called_method_fullname}]可能的原始方法 共[{len(possible_methods)}]个")
    return possible_methods



def fix_parsed_infos_called_info(parsed_infos: dict, method_info_map: dict):
    """修补被调用函数的信息"""
    for file_path, parsed_info in parsed_infos.items():
        # 修复全局方法中的调用方法信息
        global_method_infos = parsed_info.get(FileInfoKeys.METHOD_INFOS.value, [])
        for method_info in global_method_infos:
            called_method_infos = method_info.get(MethodKeys.CALLED_METHODS.value, [])
            # 填充方法中调用的其他方法的信息
            for called_method_info in called_method_infos:
                # 填充可能的方法信息
                called_possible = find_possible_called_methods(called_method_info, method_info_map)
                called_method_info[MethodKeys.MAY_CALLED.value] = called_possible

        # 修复类方法中的调用方法信息
        class_infos = parsed_info.get(FileInfoKeys.CLASS_INFOS.value, [])
        for class_info in class_infos:
            for method_info in class_info.get(ClassKeys.METHODS.value, []):
                called_method_infos = method_info.get(MethodKeys.CALLED_METHODS.value, [])
                # 填充方法中调用的其他方法的信息
                for called_method_info in called_method_infos:
                    # 填充可能的方法信息
                    called_possible = find_possible_called_methods(called_method_info, method_info_map)
                    called_method_info[MethodKeys.MAY_CALLED.value] = called_possible
    return parsed_infos


