from tree_sitter._binding import Node

from guess import guess_method_type
from tree_class_uitls import get_method_fullname, is_static_method

from tree_enums import PropertyKeys
from tree_func_utils import query_method_node_called_methods
from tree_func_utils_sub_parse import get_node_modifiers, parse_params_node, parse_return_node, create_method_result
from tree_sitter_uitls import find_first_child_by_field, get_node_filed_text, find_children_by_field


def parse_class_properties_node(class_node):
    """获取类节内部的属性定义信息"""
    def parse_class_property_node(property_node: Node) -> dict:
        """解析单个属性声明节点的信息。 """
        # property_node:(property_declaration (visibility_modifier) (static_modifier)
        # (property_element name: (variable_name (name)) default_value: (encapsed_string (string_content))))
        # 初始化属性信息
        # 获取属性元素节点
        property_element_node = find_first_child_by_field(property_node, 'property_element')
        property_info = {
            PropertyKeys.NAME.value: get_node_filed_text(property_element_node, 'name'),
            PropertyKeys.DEFAULT.value: get_node_filed_text(property_element_node, 'default_value'),

            PropertyKeys.START_LINE.value: property_node.start_point[0],
            PropertyKeys.END_LINE.value: property_node.end_point[0],

            PropertyKeys.VISIBILITY.value: get_node_filed_text(property_node, 'visibility_modifier'),
            PropertyKeys.TYPE.value: get_node_filed_text(property_node, 'primitive_type'),
            PropertyKeys.MODIFIERS.value: get_node_modifiers(property_node),
        }
        # 添加行属性
        return property_info

    # 存储返回结果
    properties = []
    # 获取请求体部分
    body_node = find_first_child_by_field(class_node, "body")
    props_nodes = find_children_by_field(body_node, 'property_declaration')
    properties = [parse_class_property_node(prop_node) for prop_node in props_nodes]
    return properties


def parse_class_methods_node(language, class_node: Node):
    """获取类内部定义的方法节点信息 """
    # body_node:(declaration_list
    # (declaration_list
    # (property_declaration (visibility_modifier) (readonly_modifier) type: (primitive_type) (property_element name: (variable_name (name)) default_value: (integer)))
    # (property_declaration (visibility_modifier) (readonly_modifier) type: (primitive_type) (property_element name: (variable_name (name)) default_value: (integer)))
    # (method_declaration (visibility_modifier) name: (name) parameters: (formal_parameters) body: (compound_statement (echo_statement (encapsed_string (string_content) (escape_sequence)))))
    # (method_declaration (visibility_modifier) name: (name) parameters: (formal_parameters) body: (compound_statement (echo_statement (encapsed_string (string_content) (escape_sequence))))))

    def parse_class_method_node(language, method_node, class_name):
        print(f"method_node:{method_node}")
        method_name = get_node_filed_text(method_node, 'name')
        start_line = method_node.start_point[0]
        end_line = method_node.end_point[0]
        parameters_node = method_node.child_by_field_name('parameters')
        params_info = parse_params_node(parameters_node)
        called_methods = query_method_node_called_methods(language, method_node)
        visibility = get_node_filed_text(method_node, 'visibility_modifier')
        modifiers = get_node_modifiers(method_node)
        method_type = guess_method_type(method_name, is_native_method_or_class=True, is_class_method=True)
        fullname = get_method_fullname(method_name, class_name, None, is_static_method(modifiers))
        body_node = find_first_child_by_field(method_node, 'body')
        return_infos = parse_return_node(body_node)
        method_info = create_method_result(None, method_name=method_name, start_line=start_line, end_line=end_line,
                                           object_name=None, class_name=class_name, fullname=fullname, method_file=None,
                                           visibility=visibility, modifiers=modifiers, method_type=method_type,
                                           params_info=params_info, return_infos=return_infos, is_native=None,
                                           called_methods=called_methods)
        return method_info


    # 获取请求体部分
    class_name = get_node_filed_text(class_node, 'name')
    body_node = find_first_child_by_field(class_node, "body")

    # 获取方法属性
    method_info = []
    method_nodes = find_children_by_field(body_node, 'method_declaration')
    for method_node in method_nodes:
        property_info = parse_class_method_node(language, method_node, class_name=class_name)
        method_info.append(property_info)
    return method_info
