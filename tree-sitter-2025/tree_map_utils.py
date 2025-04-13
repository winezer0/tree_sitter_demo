import hashlib
from collections import defaultdict

from libs_com.utils_json import print_json
from tree_enums import ClassKeys, FileInfoKeys, MethodKeys, MethodType


def get_parsed_infos_all_methods(parsed_infos:dict):
    """获取解析结果中的所有方法信息"""
    all_method_infos = []
    for file_path, parsed_info in parsed_infos.items():
        # 1.1、获取文件方法
        direct_method_infos = parsed_info.get(FileInfoKeys.METHOD_INFOS.value)
        all_method_infos.extend(direct_method_infos)
        # 1.2、获取类方法
        for class_info in parsed_info.get(FileInfoKeys.CLASS_INFOS.value):
            class_method_infos = class_info.get(ClassKeys.METHODS.value)
            all_method_infos.extend(class_method_infos)
    return all_method_infos

def build_method_fullname_method_ids_map(parsed_infos:dict):
    """整理 函数名和函数信息 映射"""
    # 1、整理出所有文件的函数
    all_method_infos = get_parsed_infos_all_methods(parsed_infos)
    # 2、创建 方法名和方法UNIQ_ID MAP ｛方法名称:[方法信息,方法信息]｝
    method_name_method_ids_map = defaultdict(list)  # 默认值为列表 无需初始化
    for method_info in all_method_infos:
        method_full_name = method_info.get(MethodKeys.FULLNAME.value)
        method_name_method_ids_map[method_full_name].append(method_info.get(MethodKeys.UNIQ_ID.value))
    return method_name_method_ids_map

def build_method_fullname_class_ids_map(parsed_infos:dict):
    """整理类函数和类信息映射"""
    method_name_class_ids_map = defaultdict(list)  # 默认值为列表 无需初始化
    for file_path,parsed_info in parsed_infos.items():
        class_infos = parsed_info.get(FileInfoKeys.CLASS_INFOS.value, [])
        for class_info in class_infos:
            for method_info in class_info.get(ClassKeys.METHODS.value, []):
                method_full_name = method_info.get(MethodKeys.FULLNAME.value)
                method_name_class_ids_map[method_full_name].append(class_info.get(ClassKeys.UNIQ_ID.value))
    return method_name_class_ids_map



def get_strs_hash(*args):
    # 计算传入的任意个字符串的MD5哈希值，并返回前8个字符。
    if not args:
        raise ValueError("至少需要提供一个字符串参数")
    # 将所有字符串连接成一个单一的字符串
    concatenated_string = '|'.join(str(arg) for arg in args)
    # 计算并返回哈希值的前8个字符
    hash_object = hashlib.md5(concatenated_string.encode('utf-8'))
    return hash_object.hexdigest()[:8]


def custom_format_path(path:str):
    return path.replace('\\', '/').replace('//', '/')


def first_fix_parsed_infos(parsed_infos:dict):
    """修复函数和类的UNIQ和FILE信息"""

    def fix_method_infos(method_infos: list[dict], file_path: str):
        """为方法信息填充ID数据等"""
        def calc_method_uniq_id(method_info: dict):
            m_file = method_info.get(MethodKeys.FILE.value)
            m_class = method_info.get(MethodKeys.CLASS.value)
            m_name = method_info.get(MethodKeys.NAME.value)
            m_start = method_info.get(MethodKeys.START_LINE.value)
            m_end = method_info.get(MethodKeys.END_LINE.value)
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

    def fix_class_infos(class_infos: list[dict], file_path: str):
        """为生成的类信息补充数据"""
        def calc_class_uniq_id(class_info: dict):
            c_file = class_info.get(ClassKeys.FILE.value)
            c_namespace = class_info.get(ClassKeys.NAMESPACE.value)
            c_name = class_info.get(ClassKeys.NAME.value)
            c_start = class_info.get(ClassKeys.START_LINE.value)
            c_end = class_info.get(ClassKeys.END_LINE.value)
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

    for file_path, parsed_info in parsed_infos.items():
        # 格式化路径
        file_path = custom_format_path(file_path)

        # 填充 全局代码中的方法信息
        global_method_infos = parsed_info.get(FileInfoKeys.METHOD_INFOS.value, [])
        parsed_info[FileInfoKeys.METHOD_INFOS.value] = fix_method_infos(global_method_infos, file_path)

        # 填充 类信息中的方法信息
        class_infos = parsed_info.get(FileInfoKeys.CLASS_INFOS.value, [])
        for class_info in class_infos:
            class_method_infos = class_info.get(ClassKeys.METHODS.value, [])
            class_info[ClassKeys.METHODS.value] = fix_method_infos(class_method_infos, file_path)

        # 填充 类信息中ID和路径信息
        class_infos = parsed_info.get(FileInfoKeys.CLASS_INFOS.value, [])
        parsed_info[FileInfoKeys.CLASS_INFOS.value] = fix_class_infos(class_infos, file_path)
    return parsed_infos


def fix_called_method_infos(called_method_infos:list[dict], file_path:str, method_fullname_method_ids_map:dict, method_fullname_class_ids_map:dict):
    """填充方法中调用的其他方法的信息"""
    # {
    #   "UNIQ_ID": null,
    #   "METHOD_FILE": "php_demo/class_call_demo/use_class.php",
    #   "METHOD_NAME": "call_class",
    #   "METHOD_START_LINE": 13,
    #   "METHOD_END_LINE": 13,
    #   "METHOD_OBJECT": null,
    #   "METHOD_CLASS": null,
    #   "METHOD_FULLNAME": "call_class",
    #   "METHOD_VISIBILITY": null,
    #   "METHOD_MODIFIERS": null,
    #   "METHOD_TYPE": "GENERAL_METHOD",
    #   "METHOD_PARAMETERS": [
    #     {
    #       "PARAM_INDEX": 0,
    #       "PARAM_VALUE": "'xxxxxxxx'",
    #       "PARAM_TYPE": "string",
    #       "PARAM_NAME": null,
    #       "PARAM_DEFAULT": null
    #     }
    #   ],
    #   "METHOD_RETURNS": null,
    #   "IS_NATIVE_METHOD": true,
    #   "CALLED_METHODS": null
    # }


    def find_called_method_file(called_method_info, file_path, method_fullname_method_ids_map:dict, method_fullname_class_ids_map:dict):
        method_name = called_method_info.get(MethodKeys.NAME.value, None)
        method_fullname = called_method_info.get(MethodKeys.FULLNAME.value, None)
        method_type =  called_method_info.get(MethodKeys.METHOD_TYPE.value)
        print(f"called method_name:{method_name} -> fullname:{method_fullname} -> method_type:{method_type}")

        # 判断是否是本地方法
        if called_method_info.get(MethodKeys.IS_NATIVE.value, False):
            print(f"called method_name:{method_name} is Native Method")
            return file_path

        # BUILTIN = "BUILTIN_METHOD"      # PHP内置方法
        if method_type in [MethodType.BUILTIN.value]:
            print("被调用的方法是内置方法,无需进行文件信息查询!!!")
            return None

        # DYNAMIC = "DYNAMIC_METHOD"      # 动态方法 （使用变量作为函数名）
        if method_type in [MethodType.DYNAMIC.value]:
            print("被调用的方法是动态方法, 查找难度过高 放弃查询!!!")
            return None

        # GENERAL = "GENERAL_METHOD"      # 自定义的普通方法
        if method_type in [MethodType.GENERAL.value]:
            print("被调用的方法是其他文件的普通全局方法 开始进行查找可能的方法")
            method_uniq_ids = method_fullname_method_ids_map.get(method_fullname, None)
            if method_uniq_ids:
                print(f"找到方法名对应方法ID信息:{method_uniq_ids}")
                # TODO 获取ID对应的实际方法名称

        # CONSTRUCT = "CONSTRUCT_METHOD"  # 类的构造方法 需要额外处理
        if  method_type in [MethodType.CONSTRUCT.value, MethodType.MAGIC.value]:
            print("被调用的方法是其他文件的类构造|魔术方法 开始进行查找可能的类对象")
            method_uniq_ids = method_fullname_method_ids_map.get(method_fullname, None)
            if method_uniq_ids:
                print(f"从函数关系找到了构造方法名对应方法ID信息:{method_uniq_ids}")
            else:
                #TODO 从类信息中去寻找可能的文件
                pass

        # CLASS = "CLASS_METHOD"          # 自定义的类方法
        if  method_type in [MethodType.CLASS.value]:
            print("被调用的方法是其他文件的类方法 开始进行查找可能的类对象")
            method_uniq_ids = method_fullname_method_ids_map.get(method_fullname, None)
            # 这里一般除了静态方法都是找不到的 需要根据多种情况进行猜测
            if method_uniq_ids:
                print(f"从函数关系找到了构造方法名对应方法ID信息:{method_uniq_ids}")
            else:
                #TODO 从类信息中去寻找可能的文件
                pass

        # 如果是普通方法就去普通方法信息中去找

        # 获取所有文件的方法名信息 查找对应的文件名信息
        # 后续需要根据导入信息进行方法排除 避免筛选结果过多

        return "UNKNOWN"

    # 开始循序进行文件信息分析
    for index, called_method_info in enumerate(called_method_infos):
        # 开始进行逐个修复
        # 寻找函数所在的文件信息
        called_method_info[MethodKeys.FILE.value] = find_called_method_file(called_method_info, file_path, method_fullname_method_ids_map, method_fullname_class_ids_map)
        print_json(called_method_info)
    return called_method_infos

def second_fix_parsed_infos(parsed_infos):
    """修补被调用函数的信息"""
    method_fullname_method_ids_map = build_method_fullname_method_ids_map(parsed_infos)
    method_fullname_class_ids_map = build_method_fullname_class_ids_map(parsed_infos)

    # TODO 填充 全局方法中调用的方法信息
    for file_path, parsed_info in parsed_infos.items():
        global_method_infos = parsed_info.get(FileInfoKeys.METHOD_INFOS.value, [])
        for method_info in global_method_infos:
            called_method_infos = method_info.get(MethodKeys.CALLED.value, [])
            method_info[MethodKeys.CALLED.value] = fix_called_method_infos(called_method_infos, file_path, method_fullname_method_ids_map, method_fullname_class_ids_map)

        # TODO 填充 类方法中调用的方法信息
        class_infos = parsed_info.get(FileInfoKeys.CLASS_INFOS.value, [])
        for class_info in class_infos:
            for method_info in class_info.get(ClassKeys.METHODS.value, []):
                called_method_infos = method_info.get(MethodKeys.CALLED.value, [])
                method_info[MethodKeys.CALLED.value] = fix_called_method_infos(called_method_infos, file_path, method_fullname_method_ids_map, method_fullname_class_ids_map)
    return parsed_infos