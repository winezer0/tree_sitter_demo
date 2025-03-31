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
def get_function_info(tree, language):
    """获取函数信息"""
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
    
    functions_info = []
    matches = function_query.matches(tree.root_node)
    
    # 获取所有函数名称用于判断本地函数
    file_functions = set()
    for _, match_dict in matches:
        if 'function.name' in match_dict:
            name_node = match_dict['function.name'][0]
            if name_node:
                file_functions.add(name_node.text.decode('utf8'))
    
    for _, match_dict in matches:
        if 'function.def' in match_dict:
            function_node = match_dict['function.def'][0]
            name_node = match_dict.get('function.name', [None])[0]
            params_node = match_dict.get('function.params', [None])[0]
            body_node = match_dict.get('function.body', [None])[0]
            
            current_function = {
                'name': name_node.text.decode('utf8') if name_node else '',
                'start_line': function_node.start_point[0] + 1,
                'end_line': function_node.end_point[0] + 1,
                'parameters': _parse_parameters(params_node) if params_node else [],
                'called_functions': _get_function_calls(body_node, language, file_functions) if body_node else []
            }
            functions_info.append(current_function)
    
    return functions_info


def get_non_function_info(tree, language):
    """获取PHP代码中非函数部分的基本信息"""
    # 获取所有函数名称用于判断本地函数
    function_name_query = language.query("""
        (function_definition
            name: (name) @function.name
        )
    """)
    file_functions = set()
    matches = function_name_query.matches(tree.root_node)
    for _, match_dict in matches:
        if 'function.name' in match_dict:
            name_node = match_dict['function.name'][0]
            if name_node:
                file_functions.add(name_node.text.decode('utf8'))
    
    # 找到所有函数定义节点
    function_query = language.query("""
        (function_definition) @function.def
    """)
    
    # 计算非函数区域的范围
    start_line = 1  # 从文件开头开始
    end_line = tree.root_node.end_point[0] + 1
    
    # 如果有函数定义，需要排除函数定义的范围
    matches = function_query.matches(tree.root_node)
    if matches:
        # 找到最后一个函数定义的结束位置
        last_end_line = 0
        for _, match_dict in matches:
            if 'function.def' in match_dict:
                node = match_dict['function.def'][0]
                if node.end_point[0] > last_end_line:
                    last_end_line = node.end_point[0]
        
        start_line = last_end_line + 2  # 最后一个函数结束后的下一行
    
    non_function_info = {
        'name': 'non_functions',
        'parameters': [],
        'return_type': None,
        'start_line': start_line,
        'end_line': end_line,
        'called_functions': []
    }

    # 捕获所有类型的函数调用
    query = language.query("""
        [
            (function_call_expression 
                function: (name) @func_name
                arguments: (arguments)
            ) @func_call
            
            (member_call_expression
                object: (variable_name) @obj_name
                name: (name) @method_name
                arguments: (arguments)
            ) @method_call
            
            (member_call_expression
                object: (subscript_expression
                    (variable_name) @var_name
                    (_) @index_value
                )
                name: (name) @method_name
                arguments: (arguments)
            ) @method_call_array
        ]
    """)

    matches = query.matches(tree.root_node)
    seen = set()  # 用于去重

    for _, match_dict in matches:
        # 处理普通函数调用
        if 'func_name' in match_dict:
            node = match_dict['func_name'][0]
            func_name = node.text.decode('utf-8')
            if func_name not in seen:
                # 判断函数类型
                func_type = 'custom'  # 默认为custom类型
                if func_name in file_functions:
                    func_type = 'local'
                elif func_name.startswith('$'):
                    func_type = 'dynamic'
                elif func_name in PHP_BUILTIN_FUNCTIONS:
                    func_type = 'builtin'

                if func_type != 'builtin':  # 不保存内置函数信息
                    non_function_info['called_functions'].append({
                        'name': func_name,
                        'type': func_type,
                        'call_type': 'function',
                        'line': node.start_point[0] + 1
                    })
                    seen.add(func_name)

        # 处理对象方法调用
        if 'method_name' in match_dict:
            method_node = match_dict['method_name'][0]
            method_name = method_node.text.decode('utf-8')
            
            # 处理数组对象方法调用
            if 'var_name' in match_dict and 'index_value' in match_dict:
                var_node = match_dict['var_name'][0]
                index_node = match_dict['index_value'][0]
                var_name = var_node.text.decode('utf-8')
                index_name = index_node.text.decode('utf-8').strip('\'\"')
                full_name = f"{var_name}[{index_name}]->{method_name}"
                obj_name = f"{var_name}[{index_name}]"
            # 处理普通对象方法调用
            elif 'obj_name' in match_dict:
                obj_node = match_dict['obj_name'][0]
                obj_name = obj_node.text.decode('utf-8')
                full_name = f"{obj_name}->{method_name}"
            else:
                continue

            if full_name not in seen:
                non_function_info['called_functions'].append({
                    'name': full_name,
                    'type': 'object_method',
                    'object': obj_name,
                    'method': method_name,
                    'call_type': 'method',
                    'line': method_node.start_point[0] + 1
                })
                seen.add(full_name)

    return non_function_info


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
                    param['default'] = sub_child.text.decode('utf8')
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
            
            (member_call_expression
                object: (subscript_expression
                    (variable_name) @var_name
                    (_) @index_value
                )
                name: (name) @method_name
            ) @method_call_array
            
            (member_call_expression
                object: (variable_name) @obj_name
                name: (name) @method_name
            ) @method_call
        ]
    """)

    called_functions = []
    seen = set()
    matches = query.matches(body_node)
    
    for _, match_dict in matches:
        # 处理普通函数调用
        if 'func_name' in match_dict:
            node = match_dict['func_name'][0]
            func_name = node.text.decode('utf-8')
            if func_name not in seen:
                # 判断函数类型
                func_type = 'custom'  # 默认为custom类型
                if func_name in file_functions:
                    func_type = 'local'
                elif func_name.startswith('$'):
                    func_type = 'dynamic'
                elif func_name in PHP_BUILTIN_FUNCTIONS:
                    func_type = 'builtin'

                if func_type != 'builtin':  # 不保存内置函数信息
                    called_functions.append({
                        'name': func_name,
                        'type': func_type,
                        'call_type': 'function',
                        'line': node.start_point[0] + 1
                    })
                    seen.add(func_name)

        # 处理数组对象的方法调用（如 $GLOBALS['db']->query）
        if 'method_name' in match_dict and 'var_name' in match_dict:
            method_node = match_dict['method_name'][0]
            var_node = match_dict['var_name'][0]
            index_node = match_dict['index_value'][0]
            
            var_name = var_node.text.decode('utf-8')
            method_name = method_node.text.decode('utf-8')
            index_name = index_node.text.decode('utf-8').strip('\'\"')
            
            full_name = f"{var_name}[{index_name}]->{method_name}"
            if full_name not in seen:
                called_functions.append({
                    'name': full_name,
                    'type': 'object_method',
                    'object': f"{var_name}[{index_name}]",
                    'method': method_name,
                    'call_type': 'method',
                    'line': method_node.start_point[0] + 1
                })
                seen.add(full_name)

    return called_functions
