from guess import guess_method_type

from tree_func_utils_sub_parse import parse_return_node, parse_params_node, create_method_result, \
    parse_function_call_node, parse_object_creation_node, parse_object_method_call_node, \
    parse_static_method_call_node
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


def query_method_node_called_methods(language, body_node, gb_classes_names=[], gb_methods_names=[], gb_object_class_infos={}):
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

    # 处理普通函数调用
    for match in matched_info:
        match_dict = match[1]
        if 'function_call' in match_dict:
            print("开始全局函数方法调用")
            function_call_node = match_dict['function_call'][0]
            called_info = parse_function_call_node(function_call_node, gb_methods_names)
            called_methods.append(called_info)

    # 添加对象创建查询
    for match in matched_info:
        match_dict = match[1]
        if 'object_creation' in match_dict:
            print("开始对象创建方法调用")
            object_creation_node = match_dict['object_creation'][0]
            called_info = parse_object_creation_node(object_creation_node, gb_classes_names)
            called_methods.append(called_info)

        # 处理对象方法调用
    for match in matched_info:
        match_dict = match[1]
        if 'member_call' in match_dict:
            print("开始解析成员方法调用")
            object_method_node = match_dict['member_call'][0]
            called_info = parse_object_method_call_node(object_method_node, gb_classes_names, gb_object_class_infos)
            called_methods.append(called_info)

        # 处理静态方法方法调用
    for match in matched_info:
        match_dict = match[1]
        if 'scoped_call' in match_dict:
            print("开始解析静态方法调用")
            static_method_node = match_dict['scoped_call'][0]
            called_info = parse_static_method_call_node(static_method_node, gb_classes_names, gb_object_class_infos)
            called_methods.append(called_info)
    return called_methods

def query_global_methods_info(language, root_node, gb_classes_names, gb_methods_names, gb_object_class_infos):
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
            print(f"function_node:{function_node}")
            # function_node:(function_definition

            # 从 function_node 中直接提取子节点
            f_name_text = get_node_filed_text(function_node, "name")
            print(f"f_name_text:{f_name_text}")
            f_start_line = function_node.start_point[0]
            f_end_line = function_node.end_point[0]
            f_body_node = find_first_child_by_field(function_node, "body")
            print(f"f_body_node:{f_body_node}")
            # 获取方法的返回信息
            f_return_infos = parse_return_node(f_body_node)
            print(f"f_return_infos:{f_return_infos}")

            # 获取返回参数信息
            f_params_node = find_first_child_by_field(function_node, "parameters")
            print(f"f_params_node:{f_params_node}")
            f_params_info = parse_params_node(f_params_node)
            print(f"f_params_info:{f_params_info}")
            # 解析函数体中的调用的其他方法
            f_called_methods = query_method_node_called_methods(language, f_body_node, gb_classes_names, gb_methods_names, gb_object_class_infos)
            print(f"f_called_methods:{f_called_methods}")

            method_type =guess_method_type(f_name_text,True,False)
            print(f"method_type:{method_type}")
            # 总结函数方法信息
            method_info = create_method_result(uniq_id=None, method_name=f_name_text, start_line=f_start_line,
                                               end_line=f_end_line, object_name=None, class_name=None, fullname=f_name_text, method_file=None,
                                               visibility=None, modifiers=None, method_type=method_type, params_info=f_params_info, return_infos=f_return_infos,
                                               is_native=None, called_methods=f_called_methods)
            functions_info.append(method_info)
    return functions_info


