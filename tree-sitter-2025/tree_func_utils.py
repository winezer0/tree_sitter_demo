from typing import Dict, List

from tree_sitter._binding import Node

from tree_define_class import query_gb_classes_define_infos
from tree_const import PHP_MAGIC_METHODS, PHP_BUILTIN_FUNCTIONS
from tree_enums import MethodKeys, GlobalCode, ParameterKeys, ReturnKeys, PHPModifier, MethodType, \
    OtherName, DefineKeys
from tree_define_method import query_gb_methods_define_infos

from tree_sitter_uitls import find_first_child_by_field, get_node_filed_text, get_node_text, get_node_type, \
    find_node_info_by_line_nearest, load_str_to_parse, find_children_by_field, trans_node_infos_names_ranges, \
    find_node_info_by_line_in_scope


def query_global_methods_info(language, root_node, gb_classes_names, gb_methods_names, gb_object_class_infos,
                              gb_namespace_infos):
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
            # print(f"function_node:{function_node}")
            # function_node:(function_definition

            # 从 function_node 中直接提取子节点
            method_name = get_node_filed_text(function_node, "name")
            # print(f"f_name_text:{f_name_text}")
            start_line = function_node.start_point[0]
            end_line = function_node.end_point[0]
            f_body_node = find_first_child_by_field(function_node, "body")
            # print(f"f_body_node:{f_body_node}")
            # 获取方法的返回信息
            return_infos = parse_return_node(f_body_node)
            # print(f"f_return_infos:{f_return_infos}")

            # 获取返回参数信息
            f_params_node = find_first_child_by_field(function_node, "parameters")
            # print(f"f_params_node:{f_params_node}")
            params_info = parse_params_node(f_params_node)
            # print(f"f_params_info:{f_params_info}")

            # 查询方法对应的命名空间信息
            namespace_info = find_node_info_by_line_in_scope(start_line, gb_namespace_infos, DefineKeys.START.value, DefineKeys.END.value)
            namespace = namespace_info.get(DefineKeys.NAME.value, None)

            # 解析函数体中的调用的其他方法
            called_methods = query_method_called_methods(language, f_body_node, gb_classes_names, gb_methods_names, gb_object_class_infos)
            # print(f"f_called_methods:{f_called_methods}")

            method_type =guess_method_type(method_name,True,False)
            # print(f"method_type:{method_type}")

            # 总结函数方法信息
            method_info = create_method_result(method_name=method_name, start_line=start_line, end_line=end_line,
                                               namespace=namespace, object_name=None, class_name=None,
                                               fullname=method_name, visibility=None, modifiers=None,
                                               method_type=method_type, params_info=params_info,
                                               return_infos=return_infos, is_native=None,
                                               called_methods=called_methods)
            functions_info.append(method_info)
    return functions_info


def query_method_called_methods(language, body_node, gb_classes_names=[], gb_methods_names=[], gb_object_class_infos={}):
    """查询方法体代码内调用的其他方法信息"""
    # print(f"body_node:{body_node}")

    method_called_sql = """
        ;查询常规函数调用
        (function_call_expression) @function_call

        ;查询对象方法创建
        (object_creation_expression) @object_creation

        ;查询对象方法调用
        (member_call_expression) @member_call

        ;查询静态方法调用
        (scoped_call_expression) @scoped_call
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
    for match in matched_info:
        match_dict = match[1]
        if 'function_call' in match_dict:
            # print("开始全局函数方法调用")
            function_call_node = match_dict['function_call'][0]
            called_info = parse_function_call_node(function_call_node, gb_methods_names)
            called_methods.append(called_info)

    # ;查询对象方法创建 object_creation_expression @ object_creation
    for match in matched_info:
        match_dict = match[1]
        if 'object_creation' in match_dict:
            # print("开始对象创建方法调用")
            object_creation_node = match_dict['object_creation'][0]
            called_info = parse_object_creation_node(object_creation_node, gb_classes_names)
            called_methods.append(called_info)

    # ;查询对象方法调用 member_call_expression @ member_call
    for match in matched_info:
        match_dict = match[1]
        if 'member_call' in match_dict:
            # print("开始解析成员方法调用")
            object_method_node = match_dict['member_call'][0]
            called_info = parse_object_member_call_node(object_method_node, gb_classes_names, gb_object_class_infos)
            called_methods.append(called_info)

    # ;查询静态方法调用 scoped_call_expression @ scoped_call
    for match in matched_info:
        match_dict = match[1]
        if 'scoped_call' in match_dict:
            # print("开始解析静态方法调用")
            static_method_node = match_dict['scoped_call'][0]
            called_info = parse_static_method_call_node(static_method_node, gb_classes_names, gb_object_class_infos)
            called_methods.append(called_info)
    return called_methods


def is_static_method(modifiers):
    if modifiers and 'static' in modifiers:
        return True
    return False


def get_class_method_fullname(class_name, method_name, is_static):
    concat = "::" if is_static or method_name in PHP_MAGIC_METHODS else "->"
    if class_name:
        fullname = f"{class_name}{concat}{method_name}"
    else:
        fullname = f"{method_name}"
    return fullname


def line_in_methods_or_classes_ranges(line_num, function_ranges, class_ranges):
    """检查行号是否在函数或类范围内"""
    return any(start <= line_num <= end for start, end in function_ranges) or any(start <= line_num <= end for start, end in class_ranges)


def has_global_code(root_node, gb_methods_ranges, gb_classes_ranges):
    """检查是否有(非class和非函数)全局代码的内容"""
    for line_num in range(root_node.start_point[0], root_node.end_point[0] + 1):
        if not line_in_methods_or_classes_ranges(line_num, gb_methods_ranges, gb_classes_ranges):
            return True
    return False


def get_global_code_info(language, root_node, gb_methods_ranges, gb_classes_ranges) -> Dict:
    """获取所有不在全局函数和类定义内的PHP代码信息"""
    # 获取所有全局函数定义信息 (名称和范围)
    if gb_methods_ranges is None:
        _, gb_methods_ranges = trans_node_infos_names_ranges(query_gb_methods_define_infos(language, root_node))
    # 获取所有类定义的代码行范围 (名称和范围)，用于排除类方法
    if gb_classes_ranges is None:
        _, gb_classes_ranges = trans_node_infos_names_ranges(query_gb_classes_define_infos(language, root_node))

    # 获取源代码的每一行
    source_lines = get_node_text(root_node).split('\n')
    # 存储非函数且非类范围内的代码块
    non_function_non_class_code = []
    # 遍历每一行代码
    for line_num, line_text in enumerate(source_lines):
        # 如果当前行既不在全局函数范围内也不在类范围内，则添加到结果中
        if not line_in_methods_or_classes_ranges(line_num, gb_methods_ranges, gb_classes_ranges):
            code_info = {
                GlobalCode.LINE.value: line_num,
                GlobalCode.CODE.value: line_text.strip()  # 去除多余空格
            }
            non_function_non_class_code.append(code_info)

    if not non_function_non_class_code:
        return None

    # 返回结果字典
    gb_code_start_line = non_function_non_class_code[0][GlobalCode.LINE.value] if non_function_non_class_code else None
    gb_code_end_line = non_function_non_class_code[-1][GlobalCode.LINE.value] if non_function_non_class_code else None
    global_code_info = {
        GlobalCode.START.value: gb_code_start_line,
        GlobalCode.END.value: gb_code_end_line,
        GlobalCode.TOTAL.value: len(non_function_non_class_code),
        GlobalCode.BLOCKS.value: non_function_non_class_code,
    }
    return global_code_info


def get_global_code_string(global_code_info):
    if not global_code_info:
        return None

    # 提取 START 和 END 行号
    nf_start_line = global_code_info[GlobalCode.START.value]
    nf_end_line = global_code_info[GlobalCode.END.value]

    # 提取 BLOCKS 并按 LINE 排序
    code_blocks = global_code_info[GlobalCode.BLOCKS.value]
    sorted_blocks = sorted(code_blocks, key=lambda x: x[GlobalCode.LINE.value])

    # 构建完整的行号空代码
    codes = ["" for _ in range(nf_start_line, nf_end_line + 1)]
    # 填充代码数据
    for block in sorted_blocks:
        line_num = block[GlobalCode.LINE.value]
        codes[line_num] = block[GlobalCode.CODE.value]

    # 将所有代码拼接成字符串
    return "\n".join(codes)


def create_method_result(method_name, start_line, end_line, namespace, object_name, class_name, fullname, visibility,
                         modifiers, method_type, params_info, return_infos, is_native, called_methods, uniq_id=None,
                         method_file=None):
    """创建方法信息的综合返回结果"""
    return {
        MethodKeys.UNIQ_ID.value: uniq_id, # 后续等信息填充完毕再主动生成uniq_id
        MethodKeys.FILE.value: method_file, # 后续再进行文件信息补充 此处主要是占位

        MethodKeys.NAME.value: method_name,
        MethodKeys.START.value: start_line,
        MethodKeys.END.value: end_line,

        MethodKeys.NAMESPACE.value: namespace,
        MethodKeys.OBJECT.value: object_name,  # 普通函数没有对象
        MethodKeys.CLASS.value: class_name,  # 普通函数不属于类
        MethodKeys.FULLNAME.value: fullname,  # 普通函数的全名就是函数名

        MethodKeys.VISIBILITY.value: visibility,  # 普通函数默认public
        MethodKeys.MODIFIERS.value: modifiers,  # 普通函数访问属性 为空

        MethodKeys.METHOD_TYPE.value: method_type,  # 本文件定义的 普通全局
        MethodKeys.PARAMS.value: params_info,  # 动态解析 函数的参数信息
        MethodKeys.RETURNS.value: return_infos,  # 动态解析 函数的返回值类型

        MethodKeys.IS_NATIVE.value: is_native,  # 被调用的函数是否在本文件内,仅当本函数是被调用函数时有值
        MethodKeys.CALLED_METHODS.value: called_methods,  # 动态解析 函数类调用的其他方法
    }


def parse_arguments_node(arguments_node: Node):
    """分析被调用函数的参数信息"""
    def parse_argument_node_type(argument_node: Node):
        """获取argument节点的类型 """
        # 查找类型信息 argument_node:(argument (encapsed_string (string_content)))
        # 定义类型映射表
        type_mapping = {
            "string": "string",
            "encapsed_string": "string",
            "integer": "integer",
            "variable_name": "variable_name"
        }
        # 遍历类型映射表，查找第一个匹配的类型
        for field, type_name in type_mapping.items():
            if find_first_child_by_field(argument_node, field):
                return type_name
        # 如果未找到任何匹配类型，返回 UNKNOWN
        return "UNKNOWN"


    args = []
    # print(f"args_node:{arguments_node}")
    # args_node:(arguments (argument (string (string_content))))

    argument_nodes = find_children_by_field(arguments_node, 'argument')
    for arg_index, argument_node in enumerate(argument_nodes):
        argument_name = get_node_text(argument_node) #参数内容
        argument_type = parse_argument_node_type(argument_node)

        argument_info = {
                ParameterKeys.INDEX.value: arg_index,
                ParameterKeys.VALUE.value: argument_name,
                ParameterKeys.TYPE.value: argument_type,
                ParameterKeys.NAME.value: None,
                ParameterKeys.DEFAULT.value: None,
            }
        args.append(argument_info)
    return args


def parse_return_node(body_node: Node):
    """查找方法的返回信息"""

    def parse_return_node(return_node: Node):
        return_info_list = []
        variable_nodes = find_children_by_field(return_node, "variable_name")
        for variable_node in variable_nodes:
            node_text = get_node_text(variable_node)
            return_info = {
                ReturnKeys.NAME.value: None,
                ReturnKeys.VALUE.value: None,
                ReturnKeys.TYPE.value: node_text,
                ReturnKeys.START.value: variable_node.start_point[0],
                ReturnKeys.END.value: variable_node.end_point[0],
            }
            return_info_list.append(return_info)
        return return_info_list

    return_nodes = find_children_by_field(body_node, "return_statement")
    return_infos = [x for return_node in return_nodes for x in parse_return_node(return_node)]
    return return_infos


def parse_params_node(params_node: Node):
    # 获取参数列表节点
    parameters = []
    if params_node:
        for param_index, param_node in enumerate(params_node.children):
            if param_node.type == 'simple_parameter':
                # 获取默认值
                default_value_node = find_first_child_by_field(param_node, 'default_value')
                parameter_info = {
                    ParameterKeys.INDEX.value: param_index,
                    ParameterKeys.NAME.value: get_node_filed_text(param_node, 'name'),
                    ParameterKeys.TYPE.value: get_node_type(default_value_node),
                    ParameterKeys.DEFAULT.value: get_node_text(default_value_node),
                    ParameterKeys.VALUE.value: None,
                }
                parameters.append(parameter_info)
    return parameters


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
    # print(f"method_type:{method_name} is{method_type}  native:{is_native}")

    return create_method_result(method_name=method_name, start_line=f_start_line, end_line=f_end_line,
                                namespace=None, object_name=None, class_name=None, fullname=method_name,
                                visibility=None, modifiers=None, method_type=method_type, params_info=arguments_info,
                                return_infos=None, is_native=is_native, called_methods=None)


def parse_object_creation_node(object_creation_node:Node, classes_names: List):
    """解析对象创建节点"""
    # print(f"object_creation_node:{object_creation_node}")
    # object_creation_node:(object_creation_expression (name) (arguments (argument (encapsed_string (string_content)))))
    class_name = get_node_filed_text(object_creation_node, 'name')
    method_name = '__construct'
    f_start_line = object_creation_node.start_point[0]
    f_end_line = object_creation_node.end_point[0]
    # print(f"class_name:{class_name} ｛method_name｝ {f_start_line} {f_end_line}")

    # 解析参数信息
    arguments_node = find_first_child_by_field(object_creation_node, 'arguments')
    arguments_info = parse_arguments_node(arguments_node)
    # print(f"arguments_info:{arguments_info}")

    # 定义是否是本文件定义的class
    is_native = class_name in classes_names # 构造方法 可以直接判断
    # print(f"is_native_class:{is_native}")

    # 定义获取函数类型
    method_type = guess_method_type(method_name, is_native, True)
    # print(f"method_type:{method_name} is {method_type}  native:{is_native} ")

    fullname = f"{class_name}::{method_name}"
    # print("fullname:", fullname)
    return create_method_result(method_name=method_name, start_line=f_start_line, end_line=f_end_line,
                                namespace=None, object_name=None, class_name=class_name, fullname=fullname,
                                visibility=None, modifiers=None, method_type=method_type, params_info=arguments_info,
                                return_infos=None, is_native=is_native, called_methods=None)


def parse_object_member_call_node(object_method_node:Node, gb_classes_names:List, gb_object_class_infos:Dict):
    # print(f"object_method_node:{object_method_node}")
    # object_method_node:(member_call_expression object: (variable_name (name)) name: (name) arguments: (arguments (argument (encapsed_string (string_content)))))

    method_name = get_node_filed_text(object_method_node, 'name')
    # print(f"method_name:{method_name}") # method_name:classMethod
    f_start_line = object_method_node.start_point[0]
    f_end_line = object_method_node.end_point[0]

    # 解析参数信息
    arguments_node = find_first_child_by_field(object_method_node, 'arguments')
    arguments_info = parse_arguments_node(arguments_node)
    # print(f"arguments_info:{arguments_info}")

    # 获取对象名称
    object_name =  get_node_filed_text(object_method_node, 'variable_name')
    # print(f"object_name:{object_name}")    # object_name:$myClass

    # 定义是否是本文件函数
    is_native, class_name = guess_called_object_is_native(object_name, f_start_line, gb_classes_names, gb_object_class_infos)

    # 定义获取函数类型
    method_type = guess_method_type(method_name, is_native, True)
    # print(f"method_type:{method_name} is {method_type}  native:{is_native}")

    # full_name 首先判断是不是显式的魔术方法调用 静态方法和构造方法在其他函数已经实现
    concat = "::" if method_type == MethodType.MAGIC_METHOD.value else "->"
    method_fullname = f"{class_name}{concat}{method_name}" if class_name else f"{object_name}{concat}{method_name}"

    return create_method_result(method_name=method_name, start_line=f_start_line, end_line=f_end_line,
                                namespace=None, object_name=object_name, class_name=class_name,
                                fullname=method_fullname, visibility=None, modifiers=None, method_type=method_type,
                                params_info=arguments_info, return_infos=None, is_native=is_native, called_methods=None)


def parse_static_method_call_node(object_method_node: Node, gb_classes_names: List, gb_object_class_infos: Dict):
    # print(f"parse_static_method_call_node:{object_method_node}")
    # parse_static_method_call_node:(scoped_call_expression scope: (name) name: (name) arguments: (arguments (argument (encapsed_string (string_content)))))

    method_name = get_node_filed_text(object_method_node, 'name')
    # print(f"method_name:{method_name}")  # method_name:classMethod
    f_start_line = object_method_node.start_point[0]
    f_end_line = object_method_node.end_point[0]

    # 解析参数信息
    arguments_node = find_first_child_by_field(object_method_node, 'arguments')
    arguments_info = parse_arguments_node(arguments_node)
    # print(f"arguments_info:{arguments_info}")

    # 获取静态方法的类名称
    class_name = get_node_filed_text(object_method_node, 'scope')
    # print(f"class_name:{class_name}")  # object_name:MyClass

    # 判断静态方法是否是 对象调用 较少见
    if str(class_name).startswith("$"):
        object_name = class_name
        is_native, class_name = guess_called_object_is_native(object_name, f_start_line, gb_classes_names, gb_object_class_infos)
    else:
        object_name = class_name
        is_native = class_name in gb_classes_names

    # 定义获取函数类型
    method_type = guess_method_type(method_name, is_native, True)
    # print(f"method_type:{method_name} is {method_type}  native:{is_native}")

    # full_name 原则而言查找的就是静态方法 TODO 如果是本文件函数的话 后续最好需要搜索对应类信息
    method_fullname = f"{class_name}::{method_name}"

    # 补充静态方法的特殊描述符号
    modifiers = [PHPModifier.STATIC.value]
    return create_method_result(method_name=method_name, start_line=f_start_line, end_line=f_end_line,
                                namespace=None, object_name=object_name, class_name=class_name,
                                fullname=method_fullname, visibility=None, modifiers=modifiers, method_type=method_type,
                                params_info=arguments_info, return_infos=None, is_native=is_native, called_methods=None)


def parse_global_code_called_methods(parser, language, root_node, gb_classes_names, gb_classes_ranges,
                                     gb_methods_names, gb_methods_ranges, gb_object_class_infos):
    """查询全部代码调用的函数信息 并且只保留其中不属于函数和类的部分"""
    if not has_global_code(root_node, gb_methods_ranges, gb_classes_ranges):
        # print("文件中不存在全局性代码...")
        return None

    # print("开始进行全局性代码额外处理...")
    # 方案1 获取所有代码信息 然后排除其中的 函数定义范围和类定义范围信息 再进行 代码解析
    global_code_info = get_global_code_info(language, root_node, gb_methods_ranges, gb_classes_ranges)
    # print(f"global_code_info:{global_code_info}")

    nf_name_txt = OtherName.NOT_IN_METHOD.value
    nf_start_line = global_code_info[GlobalCode.START.value]
    nf_end_line = global_code_info[GlobalCode.END.value]

    # 解析全局代码数据
    nf_global_code = get_global_code_string(global_code_info)
    if not nf_global_code:
        return None

    nf_code_tree = load_str_to_parse(parser, nf_global_code)
    nf_code_node = nf_code_tree.root_node
    # 查询调用的方法信息
    nf_code_called_methods = query_method_called_methods(language, nf_code_node, gb_classes_names, gb_methods_names, gb_object_class_infos)

    # 如果没有找到信息就直接返回None
    if not nf_code_called_methods:
        return None

    return create_method_result(method_name=nf_name_txt, start_line=nf_start_line, end_line=nf_end_line,
                                namespace=None, object_name=None, class_name=None, fullname=nf_name_txt,
                                visibility=None, modifiers=None, method_type=None, params_info=None, return_infos=None,
                                is_native=None, called_methods=nf_code_called_methods)

def guess_called_object_is_native(object_name, object_line, gb_classes_names, gb_object_class_infos):
    """从本文件中初始化类信息字典分析对象属于哪个类"""
    # [{'METHOD_OBJECT': '$myClass', 'METHOD_CLASS': 'MyClass', 'METHOD_START_LINE': 5},,,]
    if object_name in gb_classes_names:
        return True, object_name

    # 通过对象名称 初次筛选获取命中的类信息
    filtered_object_infos = [info for info in gb_object_class_infos if info.get(MethodKeys.OBJECT.value, None) == object_name]
    if not filtered_object_infos:
        return False, None

    # 进一步筛选最近的类创建信息
    nearest_class_info = find_node_info_by_line_nearest(object_line, filtered_object_infos, start_key=MethodKeys.START.value)
    # print(f"nearest_class_info:{nearest_class_info}")
    nearest_class_name = nearest_class_info[MethodKeys.CLASS.value]
    if nearest_class_name in gb_classes_names:
        return True, nearest_class_name
    else:
        return False, nearest_class_name


def guess_method_type(method_name, is_native_method_or_class, is_class_method):
    """根据被调用的函数完整信息猜测函数名"""
    if is_class_method:
        method_type = MethodType.CLASS_METHOD.value
        # 判断方法是否是php类的内置构造方法
        if method_name == '__construct':
            method_type = MethodType.CONSTRUCT.value
        # 判断方法是否是php类的内置魔术方法
        elif method_name in PHP_MAGIC_METHODS and is_native_method_or_class is False:
            method_type = MethodType.MAGIC_METHOD.value
    else:
        method_type = MethodType.GENERAL.value
        # 判断方法是否是php内置方法
        if method_name in PHP_BUILTIN_FUNCTIONS and is_native_method_or_class is False:
            method_type = MethodType.BUILTIN.value
        # 判断方法是否时动态调用方法
        elif method_name.startswith("$"):
            method_type = MethodType.DYNAMIC.value
    return method_type
