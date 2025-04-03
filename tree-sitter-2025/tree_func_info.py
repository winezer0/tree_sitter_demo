from tree_const import *
from tree_enums import MethodType, PHPVisibility


def analyze_direct_method_infos(tree, language):
    """获取所有函数信息，包括函数内部和非函数部分"""
    # 获取所有本地函数名称
    file_functions = get_file_funcs(tree, language)
    
    # 获取类的范围，以排除类方法
    class_ranges = get_class_ranges(language, tree)
    
    # 查询所有函数定义
    function_query = language.query("""
        ; 函数定义
        (function_definition
            name: (name) @function.name
            parameters: (formal_parameters) @function.params
            body: (compound_statement) @function.body
        ) @function.def
        
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
    
    functions_info = []
    current_function = None
    
    for pattern_index, match_dict in function_query.matches(tree.root_node):
        if 'function.def' in match_dict:
            func_node = match_dict['function.def'][0]
            # 检查函数是否在类范围内
            func_start = func_node.start_point[0] + 1
            if any(start <= func_start <= end for start, end in class_ranges):
                continue
                
            # 处理函数定义
            name_node = match_dict['function.name'][0]
            params_node = match_dict.get('function.params', [None])[0]
            body_node = match_dict.get('function.body', [None])[0]
            return_type_node = match_dict.get('function.return_type', [None])[0]
            
            # 处理返回值
            return_value = None
            if body_node:
                # 查找return语句
                return_query = language.query("""
                    (return_statement
                        (expression)? @return.value
                    ) @return.stmt
                """)
                for return_match in return_query.matches(body_node):
                    if 'return.value' in return_match[1]:
                        return_node = return_match[1]['return.value'][0]
                        return_value = return_node.text.decode('utf-8')

            # 创建新的函数信息
            current_function = {
                METHOD_NAME: name_node.text.decode('utf-8'),
                METHOD_START_LINE: func_start,
                METHOD_END_LINE: func_node.end_point[0] + 1,
                METHOD_OBJECT: None,  # 普通函数没有对象
                METHOD_FULL_NAME: name_node.text.decode('utf-8'),
                METHOD_VISIBILITY: PHPVisibility.PUBLIC.value,  # 普通函数默认public
                METHOD_MODIFIERS: [],
                # TODO  所有本文件定义的方法都叫 LOCAL_METHOD ?
                METHOD_TYPE: MethodType.LOCAL_METHOD.value,
                # TODO METHOD_RETURN_TYPE 好像没有分析成功
                METHOD_RETURN_TYPE: return_type_node.text.decode('utf-8') if return_type_node else 'unknown',
                METHOD_RETURN_VALUE: return_value,
                METHOD_PARAMETERS: process_parameters(params_node) if params_node else [],
                CALLED_METHODS: []
            }
            
            # 处理函数体中的调用
            if body_node:
                process_function_body(body_node, current_function, file_functions, language)
            
            functions_info.append(current_function)
            
    # 处理文件级别的函数调用
    if has_non_func_content(tree, class_ranges, [(f[METHOD_START_LINE], f[METHOD_END_LINE]) for f in functions_info]):
        non_function_info = process_non_function_content(tree, language, file_functions, class_ranges, functions_info)
        if non_function_info:
            functions_info.append(non_function_info)
            
    return functions_info


def get_class_ranges(language, tree):
    """获取所有类定义的范围"""
    class_query = language.query("""
        (class_declaration) @class.def
    """)
    class_ranges = []
    for match in class_query.matches(tree.root_node):
        class_node = match[1]['class.def'][0]
        class_ranges.append((
            class_node.start_point[0] + 1,
            class_node.end_point[0] + 1
        ))
    return class_ranges


def get_file_funcs(tree, language):
    """获取所有本地函数名称"""
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
                PARAMETER_INDEX: param_index,
                PARAMETER_NAME: None,
                PARAMETER_TYPE: None,
                PARAMETER_DEFAULT: None,
                PARAMETER_VALUE: None
            }
            
            # 遍历参数节点的所有子节点
            for sub_child in child.children:
                if sub_child.type == 'variable_name':
                    param_info[PARAMETER_NAME] = sub_child.text.decode('utf-8')
                elif sub_child.type in ['primitive_type', 'name', 'nullable_type']:
                    param_info[PARAMETER_TYPE] = sub_child.text.decode('utf-8')
                elif sub_child.type == '=':
                    # 处理默认值
                    value_node = child.children[-1]  # 默认值通常是最后一个子节点
                    if value_node.type == 'string':
                        default_value = value_node.text.decode('utf-8')[1:-1]  # 去掉引号
                    else:
                        default_value = value_node.text.decode('utf-8')
                    param_info[PARAMETER_DEFAULT] = default_value
                    param_info[PARAMETER_VALUE] = None
            
            # 如果参数类型未设置，尝试从变量名推断类型
            if param_info[PARAMETER_TYPE] is None:
                if param_info[PARAMETER_NAME].startswith('$'):
                    param_info[PARAMETER_TYPE] = 'mixed'  # PHP默认类型
            
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
            current_function[CALLED_METHODS].append(call_info)
    
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
            
            call_info = {
                METHOD_NAME: method_name,
                METHOD_OBJECT: object_node.text.decode('utf-8'),
                METHOD_TYPE: MethodType.OBJECT_METHOD.value,
                METHOD_PARAMETERS: process_call_parameters(args_node) if args_node else [],
                METHOD_START_LINE: method_node.start_point[0] + 1,
                METHOD_END_LINE: method_node.end_point[0] + 1,
                METHOD_FULL_NAME: f"{object_node.text.decode('utf-8')}->{method_name}",
                METHOD_VISIBILITY: PHPVisibility.PUBLIC.value,
                METHOD_MODIFIERS: [],
                METHOD_RETURN_TYPE: None,
                METHOD_RETURN_VALUE: None
            }
            
            current_function[CALLED_METHODS].append(call_info)

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
                
                # 处理参数
                args_node = match_dict.get('function_args', [None])[0]
                call_params = process_call_parameters(args_node) if args_node else []
                
                # 确保参数名称正确
                if func_name == 'is_null' and call_params:
                    call_params[0][PARAMETER_NAME] = 'username' if 'username' in current_function[METHOD_PARAMETERS] else call_params[0][PARAMETER_NAME]
                
                call_info = {
                    METHOD_NAME: func_name,
                    METHOD_START_LINE: func_node.start_point[0] + 1,
                    METHOD_END_LINE: func_node.end_point[0] + 1,
                    METHOD_OBJECT: None,
                    METHOD_FULL_NAME: func_name,
                    METHOD_TYPE: (MethodType.LOCAL_METHOD.value if func_name in file_functions else MethodType.BUILTIN_METHOD.value),
                    METHOD_VISIBILITY: PHPVisibility.PUBLIC.value,
                    METHOD_MODIFIERS: [],
                    METHOD_RETURN_TYPE: None,
                    METHOD_RETURN_VALUE: None,
                    METHOD_PARAMETERS: call_params
                }
                
                if call_info.get(METHOD_TYPE) != MethodType.BUILTIN_METHOD.value:
                    current_function[CALLED_METHODS].append(call_info)


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
            param_name = (function_params[param_index][PARAMETER_NAME] 
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
                PARAMETER_INDEX: param_index,
                PARAMETER_NAME: param_name,
                PARAMETER_TYPE: None,
                PARAMETER_DEFAULT: None,
                PARAMETER_VALUE: value
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
    function_ranges = [(f[METHOD_START_LINE], f[METHOD_END_LINE]) for f in functions_info]
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
                
                object_name = object_node.text.decode('utf-8')
                print(f"Found method call: {object_name}->{method_name} at line {line_num}")
                
                call_info = {
                    METHOD_NAME: method_name,
                    METHOD_START_LINE: line_num,
                    METHOD_END_LINE: method_node.end_point[0] + 1,
                    METHOD_OBJECT: object_name,
                    METHOD_FULL_NAME: f"{object_name}->{method_name}",
                    METHOD_TYPE: MethodType.OBJECT_METHOD.value,
                    METHOD_VISIBILITY: PHPVisibility.PUBLIC.value,
                    METHOD_MODIFIERS: [],
                    METHOD_RETURN_TYPE: None,
                    METHOD_RETURN_VALUE: None,
                    METHOD_PARAMETERS: process_call_parameters(args_node) if args_node else []
                }
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
                
                print(f"Found function call: {func_name} at line {line_num}")
                
                call_info = {
                    METHOD_NAME: func_name,
                    METHOD_START_LINE: line_num,
                    METHOD_END_LINE: call_node.end_point[0] + 1,
                    METHOD_OBJECT: None,
                    METHOD_FULL_NAME: func_name,
                    METHOD_TYPE: (MethodType.LOCAL_METHOD.value if func_name in file_functions 
                                else MethodType.CUSTOM_METHOD.value),
                    METHOD_VISIBILITY: PHPVisibility.PUBLIC.value,
                    METHOD_MODIFIERS: [],
                    METHOD_RETURN_TYPE: None,
                    METHOD_RETURN_VALUE: None,
                    METHOD_PARAMETERS: process_call_parameters(args_node) if args_node else []
                }
                non_func_calls.append(call_info)
    
    if non_func_calls:
        return {
            METHOD_NAME: NOT_IN_FUNCS,
            METHOD_START_LINE: tree.root_node.start_point[0] + 1,
            METHOD_END_LINE: tree.root_node.end_point[0] + 1,
            METHOD_OBJECT: None,
            METHOD_FULL_NAME: NOT_IN_FUNCS,
            METHOD_VISIBILITY: "PUBLIC",
            METHOD_MODIFIERS: [],
            METHOD_TYPE: MethodType.FILES_METHOD.value,
            METHOD_RETURN_TYPE: None,
            METHOD_RETURN_VALUE: None,
            METHOD_PARAMETERS: [],
            CALLED_METHODS: non_func_calls
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
        METHOD_NAME: "__construct",
        METHOD_START_LINE: line_num,
        METHOD_END_LINE: class_node.end_point[0] + 1,
        METHOD_OBJECT: class_name,
        METHOD_FULL_NAME: f"{class_name}::__construct",
        METHOD_TYPE: MethodType.CONSTRUCTOR.value,
        METHOD_VISIBILITY: PHPVisibility.PUBLIC.value,
        METHOD_MODIFIERS: [],
        METHOD_RETURN_TYPE: class_name,
        METHOD_RETURN_VALUE: class_name,
        METHOD_PARAMETERS: process_call_parameters(args_node) if args_node else []
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