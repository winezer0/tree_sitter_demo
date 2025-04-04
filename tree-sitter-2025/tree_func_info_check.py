from typing import Tuple, List

from tree_const import PHP_MAGIC_METHODS, PHP_BUILTIN_FUNCTIONS
from tree_enums import MethodKeys, PHPVisibility, MethodType, ParameterKeys, ClassKeys, PHPModifier


def create_general_method_res(f_name_txt, f_start_line, f_end_line, f_params_info, f_return_type, f_return_value, f_called_methods, f_is_native):
    """创建本文件定义的普通函数的信息格式 14个值"""
    return {
                MethodKeys.NAME.value: f_name_txt,
                MethodKeys.START_LINE.value: f_start_line,
                MethodKeys.END_LINE.value:f_end_line,

                MethodKeys.OBJECT.value: "",                    # 普通函数没有对象
                MethodKeys.CLASS.value: "",                     # 普通函数不属于类
                MethodKeys.FULLNAME.value: f_name_txt,          # 普通函数的全名就是函数名
                MethodKeys.VISIBILITY.value: PHPVisibility.PUBLIC.value,    # 普通函数默认public
                MethodKeys.MODIFIERS.value: [],                 # 普通函数访问属性 为空
                MethodKeys.METHOD_TYPE.value: MethodType.GENERAL.value,    # 本文件定义的 普通全局

                MethodKeys.PARAMS.value: f_params_info,         # 动态解析 函数的参数信息
                MethodKeys.RETURN_TYPE.value: f_return_type,    # 动态解析 函数的返回值类型
                MethodKeys.RETURN_VALUE.value: f_return_value,  # 动态解析 函数的返回值
                MethodKeys.CALLED.value: f_called_methods,      # 动态解析 函数类调用的其他方法
                MethodKeys.IS_NATIVE.value: f_is_native,        # 被调用的函数是否在本文件内,仅当本函数是被调用函数时有值
    }


def create_called_method_res(f_name_txt, f_start_line, f_end_line, f_called_object, f_called_class, f_fullname,
                             f_modifiers, f_method_type, f_params_info, f_return_type, f_return_value, f_is_native):
    """创建本文件调用的函数的返回格式(应该只有普通函数) 14个值"""
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
                MethodKeys.IS_NATIVE.value: f_is_native,        # 被调用的函数是否在本文件内,仅当本函数是被调用函数时有值
    }


def query_general_methods_define_names_ranges(tree, language) -> Tuple[set, set[Tuple[int, int]]]:
    """
    获取所有本地普通函数（全局函数）的名称及其范围。

    :param tree: 語法樹
    :param language: 語言解析器
    :return: 一個元組，包含兩個元素：
             - 第一個元素是函數名稱的集合
             - 第二個元素是函數範圍的列表，每個範圍是一個 (起始行, 結束行) 的元組
    """
    file_methods_names = set()
    file_methods_ranges = set()

    # 定义查询语句
    function_query = language.query("""
        (function_definition
            name: (name) @function.name
        ) @function.def
    """)
    for match in function_query.matches(tree.root_node):
        match_dict = match[1]
        function_name_mark = 'function.name'
        if function_name_mark in match_dict:
            name_node = match_dict[function_name_mark][0]
            if name_node:
                file_methods_names.add(name_node.text.decode('utf8'))

        function_def_mark = 'function.def'
        if function_def_mark in match_dict:
            function_node = match_dict[function_def_mark][0]
            if function_node:
                file_methods_ranges.add((function_node.start_point[0], function_node.end_point[0]))
    return file_methods_names, file_methods_ranges

def query_classes_define_names_ranges(tree, language) -> Tuple[set[str], set[Tuple[int, int]]]:
    """获取所有类定义的类名及其代码行范围。 """
    class_names = set()  # 存儲類名稱
    class_ranges = set()  # 存儲類範圍

    # 定義查詢語句，匹配類定義，捕獲類名和整個類節點
    class_query = language.query("""
        (class_declaration
            name: (name) @class.name
        ) @class.def
    """)

    for match in class_query.matches(tree.root_node):
        match_dict = match[1]

        class_name_mark = 'class.name'
        if class_name_mark in match_dict:
            name_node = match_dict[class_name_mark][0]
            if name_node:
                class_names.add(name_node.text.decode('utf8'))

        class_def_mark = 'class.def'
        if class_def_mark in match_dict:
            class_node = match_dict[class_def_mark][0]
            if class_node:
                class_ranges.add((
                    class_node.start_point[0] + 1,
                    class_node.end_point[0] + 1
                ))
    return class_names, class_ranges

def query_general_methods_info(tree, language, classes_ranges, classes_names, gb_methods_names):
    # 查询所有函数定义
    function_query = language.query("""
        ; 全局函数定义
        (function_definition
            name: (name) @function.name
            parameters: (formal_parameters) @function.params
            body: (compound_statement) @function.body
        ) @function.def
    """)
    #     ; 全局函数调用  好像本处没有用上
    #     (function_call_expression
    #         (name) @function_call
    #         (arguments) @function_args
    #     )
    #
    #     ; 对象方法调用 好像本处没有用上
    #     (member_call_expression
    #         object: (variable_name) @method.object
    #         name: (name) @method.name
    #         arguments: (arguments) @method.args
    #     ) @method.call
    #
    #     ; 对象创建调用 好像本处没有用上
    #     (object_creation_expression
    #         (name) @new_class_name
    #         (arguments) @constructor_args
    #     ) @new_expr


    functions_info = []
    # 解析所有函数信息
    query_matches = function_query.matches(tree.root_node)
    for pattern_index, match_dict in query_matches:
        if 'function.def' in match_dict:
            function_node = match_dict['function.def'][0]
            # 检查函数是否在类范围内
            if any(start <= function_node.start_point[0] + 1 <= end for start, end in classes_ranges):
                continue

            # 处理函数定义
            f_name_node = match_dict['function.name'][0]
            f_params_node = match_dict.get('function.params', [None])[0]
            f_body_node = match_dict.get('function.body', [None])[0]
            f_return_type_node = match_dict.get('function.return_type', [None])[0]

            # 获取方法的返回值 TODO 函数返回值好像没有获取成功
            f_return_value = query_method_return_value(language, f_body_node)
            # 获取方法的返回类型  TODO METHOD_RETURN_TYPE 好像没有分析成功
            f_return_type = f_return_type_node.text.decode('utf-8') if f_return_type_node else None
            f_params_info = parse_node_params_info(f_params_node) if f_params_node else []

            f_name_txt = f_name_node.text.decode('utf-8')
            f_start_line = function_node.start_point[0] + 1
            f_end_line = function_node.end_point[0] + 1
            # 解析函数体中的调用的其他方法
            f_called_methods = query_method_body_called_methods(language, f_body_node, classes_names, gb_methods_names)
            # 总结函数方法结果
            method_info = create_general_method_res(f_name_txt, f_start_line, f_end_line, f_params_info, f_return_type, f_return_value, f_called_methods, None)
            functions_info.append(method_info)
    return functions_info


def has_not_function_content(tree, class_ranges, function_ranges):
    """检查是否有非class和非函数的内容"""
    root_start = tree.root_node.start_point[0] + 1
    root_end = tree.root_node.end_point[0] + 1

    for i in range(root_start, root_end + 1):
        if (not any(start <= i <= end for start, end in function_ranges) and
            not any(start <= i <= end for start, end in class_ranges)):
            return True
    return False


def query_method_return_value(language, body_node):
    """查找方法的返回值"""
    f_return_value = None
    if not body_node:
        return f_return_value
    # 进行查找
    return_value_query = language.query("""
                    (return_statement
                        (expression)? @return.value
                    ) @return.stmt
                """)
    for return_match in return_value_query.matches(body_node):
        if 'return.value' in return_match[1]:
            return_node = return_match[1]['return.value'][0]
            f_return_value = return_node.text.decode('utf-8')
    return f_return_value


def parse_node_params_info(params_node):
    """解析函数节点的函数参数信息"""
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
                child_text = sub_child.text.decode('utf-8')
                if sub_child.type == 'variable_name':
                    param_info[ParameterKeys.PARAM_NAME.value] = child_text
                elif sub_child.type in ['primitive_type', 'name', 'nullable_type']:
                    param_info[ParameterKeys.PARAM_TYPE.value] = child_text
                elif sub_child.type == '=':
                    # 处理默认值
                    value_node = child.children[-1]  # 默认值通常是最后一个子节点
                    if value_node.type == 'string':
                        default_value = value_node.text.decode('utf-8')[1:-1]  # 去掉引号
                    else:
                        default_value = value_node.text.decode('utf-8')
                    param_info[ParameterKeys.PARAM_DEFAULT.value] = default_value
                    param_info[ParameterKeys.PARAM_VALUE.value] = None

            # 如果参数类型未设置，尝试从变量名推断类型 # TODO 需要考虑优化实现参数节点解析
            if param_info[ParameterKeys.PARAM_TYPE.value] is None:
                if param_info[ParameterKeys.PARAM_NAME.value].startswith('$'):
                    param_info[ParameterKeys.PARAM_TYPE.value] = 'mixed'  # PHP默认类型

            parameters.append(param_info)
            param_index += 1

    return parameters


def query_method_body_called_methods(language, body_node, classes_names, gb_methods_names):
    """查询方法体代码内调用的其他方法信息"""
    if not body_node:
        return []

    called_method_query = language.query("""
        ;查询常规函数调用
        (function_call_expression
            (name) @function_call
            (arguments) @function_args
        )
        ;查询对象方法创建
        (object_creation_expression
            (name) @new_class_name
            (arguments) @constructor_args
        ) @new_expr

        ;查询对象方法调用
        (member_call_expression
            object: (_) @method.object
            name: (name) @method.name
            arguments: (arguments) @method.args
        ) @method.call
    """)

    queried_info = called_method_query.matches(body_node)
    called_methods = []
    # 处理普通函数调用
    # call_general_method_query = language.query("""
    #     (function_call_expression
    #         function: (name) @function_call
    #         arguments: (arguments) @function_args
    #     )
    # """)
    seen_calls = set()

    for match in queried_info:
        match_dict = match[1]
        if 'function_call' in match_dict:
            func_node = match_dict['function_call'][0]
            func_name = func_node.text.decode('utf-8')
            called_func_key = f"{func_name}:{func_node.start_point[0]}"

            if called_func_key not in seen_calls:
                seen_calls.add(called_func_key)
                args_node = match_dict.get('function_args', [None])[0]

            method_is_native = func_name in gb_methods_names  # 分析函数是否属于本文件函数
            called_general_method = res_called_general_method(func_node, func_name, args_node, method_is_native)
            if called_general_method[MethodKeys.METHOD_TYPE.value] != MethodType.BUILTIN.value:
                called_methods.append(called_general_method)

    # # 添加对象创建查询
    # call_object_construct_query = language.query("""
    #     (object_creation_expression
    #         (name) @new_class_name
    #         (arguments) @constructor_args
    #     ) @new_expr
    # """)

    # 处理对象创建
    for match in queried_info:
        match_dict = match[1]
        if 'new_class_name' in match_dict:
            class_node = match_dict['new_class_name'][0]
            args_node = match_dict.get('constructor_args', [None])[0]
            class_name = class_node.text.decode('utf-8')
            class_is_native = class_name in classes_names
            called_construct_method = res_called_construct_method(class_node, args_node, class_is_native)
            called_methods.append(called_construct_method)

    # # 原有的对象方法调用查询
    # call_object_method_query = language.query("""
    #     (member_call_expression
    #         object: (_) @method.object
    #         name: (name) @method.name
    #         arguments: (arguments) @method.args
    #     ) @method.call
    # """)

    # 处理对象方法调用
    for match in queried_info:
        match_dict = match[1]
        if 'method.call' in match_dict:
            method_node = match_dict['method.call'][0]
            object_node = match_dict['method.object'][0]
            method_name = match_dict['method.name'][0].text.decode('utf-8')
            args_node = match_dict.get('method.args', [None])[0]

            object_name = object_node.text.decode('utf-8')
            class_is_native = True if object_name in classes_names else None # TODO 需要进一步进行分析
            method_is_static = object_name in classes_names
            called_object_method = res_called_object_method(object_node, method_node, args_node, method_name,
                                                            class_is_native, method_is_static)
            called_methods.append(called_object_method)
    return called_methods


def parse_called_method_params(args_node):
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


def line_in_methods_or_classes_ranges(line_num, function_ranges, class_ranges):
    """检查行号是否在函数或类范围内"""
    return any(start <= line_num <= end for start, end in function_ranges) or any(start <= line_num <= end for start, end in class_ranges)


def query_not_method_called_methods(tree, language, classes_names, classes_ranges, gb_methods_names, gb_methods_ranges):
    """查询全部代码调用的函数信息 并且只保留其中不属于函数和类的部分"""
    queried = language.query("""
        ;查询常规函数调用
        (function_call_expression
            (name) @function_call
            (arguments) @function_args
        )
    
        ;查询对象方法创建
        (object_creation_expression
            (name) @new_class_name
            (arguments) @constructor_args
        ) @new_expr
    
        ; 查询对象方法调用
        (member_call_expression
            object: (_) @method.object
            name: (name) @method.name
            arguments: (arguments) @method.args
        ) @method.call
    """)

    nf_called_infos = []

    # 处理对象方法调用
    for match in queried.matches(tree.root_node):
        match_dict = match[1]
        if 'method.call' in match_dict:
            method_node = match_dict['method.call'][0]
            start_line = method_node.start_point[0] + 1

            if not line_in_methods_or_classes_ranges(start_line, gb_methods_ranges, classes_ranges):
                method_name = match_dict['method.name'][0].text.decode('utf-8')
                object_node = match_dict['method.object'][0]
                args_node = match_dict.get('method.args', [None])[0]

                object_name = object_node.text.decode('utf-8')
                class_is_native = True if object_name in classes_names else None  # TODO 需要进一步进行分析
                method_is_static = object_name in classes_names
                nf_called_info = res_called_object_method(object_node, method_node, args_node, method_name,
                                                          class_is_native, method_is_static)
                nf_called_infos.append(nf_called_info)

    # 处理对象创建
    for match in queried.matches(tree.root_node):
        match_dict = match[1]
        if 'new_class_name' in match_dict:
            class_node = match_dict['new_class_name'][0]
            start_line = class_node.start_point[0] + 1

            class_name = class_node.text.decode('utf-8')
            class_is_native = class_name in classes_names

            if not line_in_methods_or_classes_ranges(start_line, gb_methods_ranges, classes_ranges):
                args_node = match_dict.get('constructor_args', [None])[0]
                nf_called_info = res_called_construct_method(class_node, args_node, class_is_native)
                nf_called_infos.append(nf_called_info)

    # 处理普通函数调用
    for match in queried.matches(tree.root_node):
        match_dict = match[1]
        if 'function_call' in match_dict:
            func_node = match_dict['function_call'][0]
            start_line = func_node.start_point[0] + 1

            if not line_in_methods_or_classes_ranges(start_line, gb_methods_ranges, classes_ranges):
                func_name = func_node.text.decode('utf-8')
                args_node = match_dict.get('function_args', [None])[0]

                # 分析函数类型
                method_is_native = func_name in gb_methods_names
                nf_called_info = res_called_general_method(func_node, func_name, args_node, method_is_native)
                nf_called_infos.append(nf_called_info)

    # 判断函数是否有内容, 有的话进行结果返回
    if nf_called_infos:
        nf_name_txt = ClassKeys.NOT_IN_METHOD.value
        nf_start_line = tree.root_node.start_point[0] + 1
        nf_end_line = tree.root_node.end_point[0] + 1
        return create_general_method_res(nf_name_txt, nf_start_line, nf_end_line, None, None, None, nf_called_infos, None)
    return None


def guess_method_type(func_name, method_is_native, is_class_method):
    """根据被调用的函数完整信息猜测函数名"""
    if is_class_method:
        method_type = MethodType.CLASS.value
        # 判断方法是否是php类的内置构造方法
        if func_name == '__construct':
            method_type = MethodType.CONSTRUCT.value
        # 判断方法是否是php类的内置魔术方法
        elif func_name in PHP_MAGIC_METHODS and method_is_native is False:
            method_type = MethodType.BUILTIN.value
    else:
        method_type = MethodType.GENERAL.value
        # 判断方法是否是php内置方法
        if func_name in PHP_BUILTIN_FUNCTIONS and method_is_native is False:
            method_type = MethodType.BUILTIN.value
        # 判断方法是否时动态调用方法
        elif func_name.startswith("$"):
            method_type = MethodType.DYNAMIC.value
    return method_type


def res_called_construct_method(class_node, args_node, f_is_native):
    """处理构造函数调用的通用函数
    Args:
        class_node: 类名节点
        args_node: 构造函数参数节点
        f_is_native: 是否是本地的类
    Returns:
        dict: 构造函数调用信息
    """
    f_name_txt = "__construct"  # 固定
    f_called_class = class_node.text.decode('utf-8')
    f_called_object = f_called_class # 原则是构造方法没有对象的
    f_fullname = f"{f_called_class}::__construct"  # 固定
    f_method_type = guess_method_type(f_name_txt, f_is_native, True)
    f_start_line = class_node.start_point[0] + 1
    f_end_line = class_node.end_point[0] + 1
    f_params_info = parse_called_method_params(args_node) if args_node else []
    print(f"Found constructor call: {f_fullname} at line {f_start_line}")
    return create_called_method_res(f_name_txt, f_start_line, f_end_line, f_called_object, f_called_class, f_fullname,
                                    None, f_method_type, f_params_info, f_called_class, f_called_class, f_is_native)


def res_called_object_method(object_node, method_node, args_node, f_name_txt, f_is_native, f_is_static):
    """处理对象方法调用的通用函数
    Args:
        :param method_node: 方法调用节点
        :param object_node: 对象节点
        :param args_node: 参数节点
        :param f_name_txt: 方法名
        :param f_is_native: 方法是不是本地文件内的函数 需要进一步分析
        :param f_is_static: 调用方式是不是静态调用 需要分析对象名称
    Returns:
        dict: 方法调用信息
    """

    f_start_line = method_node.start_point[0] + 1
    f_end_line = method_node.end_point[0] + 1
    f_called_object = object_node.text.decode('utf-8')
    f_method_type = guess_method_type(f_name_txt, f_is_native, True)
    f_called_class = object_node.text.decode('utf-8') if f_is_static else None
    f_modifiers = [PHPModifier.STATIC.value] if f_is_static else []
    f_fullname = f"{f_called_object}::{f_name_txt}" if f_is_static is True else f"{f_called_object}->{f_name_txt}"
    f_params_info = parse_called_method_params(args_node) if args_node else []
    print(f"Found method call: {f_called_object}->{f_name_txt} at line {f_start_line}")
    return create_called_method_res(f_name_txt, f_start_line, f_end_line, f_called_object, f_called_class, f_fullname,
                                    f_modifiers, f_method_type, f_params_info, None, None, f_is_native)


def res_called_general_method(method_node, f_name_txt, args_node, f_is_native):
    """处理普通函数调用的通用函数
    Args:
        func_node: 函数调用节点
        f_name_txt: 函数名
        args_node: 参数节点
        :param f_is_native: 方法是不是本地方法
    Returns:
        dict: 函数调用信息
    """
    f_start_line = method_node.start_point[0] + 1
    f_end_line = method_node.end_point[0] + 1
    f_method_type = guess_method_type(f_name_txt, f_is_native, False)
    f_params_info = parse_called_method_params(args_node) if args_node else []
    print(f"Found function call: {f_name_txt} at line {f_start_line}")
    return create_called_method_res(f_name_txt, f_start_line, f_end_line, None, None, f_name_txt,
                                    None, f_method_type, f_params_info, None, None, f_is_native)

