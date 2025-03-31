from tree_func_info import PHP_BUILTIN_FUNCTIONS

CLASS_INFO = 'classes'
FUNCTIONS = 'functions'


def build_function_map(parse_info):
    """建立函数和类方法名到文件位置的映射"""
    function_map = {}

    # 第一遍：建立基本映射
    for file_path, file_info in parse_info.items():
        # 记录普通函数的 函数名->函数信息关系
        print("开始建立常规函数的映射...")
        for func_info in file_info.get(FUNCTIONS):
            func_name = func_info['name']

            if func_name not in function_map:
                function_map[func_name] = []

            func_dict = {
                'type': 'function',
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
                    'type': 'method',
                    'static': method.get('static'),
                    'visibility': method.get('visibility'),
                    'parameters': method.get('parameters'),
                    'line': method.get('line'),
                }
                function_map[full_method_name].append(full_method_info)

    return function_map

def build_classes_map(parse_info):
    """建立函数和类方法名到文件位置的映射"""
    class_map = {}

    for file_path, file_info in parse_info.items():
        print("开始建立类信息的映射...")
        for class_info in file_info.get(CLASS_INFO):
            class_name = class_info.get('name')
            class_dict = {
                'file': file_path,
                'extends': class_info.get('extends'),  # class中暂未实现分析extends,后续需要实现
                'methods': {},
                'properties': class_info.get('properties')
            }
            class_map[class_name] = class_dict

            for method in class_info.get('methods'):
                method_name = method['name']
                class_map[class_name]['methods'][method_name] = method

    return class_map


def find_method_in_hierarchy(class_map, class_name, method_name):
    """在类继承层次中查找方法"""
    current_class = class_name
    while current_class in class_map:
        if method_name in class_map[current_class]['methods']:
            return class_map[current_class]['methods'][method_name], current_class
        current_class = class_map[current_class].get('extends')
    return None, None

def process_method_call(caller, called_func, file_path):
    """处理方法调用"""
    if called_func.get('call_type') == 'method':
        obj = called_func.get('object', '')
        method = called_func.get('method', '')

        # 处理 $this 调用
        if obj == '$this':
            caller_class = caller.get('class')
            if caller_class:
                method_info, actual_class = find_method_in_hierarchy(caller_class, method)
                if method_info:
                    # 修改调用类型为 object_method
                    add_call_relation(caller, method_info, 'object_method', file_path,
                                      called_func.get('line'), actual_class)

        # 处理对象方法调用
        elif '->' in obj:
            # 修改调用类型为 object_method
            add_call_relation(caller, method, 'object_method', file_path,
                              called_func.get('line'))

def process_constructor_call(class_map, function_map, caller, class_name, file_path, line):
    """处理构造函数调用"""
    if class_name in class_map:
        constructor_name = f"{class_name}::__construct"
        if constructor_name in function_map:
            # 修改调用类型为 object_creation
            for location in function_map[constructor_name]:
                add_call_relation(caller, location, 'object_creation', file_path, line, class_name)

                # 处理父类构造函数调用
                parent_class = class_map[class_name].get('extends')
                if parent_class:
                    parent_constructor = f"{parent_class}::__construct"
                    if parent_constructor in function_map:
                        # 修改调用类型为 parent_constructor
                        add_call_relation(caller, function_map[parent_constructor][0],
                                          'parent_constructor', file_path, line, parent_class)

def add_call_relation(caller, callee, call_type, file_path, line, class_name=None):
    """添加调用关系"""
    call_info = {
        'type': call_type,
        'file': file_path,
        'line': line
    }

    if class_name:
        call_info['class'] = class_name

    if isinstance(callee, dict):
        call_info['function'] = callee.get('method', callee.get('name'))
    else:
        call_info['function'] = callee

    if 'calls' not in caller:
        caller['calls'] = []
    caller['calls'].append(call_info)

    # 添加反向调用关系
    if isinstance(callee, dict):
        if 'called_by' not in callee:
            callee['called_by'] = []
        callee['called_by'].append({
            'name': caller.get('name') or f"{caller.get('class')}::{caller.get('method')}",
            'file': file_path,
            'line': line
        })


def analyze_func_relation(parse_info):
    """分析项目中所有函数和类方法的调用关系"""
    print("\n开始分析函数调用关系...")

    # 建立函数和类映射
    function_map = build_function_map(parse_info)
    class_map = build_classes_map(parse_info)
    print(f"已建立函数映射，共 {len(function_map)} 个函数/方法")
    print(f"function_map:{function_map}")
    print(f"已建立类映射，共 {len(class_map)} 个对象/方法")
    print(f"class_map:{class_map}")


    # 初始化调用关系字段
    for file_info in parse_info.values():
        for func_info in file_info.get(FUNCTIONS, []):
            func_info['calls'] = []
            func_info['called_by'] = []  # 确保每个函数都有 called_by 字段

        for class_info in file_info.get(CLASS_INFO, []):
            for method in class_info.get('methods', []):
                method['calls'] = []
                method['called_by'] = []

    # 分析每个文件
    for file_path, file_info in parse_info.items():
        print(f"\n分析文件: {file_path}")
        
        # 分析普通函数调用
        for func in file_info.get(FUNCTIONS, []):
            for called_func in func.get('called_functions', []):
                if called_func.get('call_type') == 'constructor':
                    class_name = called_func['name'].replace('new ', '')
                    process_constructor_call(func, class_name, file_path, called_func.get('line'))
                elif called_func.get('call_type') == 'method':
                    process_method_call(func, called_func, file_path)
                elif called_func.get('call_type') == 'local':
                    # 处理本地函数调用
                    if called_func['name'] in function_map:
                        add_call_relation(func, called_func['name'], 'function', 
                                       file_path, called_func.get('line'))

        # 分析类方法调用
        for class_info in file_info.get(CLASS_INFO, []):
            class_name = class_info['name']
            for method in class_info.get('methods', []):
                method['calls'] = []
                method['called_by'] = []
                # 处理构造函数中的父类构造函数调用
                if method['name'] == '__construct' and class_info.get('extends'):
                    parent_class = class_info['extends']
                    process_constructor_call(method, parent_class, file_path, method.get('line'))
                
                # 处理方法中的调用
                for called_func in method.get('calls', []):
                    if called_func.get('type') == 'object_method':
                        process_method_call(method, called_func, file_path)
                    elif called_func.get('type') == 'local':
                        # 处理本地函数调用
                        if called_func['name'] in function_map:
                            add_call_relation(method, called_func['name'], 'function',
                                           file_path, called_func.get('line'))

    return parse_info
