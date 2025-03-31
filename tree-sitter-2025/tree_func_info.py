import os


# 从文件加载 PHP 内置函数列表
def load_php_builtin_functions():
    functions = set()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'PHP_BUILTIN_FUNCTIONS.txt')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    functions.add(line)
        return functions
    except FileNotFoundError:
        print(f"警告: 未找到函数列表文件 {file_path}")
        return set()


# 加载 PHP 内置函数列表
PHP_BUILTIN_FUNCTIONS = load_php_builtin_functions()


# 修改函数类型判断逻辑
def get_all_function_info(tree, language):
    """获取所有函数信息，包括函数内部和非函数部分"""
    # 首先定义所有需要的查询
    class_query = language.query("""
        (class_declaration) @class.def
    """)

    function_query = language.query("""
        (function_definition
            name: (name) @function.name
            parameters: (formal_parameters
                (simple_parameter
                    name: (variable_name) @param.name
                    type: (_)? @param.type
                    default_value: (_)? @param.default
                )*
            ) @function.params
            body: (compound_statement) @function.body
        ) @function.def
    """)

    file_level_query = language.query("""
        (program
            (expression_statement
                [(function_call_expression
                    function: (name) @function_name
                    arguments: (arguments) @function_args
                )
                (object_creation_expression
                    (name) @class_name
                )
                (member_call_expression
                    object: (_) @object
                    name: (name) @method_name
                )
                (scoped_call_expression
                    scope: (name) @class_scope
                    name: (name) @static_method_name
                )
                (binary_expression
                    (function_call_expression
                        function: (name) @concat_func_name
                    )
                )]
            )
        )
    """)

    # 获取所有类定义的范围
    class_ranges = []
    for match in class_query.matches(tree.root_node):
        class_node = match[1]['class.def'][0]
        class_ranges.append((
            class_node.start_point[0] + 1,
            class_node.end_point[0] + 1
        ))

    # 获取函数定义
    function_query = language.query("""
        (function_definition
            name: (name) @function.name
            parameters: (formal_parameters
                (simple_parameter
                    name: (variable_name) @param.name
                    type: (_)? @param.type
                    default_value: (_)? @param.default
                )*
            ) @function.params
            body: (compound_statement) @function.body
        ) @function.def
    """)

    # 获取所有函数名称
    file_functions = set()
    matches = function_query.matches(tree.root_node)
    for _, match_dict in matches:
        if 'function.name' in match_dict:
            name_node = match_dict['function.name'][0]
            if name_node:
                file_functions.add(name_node.text.decode('utf8'))

    # 获取函数信息
    functions_info = []
    function_ranges = []

    for _, match_dict in matches:
        if 'function.def' in match_dict:
            function_node = match_dict['function.def'][0]
            # 检查函数是否在类定义范围内
            func_start = function_node.start_point[0] + 1
            func_end = function_node.end_point[0] + 1
            
            # 如果函数不在任何类的范围内，才添加到函数列表中
            if not any(class_start <= func_start <= class_end for class_start, class_end in class_ranges):
                name_node = match_dict.get('function.name', [None])[0]
                params_node = match_dict.get('function.params', [None])[0]
                body_node = match_dict.get('function.body', [None])[0]

                current_function = {
                    'name': name_node.text.decode('utf8') if name_node else '',
                    'start_line': func_start,
                    'end_line': func_end,
                    'parameters': _parse_parameters(params_node) if params_node else [],
                    'called_functions': _get_function_calls(body_node, language, file_functions) if body_node else []
                }
                functions_info.append(current_function)
                function_ranges.append((func_start, func_end))

    # 检查是否存在非函数和非类的内容
    root_start = tree.root_node.start_point[0] + 1
    root_end = tree.root_node.end_point[0] + 1
    
    has_non_function_content = False
    for i in range(root_start, root_end + 1):
        if (not any(start <= i <= end for start, end in function_ranges) and
            not any(start <= i <= end for start, end in class_ranges)):
            has_non_function_content = True
            break
    
    # 获取文件级函数调用
    file_level_calls = []
    if has_non_function_content:
        # 获取非函数部分的调用
        non_function_calls = [
            call for call in _get_function_calls(tree.root_node, language, file_functions)
            if not any(start <= call['line'] <= end for start, end in function_ranges) and
               not any(start <= call['line'] <= end for start, end in class_ranges)
        ]
        
        # 获取文件级调用并去重
        seen_calls = {(call['name'], call['line']) for call in non_function_calls}
        
        # 获取文件级调用
        for match in file_level_query.matches(tree.root_node):
            if 'function_name' in match[1] or 'concat_func_name' in match[1]:
                func_node = match[1].get('function_name', [None])[0] or match[1]['concat_func_name'][0]
                func_name = func_node.text.decode('utf8')
                line_num = func_node.start_point[0] + 1
                
                # 检查是否已经记录过这个调用
                if (func_name, line_num) not in seen_calls and func_name != 'echo':
                    func_type = 'custom'
                    if func_name in file_functions:
                        func_type = 'local'
                    elif func_name in PHP_BUILTIN_FUNCTIONS:
                        func_type = 'builtin'
                    file_level_calls.append({
                        'name': func_name,
                        'call_type': func_type,
                        'line': line_num
                    })
                    seen_calls.add((func_name, line_num))
            elif 'class_name' in match[1]:
                class_node = match[1]['class_name'][0]
                file_level_calls.append({
                    'name': f"new {class_node.text.decode('utf8')}",
                    'call_type': 'constructor',  # 修改 type 为 call_type
                    'line': class_node.start_point[0] + 1
                })
            elif 'method_name' in match[1]:
                object_node = match[1]['object'][0]
                method_node = match[1]['method_name'][0]
                file_level_calls.append({
                    'name': f"{object_node.text.decode('utf8')}->{method_node.text.decode('utf8')}",
                    'call_type': 'method',  # 修改 type 为 call_type
                    'line': method_node.start_point[0] + 1
                })
            elif 'static_method_name' in match[1]:
                class_node = match[1]['class_scope'][0]
                method_node = match[1]['static_method_name'][0]
                file_level_calls.append({
                    'name': f"{class_node.text.decode('utf8')}::{method_node.text.decode('utf8')}",
                    'call_type': 'static_method',  # 修改 type 为 call_type
                    'line': method_node.start_point[0] + 1
                })

        # 合并所有文件级调用到 non_functions，确保不重复
        all_calls = non_function_calls + [
            call for call in file_level_calls
            if (call['name'], call['line']) not in {(c['name'], c['line']) for c in non_function_calls}
        ]

        if all_calls:  # 只在有函数调用时添加
            non_function_info = {
                'name': 'non_functions',
                'parameters': [],
                'return_type': None,
                'start_line': root_start,
                'end_line': root_end,
                'called_functions': all_calls
            }
            functions_info.append(non_function_info)

    return functions_info


def _parse_parameters(params_node):
    """解析函数参数"""
    parameters = []
    if not params_node:
        return parameters

    # 遍历所有参数节点
    for child in params_node.children:
        if child.type == 'simple_parameter':
            param = {}
            # 获取参数名
            for sub_child in child.children:
                if sub_child.type == 'variable_name':
                    param['name'] = sub_child.text.decode('utf8')
                elif sub_child.type == 'null':
                    param['default'] = 'null'
                elif sub_child.type == 'string':
                    # 去掉字符串两端的引号
                    default_value = sub_child.text.decode('utf8')
                    param['default'] = default_value.strip('\'\"')
            if param:
                parameters.append(param)

    return parameters


def _get_function_calls(body_node, language, file_functions):
    """获取函数体内的函数调用信息"""
    if not body_node:
        return []

    query = language.query("""
        [
            (function_call_expression 
                function: (name) @func_name
            ) @func_call
            
            (object_creation_expression
                (name) @class_name
            ) @new_object
            
            (member_call_expression
                object: (variable_name) @obj_name
                name: (name) @method_name
            ) @method_call
            
            (scoped_call_expression
                scope: (name) @class_scope
                name: (name) @static_method_name
            ) @static_call
        ]
    """)

    called_functions = []
    seen = set()  # 修改为使用 (name, line) 元组作为唯一标识
    matches = query.matches(body_node)

    for _, match_dict in matches:
        # 处理普通函数调用
        if 'func_name' in match_dict:
            node = match_dict['func_name'][0]
            func_name = node.text.decode('utf-8')
            line_num = node.start_point[0] + 1
            call_id = (func_name, line_num)  # 新增：使用函数名和行号组合作为唯一标识
            
            if func_name != 'echo' and call_id not in seen:  # 修改：使用新的唯一标识判断
                func_type = 'custom'
                if func_name in file_functions:
                    func_type = 'local'
                elif func_name in PHP_BUILTIN_FUNCTIONS:
                    func_type = 'builtin'
                called_functions.append({
                    'name': func_name,
                    'call_type': func_type,
                    'line': line_num
                })
                seen.add(call_id)  # 修改：记录新的唯一标识
        
        # 处理对象创建
        elif 'class_name' in match_dict:
            node = match_dict['class_name'][0]
            class_name = node.text.decode('utf-8')
            line_num = node.start_point[0] + 1
            full_name = f"new {class_name}"
            call_id = (full_name, line_num)  # 新增：使用完整名称和行号组合
            
            if call_id not in seen:  # 修改：使用新的唯一标识判断
                called_functions.append({
                    'name': full_name,
                    'call_type': 'constructor',
                    'line': line_num
                })
                seen.add(call_id)
        
        # 处理方法调用
        elif 'method_name' in match_dict and 'obj_name' in match_dict:
            obj_node = match_dict['obj_name'][0]
            method_node = match_dict['method_name'][0]
            full_name = f"{obj_node.text.decode('utf-8')}->{method_node.text.decode('utf-8')}"
            if full_name not in seen:
                called_functions.append({
                    'name': full_name,
                    'call_type': 'method',  # 修改 type 为 call_type
                    'line': method_node.start_point[0] + 1
                })
                seen.add(full_name)
        
        # 处理静态方法调用
        elif 'static_method_name' in match_dict:
            class_node = match_dict['class_scope'][0]  # 修改 match[1] 为 match_dict
            method_node = match_dict['static_method_name'][0]
            full_name = f"{class_node.text.decode('utf-8')}::{method_node.text.decode('utf-8')}"
            if full_name not in seen:
                called_functions.append({
                    'name': full_name,
                    'call_type': 'static_method',
                    'line': method_node.start_point[0] + 1
                })
                seen.add(full_name)

    return called_functions
