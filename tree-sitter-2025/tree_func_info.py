from tree_const import *
from tree_enums import MethodType, PHPVisibility, MethodKeys, ParameterKeys, ClassKeys


def create_direct_method_info(f_name_txt, f_start_line, f_end_line, f_params_info, f_return_type, f_return_value, f_called_methods, f_is_native):
    return {
                MethodKeys.NAME.value: f_name_txt,
                MethodKeys.START_LINE.value: f_start_line,
                MethodKeys.END_LINE.value:f_end_line,
                MethodKeys.OBJECT.value: "",                    # 普通函数没有对象
                MethodKeys.CLASS.value: "",                     # 普通函数不属于类
                MethodKeys.FULLNAME.value: f_name_txt,          # 普通函数的全名就是函数名
                MethodKeys.VISIBILITY.value: PHPVisibility.PUBLIC.value,    # 普通函数默认public
                MethodKeys.MODIFIERS.value: [],                 # 普通函数访问属性
                MethodKeys.METHOD_TYPE.value: MethodType.GLOBAL.value,    # 所有本文件定义的 普通全局 方法都规定为 GLOBAL_METHOD
                MethodKeys.PARAMS.value: f_params_info,         # 动态解析 函数的参数信息
                MethodKeys.RETURN_TYPE.value: f_return_type,    # 动态解析 函数的返回值类型
                MethodKeys.RETURN_VALUE.value: f_return_value,  # 动态解析 函数的返回值
                MethodKeys.CALLED.value: f_called_methods,      # 动态解析 函数类调用的其他方法
                MethodKeys.CALLED_BY.value: [],                 # 在后续进行调用分析时补充
                MethodKeys.IS_NATIVE.value: f_is_native,        # 被调用的函数是否在本文件内,仅当本函数是被调用函数时有值
    }


def create_called_method_info(f_name_txt, f_start_line, f_end_line, f_called_object, f_called_class, f_fullname,
                              f_modifiers, f_method_type, f_params_info, f_return_type, f_return_value, f_is_native):
    return {
                MethodKeys.NAME.value: f_name_txt,            # 被调用函名
                MethodKeys.START_LINE.value: f_start_line,      # 被调用函数行号
                MethodKeys.END_LINE.value:f_end_line,           # 被调用函数末行
                MethodKeys.OBJECT.value: f_called_object,       # 被调用函数对象
                MethodKeys.CLASS.value: f_called_class,         # 普通函数不属于类
                MethodKeys.FULLNAME.value: f_fullname,          # 普通函数的全名就是函数名
                MethodKeys.VISIBILITY.value: PHPVisibility.PUBLIC.value,      # 被调用的函数说明肯定是public
                MethodKeys.MODIFIERS.value: f_modifiers,        # 普通函数访问属性
                MethodKeys.METHOD_TYPE.value: f_method_type,    # 所有本文件定义的 普通全局 方法都规定为 GLOBAL_METHOD
                MethodKeys.PARAMS.value: f_params_info,         # 动态解析 函数的参数信息
                MethodKeys.RETURN_TYPE.value: f_return_type,    # 动态解析 函数的返回值类型
                MethodKeys.RETURN_VALUE.value: f_return_value,  # 动态解析 函数的返回值
                MethodKeys.CALLED.value: [],                    # 被调用函数的信息不应该在这里有这个
                MethodKeys.CALLED_BY.value: [],                 # 在后续进行调用分析时补充
                MethodKeys.IS_NATIVE.value: f_is_native,        # 被调用的函数是否在本文件内,仅当本函数是被调用函数时有值
    }


def analyze_direct_method_infos(tree, language):
    """获取所有函数信息，包括函数内部和非函数部分"""
    # 获取所有本地函数名称
    file_functions = get_file_functions(tree, language)
    
    # 获取所有类定义的代码行范围，以排除类方法 本文件不处理类方法
    classes_ranges = get_classes_ranges(tree, language)

    # 获取文件中的所有函数信息
    functions_info = process_functions_infos(tree, language, file_functions, classes_ranges)

    # 处理文件级别的函数调用
    functions_ranges = get_functions_ranges(functions_info)
    if has_non_func_content(tree, classes_ranges, functions_ranges):
        non_function_info = process_non_function_content(tree, language, file_functions, classes_ranges, functions_ranges)
        if non_function_info:
            functions_info.append(non_function_info)
    return functions_info


def get_functions_ranges(functions_info):
    """基于所有函数信息 获取函数代码行范围段"""
    return [(func[MethodKeys.START_LINE.value], func[MethodKeys.END_LINE.value]) for func in functions_info]


def process_functions_infos(tree, language, file_functions, class_ranges):
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
    # 解析所有函数信息
    for pattern_index, match_dict in function_query.matches(tree.root_node):
        if 'function.def' in match_dict:
            function_node = match_dict['function.def'][0]
            # 检查函数是否在类范围内
            if any(start <= function_node.start_point[0] + 1 <= end for start, end in class_ranges):
                continue

            # 处理函数定义
            f_name_node = match_dict['function.name'][0]
            f_params_node = match_dict.get('function.params', [None])[0]
            f_body_node = match_dict.get('function.body', [None])[0]
            f_return_type_node = match_dict.get('function.return_type', [None])[0]

            f_name_txt = f_name_node.text.decode('utf-8')
            # 获取方法的返回值 TODO 函数返回值好像没有获取成功
            f_return_value = find_method_return_value(language, f_body_node)
            # 获取方法的返回类型  TODO METHOD_RETURN_TYPE 好像没有分析成功
            f_return_type = f_return_type_node.text.decode('utf-8') if f_return_type_node else 'unknown'
            f_params_info = process_parameters(f_params_node) if f_params_node else []

            f_start_line = function_node.start_point[0] + 1
            f_end_line = function_node.end_point[0] + 1
            # 解析函数体中的调用的其他方法
            f_called_methods = process_function_body(f_body_node, file_functions, language)
            # 总结函数方法结果
            method_info = create_direct_method_info(f_name_txt, f_start_line, f_end_line, f_params_info, f_return_type, f_return_value, f_called_methods, None)
            functions_info.append(method_info)
    return functions_info


def find_method_return_value(language, f_body_node):
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


def get_classes_ranges(tree, language):
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


def get_file_functions(tree, language):
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


def process_function_body(body_node, file_functions, language):
    if not body_node:
        return []

    called_methods = []
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
            
            called_info = process_call_construct(class_node, args_node, line_num)
            called_methods.append(called_info)
    
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
            
            called_info = process_call_method(method_node, object_node, method_name, args_node, line_num)
            called_methods.append(called_info)

    # 处理普通函数调用
    called_functions_query = language.query("""
        (function_call_expression
            function: (name) @function_call
            arguments: (arguments) @function_args
        )
    """)
    matches = called_functions_query.matches(body_node)
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
                
                called_info = process_call_function(func_node, func_name, args_node, line_num, file_functions)
                if called_info[MethodKeys.METHOD_TYPE.value] != MethodType.BUILTIN.value:
                    called_methods.append(called_info)
    return called_methods


def process_called_method_params(args_node):
    """分析被调用函数的参数信息"""
    parameters = []
    param_index = 0
    
    for arg in args_node.children:
        if arg.type not in [',', '(', ')']:
            param_name =  f"$arg{param_index}"

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
    """检查是否有非class和非函数的内容"""
    root_start = tree.root_node.start_point[0] + 1
    root_end = tree.root_node.end_point[0] + 1
    
    for i in range(root_start, root_end + 1):
        if (not any(start <= i <= end for start, end in function_ranges) and
            not any(start <= i <= end for start, end in class_ranges)):
            return True
    return False


def process_non_function_content(tree, language, file_functions, class_ranges, functions_ranges):
    """处理非函数部分的内容"""
    nf_called_infos = []
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
            
            if not line_in_ranges(line_num, functions_ranges, class_ranges):
                object_node = match_dict['method.object'][0]
                method_name = match_dict['method.name'][0].text.decode('utf-8')
                args_node = match_dict.get('method.args', [None])[0]
                
                nf_called_info = process_call_method(method_node, object_node, method_name, args_node, line_num)
                nf_called_infos.append(nf_called_info)
        
        # 处理对象创建
        elif 'new_class_name' in match_dict:
            class_node = match_dict['new_class_name'][0]
            line_num = class_node.start_point[0] + 1
            
            if not line_in_ranges(line_num, functions_ranges, class_ranges):
                args_node = match_dict.get('constructor_args', [None])[0]
                nf_called_info = process_call_construct(class_node, args_node, line_num)
                nf_called_infos.append(nf_called_info)
        
        # 处理普通函数调用
        elif 'function_call' in match_dict:
            call_node = match_dict['function_call'][0]
            line_num = call_node.start_point[0] + 1
            
            if not line_in_ranges(line_num, functions_ranges, class_ranges):
                func_name = call_node.text.decode('utf-8')
                args_node = match_dict.get('function_args', [None])[0]
                
                nf_called_info = process_call_function(call_node, func_name, args_node, line_num, file_functions)
                nf_called_infos.append(nf_called_info)
    
    if nf_called_infos:
        nf_name_txt = ClassKeys.NOT_IN_METHOD.value
        nf_start_line = tree.root_node.start_point[0] + 1
        nf_end_line = tree.root_node.end_point[0] + 1
        return create_direct_method_info(nf_name_txt, nf_start_line, nf_end_line, None, None, None, nf_called_infos, None)
    return None


def line_in_ranges(line_num, function_ranges, class_ranges):
    """检查行号是否在函数或类范围内"""
    return any(start <= line_num <= end for start, end in function_ranges) or any(start <= line_num <= end for start, end in class_ranges)


def process_call_construct(class_node, args_node, line_num):
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
        MethodKeys.FULLNAME.value: f"{class_name}::__construct",
        MethodKeys.METHOD_TYPE.value: MethodType.CONSTRUCT.value,
        MethodKeys.VISIBILITY.value: PHPVisibility.PUBLIC.value,
        MethodKeys.MODIFIERS.value: [],
        MethodKeys.RETURN_TYPE.value: class_name,
        MethodKeys.RETURN_VALUE.value: class_name,
        MethodKeys.PARAMS.value: process_called_method_params(args_node) if args_node else []
    }


def process_call_method(method_node, object_node, method_name, args_node, line_num):
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
        MethodKeys.FULLNAME.value: f"{object_name}->{method_name}",
        MethodKeys.METHOD_TYPE.value: MethodType.CLASS.value,
        MethodKeys.VISIBILITY.value: PHPVisibility.PUBLIC.value,
        MethodKeys.MODIFIERS.value: [],
        MethodKeys.RETURN_TYPE.value: None,
        MethodKeys.RETURN_VALUE.value: None,
        MethodKeys.PARAMS.value: process_called_method_params(args_node) if args_node else []
    }


def process_call_function(call_node, func_name, args_node, line_num, file_functions):
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
    if func_name in file_functions:
         method_is_native = True

    method_type = MethodType.GLOBAL.value
    if func_name in PHP_BUILTIN_FUNCTIONS and not method_is_native:
        # 判断方法是否是php内置方法
        method_type = MethodType.BUILTIN.value
    elif func_name.startswith("$"):
        # 判断方法是否时动态调用方法
        method_type = MethodType.DYNAMIC.value

    return {
        MethodKeys.NAME.value: func_name,
        MethodKeys.START_LINE.value: line_num,
        MethodKeys.END_LINE.value: call_node.end_point[0] + 1,
        MethodKeys.OBJECT.value: None,
        MethodKeys.FULLNAME.value: func_name,
        MethodKeys.METHOD_TYPE.value: method_type,
        MethodKeys.VISIBILITY.value: PHPVisibility.PUBLIC.value,
        MethodKeys.MODIFIERS.value: [],
        MethodKeys.RETURN_TYPE.value: None,
        MethodKeys.RETURN_VALUE.value: None,
        MethodKeys.PARAMS.value: process_called_method_params(args_node) if args_node else []
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