from typing import List, Dict

from tree_sitter._binding import Node

from guess import guess_method_type, guess_called_object_is_native
from tree_enums import ParameterKeys, PHPModifier, MethodKeys, ReturnKeys
from tree_sitter_uitls import find_first_child_by_field, find_children_by_field, get_node_text, get_node_filed_text, \
    get_node_type


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


def parse_arguments_node(arguments_node: Node):
    """分析被调用函数的参数信息 TODO优化为参数节点解析格式"""
    args = []
    arg_index = 0
    print(f"args_node:{arguments_node}")
    # args_node:(arguments (argument (string (string_content))))

    argument_nodes = find_children_by_field(arguments_node, 'argument')
    for arg_index, argument_node in enumerate(argument_nodes):
        arg_name = get_node_text(argument_node) #参数内容
        arg_type = parse_argument_node_type(argument_node)

        arg_info = {
                ParameterKeys.INDEX.value: arg_index,
                ParameterKeys.VALUE.value: arg_name,
                ParameterKeys.TYPE.value: arg_type,
                ParameterKeys.NAME.value: None,
                ParameterKeys.DEFAULT.value: None,
            }
        args.append(arg_info)
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


def get_node_modifiers(any_none:Node):
    """获取指定节点（方法|属性|类）的特殊描述符信息"""
    modifiers = []
    if find_first_child_by_field(any_none, 'abstract_modifier'):
        modifiers.append(PHPModifier.ABSTRACT.value)
    if find_first_child_by_field(any_none, 'final_modifier'):
        modifiers.append(PHPModifier.FINAL.value)
    if find_first_child_by_field(any_none, 'readonly_modifier'):
        modifiers.append(PHPModifier.READONLY.value)
    if find_first_child_by_field(any_none, 'static_modifier'):
        modifiers.append(PHPModifier.STATIC.value)
    return modifiers


def parse_params_node(params_node: Node):
    def parse_simple_parameter(param_node: Node, param_index: int = None) -> dict:
        """解析单个简单参数节点的信息。 """
        # 获取默认值
        default_value_node = find_first_child_by_field(param_node, 'default_value')
        # 初始化参数信息
        param_info = {
            ParameterKeys.NAME.value: get_node_filed_text(param_node, 'name'),
            ParameterKeys.TYPE.value: get_node_type(default_value_node),
            ParameterKeys.DEFAULT.value: get_node_text(default_value_node),
            ParameterKeys.VALUE.value: None, ParameterKeys.INDEX.value: param_index
        }
        return param_info

    # 获取参数列表节点
    parameters = []
    if params_node:
        param_index = 0
        for param_node in params_node.children:
            if param_node.type == 'simple_parameter':
                parameter_info = parse_simple_parameter(param_node, param_index)
                param_index += 1
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


def parse_object_member_call_node(object_method_node:Node, gb_classes_names:List, gb_object_class_infos:Dict):
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


def parse_static_method_call_node(object_method_node: Node, gb_classes_names: List, gb_object_class_infos: Dict):
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
