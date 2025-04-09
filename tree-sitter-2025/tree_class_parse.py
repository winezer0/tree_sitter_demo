from tree_sitter._binding import Node

from guess import guess_method_type, find_nearest_namespace

from tree_enums import PropertyKeys, ClassKeys
from tree_func_utils import query_method_node_called_methods, is_static_method, get_method_fullname
from tree_func_utils_sub_parse import get_node_modifiers, parse_params_node, parse_return_node, create_method_result
from tree_sitter_uitls import find_first_child_by_field, get_node_filed_text, find_children_by_field, \
    extract_node_text_infos

def creat_class_result(class_name, namespace, start_line, end_line, visibility, modifiers, extends, interfaces, properties, is_interface, class_methods):
    class_info = {
        ClassKeys.NAME.value: class_name,
        ClassKeys.NAMESPACE.value: namespace,

        ClassKeys.START_LINE.value: start_line,
        ClassKeys.END_LINE.value: end_line,

        ClassKeys.VISIBILITY.value: visibility,  # 默认可见性 Php类没有可见性
        ClassKeys.MODIFIERS.value: modifiers, # 特殊属性

        ClassKeys.EXTENDS.value: extends,
        ClassKeys.INTERFACES.value: interfaces,
        ClassKeys.PROPERTIES.value: properties,

        ClassKeys.IS_INTERFACE.value: is_interface,

        ClassKeys.METHODS.value: class_methods,
    }
    return class_info


def query_namespace_define_infos(language, root_node):
    """获取所有本地命名空间的定义 返回node字典格式"""
    namespace_define_query = language.query("""
    ;匹配命名空间定义信息
    (namespace_definition
        name: (namespace_name) @namespace_name
    ) @namespace.def
    """)
    namespace_infos = extract_node_text_infos(root_node, namespace_define_query, 'namespace.def', need_node_field='name')
    return namespace_infos


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


def parse_class_define_info(language, class_define_node, is_interface, namespaces_infos):
    """
    解析类定义信息，使用 child_by_field_name 提取字段。
    :param class_define_node: 类定义节点 (Tree-sitter 节点)
    :return: 包含类信息的字典
    """
    # 获取类名
    class_name = get_node_filed_text(class_define_node, 'name')

    # 获取类的起始和结束行号
    start_line = class_define_node.start_point[0]
    end_line = class_define_node.end_point[0]

    # 反向查询命名空间信息
    namespaces = find_nearest_namespace(start_line, namespaces_infos)

    # 获取继承信息
    extends = None
    base_clause_node = find_first_child_by_field(class_define_node, 'base_clause')
    if base_clause_node:
        extends_nodes = find_children_by_field(base_clause_node, "name")
        extends_nodes = [{node.text.decode('utf-8'): None} for node in extends_nodes]
        # extends_nodes:[{'MyAbstractClassA': None}, {'MyAbstractClassB': None}]
        extends = extends_nodes

    # 获取接口信息
    interfaces = None
    interface_clause_node = find_first_child_by_field(class_define_node, 'class_interface_clause')
    if interface_clause_node:
        implements_nodes = find_children_by_field(interface_clause_node, "name")
        implements_nodes= [{node.text.decode('utf-8'): None} for node in implements_nodes]
        # implements_nodes:[{'MyInterface': None}, {'MyInterfaceB': None}]
        interfaces = implements_nodes

    # 获取类修饰符
    modifiers = get_node_modifiers(class_define_node)

    # 获取类的可见性 # 在 PHP 中，类的声明本身没有可见性修饰符
    visibility = get_node_filed_text(class_define_node, 'visibility_modifier')

    # 添加类属性信息
    properties = parse_class_properties_node(class_define_node)

    # 添加类方法信息
    class_methods = parse_class_methods_node(language, class_define_node)
    return creat_class_result(class_name=class_name, namespace=namespaces, start_line=start_line, end_line=end_line,
                              visibility=visibility, modifiers=modifiers, extends=extends, interfaces=interfaces,
                              properties=properties, is_interface=is_interface, class_methods=class_methods)

