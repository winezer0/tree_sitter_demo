from typing import Tuple

from tree_sitter._binding import Node

from guess import guess_called_object_is_native

from tree_enums import PHPModifier, MethodKeys, MethodType
from tree_func_utils_sub_parse import parse_params_node_params_info, query_method_return_value
from tree_sitter_uitls import find_first_child_by_field, extract_node_text_infos, get_node_filed_text, get_node_text

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


def query_global_methods_define_infos(language, root_node) -> Tuple[set, set[Tuple[int, int]]]:
    """ 获取所有本地普通函数（全局函数）的名称及其范围。"""
    # 定义查询语句
    function_query = language.query("""
        (function_definition
            name: (name) @function.name
        ) @function.def
    """)

    function_define_infos = extract_node_text_infos(root_node, function_query, 'function.def', need_node_field='name')
    return function_define_infos


def query_classes_define_infos(language, root_node) -> Tuple[set[str], set[Tuple[int, int]]]:
    """获取所有类定义的类名及其代码行范围。 """
    # 定义查询语句，匹配类型定义
    class_def_query = language.query("""
        ;匹配普通|抽象|final类定义信息
        (class_declaration
            name: (name) @class.name
        ) @class.def

        ;匹配接口类定义信息
        (interface_declaration
            name: (name) @class.name
        ) @class.def
    """)

    class_define_infos = extract_node_text_infos(root_node, class_def_query, 'class.def', need_node_field='name')
    return class_define_infos


def query_node_created_class_object_infos(language: object, tree_node: Node) -> list[dict]:
    """获取节点中中所有创建的类对象和名称关系"""
    # 定义查询语句
    new_object_query = language.query("""
        ; 查询对象方法创建 同时获取返回值
        (assignment_expression
            left: (variable_name) @left_variable
            right: (
                (object_creation_expression
                   (name) @new_class_name
                   (arguments) @constructor_args
                ) @new_expr
            )
        ) @assignment_expr
    """)

    # 存储结果的列表
    object_class_dicts = []
    # 遍历匹配结果
    for match in new_object_query.matches(tree_node):
        match_dict = match[1]

        # 提取 assignment_expr 节点
        if 'assignment_expr' in match_dict:
            assignment_expr_node = match_dict['assignment_expr'][0]
            start_line = assignment_expr_node.start_point[0]
            end_line = assignment_expr_node.end_point[0]

            # 初始化变量
            # 使用 child_by_field_name 提取左侧变量名
            left_node = find_first_child_by_field(assignment_expr_node, 'left')
            object_name = get_node_text(left_node)

            # 使用 child_by_field_name 提取右侧表达式
            right_expr_node = find_first_child_by_field(assignment_expr_node, 'right')
            if right_expr_node and right_expr_node.type == 'object_creation_expression':
                class_name = get_node_filed_text(right_expr_node, 'name')
                if class_name and object_name:
                    object_info = {
                        MethodKeys.OBJECT.value: object_name,
                        MethodKeys.CLASS.value: class_name,
                        MethodKeys.START_LINE.value: start_line,
                        MethodKeys.END_LINE.value: end_line,
                    }
                    object_class_dicts.append(object_info)
    return object_class_dicts


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


# ========================================

def get_node_modifiers(node:Node):
    """获取指定节点（方法|属性|类）的特殊描述符信息"""
    modifiers = []
    if find_first_child_by_field(node, 'abstract_modifier'):
        modifiers.append(PHPModifier.ABSTRACT.value)
    if find_first_child_by_field(node, 'final_modifier'):
        modifiers.append(PHPModifier.FINAL.value)
    if find_first_child_by_field(node, 'readonly_modifier'):
        modifiers.append(PHPModifier.READONLY.value)
    if find_first_child_by_field(node, 'static_modifier'):
        modifiers.append(PHPModifier.STATIC.value)
    return modifiers

def query_method_node_called_methods(language, body_node, classes_names=[], gb_methods_names=[], object_class_infos={}):
    """查询方法体代码内调用的其他方法信息"""
    if not body_node:
        return []

    # print(f"body_node:{body_node}")
    # body_node:(compound_statement (expression_statement (function_call_expression function: (name) arguments: (arguments (argument (assignment_expression left: (variable_name (name)) right: (string (string_content))))))))

    called_method_query = language.query(TREE_SITTER_PHP_METHOD_CALLED_STAT)

    queried_info = called_method_query.matches(body_node)
    called_methods = []
    # 处理普通函数调用
    # 按行处理重复函数名称的版本  实际没有必要 PHP不支持定义同名函数
    seen_calls = set()
    for match in queried_info:
        match_dict = match[1]
        if 'function_call' in match_dict:
            func_node = match_dict['function_call'][0]
            func_name = func_node.text.decode('utf-8')
            func_line = func_node.start_point[0]
            called_func_key = f"{func_name}:{func_line}"
            if called_func_key not in seen_calls:
                seen_calls.add(called_func_key)
                args_node = match_dict.get('function_args', [None])[0]
                method_is_native = func_name in gb_methods_names  # 分析函数是否属于本文件函数
                called_general_method = res_called_general_method(func_node, func_name, args_node, method_is_native)
                if called_general_method[MethodKeys.METHOD_TYPE.value] != MethodType.BUILTIN.value:
                    called_methods.append(called_general_method)

    # # 添加对象创建查询
    # 处理对象创建
    for match in queried_info:
        match_dict = match[1]
        if 'new_class_name' in match_dict:
            class_node = match_dict['new_class_name'][0]
            args_node = match_dict.get('constructor_args', [None])[0]
            class_name = class_node.text.decode('utf-8')
            class_is_native = class_name in classes_names # 构造方法 可以直接判断
            called_construct_method = res_called_construct_method(class_node, args_node, class_is_native)
            called_methods.append(called_construct_method)

    # 处理对象方法调用
    for match in queried_info:
        match_dict = match[1]
        if 'member.call' in match_dict or 'static.call' in match_dict:
            # 根据静态方法和普通对象方法的语法查询结果关键字进行判断是否是静态方法
            is_static_call = 'static.call' in match_dict
            method_node = match_dict['static.call'][0] if is_static_call else match_dict['member.call'][0]
            object_node = match_dict['method.object'][0]
            method_name = match_dict['method.name'][0].text.decode('utf-8')
            args_node = match_dict.get('method.args', [None])[0]

            object_name = object_node.text.decode('utf-8')
            object_line = object_node.start_point[0]
            class_is_native, class_name = guess_called_object_is_native(object_name, object_line, classes_names, object_class_infos)
            called_object_method = res_called_object_method(
                object_node, method_node, args_node, method_name, class_is_native, is_static_call, class_name)
            called_methods.append(called_object_method)

    return called_methods


def query_global_methods_info_old(language, root_node, classes_ranges, classes_names, gb_methods_names,
                                  object_class_infos):
    """查询节点中的所有全局函数定义信息 需要优化"""
    # 查询所有函数定义
    function_query = language.query("""
        ; 全局函数定义
        (function_definition
            name: (name) @function.name
            parameters: (formal_parameters) @function.params
            body: (compound_statement) @function.body
        ) @function.def
    """)

    functions_info = []
    # 解析所有函数信息
    query_matches = function_query.matches(root_node)
    for pattern_index, match_dict in query_matches:
        if 'function.def' in match_dict:
            function_node = match_dict['function.def'][0]
            # 检查函数是否在类范围内
            if any(start <= function_node.start_point[0] <= end for start, end in classes_ranges):
                continue

            # 处理函数定义
            f_name_node = match_dict['function.name'][0]
            f_params_node = match_dict.get('function.params', [None])[0]
            f_body_node = match_dict.get('function.body', [None])[0]

            # 获取方法的返回值 TODO 函数返回值好像没有获取成功
            f_return_value = query_method_return_value(language, f_body_node)
            # 获取方法的返回类型  TODO METHOD_RETURN_TYPE 好像没有分析成功
            f_return_type_node = match_dict.get('function.return_type', [None])[0]
            f_return_type = f_return_type_node.text.decode('utf-8') if f_return_type_node else None
            # 获取返回参数信息
            f_params_info = parse_params_node_params_info(f_params_node) if f_params_node else []

            f_name_txt = f_name_node.text.decode('utf-8')
            f_start_line = function_node.start_point[0]
            f_end_line = function_node.end_point[0]
            # 解析函数体中的调用的其他方法
            f_called_methods = query_method_node_called_methods(language, f_body_node, classes_names, gb_methods_names, object_class_infos)
            # 总结函数方法结果
            method_info = create_method_result_dict(f_name_txt, f_start_line, f_end_line, f_params_info, f_return_type, f_return_value, f_called_methods, None)
            functions_info.append(method_info)
    return functions_info


