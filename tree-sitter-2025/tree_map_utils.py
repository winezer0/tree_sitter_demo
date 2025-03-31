from tree_const import FUNCTIONS, CLASS_INFO, FUNCTION, CLASS_METHOD


def init_calls_value(parsed_infos):
    # 初始化调用关系字段
    if parsed_infos:
        for _, parsed_info in parsed_infos.items():
            for function_info in parsed_info.get(FUNCTIONS, []):
                if 'calls' not in function_info:
                    function_info['calls'] = []
                if 'called_by' not in function_info:
                    function_info['called_by'] = []

            for class_info in parsed_info.get(CLASS_INFO, []):
                for function_info in class_info.get('methods', []):
                    if 'calls' not in function_info:
                        function_info['calls'] = []
                    if 'called_by' not in function_info:
                        function_info['called_by'] = []
    return parsed_infos


def build_function_map(parsed_infos):
    """建立函数和类方法名到文件位置的映射 func -> list 格式""" 
    function_map = {}
    # 第一遍：建立基本映射
    for file_path, file_info in parsed_infos.items():
        # 记录普通函数的 函数名->函数信息关系
        for func_info in file_info.get(FUNCTIONS):
            func_name = func_info['name']

            if func_name not in function_map:
                function_map[func_name] = []

            func_dict = {
                'type': FUNCTION,
                'file': file_path,
                'parameters': func_info.get('parameters'),
                'line': func_info.get('start_line')
            }
            function_map[func_name].append(func_dict)

        print("开始建立类函数的映射...")
        for class_info in file_info.get(CLASS_INFO):
            class_name = class_info.get('name')
            # 记录类的方法
            for method in class_info.get('methods'):
                method_name = method.get('name')
                full_method_name = f"{class_name}::{method_name}"

                # 记录到函数映射
                if full_method_name not in function_map:
                    function_map[full_method_name] = []

                full_method_info = {
                    'file': file_path,
                    'class': class_name,
                    'method': method_name,
                    'type': CLASS_METHOD,
                    'static': method.get('static'),
                    'visibility': method.get('visibility'),
                    'parameters': method.get('parameters'),
                    'line': method.get('line'),
                }
                function_map[full_method_name].append(full_method_info)

    return function_map


def build_classes_map(parsed_infos):
    """建立函数和类方法名到文件位置的映射 class_name-> {class_name:class_dict}格式"""
    class_map = {}

    for file_path, file_info in parsed_infos.items():
        print("开始建立类信息的映射...")
        for class_info in file_info.get(CLASS_INFO):
            class_name = class_info.get('name')
            class_dict = {
                'name': class_info.get('name'),
                'file': file_path,
                'type': class_info.get('type'),
                'properties': class_info.get('properties'),
                'methods': {},
            }
            class_map[class_name] = class_dict

            for method in class_info.get('methods'):
                method_name = method['name']
                class_map[class_name]['methods'][method_name] = method
    return class_map


php_magic_methods = [
    '__construct',   # 构造函数，在对象创建时调用
    '__destruct',    # 析构函数，在对象销毁时调用
    '__call',        # 在调用不可访问的方法时触发
    '__callStatic',  # 在调用不可访问的静态方法时触发
    '__get',         # 在尝试读取不可访问的属性时触发
    '__set',         # 在尝试设置不可访问的属性时触发
    '__isset',       # 在对不可访问的属性调用 isset() 或 empty() 时触发
    '__unset',       # 在对不可访问的属性调用 unset() 时触发
    '__toString',    # 在将对象当作字符串使用时触发
    '__invoke',      # 在尝试将对象当作函数调用时触发
    '__clone',       # 在克隆对象时触发
    '__sleep',       # 在序列化对象前触发
    '__wakeup',      # 在反序列化对象后触发
    '__serialize',   # 在序列化对象时触发（PHP 7.4+）
    '__unserialize', # 在反序列化对象时触发（PHP 7.4+）
    '__set_state',   # 在调用 var_export() 导出对象时触发
    '__debugInfo',   # 在使用 var_dump() 输出对象时触发
    '__autoload',    # 自动加载类（已弃用，推荐使用 spl_autoload_register）
]

def is_php_magic_method(method_name):
    """
    检查给定的方法名是否是 PHP 的内置魔术方法。

    :param method_name: 要检查的方法名。
    :return: 如果是 PHP 魔术方法，返回 True；否则返回 False。
    """
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
        methods = class_info.get('methods', {})
        if method_name in methods:
            possible_class_info.append(class_info)
    return possible_class_info
