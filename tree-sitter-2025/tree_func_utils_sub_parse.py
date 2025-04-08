from tree_sitter._binding import Node

from tree_enums import ParameterKeys, PHPModifier, ReturnKeys
from tree_sitter_uitls import find_first_child_by_field, find_children_by_field, get_node_text, get_node_filed_text, \
    get_node_type


def parse_argument_node_type(argument_node):
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

def parse_arguments_node(args_node):
    """分析被调用函数的参数信息 TODO优化为参数节点解析格式"""
    args = []
    arg_index = 0
    print(f"args_node:{args_node}")
    # args_node:(arguments (argument (string (string_content))))

    argument_nodes = find_children_by_field(args_node, 'argument')
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


def parse_body_node_return_info(body_node: Node):
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
