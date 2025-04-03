from tree_const import *
from tree_enums import MethodType, PHPVisibility, MethodKeys, ParameterKeys, ClassKeys


def analyze_direct_method_infos(tree, language):
    """获取所有函数信息，包括函数内部和非函数部分"""
    # 获取所有本地函数名称
    file_functions = get_file_funcs(tree, language)
    
    # 获取所有类定义的代码行范围，以排除类方法 本文件不处理类方法
    class_ranges = get_class_ranges(language, tree)
    
    # 查询所有函数定义
    function_query = language.query("""
        ; 全局函数定义
        (function_definition
            name: (name) @function.name
            parameters: (formal_parameters) @function.params
            body: (compound_statement) @function.body
        ) @function.def
        
        ; 全局函数调用
        (function_call_expression
            (name) @function_call
            (arguments) @function_args
        )
        
        ; 对象方法调用
        (member_call_expression
            object: (variable_name) @method.object
            name: (name) @method.name
            arguments: (arguments) @method.args
        ) @method.call
        
        ; 对象创建调用
        (object_creation_expression
            (name) @new_class_name
            (arguments) @constructor_args
        ) @new_expr
    """)
    
    functions_info = []

    for pattern_index, match_dict in function_query.matches(tree.root_node):
        if 'function.def' in match_dict:
            func_node = match_dict['function.def'][0]
            # 检查函数是否在类范围内
            if any(start <= func_node.start_point[0] + 1 <= end for start, end in class_ranges):
                continue
                
            # 处理函数定义
            f_name_node = match_dict['function.name'][0]
            f_params_node = match_dict.get('function.params', [None])[0]
            f_body_node = match_dict.get('function.body', [None])[0]
            f_return_type_node = match_dict.get('function.return_type', [None])[0]
            
            # 获取方法的返回值 TODO 函数返回值好像没有获取成功
            f_return_value = find_method_return_value(language, f_body_node)

            # 创建新的函数信息
            current_function = {
                MethodKeys.NAME.value: f_name_node.text.decode('utf-8'),
                MethodKeys.START_LINE.value: func_node.start_point[0] + 1,
                MethodKeys.END_LINE.value: func_node.end_point[0] + 1,
                MethodKeys.OBJECT.value: "",                                      # 普通函数没有对象
                MethodKeys.FULL_NAME.value: f_name_node.text.decode('utf-8'),
                MethodKeys.VISIBILITY.value: PHPVisibility.PUBLIC.value,          # 普通函数默认public
                MethodKeys.MODIFIERS.value: [],
                MethodKeys.METHOD_TYPE.value: MethodType.GLOBAL.value,     # 所有本文件定义的 普通全局 方法都叫 CUSTOM_METHOD
                # TODO METHOD_RETURN_TYPE 好像没有分析成功
                MethodKeys.RETURN_TYPE.value: f_return_type_node.text.decode('utf-8') if f_return_type_node else 'unknown',
                MethodKeys.RETURN_VALUE.value: f_return_value,
                MethodKeys.PARAMS.value: process_parameters(f_params_node) if f_params_node else [],
                MethodKeys.CALLED.value: []
            }
            
            # 处理函数体中的调用
            if f_body_node:
                process_function_body(f_body_node, current_function, file_functions, language)
            
            functions_info.append(current_function)
            
    # 处理文件级别的函数调用
    if has_non_func_content(tree, class_ranges, [(f[MethodKeys.START_LINE.value], f[MethodKeys.END_LINE.value]) for f in functions_info]):
        non_function_info = process_non_function_content(tree, language, file_functions, class_ranges, functions_info)
        if non_function_info:
            functions_info.append(non_function_info)
            
    return functions_info


def find_method_return_value(f_body_node, language):
    """查找方法的返回值"""
    f_return_value = None
    if not f_body_node:
        return f_return_value
    # 进行查找
    return_value_query = language.query("""
                    (return_statement
                        (expression)? @return.value
                    ) @return.stmt
                """)
    for return_match in return_value_query.matches(f_body_node):
        if 'return.value' in return_match[1]:
            return_node = return_match[1]['return.value'][0]
            f_return_value = return_node.text.decode('utf-8')
    return f_return_value


def get_class_ranges(language, tree):
    """获取所有class定义的代码行范围 """
    class_query = language.query("""
        (class_declaration) @class.def
    """)
    class_ranges = []
    for match in class_query.matches(tree.root_node):
        class_node = match[1]['class.def'][0]
        class_node_point = (
            class_node.start_point[0] + 1,
            class_node.end_point[0] + 1
        )
        class_ranges.append(class_node_point)
    return class_ranges


def get_file_funcs(tree, language):
    """获取所有本地普通函数（全局函数）名称"""
    file_functions = set()
    function_query = language.query("""
        (function_definition
            name: (name) @function.name
        )
    """)
    for match in function_query.matches(tree.root_node):
        if 'function.name' in match[1]:
            name_node = match[1]['function.name'][0]
            if name_node:
                file_functions.add(name_node.text.decode('utf8'))
    return file_functions


def process_parameters(params_node):
    """处理函数参数"""
    parameters = []
    param_index = 0
    
    for child in params_node.children:
        if child.type == 'simple_parameter':
            param_info = {
                ParameterKeys.PARAM_INDEX.value: param_index,
                ParameterKeys.PARAM_NAME.value: None,
                ParameterKeys.PARAM_TYPE.value: None,
                ParameterKeys.PARAM_DEFAULT.value: None,
                ParameterKeys.PARAM_VALUE.value: None
            }
            
            # 遍历参数节点的所有子节点
            for sub_child in child.children:
                if sub_child.type == 'variable_name':
                    param_info[ParameterKeys.PARAM_NAME.value] = sub_child.text.decode('utf-8')
                elif sub_child.type in ['primitive_type', 'name', 'nullable_type']:
                    param_info[ParameterKeys.PARAM_TYPE.value] = sub_child.text.decode('utf-8')
                elif sub_child.type == '=':
                    # 处理默认值
                    value_node = child.children[-1]  # 默认值通常是最后一个子节点
                    if value_node.type == 'string':
                        default_value = value_node.text.decode('utf-8')[1:-1]  # 去掉引号
                    else:
                        default_value = value_node.text.decode('utf-8')
                    param_info[ParameterKeys.PARAM_DEFAULT.value] = default_value
                    param_info[ParameterKeys.PARAM_VALUE.value] = None
            
            # 如果参数类型未设置，尝试从变量名推断类型
            if param_info[ParameterKeys.PARAM_TYPE.value] is None:
                if param_info[ParameterKeys.PARAM_NAME.value].startswith('$'):
                    param_info[ParameterKeys.PARAM_TYPE.value] = 'mixed'  # PHP默认类型
            
            parameters.append(param_info)
            param_index += 1
            
    return parameters


def process_function_body(body_node, current_function, file_functions, language):
    # 添加对象创建查询
    constructor_query = language.query("""
        (object_creation_expression
            (name) @new_class_name
            (arguments) @constructor_args
        ) @new_expr
    """)
    
    # 处理对象创建
    for match in constructor_query.matches(body_node):
        if 'new_class_name' in match[1]:
            class_node = match[1]['new_class_name'][0]
            args_node = match[1].get('constructor_args', [None])[0]
            line_num = class_node.start_point[0] + 1
            
            call_info = process_constructor_call(class_node, args_node, line_num)
            current_function[MethodKeys.CALLED.value].append(call_info)
    
    # 原有的对象方法调用查询
    method_call_query = language.query("""
        (member_call_expression
            object: (_) @method.object
            name: (name) @method.name
            arguments: (arguments) @method.args
        ) @method.call
    """)
    
    # 处理对象方法调用
    for match in method_call_query.matches(body_node):
        if 'method.call' in match[1]:
            method_node = match[1]['method.call'][0]
            object_node = match[1]['method.object'][0]
            method_name = match[1]['method.name'][0].text.decode('utf-8')
            args_node = match[1].get('method.args', [None])[0]
            line_num = method_node.start_point[0] + 1
            
            call_info = process_method_call(method_node, object_node, method_name, args_node, line_num)
            current_function[MethodKeys.CALLED.value].append(call_info)

    # 处理普通函数调用
    call_query = language.query("""
        (function_call_expression
            function: (name) @function_call
            arguments: (arguments) @function_args
        )
    """)
    
    matches = call_query.matches(body_node)
    seen_calls = set()
    
    for match in matches:
        match_dict = match[1]
        if 'function_call' in match_dict:
            func_node = match_dict['function_call'][0]
            func_name = func_node.text.decode('utf-8')
            call_key = f"{func_name}:{func_node.start_point[0]}"
            
            if call_key not in seen_calls:
                seen_calls.add(call_key)
                args_node = match_dict.get('function_args', [None])[0]
                line_num = func_node.start_point[0] + 1
                
                call_info = process_function_call(func_node, func_name, args_node, line_num, file_functions)
                if call_info[MethodKeys.METHOD_TYPE.value] != MethodType.BUILTIN.value:
                    current_function[MethodKeys.CALLED.value].append(call_info)


def process_call_parameters(args_node, function_params=None):
    """
    Args:
        args_node: 参数节点
        function_params: 函数定义中的参数信息（可选）
    """
    parameters = []
    param_index = 0
    
    for arg in args_node.children:
        if arg.type not in [',', '(', ')']:
            param_name = (function_params[param_index][ParameterKeys.PARAM_NAME.value]
                        if function_params and param_index < len(function_params)
                        else f"$arg{param_index}")
            
            # 处理赋值表达式
            arg_text = arg.text.decode('utf-8')
            if '=' in arg_text:
                _, value = arg_text.split('=', 1)
                value = value.strip()
            else:
                value = arg_text
                
            param_info = {
                ParameterKeys.PARAM_INDEX.value: param_index,
                ParameterKeys.PARAM_NAME.value: param_name,
                ParameterKeys.PARAM_TYPE.value: None,
                ParameterKeys.PARAM_DEFAULT.value: None,
                ParameterKeys.PARAM_VALUE.value: value
            }
            parameters.append(param_info)
            param_index += 1
            
    return parameters


def has_non_func_content(tree, class_ranges, function_ranges):
    """检查是否有非函数内容"""
    root_start = tree.root_node.start_point[0] + 1
    root_end = tree.root_node.end_point[0] + 1
    
    for i in range(root_start, root_end + 1):
        if (not any(start <= i <= end for start, end in function_ranges) and
            not any(start <= i <= end for start, end in class_ranges)):
            return True
    return False


def process_non_function_content(tree, language, file_functions, class_ranges, functions_info):
    """处理非函数部分的内容"""
    function_ranges = [(f[MethodKeys.START_LINE.value], f[MethodKeys.END_LINE.value]) for f in functions_info]
    non_func_calls = []
    
    query = language.query("""
        ; 函数调用
        (function_call_expression
            (name) @function_call
            (arguments) @function_args
        )
        
        ; 对象方法调用
        (member_call_expression
            object: (variable_name) @method.object
            name: (name) @method.name
            arguments: (arguments) @method.args
        ) @method.call
        
        ; 对象创建
        (object_creation_expression
            (name) @new_class_name
            (arguments) @constructor_args
        ) @new_expr
    """)
    
    for match in query.matches(tree.root_node):
        match_dict = match[1]
        
        # 处理对象方法调用
        if 'method.call' in match_dict:
            method_node = match_dict['method.call'][0]
            line_num = method_node.start_point[0] + 1
            
            if not _is_in_range(line_num, function_ranges, class_ranges):
                object_node = match_dict['method.object'][0]
                method_name = match_dict['method.name'][0].text.decode('utf-8')
                args_node = match_dict.get('method.args', [None])[0]
                
                call_info = process_method_call(method_node, object_node, method_name, args_node, line_num)
                non_func_calls.append(call_info)
        
        # 处理对象创建
        elif 'new_class_name' in match_dict:
            class_node = match_dict['new_class_name'][0]
            line_num = class_node.start_point[0] + 1
            
            if not _is_in_range(line_num, function_ranges, class_ranges):
                args_node = match_dict.get('constructor_args', [None])[0]
                call_info = process_constructor_call(class_node, args_node, line_num)
                non_func_calls.append(call_info)
        
        # 处理普通函数调用
        elif 'function_call' in match_dict:
            call_node = match_dict['function_call'][0]
            line_num = call_node.start_point[0] + 1
            
            if not _is_in_range(line_num, function_ranges, class_ranges):
                func_name = call_node.text.decode('utf-8')
                args_node = match_dict.get('function_args', [None])[0]
                
                call_info = process_function_call(call_node, func_name, args_node, line_num, file_functions)
                non_func_calls.append(call_info)
    
    if non_func_calls:
        return {
            MethodKeys.NAME.value: ClassKeys.NOT_IN_METHOD.value,
            MethodKeys.START_LINE.value: tree.root_node.start_point[0] + 1,
            MethodKeys.END_LINE.value: tree.root_node.end_point[0] + 1,
            MethodKeys.OBJECT.value: None,
            MethodKeys.FULL_NAME.value: ClassKeys.NOT_IN_METHOD.value,
            MethodKeys.VISIBILITY.value: PHPVisibility.PUBLIC.value,
            MethodKeys.MODIFIERS.value: [],
            MethodKeys.METHOD_TYPE.value: MethodType.FILES.value,
            MethodKeys.RETURN_TYPE.value: None,
            MethodKeys.RETURN_VALUE.value: None,
            MethodKeys.PARAMS.value: [],
            MethodKeys.CALLED.value: non_func_calls
        }
    
    return None


def _is_in_range(line_num, function_ranges, class_ranges):
    """检查行号是否在函数或类范围内"""
    return (any(start <= line_num <= end for start, end in function_ranges) or
            any(start <= line_num <= end for start, end in class_ranges))


def process_constructor_call(class_node, args_node, line_num):
    """处理构造函数调用的通用函数
    Args:
        class_node: 类名节点
        args_node: 构造函数参数节点
        line_num: 调用所在行号
    Returns:
        dict: 构造函数调用信息
    """
    class_name = class_node.text.decode('utf-8')
    print(f"Found constructor call: {class_name}::__construct at line {line_num}")
    
    return {
        MethodKeys.NAME.value: "__construct",
        MethodKeys.START_LINE.value: line_num,
        MethodKeys.END_LINE.value: class_node.end_point[0] + 1,
        MethodKeys.OBJECT.value: class_name,
        MethodKeys.FULL_NAME.value: f"{class_name}::__construct",
        MethodKeys.METHOD_TYPE.value: MethodType.CONSTRUCT.value,
        MethodKeys.VISIBILITY.value: PHPVisibility.PUBLIC.value,
        MethodKeys.MODIFIERS.value: [],
        MethodKeys.RETURN_TYPE.value: class_name,
        MethodKeys.RETURN_VALUE.value: class_name,
        MethodKeys.PARAMS.value: process_call_parameters(args_node) if args_node else []
    }


def process_method_call(method_node, object_node, method_name, args_node, line_num):
    """处理对象方法调用的通用函数
    Args:
        method_node: 方法调用节点
        object_node: 对象节点
        method_name: 方法名
        args_node: 参数节点
        line_num: 调用所在行号
    Returns:
        dict: 方法调用信息
    """
    object_name = object_node.text.decode('utf-8')
    print(f"Found method call: {object_name}->{method_name} at line {line_num}")
    
    return {
        MethodKeys.NAME.value: method_name,
        MethodKeys.START_LINE.value: line_num,
        MethodKeys.END_LINE.value: method_node.end_point[0] + 1,
        MethodKeys.OBJECT.value: object_name,
        MethodKeys.FULL_NAME.value: f"{object_name}->{method_name}",
        MethodKeys.METHOD_TYPE.value: MethodType.CLASS.value,
        MethodKeys.VISIBILITY.value: PHPVisibility.PUBLIC.value,
        MethodKeys.MODIFIERS.value: [],
        MethodKeys.RETURN_TYPE.value: None,
        MethodKeys.RETURN_VALUE.value: None,
        MethodKeys.PARAMS.value: process_call_parameters(args_node) if args_node else []
    }


def process_function_call(call_node, func_name, args_node, line_num, file_functions):
    """处理普通函数调用的通用函数
    Args:
        call_node: 函数调用节点
        func_name: 函数名
        args_node: 参数节点
        line_num: 调用所在行号
        file_functions: 本地函数集合
    Returns:
        dict: 函数调用信息
    """
    print(f"Found function call: {func_name} at line {line_num}")

    # 分析函数类型
    method_type = MethodType.GLOBAL.value
    if func_name in file_functions:
         method_type = MethodType.IS_NATIVE.value
    elif func_name in PHP_BUILTIN_FUNCTIONS:
         method_type = MethodType.IS_NATIVE.value

    return {
        MethodKeys.NAME.value: func_name,
        MethodKeys.START_LINE.value: line_num,
        MethodKeys.END_LINE.value: call_node.end_point[0] + 1,
        MethodKeys.OBJECT.value: None,
        MethodKeys.FULL_NAME.value: func_name,
        MethodKeys.METHOD_TYPE.value: method_type,
        MethodKeys.VISIBILITY.value: PHPVisibility.PUBLIC.value,
        MethodKeys.MODIFIERS.value: [],
        MethodKeys.RETURN_TYPE.value: None,
        MethodKeys.RETURN_VALUE.value: None,
        MethodKeys.PARAMS.value: process_call_parameters(args_node) if args_node else []
    }


if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.utils_json import print_json
    from tree_func_utils import read_file_to_parse

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/class_call_demo/use_class.php"
    php_file_tree = read_file_to_parse(PARSER, php_file)
    code = analyze_direct_method_infos(php_file_tree, LANGUAGE)
    print_json(code)