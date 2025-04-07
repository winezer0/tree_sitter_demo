from tree_sitter._binding import Node

from tree_enums import ParameterKeys, PHPModifier
from tree_sitter_uitls import find_first_child_by_field


def parse_called_method_params(args_node):
    """分析被调用函数的参数信息 TODO优化为参数节点解析格式"""
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
                ParameterKeys.INDEX.value: param_index,
                ParameterKeys.NAME.value: param_name,
                ParameterKeys.TYPE.value: None,
                ParameterKeys.DEFAULT.value: None,
                ParameterKeys.VALUE.value: value
            }
            parameters.append(param_info)
            param_index += 1

    return parameters


def parse_params_node_params_info(params_node):
    """解析函数节点的函数参数信息"""
    parameters = []
    param_index = 0

    for child in params_node.children:
        if child.type == 'simple_parameter':
            param_info = {
                ParameterKeys.INDEX.value: param_index,
                ParameterKeys.NAME.value: None,
                ParameterKeys.TYPE.value: None,
                ParameterKeys.DEFAULT.value: None,
                ParameterKeys.VALUE.value: None
            }

            # 遍历参数节点的所有子节点
            for sub_child in child.children:
                child_text = sub_child.text.decode('utf-8')
                if sub_child.type == 'variable_name':
                    param_info[ParameterKeys.NAME.value] = child_text
                elif sub_child.type in ['primitive_type', 'name', 'nullable_type']:
                    param_info[ParameterKeys.TYPE.value] = child_text
                elif sub_child.type == '=':
                    # 处理默认值
                    value_node = child.children[-1]  # 默认值通常是最后一个子节点
                    if value_node.type == 'string':
                        default_value = value_node.text.decode('utf-8')[1:-1]  # 去掉引号
                    else:
                        default_value = value_node.text.decode('utf-8')
                    param_info[ParameterKeys.DEFAULT.value] = default_value
                    param_info[ParameterKeys.VALUE.value] = None

            # 如果参数类型未设置，尝试从变量名推断类型 # TODO 需要考虑优化实现参数节点解析
            if param_info[ParameterKeys.TYPE.value] is None:
                if param_info[ParameterKeys.NAME.value].startswith('$'):
                    param_info[ParameterKeys.TYPE.value] = 'mixed'  # PHP默认类型

            parameters.append(param_info)
            param_index += 1

    return parameters


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
    for match in return_value_query.matches(body_node):
        match_dict = match[1]
        if 'return.value' in match_dict:
            return_node = match_dict['return.value'][0]
            f_return_value = return_node.text.decode('utf-8')
    return f_return_value


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
