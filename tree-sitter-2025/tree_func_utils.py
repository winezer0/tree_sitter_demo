from tree_sitter._binding import Node

from guess import guess_called_object_is_native, guess_method_type

from tree_enums import MethodKeys, MethodType
from tree_func_utils_sub_parse import parse_body_node_return_info, parse_params_node, parse_arguments_node
from tree_sitter_uitls import find_first_child_by_field, get_node_filed_text

TREE_SITTER_PHP_METHOD_CALLED_STAT = """
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
    ) @member.call

    ;查询静态方法调用
    (scoped_call_expression
        scope: (_) @method.object
        name: (name) @method.name
        arguments: (arguments)? @method.args
    ) @static.call
"""


def create_method_result_dict(uniq_id, method_name, start_line, end_line, object_name, class_name, method_fullname, method_file, visibility, modifiers, method_type, params_info, return_type, return_value, is_native, called_methods):
    """创建方法信息的综合返回结果"""
    return {
        MethodKeys.UNIQ_ID.value: uniq_id,
        MethodKeys.NAME.value: method_name,
        MethodKeys.START_LINE.value: start_line,
        MethodKeys.END_LINE.value: end_line,

        MethodKeys.OBJECT.value: object_name,  # 普通函数没有对象
        MethodKeys.CLASS.value: class_name,  # 普通函数不属于类
        MethodKeys.FULLNAME.value: method_fullname,  # 普通函数的全名就是函数名
        MethodKeys.FILE.value: method_file,

        MethodKeys.VISIBILITY.value: visibility,  # 普通函数默认public
        MethodKeys.MODIFIERS.value: modifiers,  # 普通函数访问属性 为空

        MethodKeys.METHOD_TYPE.value: method_type,  # 本文件定义的 普通全局
        MethodKeys.PARAMS.value: params_info,  # 动态解析 函数的参数信息
        MethodKeys.RETURN_TYPE.value: return_type,  # 动态解析 函数的返回值类型
        MethodKeys.RETURN_VALUE.value: return_value,  # 动态解析 函数的返回值

        MethodKeys.IS_NATIVE.value: is_native,  # 被调用的函数是否在本文件内,仅当本函数是被调用函数时有值
        MethodKeys.CALLED.value: called_methods,  # 动态解析 函数类调用的其他方法
    }


def query_method_node_called_methods(language, body_node, classes_names=[], gb_methods_names=[], object_class_infos={}):
    """查询方法体代码内调用的其他方法信息"""
    print(f"body_node:{body_node}")


    method_called_sql = """
        ;查询常规函数调用
        (function_call_expression
            (name) 
            (arguments) 
        ) @function_call

        ;查询对象方法创建
        (object_creation_expression
          (name) 
          (arguments) 
        ) @object_creation

        ;查询对象方法调用
        (member_call_expression
            (_) 
            (name) 
            (arguments) 
        ) @member_call

        ;查询静态方法调用
        (scoped_call_expression
            (_)
            (name) 
            (arguments)
        ) @scoped_call
    """

    called_method_query = language.query(method_called_sql)
    matched_info = called_method_query.matches(body_node)

    # body_node:
    # (compound_statement (expression_statement (assignment_expression
    # left: (variable_name (name))
    # right: (object_creation_expression (name) (arguments (argument (encapsed_string (string_content))))))) (expression_statement (assignment_expression
    # left: (variable_name (name))
    # right: (scoped_call_expression scope: (name) name: (name) arguments: (arguments (argument (encapsed_string (string_content)))))))
    # (return_statement (variable_name (name))) (return_statement (variable_name (name))))
    called_methods = []

    # ;查询常规函数调用 function_call_expression @ function_call
    # ;查询对象方法创建 object_creation_expression @ object_creation
    # ;查询对象方法调用 member_call_expression @ member_call
    # ;查询静态方法调用 scoped_call_expression @ scoped_call

    def parse_function_call_expression(function_call_node:Node):
        called_info = {}
        print(f"function_call_node:{function_call_node}")
        # (function_call_expression function: (name) arguments: (arguments (argument (string (string_content)))))
        method_name = get_node_filed_text(function_call_node, 'name')
        f_start_line = func_node.start_point[0]
        f_end_line = func_node.end_point[0]
        # 解析参数信息
        arguments_node = find_first_child_by_field(function_call_node, 'arguments')
        args_info = parse_arguments_node(arguments_node)

        # 定义是否是本文件函数
        method_is_native = method_name in gb_methods_names
        is_class_method = False
        # 定义获取函数类型
        method_type = guess_method_type(method_name, method_is_native, is_class_method)
        print(f"method_type:{method_name} is{method_type}  native:{method_is_native} ")
        # TODO 合并结果并返回
        return called_info

    # 处理普通函数调用
    for match in matched_info:
        match_dict = match[1]
        if 'function_call' in match_dict:
            func_node = match_dict['function_call'][0]
            called_info = parse_function_call_expression(func_node)
            called_methods.append(called_info)

    # # # 添加对象创建查询
    # for match in matched_info:
    #     match_dict = match[1]
    #     if 'new_class_name' in match_dict:
    #         class_node = match_dict['new_class_name'][0]
    #         args_node = match_dict.get('constructor_args', [None])[0]
    #         class_name = class_node.text.decode('utf-8')
    #         class_is_native = class_name in classes_names # 构造方法 可以直接判断
    #         called_construct_method = res_called_construct_method(class_node, args_node, class_is_native)
    #         called_methods.append(called_construct_method)
    #
    # # 处理对象方法和静态方法调用
    # for match in matched_info:
    #     match_dict = match[1]
    #     if 'member.call' in match_dict or 'static.call' in match_dict:
    #         # 根据静态方法和普通对象方法的语法查询结果关键字进行判断是否是静态方法
    #         is_static_call = 'static.call' in match_dict
    #         method_node = match_dict['static.call'][0] if is_static_call else match_dict['member.call'][0]
    #         object_node = match_dict['method.object'][0]
    #         method_name = match_dict['method.name'][0].text.decode('utf-8')
    #         args_node = match_dict.get('method.args', [None])[0]
    #
    #         object_name = object_node.text.decode('utf-8')
    #         object_line = object_node.start_point[0]
    #         class_is_native, class_name = guess_called_object_is_native(object_name, object_line, classes_names, object_class_infos)
    #         called_object_method = res_called_object_method(object_node, method_node, args_node, method_name, class_is_native, is_static_call, class_name)
    #         called_methods.append(called_object_method)

    return called_methods

def query_global_methods_info(language, root_node, classes_ranges, classes_names, gb_methods_names, object_class_infos):
    """查询节点中的所有全局函数定义信息 需要优化"""
    # 查询所有函数定义
    function_query = language.query("""
        ; 全局函数定义
        (function_definition) @function.def
    """)

    functions_info = []
    # 解析所有函数信息
    query_matches = function_query.matches(root_node)
    for pattern_index, match_dict in query_matches:
        if 'function.def' in match_dict:
            function_node = match_dict['function.def'][0]
            # 检查函数是否在类范围内
            if any(start <= function_node.start_point[0] <= end for start, end in classes_ranges):
                print("存在函数定义在内范围中!!!")
                continue

            print(f"function_node:{function_node}")
            # function_node:(function_definition
            # name: (name)
            # parameters: (formal_parameters (simple_parameter name: (variable_name (name)) default_value: (string (string_content))))
            # body: (compound_statement
            # (expression_statement (assignment_expression left: (variable_name (name))
            # right: (object_creation_expression (name) (arguments (argument (encapsed_string (string_content)))))))
            # (expression_statement (assignment_expression left: (variable_name (name))
            # right: (scoped_call_expression scope: (name) name: (name) arguments: (arguments (argument (encapsed_string (string_content)))))))))

            # 从 function_node 中直接提取子节点
            f_start_line = function_node.start_point[0]
            f_end_line = function_node.end_point[0]
            f_name_text = get_node_filed_text(function_node, "name")
            print(f"f_name_text:{f_name_text}")

            f_body_node = find_first_child_by_field(function_node, "body")
            print(f"f_body_node:{f_body_node}")
            # 获取方法的返回信息
            f_return_infos = parse_body_node_return_info(f_body_node)
            print(f"f_return_infos:{f_return_infos}")

            # 获取返回参数信息
            f_params_node = find_first_child_by_field(function_node, "parameters")
            print(f"f_params_node:{f_params_node}")
            f_params_info = parse_params_node(f_params_node)
            print(f"f_params_info:{f_params_info}")
            # 解析函数体中的调用的其他方法
            f_called_methods = query_method_node_called_methods(language, f_body_node, classes_names, gb_methods_names, object_class_infos)
            print(f"f_called_methods:{f_called_methods}")
            exit()
            # 总结函数方法信息
            method_info = create_method_result_dict(f_name_txt, f_start_line, f_end_line, f_params_info, f_return_type, f_return_value, f_called_methods, None)
            functions_info.append(method_info)
    return functions_info