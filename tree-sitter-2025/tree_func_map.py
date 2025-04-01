from libs_com.utils_json import print_json
from tree_const import *
from tree_map_utils import init_calls_value, build_function_map, build_classes_map, is_php_magic_method, \
    find_class_infos_by_method


def analyze_func_relation(parsed_infos):
    """分析项目中所有函数和类方法的调用关系"""
    print("\n开始分析函数调用关系...")

    # 建立函数和类映射
    function_map = build_function_map(parsed_infos)
    print(f"已建立函数映射，共 {len(function_map)} 个函数/方法")
    print_json(function_map)

    # 初始化调用关系字段
    parsed_infos = init_calls_value(parsed_infos)

    # 根据 called_functions信息 补充更详细的调用信息
    # parsed_infos = build_calls_func_relation(parsed_infos, function_map)
    parsed_infos = build_calls_class_relation(function_map, parsed_infos)

    # 根据 calls 信息 补充被调用关系
    print("\n开始建立被调用关系...")
    # parsed_infos = build_called_by_func_relation(parsed_infos, function_map)
    parsed_infos =  build_called_by_class_relation(function_map, parsed_infos)

    return parsed_infos


def find_local_call_relation(func_info, call_func, file_path, class_name=None):
    """补充调用关系"""
    # 不知道为啥要加这个class
    if call_func['name'] in call_func:
        call_func_info = {**call_func, 'func_file': file_path, 'class': class_name if class_name else ''}
        func_info['calls'].append(call_func_info)
    else:
        print(f"在映射列表内没有找到对应 LOCAL_METHOD 函数名称:{call_func['name']}")
    return func_info

def find_custom_call_relation(func_info, called_func, function_map, class_name=None):
    """补充调用关系"""
    # 从映射列表内查询函数名可能的函数信息
    if called_func['name'] in function_map:
        probably_func_infos = function_map.get(called_func.get('name'))
        for probably_func_info in probably_func_infos:
            file_path = probably_func_info.get('file')
            call_func_info = {**called_func, **probably_func_info, 'func_file': file_path, 'class': class_name if class_name else ''}
            func_info['calls'].append(call_func_info)
    else:
        print(f"在映射列表内没有找到对应 CUSTOM_METHOD 函数名称:{called_func['name']}")
    return func_info


def build_called_by_func_relation(parsed_infos, function_map):
    """根据函数的调用信息(calls)补充被调用关系(called_by)"""
    for file_path, parsed_info in parsed_infos.items():
        # 处理普通函数的调用关系
        for calling_func in parsed_info.get(FUNCTIONS, []):
            for call_info in calling_func.get('calls', []):
                # 构建调用者信息
                caller_info = {
                    'name': calling_func['name'],
                    'file': file_path,
                    'line': calling_func.get('start_line'),
                    'type': calling_func.get('type', FUNCTION)
                }
                
                # 获取被调用函数的信息
                called_name = call_info.get('name')
                called_class = call_info.get('class')
                print(f"发现调用者信息:{caller_info}")
                print(f"查找被调用者信息:{called_name}-{called_class}")
                # 使用function_map查找被调用函数
                if called_class:  # 如果是类方法
                    full_method_name = f"{called_class}::{called_name}"
                    if full_method_name in function_map:
                        for func_info in function_map[full_method_name]:
                            called_file = func_info['file']
                            # 在类方法中查找并添加调用关系
                            for class_info in parsed_infos[called_file].get(CLASS_INFO, []):
                                if class_info['name'] == called_class:
                                    for method in class_info.get('methods', []):
                                        if method['name'] == called_name:
                                            method['called_by'].append(caller_info)
                else:  # 如果是普通函数
                    if called_name in function_map:
                        for func_info in function_map[called_name]:
                            print(f"找到被调用函数信息:{func_info}")
                            called_file = func_info['file']
                            # 在普通函数中查找并添加调用关系
                            for func in parsed_infos[called_file].get(FUNCTIONS, []):
                                if func['name'] == called_name:
                                    func['called_by'].append(caller_info)
                                print(f"找到被调用函数信息:{func['called_by']}")
    return parsed_infos


def build_called_by_class_relation(function_map, parsed_infos):
    # 处理类方法的调用关系
    for file_path, parsed_info in parsed_infos.items():
        for class_info in parsed_info.get(CLASS_INFO, []):
            class_name = class_info['name']
            for method in class_info.get('methods', []):
                for call_info in method.get('calls', []):
                    # 构建调用者信息
                    caller_info = {
                        'name': method['name'],
                        'class': class_name,
                        'file': file_path,
                        'line': method.get('line'),
                        'type': CLASS_METHOD
                    }

                    # 获取被调用函数的信息
                    called_name = call_info.get('name')
                    called_class = call_info.get('class')

                    # 使用function_map查找被调用函数
                    if called_class:  # 如果是类方法
                        full_method_name = f"{called_class}::{called_name}"
                        if full_method_name in function_map:
                            for func_info in function_map[full_method_name]:
                                called_file = func_info['file']
                                # 在类方法中查找并添加调用关系
                                for target_class in parsed_infos[called_file].get(CLASS_INFO, []):
                                    if target_class['name'] == called_class:
                                        for target_method in target_class.get('methods', []):
                                            if target_method['name'] == called_name:
                                                if 'called_by' not in target_method:
                                                    target_method['called_by'] = []
                                                target_method['called_by'].append(caller_info)
                    else:  # 如果是普通函数
                        if called_name in function_map:
                            for func_info in function_map[called_name]:
                                called_file = func_info['file']
                                # 在普通函数中查找并添加调用关系
                                for func in parsed_infos[called_file].get(FUNCTIONS, []):
                                    if func['name'] == called_name:
                                        if 'called_by' not in func:
                                            func['called_by'] = []
                                        func['called_by'].append(caller_info)
    return parsed_infos

def process_constructor_call(parsed_infos, func_info, called_func):
    """处理构造函数调用"""
    class_name = called_func['name'].replace('new ', '')
    line = called_func.get('line')

    print(f"处理构造函数调用...{class_name}")
    class_map = build_classes_map(parsed_infos)
    print(f"class_map:{class_map}")
    # class_map:
    # {'MyClass': {'file': 'MyClass.php', 'type': 'class',
    # 'methods': {'classMethod': {'name': 'classMethod', 'visibility': 'public', 'static': False, 'line': 5, 'parameters': [{'name': '$input', 'type': None}],
    # 'called_functions': [{'name': 'call_func', 'type': 'custom', 'call_type': 'function', 'line': 7}],
    # 'calls': [],
    # 'called_by': []}},
    # 'properties': []}}
    if not class_name in class_map:
        print(f"没有在类映射关系中找到Class:{class_name} -> {class_map.keys()}!!!")
        exit()
    if class_name in class_map:
        # 查找目标类的构造函数
        map_find_info = class_map[class_name]
        class_file = map_find_info.get('file')
        print(f"在类映射关系中找到Class:{class_name} -> {class_file} -> {map_find_info}!!!")
        for class_file_info in parsed_infos[class_file].get(CLASS_INFO, []):
            print(f"找到class对应文件的CLASS_INFO信息:{class_file} -> {class_file_info}")
            if class_file_info['name'] == class_name:
                for method in class_file_info.get('methods', []):
                    print(f"class method:{method}")
                    if '__construct' in method:
                        print("class {class_file} 已实现构造函数")
                        if method['name'] == '__construct':
                            # 构建调用信息
                            call_info = {
                                'name': '__construct',
                                'type': CONSTRUCTOR,
                                'class': class_name,
                                'line': line,
                                'func_file': class_file
                            }
                            # 添加调用关系
                            func_info['calls'].append(call_info)
    return func_info


def process_object_method_call(parsed_infos, func_info, called_func):
    """处理对象方法调用"""
    print(f"处理对象方法调用...{called_func}")
    class_name = called_func['name'].split("->")[0].strip("$")
    method_name = called_func['name'].split("->")[-1].strip("$")
    line = called_func.get('line')
    print(f"处理对象方法调用...{class_name}::{method_name}")
    class_map = build_classes_map(parsed_infos)
    # 没有在类映射关系中找到Class:myClass -> dict_keys(['MyClass'])!!!
    # TODO 实现传入变量和导入关系,获取到更准确的调用关系,目前就直接使用模糊查询
    # 原则上在没有传入变量关系时,是没有办法找到对应关系的
    class_infos = []
    if class_name in class_map:
        print(f"在类映射关系中找到Class:{class_name} -> {class_map}!!!")
        class_infos = [class_map[class_name]]
    else:
        # 入如果方法不是类的内置方法的话
        if not is_php_magic_method(method_name):
            class_infos = find_class_infos_by_method(method_name, class_map)
            print(f"通过方法名找到可能的类为:{class_infos}")
    # 查找目标类
    for map_find_info in class_infos:
        class_file = map_find_info.get('file')
        new_class_name = map_find_info.get('name')
        print(f"在类映射关系中找到Class:{class_name} ON {new_class_name} -> {class_file} -> {map_find_info}!!!")
    
        # 查找目标方法
        for class_file_info in parsed_infos[class_file].get(CLASS_INFO, []):
            # 不要在比较类名,一般都是不相等的，直接比较函数名
            if class_file_info['name'] == new_class_name:
                for method in class_file_info.get('methods', []):
                    if method['name'] == method_name:
                        # 构建调用信息
                        call_info = {
                            'name': method_name,
                            'type': OBJECT_METHOD,
                            'class': new_class_name,
                            'line': line,
                            'func_file': class_file
                        }
                        # 添加调用关系
                        func_info['calls'].append(call_info)
    return func_info

# 在 build_calls_func_relation 函数中
def build_calls_func_relation(parsed_infos, function_map):
    """处理普通函数的调用关系"""
    # 分析每个文件
    for file_path, parsed_info in parsed_infos.items():
        print(f"\n分析文件 build_calls_func_relation: {file_path}")
        # 分析普通函数调用
        parsed_info_functions = parsed_info.get(FUNCTIONS, [])
        for index, func_info in enumerate(parsed_info_functions):
            for called_func in func_info.get(CALLED_FUNCTIONS, []):
                func_type = called_func.get(FUNCTION_TYPE)
                if func_type == BUILTIN_METHOD:
                    print("跳过对内置函数函数的寻找调用...")
                # 如果本地函数
                elif func_type == LOCAL_METHOD:
                    # 处理本地函数调用
                    print(f"处理{func_type}函数调用:{called_func}")
                    func_info = find_local_call_relation(func_info, called_func, file_path)
                    parsed_info_functions[index] = func_info

                # 如果自定义函数
                elif func_type == CUSTOM_METHOD:
                    # 处理自定义的函数调用
                    print(f"处理{func_type}函数调用:{called_func}")
                    func_info = find_custom_call_relation(func_info, called_func, function_map)
                    parsed_info_functions[index] = func_info
                else:
                    # 如果class的构造函数
                    if func_type in [CONSTRUCTOR]:
                        func_info = process_constructor_call(parsed_infos, func_info, called_func)
                        parsed_info_functions[index] = func_info
                    # 如果class对象的函数
                    elif func_type in [OBJECT_METHOD, STATIC_METHOD]:
                        print(f"发现对象方法调用 {func_type} -> {called_func}!!!")
                        func_info = process_object_method_call(parsed_infos, func_info, called_func)
                        parsed_info_functions[index] = func_info
                    else:
                        print(f"发现未预期的调用格式 {func_type}, 必须实现 -> {called_func}")
                        print(func_info)
                        exit()

    return parsed_infos

def build_calls_class_relation(function_map, parsed_infos):
    """处理类方法的调用关系"""
    # 分析类方法调用
    for file_path, parsed_info in parsed_infos.items():
        print(f"\n分析文件 build_calls_class_relation: {file_path}")
        for class_info in parsed_info.get(CLASS_INFO, []):
            print(f"class_info:{class_info}")
            class_name = class_info['name']
            for method_info in class_info.get('methods', []):
                # 处理构造函数中的父类构造函数调用
                if method_info['name'] == '__construct' and class_info.get('extends'):
                    parent_class = class_info['extends']
                    if parent_class in function_map:
                        parent_constructor = {
                            'name': '__construct',
                            'type': CONSTRUCTOR,
                            'class': parent_class,
                            'line': method_info.get('line')
                        }
                        method_info = find_local_call_relation(method_info, parent_constructor, file_path, parent_class)

                # 处理方法中的函数调用
                for called_func in method_info.get(CALLED_FUNCTIONS, []):
                    func_type = called_func.get(FUNCTION_TYPE)
                    if func_type == BUILTIN_METHOD:
                        print("跳过对内置函数的寻找调用...")
                        continue

                    elif func_type == LOCAL_METHOD:
                        # 处理本地函数调用
                        print(f"处理类方法中的{func_type}函数调用:{called_func}")
                        if called_func['name'] in function_map:
                            method_info = find_local_call_relation(method_info, called_func, file_path)
                        else:
                            print(f"在映射列表内没有找到对应 LOCAL_METHOD 函数名称:{called_func['name']}")
                            continue

                    elif func_type == CUSTOM_METHOD:
                        # 处理自定义函数调用
                        print(f"处理类方法中的{func_type}函数调用:{called_func}")
                        method_info = find_custom_call_relation(method_info, called_func, function_map)

                    elif func_type == CONSTRUCTOR:
                        # 处理构造函数调用
                        print(f"处理类方法中的构造函数调用:{called_func}")
                        class_name = called_func['name'].replace('new ', '')
                        if class_name in function_map:
                            constructor_info = {
                                'name': '__construct',
                                'type': CONSTRUCTOR,
                                'class': class_name,
                                'line': called_func.get('line')
                            }
                            method_info = find_local_call_relation(method_info, constructor_info, file_path, class_name)

                    elif func_type in [OBJECT_METHOD, STATIC_METHOD]:
                        # 处理对象方法调用
                        print(f"处理类方法中的对象方法调用:{called_func}")
                        if 'class' in called_func and called_func['class'] in function_map:
                            target_class = called_func['class']
                            method_name = called_func['name']
                            full_method_name = f"{target_class}::{method_name}"

                            if full_method_name in function_map:
                                method_info = find_local_call_relation(method_info, called_func, file_path,
                                                                       target_class)
                            else:
                                print(f"在映射列表内没有找到对应方法:{full_method_name}")
                                continue
                    else:
                        print(f"发现未预期的调用格式 {func_type} -> {called_func}")
                        continue
    return parsed_infos