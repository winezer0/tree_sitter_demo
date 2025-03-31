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


def build_function_map(parse_info):
    """建立函数和类方法名到文件位置的映射 func -> list 格式""" 
    function_map = {}
    # 第一遍：建立基本映射
    for file_path, file_info in parse_info.items():
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


def build_classes_map(parse_info):
    """建立函数和类方法名到文件位置的映射 class_name-> {class_name:class_dict}格式"""
    class_map = {}

    for file_path, file_info in parse_info.items():
        print("开始建立类信息的映射...")
        for class_info in file_info.get(CLASS_INFO):
            class_name = class_info.get('name')
            class_dict = {
                'file': file_path,
                'type': class_info.get('type'),
                'methods': {},
                'properties': class_info.get('properties')
            }
            class_map[class_name] = class_dict

            for method in class_info.get('methods'):
                method_name = method['name']
                class_map[class_name]['methods'][method_name] = method
    return class_map
