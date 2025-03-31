def build_function_map(parse_info):
    """建立函数名到文件位置的映射"""
    function_map = {}

    # 建立函数映射
    for file_path, file_info in parse_info.items():
        for func in file_info.get('functions', []):
            func_name = func['name']
            if func_name not in function_map:
                function_map[func_name] = []

            # 添加函数位置信息
            function_map[func_name].append({
                'file': file_path,
                'parameters': func.get('parameters', []),
                'start_line': func['start_line'],
                'end_line': func['end_line']
            })

    return function_map


def analyze_func_relation(parse_info):
    """分析项目中所有函数的调用关系"""
    print("\n开始分析函数调用关系...")

    # 首先为所有函数初始化调用关系字段
    for file_info in parse_info.values():
        for func in file_info.get('functions', []):
            func['calls'] = []
            func['called_by'] = []

    # 建立函数映射
    function_map = build_function_map(parse_info)
    print(f"已建立函数映射，共 {len(function_map)} 个函数")

    # 分析每个文件中的函数调用
    for file_path, file_info in parse_info.items():
        print(f"\n分析文件: {file_path}")
        for func in file_info.get('functions', []):
            # print(f"  分析函数: {func['name']}")
            # 处理该函数调用的其他函数
            called_functions = func.get('called_functions', [])
            for called_func in called_functions:
                func_name = called_func['name']
                func_type = called_func.get('type', '')
                line_number = called_func.get('line')  # 获取行号信息

                # 忽略内置函数
                if func_type == 'builtin':
                    continue

                # 处理对象方法调用
                if called_func['call_type'] == 'method':
                    # 获取对象名和方法名
                    object_name = called_func.get('object', '')
                    method_name = func_name.split('->')[-1] if '->' in func_name else func_name

                    # 添加方法调用信息（添加行号）
                    func['calls'].append({
                        'function': method_name,
                        'object': object_name,
                        'type': 'method',
                        'file': file_path,
                        'line': line_number  # 使用获取到的行号
                    })
                    # print(f"    添加方法调用信息: {object_name}->{method_name}")
                    continue

                # 处理本地函数调用
                if func_type == 'local':
                    # print(f"    在当前文件中查找本地函数: {func_name}")
                    # 在当前文件中查找函数定义
                    for target_func in file_info['functions']:
                        if target_func['name'] == func_name:
                            func['calls'].append({
                                'function': func_name,
                                'file': file_path,
                                'type': 'local',
                                'line': line_number  # 添加行号
                            })
                            target_func['called_by'].append({
                                'file': file_path,
                                'function': func['name'],
                                'type': 'local',
                                'line': line_number  # 添加行号
                            })
                            # print(f"    添加本地调用信息: {func_name}")
                            break
                    continue

                # 处理全局函数调用
                if func_name in function_map:
                    locations = function_map[func_name]
                    # print(f"    找到函数 {func_name} 的定义位置: {len(locations)} 处")

                    # 添加调用信息
                    for location in locations:
                        func['calls'].append({
                            'function': func_name,
                            'file': location['file'],
                            'type': 'global',
                            'line': line_number  # 添加行号
                        })
                        # print(f"    添加调用信息: {func_name} -> {location['file']}")

                        # 在目标函数中添加被调用信息
                        target_found = False
                        for target_func in parse_info[location['file']]['functions']:
                            if target_func['name'] == func_name:
                                target_func['called_by'].append({
                                    'file': file_path,
                                    'function': func['name'],
                                    'type': 'global',
                                    'line': line_number  # 添加行号
                                })
                                target_found = True
                                # print(f"    添加被调用信息: {func['name']} <- {func_name}")
                                break

                        if not target_found:
                            print(f"    警告: 未找到目标函数 {func_name} 的定义")
                else:
                    print(f"    警告: 未找到函数 {func_name} 的定义位置")

    return parse_info
