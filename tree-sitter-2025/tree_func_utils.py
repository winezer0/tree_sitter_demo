from typing import List, Dict

from tree_sitter._binding import Node

from guess import guess_called_object_is_native, guess_method_type, find_nearest_info_by_line

from tree_enums import MethodKeys, MethodType, PHPModifier
from tree_func_utils_sub_parse import parse_body_node_return_info, parse_params_node, parse_arguments_node
from tree_sitter_uitls import find_first_child_by_field, get_node_filed_text, calc_unique_key

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


def create_method_result(uniq_id, method_name, start_line, end_line, object_name, class_name, fullname, method_file,
                         visibility, modifiers, method_type, params_info, return_infos, is_native, called_methods):
    """创建方法信息的综合返回结果"""
    return {
        MethodKeys.UNIQ_ID.value: uniq_id,
        MethodKeys.NAME.value: method_name,
        MethodKeys.START_LINE.value: start_line,
        MethodKeys.END_LINE.value: end_line,

        MethodKeys.OBJECT.value: object_name,  # 普通函数没有对象
        MethodKeys.CLASS.value: class_name,  # 普通函数不属于类
        MethodKeys.FULLNAME.value: fullname,  # 普通函数的全名就是函数名
        MethodKeys.FILE.value: method_file,

        MethodKeys.VISIBILITY.value: visibility,  # 普通函数默认public
        MethodKeys.MODIFIERS.value: modifiers,  # 普通函数访问属性 为空

        MethodKeys.METHOD_TYPE.value: method_type,  # 本文件定义的 普通全局
        MethodKeys.PARAMS.value: params_info,  # 动态解析 函数的参数信息
        MethodKeys.RETURNS.value: return_infos,  # 动态解析 函数的返回值类型

        MethodKeys.IS_NATIVE.value: is_native,  # 被调用的函数是否在本文件内,仅当本函数是被调用函数时有值
        MethodKeys.CALLED.value: called_methods,  # 动态解析 函数类调用的其他方法
    }


def parse_function_call_node(function_call_node:Node, gb_methods_names: List):
    """解析函数调用节点"""
    # print(f"function_call_node:{function_call_node}")
    # (function_call_expression function: (name) arguments: (arguments (argument (string (string_content)))))
    method_name = get_node_filed_text(function_call_node, 'name')
    f_start_line = function_call_node.start_point[0]
    f_end_line = function_call_node.end_point[0]
    # 解析参数信息
    arguments_node = find_first_child_by_field(function_call_node, 'arguments')
    arguments_info = parse_arguments_node(arguments_node)

    # 定义是否是本文件函数
    is_native = method_name in gb_methods_names
    # 定义获取函数类型
    method_type = guess_method_type(method_name, is_native, False)
    print(f"method_type:{method_name} is{method_type}  native:{is_native}")

    return create_method_result(uniq_id=None, method_name=method_name, start_line=f_start_line, end_line=f_end_line,
                                object_name=None, class_name=None, fullname=method_name, method_file=None,
                                visibility=None, modifiers=None, method_type=method_type, params_info=arguments_info,
                                return_infos=None, is_native=is_native, called_methods=None)

def parse_object_creation_node(object_creation_node:Node, classes_names: List):
    """解析对象创建节点"""
    print(f"object_creation_node:{object_creation_node}")
    # object_creation_node:(object_creation_expression (name) (arguments (argument (encapsed_string (string_content)))))
    class_name = get_node_filed_text(object_creation_node, 'name')
    method_name = '__construct'
    f_start_line = object_creation_node.start_point[0]
    f_end_line = object_creation_node.end_point[0]
    print(f"class_name:{class_name} ｛method_name｝ {f_start_line} {f_end_line}")

    # 解析参数信息
    arguments_node = find_first_child_by_field(object_creation_node, 'arguments')
    arguments_info = parse_arguments_node(arguments_node)
    print(f"arguments_info:{arguments_info}")

    # 定义是否是本文件定义的class
    is_native = class_name in classes_names # 构造方法 可以直接判断
    print(f"is_native_class:{is_native}")

    # 定义获取函数类型
    method_type = guess_method_type(method_name, is_native, True)
    print(f"method_type:{method_name} is {method_type}  native:{is_native} ")

    fullname = f"{class_name}::{method_name}"
    print("fullname:", fullname)
    return create_method_result(uniq_id=None, method_name=method_name, start_line=f_start_line, end_line=f_end_line,
                                object_name=None, class_name=class_name, fullname=fullname, method_file=None,
                                visibility=None, modifiers=None, method_type=method_type, params_info=arguments_info,
                                return_infos=None, is_native=is_native, called_methods=None)


def parse_object_method_call_node(object_method_node:None, gb_classes_names:List, gb_object_class_infos:Dict):
    # print(f"object_method_node:{object_method_node}")
    # object_method_node:(member_call_expression object: (variable_name (name)) name: (name) arguments: (arguments (argument (encapsed_string (string_content)))))

    method_name = get_node_filed_text(object_method_node, 'name')
    print(f"method_name:{method_name}") # method_name:classMethod
    f_start_line = object_method_node.start_point[0]
    f_end_line = object_method_node.end_point[0]

    # 解析参数信息
    arguments_node = find_first_child_by_field(object_method_node, 'arguments')
    arguments_info = parse_arguments_node(arguments_node)
    print(f"arguments_info:{arguments_info}")

    # 获取对象名称
    object_name =  get_node_filed_text(object_method_node, 'variable_name')
    print(f"object_name:{object_name}")    # object_name:$myClass

    # 定义是否是本文件函数
    is_native,class_name = guess_called_object_is_native(object_name, f_start_line, gb_classes_names, gb_object_class_infos)

    # 定义获取函数类型
    method_type = guess_method_type(method_name, is_native, True)
    print(f"method_type:{method_name} is {method_type}  native:{is_native}")

    # full_name
    method_fullname = f"{object_name}:{method_name}"

    return create_method_result(uniq_id=None, method_name=method_name, start_line=f_start_line, end_line=f_end_line,
                                object_name=object_name, class_name=class_name, fullname=method_fullname,
                                method_file=None, visibility=None, modifiers=None, method_type=method_type,
                                params_info=arguments_info, return_infos=None, is_native=is_native, called_methods=None)


def parse_static_method_call_node(object_method_node: None, gb_classes_names: List, gb_object_class_infos: Dict):
    print(f"parse_static_method_call_node:{object_method_node}")
    # parse_static_method_call_node:(scoped_call_expression scope: (name) name: (name) arguments: (arguments (argument (encapsed_string (string_content)))))


    method_name = get_node_filed_text(object_method_node, 'name')
    print(f"method_name:{method_name}")  # method_name:classMethod
    f_start_line = object_method_node.start_point[0]
    f_end_line = object_method_node.end_point[0]

    # 解析参数信息
    arguments_node = find_first_child_by_field(object_method_node, 'arguments')
    arguments_info = parse_arguments_node(arguments_node)
    print(f"arguments_info:{arguments_info}")

    # 获取类名称
    class_name = get_node_filed_text(object_method_node, 'scope')
    print(f"class_name:{class_name}")  # object_name:MyClass

    # 判断静态方法是否是 对象调用 较少见
    object_name = class_name if str(class_name).startswith("$") else None
    # 定义是否是本文件函数
    if not object_name:
        is_native = class_name in gb_classes_names
    else:
        print(f"object_name:{object_name}")
        is_native, class_name = guess_called_object_is_native(object_name, f_start_line, gb_classes_names, gb_object_class_infos)

    # 定义获取函数类型
    method_type = guess_method_type(method_name, is_native, True)
    print(f"method_type:{method_name} is {method_type}  native:{is_native}")

    # full_name
    method_fullname = f"{class_name}:{method_name}"

    # 补充静态方法的特殊描述符号
    modifiers = [PHPModifier.STATIC.value]
    return create_method_result(uniq_id=None, method_name=method_name, start_line=f_start_line, end_line=f_end_line,
                                object_name=object_name, class_name=class_name, fullname=method_fullname,
                                method_file=None, visibility=None, modifiers=modifiers, method_type=method_type,
                                params_info=arguments_info, return_infos=None, is_native=is_native, called_methods=None)



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

def query_global_methods_info(language, root_node, classes_ranges, gb_classes_names, gb_methods_names, gb_object_class_infos):
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
            f_name_text = get_node_filed_text(function_node, "name")
            print(f"f_name_text:{f_name_text}")
            f_start_line = function_node.start_point[0]
            f_end_line = function_node.end_point[0]
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