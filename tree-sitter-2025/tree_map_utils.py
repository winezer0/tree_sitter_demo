import hashlib
from collections import defaultdict

from libs_com.utils_json import print_json
from tree_enums import ClassKeys, FileInfoKeys, MethodKeys, MethodType

GLOBAL_METHOD_ID_METHOD_INFO_MAP = "GLOBAL_METHOD_ID_METHOD_INFO_MAP"
GLOBAL_METHOD_FULLNAME_METHOD_IDS_MAP = "GLOBAL_METHOD_FULLNAME_METHOD_IDS_MAP"

CLASS_ID_CLASS_INFO_MAP = "CLASS_ID_CLASS_INFO_MAP"
CLASS_NAME_CLASS_IDS_MAP = "CLASS_NAME_CLASS_IDS_MAP"
CLASS_NAMESPACE_CLASS_IDS_MAP = "CLASS_NAMESPACE_CLASS_IDS_MAP"
CLSS_METHOD_FULLNAME_CLASS_IDS_MAP = "CLSS_METHOD_FULLNAME_CLASS_IDS_MAP"
CLSS_METHOD_NAME_CLASS_IDS_MAP = "CLSS_METHOD_NAME_CLASS_IDS_MAP"

def get_parsed_infos_all_global_methods(parsed_infos: dict):
    """获取解析结果中的所有全局方法信息"""
    all_method_infos = []
    for file_path, parsed_info in parsed_infos.items():
        # 1.1、获取文件中的全局方法
        global_method_infos = parsed_info.get(FileInfoKeys.METHOD_INFOS.value, [])
        all_method_infos.extend(global_method_infos)
    return all_method_infos


def get_parsed_infos_all_class_methods(parsed_infos: dict):
    """获取解析结果中的所有类方法信息"""
    all_method_infos = []
    for file_path, parsed_info in parsed_infos.items():
        for class_info in parsed_info.get(FileInfoKeys.CLASS_INFOS.value, []):
            class_method_infos = class_info.get(ClassKeys.METHODS.value, [])
            all_method_infos.extend(class_method_infos)
    return all_method_infos


def get_parsed_infos_all_class_infos(parsed_infos: dict):
    """获取解析结果中的所有类信息"""
    all_class_infos = []
    for file_path, parsed_info in parsed_infos.items():
        class_infos = parsed_info.get(FileInfoKeys.CLASS_INFOS.value, [])
        all_class_infos.extend(class_infos)
    return all_class_infos



def build_method_info_map(parsed_infos:dict):
    def build_method_fullname_method_ids_map(all_method_infos: list[dict]):
        """整理 method name -> method id 的映射 ｛方法名称:[函数ID,函数ID]｝"""
        method_name_method_ids_map = defaultdict(list)  # 默认值为列表 无需初始化
        for method_info in all_method_infos:
            method_fullname = method_info.get(MethodKeys.FULLNAME.value)
            method_uniq_id = method_info.get(MethodKeys.UNIQ_ID.value)
            method_name_method_ids_map[method_fullname].append(method_uniq_id)
        return method_name_method_ids_map

    def build_method_id_method_info_map(all_method_infos: dict):
        """整理 method id -> method info 的映射 ｛函数ID:方法信息｝"""
        method_id_method_info_map = {}
        for method_info in all_method_infos:
            method_uniq_id = method_info.get(MethodKeys.UNIQ_ID.value)
            method_id_method_info_map[method_uniq_id] = method_info
        return method_id_method_info_map

    def build_class_id_class_info_map(all_class_infos: dict):
        """创建class id -> class info 的映射  ｛类ID:类信息｝"""
        class_id_class_info_map = {}
        for class_info in all_class_infos:
            class_uniq_id = class_info.get(ClassKeys.UNIQ_ID.value)
            class_id_class_info_map[class_uniq_id] = class_info
        return class_id_class_info_map

    def build_method_fullname_class_ids_map(all_class_infos: dict):
        """整理 class method name -> class id 的映射 ｛类方法名称:[类ID,类ID]｝"""
        method_name_class_ids_map = defaultdict(list)  # 默认值为列表 无需初始化
        for class_info in all_class_infos:
            class_uniq_id = class_info.get(ClassKeys.UNIQ_ID.value)
            for method_info in class_info.get(ClassKeys.METHODS.value, []):
                method_fullname = method_info.get(MethodKeys.FULLNAME.value)
                method_name_class_ids_map[method_fullname].append(class_uniq_id)
        return method_name_class_ids_map

    def build_method_name_class_ids_map(all_class_infos: dict):
        """整理 class method name -> class id 的映射 ｛类方法名称:[类ID,类ID]｝"""
        method_name_class_ids_map = defaultdict(list)  # 默认值为列表 无需初始化
        for class_info in all_class_infos:
            class_uniq_id = class_info.get(ClassKeys.UNIQ_ID.value)
            for method_info in class_info.get(ClassKeys.METHODS.value, []):
                method_name = method_info.get(MethodKeys.NAME.value)
                method_name_class_ids_map[method_name].append(class_uniq_id)
        return method_name_class_ids_map


    def build_class_name_class_ids_map(all_class_infos: dict):
        """创建class name -> class ids 的映射 ｛类名称:[类ID,类ID]｝"""
        class_name_class_ids_map = defaultdict(list)  # 默认值为列表 无需初始化
        for class_info in all_class_infos:
            class_name = class_info.get(ClassKeys.NAME.value)
            class_uniq_id = class_info.get(ClassKeys.UNIQ_ID.value)
            class_name_class_ids_map[class_name].append(class_uniq_id)
        return class_name_class_ids_map

    def build_class_namespace_class_ids_map(all_class_infos: dict):
        """创建class namespace -> class ids 的映射 ｛类命名空间:[类ID,类ID]｝"""
        class_namespace_class_ids_map = defaultdict(list)  # 默认值为列表 无需初始化
        for class_info in all_class_infos:
            class_namespace = class_info.get(ClassKeys.NAMESPACE.value)
            class_uniq_id = class_info.get(ClassKeys.UNIQ_ID.value)
            class_namespace_class_ids_map[class_namespace].append(class_uniq_id)
        return class_namespace_class_ids_map

    # 1、整理出所有文件中的全局函数信息|类信息
    all_global_methods = get_parsed_infos_all_global_methods(parsed_infos)
    all_class_methods = get_parsed_infos_all_class_methods(parsed_infos)
    all_class_infos = get_parsed_infos_all_class_infos(parsed_infos)

    method_info_map = {
        # 全局方法id->方法详情 的对应关系
        GLOBAL_METHOD_ID_METHOD_INFO_MAP: build_method_id_method_info_map(all_global_methods),
        # 全局方法名称->方法id 的对应关系
        GLOBAL_METHOD_FULLNAME_METHOD_IDS_MAP: build_method_fullname_method_ids_map(all_global_methods),

        # 类ID -> 类详情 的对应关系
        CLASS_ID_CLASS_INFO_MAP: build_class_id_class_info_map(all_class_infos),
        # 类方法名 -> 类IDs 的对应关系
        CLSS_METHOD_NAME_CLASS_IDS_MAP :build_method_name_class_ids_map(all_class_infos),
        # 类完整方法名 -> 类 IDs 的对应关系
        CLSS_METHOD_FULLNAME_CLASS_IDS_MAP: build_method_fullname_class_ids_map(all_class_infos),
        # 类名称 -> 类IDs 的对应关系
        CLASS_NAME_CLASS_IDS_MAP: build_class_name_class_ids_map(all_class_infos),
        # 类空间 -> 类IDs 的对应关系
        CLASS_NAMESPACE_CLASS_IDS_MAP: build_class_namespace_class_ids_map(all_class_infos),
    }

    return method_info_map

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


def fix_parsed_infos_basic_info(parsed_infos:dict):
    """修复函数和类的UNIQ和FILE信息"""

    def fix_method_infos_uniq_id(method_infos: list[dict], file_path: str):
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

    def fix_class_infos_uniq_id(class_infos: list[dict], file_path: str):
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

    def fix_called_method_infos_file(called_method_infos: list[dict], file_path: str):
        # 循环进行信息补充
        for index, called_method_info in enumerate(called_method_infos):
            # 修复方法信息的文件路径
            if not called_method_info.get(MethodKeys.FILE.value):
                if called_method_info.get(MethodKeys.IS_NATIVE.value,False):
                    # 如果文件路径不存在 并且是本地方法的话 就设置文件路径
                    called_method_info[MethodKeys.FILE.value] = file_path
                    called_method_infos[index] = called_method_info
        return called_method_infos


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

        # 填充 called_methods中的部分已知路径信息
        global_method_infos = parsed_info.get(FileInfoKeys.METHOD_INFOS.value, [])
        for global_method_info in global_method_infos:
            # 获取调用方法信息 并逐个进行修改
            called_method_infos = global_method_info.get(MethodKeys.CALLED.value, [])
            global_method_info[MethodKeys.CALLED.value] = fix_called_method_infos_file(called_method_infos, file_path)

        class_infos = parsed_info.get(FileInfoKeys.CLASS_INFOS.value, [])
        for class_info in class_infos:
            class_method_infos = class_info.get(ClassKeys.METHODS.value, [])
            for class_method_info in class_method_infos:
                called_method_infos = class_method_info.get(MethodKeys.CALLED.value, [])
                class_method_info[MethodKeys.CALLED.value] = fix_called_method_infos_file(called_method_infos, file_path)

    return parsed_infos



def fix_called_method_infos(called_method_infos: list[dict], method_info_map: dict):
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

    def find_possible_class_methods(called_method_info:dict, method_info_map:dict):
        possible_class_infos = []

        class_id_class_info_map =  method_info_map.get(CLASS_ID_CLASS_INFO_MAP)
        clss_method_fullname_class_ids_map =  method_info_map.get(CLSS_METHOD_FULLNAME_CLASS_IDS_MAP)
        class_name_class_ids_map =  method_info_map.get(CLASS_NAME_CLASS_IDS_MAP)
        clss_method_name_class_ids_map =  method_info_map.get(CLSS_METHOD_NAME_CLASS_IDS_MAP)
        class_namespace_class_ids_map =  method_info_map.get(CLASS_NAMESPACE_CLASS_IDS_MAP)

        possible_class_ids = None
        # 1、直接通过完整的方法直接查找可能的类信息
        if possible_class_ids is None:
            method_fullname = called_method_info.get(MethodKeys.FULLNAME.value)
            possible_class_ids = clss_method_fullname_class_ids_map.get(method_fullname)
            if possible_class_ids:
                print(f"通过完整方法名 {method_fullname} 找到可能的class ids:{possible_class_ids}")

        # 2、通过类名进行查找可能的类信息
        if possible_class_ids is None:
            class_name = called_method_info.get(MethodKeys.CALLED.value)
            possible_class_ids = class_name_class_ids_map.get(class_name, None)
            if possible_class_ids:
                print(f"通过完整类名 {class_name} 找到可能的class ids:{possible_class_ids}")

        # 3、通过不完整的方法名查找可能的对象名
        if possible_class_ids is None:
            method_name = called_method_info.get(MethodKeys.NAME.value)
            possible_class_ids = clss_method_name_class_ids_map.get(class_name)
            if possible_class_ids:
                print(f"通过不完整方法名 {method_name} 找到可能的class ids:{possible_class_ids}")

        if not possible_class_ids:
            print(f"所有文件类信息中都没有找到可能的类方法:{method_fullname} 请检查!!!")
            return None

        # 获取 ids 对应的方法详情数据
        possible_class_infos = [class_id_class_info_map.get(cid) for cid in possible_class_ids]

        # TODO 通过本地方法进行筛选

        # TODO Class方法可以通过特殊描述符、可访问性再次进行过滤

        # TODO 通过命名空间信息查找可能的对象 方法暂未实现命名空间信息 需要在解析时进行实现
        # TODO 可以通过导入信息进一步补充筛选

        return possible_class_infos

    def find_possible_global_methods(called_method_info:dict, method_info_map:dict):
        """查找多个uniq中最有可能的方法"""
        global_method_id_method_info_map = method_info_map.get(GLOBAL_METHOD_ID_METHOD_INFO_MAP)
        global_method_name_method_ids_map = method_info_map.get(GLOBAL_METHOD_FULLNAME_METHOD_IDS_MAP)

        # 获取被调用类的信息
        possible_method_ids = None

        # 通过完整的方法名称查找可能的全局方法信息
        method_fullname = called_method_info.get(MethodKeys.FULLNAME.value)
        if possible_method_ids is None:
            possible_method_ids = global_method_name_method_ids_map.get(method_fullname, [])
            if possible_method_ids:
                print(f"通过完整方法名 {method_fullname} 找到可能的class ids:{possible_method_ids}")

        if not possible_method_ids:
            print(f"所有文件函数信息中都没有找到可能方法:{method_fullname} 请检查!!!")
            return None

        # 获取 ids 对应的方法详情数据
        possible_method_infos = [global_method_id_method_info_map.get(mid) for mid in possible_method_ids]

        # 寻找对应的可能的方法函数
        filtered_method_infos = []
        # 通过本地方法标志进行初次筛选
        method_is_native_value = MethodKeys.IS_NATIVE.value
        if called_method_info.get(method_is_native_value, False):
            # 查找其中文件名和 called_method_info 中的文件名相同的对象
            is_native_file = called_method_info[MethodKeys.FILE.value]
            for possible_method_info in possible_method_infos:
                possible_file = possible_method_info[MethodKeys.FILE.value]
                if is_native_file and possible_file and possible_file == is_native_file:
                    filtered_method_infos.append(possible_method_info)
                    print(f"找到可能的本地方法信息:{possible_method_info}")
            if filtered_method_infos:
                possible_method_infos = filtered_method_infos
            else:
                print(f"没有找到对应的本地方法:{method_fullname} By File [{is_native_file}] 请检查!!!")
                return None

        # 通过参数数量再一次进行过滤 对于java等语言可以通过参数类型进行过滤
        filtered_method_infos = []
        for possible_method_info in possible_method_infos:
            if len(possible_method_info[MethodKeys.PARAMS.value]) >= len(called_method_info[MethodKeys.PARAMS.value]):
                filtered_method_infos.append(possible_method_info)
                print(f"找到可能的方法信息:{possible_method_info}")
        if filtered_method_infos:
            possible_method_infos = filtered_method_infos
        # TODO 可以通过导入信息进一步补充筛选
        return possible_method_infos

    def find_called_method_possible_methods(called_method_info, method_info_map:dict):
        method_fullname = called_method_info.get(MethodKeys.FULLNAME.value)
        method_type =  called_method_info.get(MethodKeys.METHOD_TYPE.value)
        print(f"called method fullname:{method_fullname} -> method_type:{method_type}")

        # BUILTIN = "BUILTIN_METHOD"      # PHP内置方法
        if method_type in [MethodType.BUILTIN.value]:
            print("被调用的方法是内置方法,无需进行文件信息查询!!!")
            return None

        # DYNAMIC = "DYNAMIC_METHOD"      # 动态方法 （使用变量作为函数名）
        if method_type in [MethodType.DYNAMIC.value]:
            print("被调用的方法是动态方法, 查找难度过高 暂时放弃查询!!!")
            return None

        # GENERAL = "GENERAL_METHOD"      # 自定义的普通方法
        if method_type in [MethodType.GENERAL.value]:
            print("被调用的方法是其他文件的普通全局方法 开始进行查找可能的方法")
            possible_methods = find_possible_global_methods(called_method_info, method_info_map)
            if possible_methods:
                print(f"查找到 {method_fullname} 可能的原始方法 共[{len(possible_methods)}]个")
                return possible_methods
            else:
                print(f"没有找到全局方法名对应的原始方法信息:{method_fullname}!!!")
                return None

        # 开始查找类方法
        if  method_type in [MethodType.CONSTRUCT.value, MethodType.MAGIC.value, MethodType.CLASS.value]:
            print("被调用的方法是 类方法 开始进行查找可能的类对象")
            possible_methods = find_possible_class_methods(called_method_info, method_info_map)
            if possible_methods:
                print(f"查找到 {method_fullname} 可能的原始类方法 共[{len(possible_methods)}]个")
                return possible_methods
            else:
                print(f"没有找到类方法名对应的原始方法信息:{method_fullname}!!!")
                return None



        return  None

    # 开始循序进行文件信息分析
    for index, called_method_info in enumerate(called_method_infos):
        # 开始进行逐个修复
        # 寻找函数所在的文件信息
        called_method_info[MethodKeys.FILE.value] = find_called_method_possible_methods(called_method_info, method_info_map)
        print_json(called_method_info)
    return called_method_infos

def fix_parsed_infos_called_info(parsed_infos):
    """修补被调用函数的信息"""

    # 获取常用的对应关系映射
    method_info_map = build_method_info_map(parsed_infos)

    # TODO 填充 全局方法中调用的方法信息
    for file_path, parsed_info in parsed_infos.items():
        global_method_infos = parsed_info.get(FileInfoKeys.METHOD_INFOS.value, [])
        for method_info in global_method_infos:
            called_method_infos = method_info.get(MethodKeys.CALLED.value, [])
            method_info[MethodKeys.CALLED.value] = fix_called_method_infos(called_method_infos, method_info_map)

        # TODO 填充 类方法中调用的方法信息
        class_infos = parsed_info.get(FileInfoKeys.CLASS_INFOS.value, [])
        for class_info in class_infos:
            for method_info in class_info.get(ClassKeys.METHODS.value, []):
                called_method_infos = method_info.get(MethodKeys.CALLED.value, [])
                method_info[MethodKeys.CALLED.value] = fix_called_method_infos(called_method_infos, method_info_map)
    return parsed_infos