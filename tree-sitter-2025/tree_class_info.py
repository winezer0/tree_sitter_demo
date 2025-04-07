from typing import List, Dict, Any

from tree_sitter._binding import Node

from tree_class_uitls import query_namespace_define_infos, find_nearest_namespace, parse_class_properties_node
from tree_enums import PHPVisibility, ClassKeys, ParameterKeys, MethodKeys
from tree_func_utils import get_node_modifiers, query_method_node_called_methods, \
    query_global_methods_define_infos, query_classes_define_infos
from guess import get_node_names_ranges
from tree_sitter_uitls import find_first_child_by_field, find_children_by_field, get_node_filed_text, read_file_to_parse

TREE_SITTER_CLASS_DEFINE_QUERY = """
    ;匹配类定义信息 含abstract类和final类
    (class_declaration) @class.def
    ;匹配接口定义
    (interface_declaration) @interface.def
"""


def analyze_class_infos(tree, language) -> List[Dict[str, Any]]:
    """提取所有类定义信息"""
    # 获取所有本地函数名称
    gb_methods_names,gb_methods_ranges=get_node_names_ranges(query_global_methods_define_infos(language, tree.root_node))
    print(f"gb_methods_names:{gb_methods_names}")
    # gb_methods_names:{'call_class'}

    # 获取所有类定义的代码行范围，以排除类方法 本文件不处理类方法
    classes_names, classes_ranges= get_node_names_ranges(query_classes_define_infos(language, tree.root_node))
    print(f"classes_names:{classes_names}")
    # classes_names:{'InterfaceImplementation', 'MyAbstractClass', 'ConcreteClass', 'MyInterface', 'MyClass'}

    # 获取所有命名空间信息
    namespaces_infos = query_namespace_define_infos(tree, language)
    print(namespaces_infos)
    # [{'NAME': 'App\\Namespace1', 'START': 7, 'END': 41, 'UNIQ': 'App\\Namespace1|7,41'},

    class_info_query = language.query(TREE_SITTER_CLASS_DEFINE_QUERY)
    class_info_matches = class_info_query.matches(tree.root_node)

    # 函数调用解析部分
    class_infos = []
    for pattern_index, match_dict in class_info_matches:
        # 添加调试信息
        print(f"{pattern_index}/{len(class_info_matches)} Pattern match type:", [key for key in match_dict.keys()])
        # 一次性解析类信息
        class_def_mark = 'class.def'  # 语法中表示类定义
        inter_def_mark = 'interface.def' # 语法中表示接口定义
        if class_def_mark in match_dict or inter_def_mark in match_dict:
            # 处理类信息时使用当前命名空间 # 如果命名空间栈非空，使用栈顶命名空间
            is_interface = inter_def_mark in match_dict
            class_node = match_dict[inter_def_mark][0] if is_interface else match_dict[class_def_mark][0]
            class_info = parse_class_define_info(class_node)
            if class_info:
                # 反向查询命名空间信息
                class_info[ClassKeys.NAMESPACE.value] = find_nearest_namespace(class_info[ClassKeys.START_LINE.value], namespaces_infos)
                class_info[ClassKeys.IS_INTERFACE.value] = is_interface

            # 添加类属性信息
            class_properties = parse_class_properties_node(class_node)
            class_info[ClassKeys.PROPERTIES.value] = class_properties
            # 添加类方法信息
            class_methods = parse_class_methods_node(language, class_node)
            print(f"class_methods:{class_methods}")
            class_info[ClassKeys.METHODS.value] = class_methods
    return class_infos


def parse_class_define_info(class_def_node):
    """
    解析类定义信息，使用 child_by_field_name 提取字段。
    :param class_def_node: 类定义节点 (Tree-sitter 节点)
    :return: 包含类信息的字典
    """
    # 初始化类信息
    class_info = {
        ClassKeys.NAME.value: None,
        ClassKeys.NAMESPACE.value: None,
        ClassKeys.VISIBILITY.value: PHPVisibility.PUBLIC.value,  # 默认可见性 Php类没有可见性
        ClassKeys.MODIFIERS.value: [], # 特殊属性
        ClassKeys.START_LINE.value: None,
        ClassKeys.END_LINE.value: None,

        ClassKeys.EXTENDS.value: [],
        ClassKeys.INTERFACES.value: [],
        ClassKeys.PROPERTIES.value: [],
        ClassKeys.METHODS.value: [],

        ClassKeys.IS_INTERFACE.value: None,
    }

    # 获取类名
    class_name_node = class_def_node.child_by_field_name('name')
    if class_name_node:
        class_name = class_name_node.text.decode('utf-8')
        class_info[ClassKeys.NAME.value] = class_name

    # 获取继承信息
    base_clause_node = find_first_child_by_field(class_def_node, 'base_clause')
    if base_clause_node:
        extends_nodes = find_children_by_field(base_clause_node, "name")
        extends_nodes = [{node.text.decode('utf-8'): None} for node in extends_nodes]
        # extends_nodes:[{'MyAbstractClassA': None}, {'MyAbstractClassB': None}]
        class_info[ClassKeys.EXTENDS.value] = extends_nodes

    # 获取接口信息
    interface_clause_node = find_first_child_by_field(class_def_node, 'class_interface_clause')
    if interface_clause_node:
        implements_nodes = find_children_by_field(interface_clause_node, "name")
        implements_nodes= [{node.text.decode('utf-8'): None} for node in implements_nodes]
        # implements_nodes:[{'MyInterface': None}, {'MyInterfaceB': None}]
        class_info[ClassKeys.INTERFACES.value] = implements_nodes

    # 获取类修饰符
    class_info[ClassKeys.MODIFIERS.value] = get_node_modifiers(class_def_node)

    # 获取类的可见性 # 在 PHP 中，类的声明本身没有可见性修饰符
    class_info[ClassKeys.VISIBILITY.value] = get_node_filed_text(class_def_node, 'visibility_modifier')

    # 获取类的起始和结束行号
    class_info[ClassKeys.START_LINE.value] = class_def_node.start_point[0]
    class_info[ClassKeys.END_LINE.value] = class_def_node.end_point[0]
    return class_info


def parse_method_parameters(method_node: Node) -> list:
    """
    解析方法声明节点中的参数信息。
    :param method_node: 方法声明节点 (Tree-sitter 节点)
    :return: 包含所有参数信息的列表
    """
    parameters = []
    # 获取参数列表节点
    parameters_node = method_node.child_by_field_name('parameters')
    if parameters_node:
        param_index = 0
        for param_node in parameters_node.children:
            if param_node.type == 'simple_parameter':
                parameter_info = parse_simple_parameter(param_node, param_index)
                param_index += 1
                parameters.append(parameter_info)
    return parameters


def parse_simple_parameter(param_node: Node, param_index: int = None) -> dict:
    """
    解析单个简单参数节点的信息。
    :param param_node: 简单参数节点 (Tree-sitter 节点)
    :param param_index: 参数索引号
    :return: 包含参数信息的字典
    """
    # 初始化参数信息
    parameter_info = {
        ParameterKeys.NAME.value: None,  # 参数名
        ParameterKeys.TYPE.value: None,  # 参数类型（如果存在）
        ParameterKeys.DEFAULT.value: None,  # 默认值（如果存在）
        ParameterKeys.VALUE.value: None,  # 值 函数定义时没有值
        ParameterKeys.INDEX.value: param_index,  # 索引
    }

    # 获取参数名
    parameter_info[ParameterKeys.NAME.value] = get_node_filed_text(param_node, 'name')

    # 获取默认值
    default_value_node = find_first_child_by_field(param_node, 'default_value')
    if default_value_node:
        parameter_info[ParameterKeys.DEFAULT.value] = default_value_node.text.decode('utf-8')
        # 从默认值节点的类型推断参数类型
        parameter_info[ParameterKeys.TYPE.value] = default_value_node.type

    return parameter_info


def parse_method_called_methods(language, method_node):
    # method_body_node = find_first_child_by_field(method_node, 'body')
    body_called_methods = query_method_node_called_methods(language, method_node)
    return body_called_methods

def parse_method_node(language, method_node):
    print(f"method_node:{method_node}")
    method_info = {
        MethodKeys.START_LINE.value: method_node.start_point[0],
        MethodKeys.END_LINE.value: method_node.end_point[0],
        MethodKeys.NAME.value: get_node_filed_text(method_node, 'name'),  # 方法名称
        MethodKeys.PARAMS.value: parse_method_parameters(method_node),  # 方法参数列表
        MethodKeys.VISIBILITY.value: get_node_filed_text(method_node, 'visibility_modifier'), # 获取可见性修饰符
        MethodKeys.MODIFIERS.value: get_node_modifiers(method_node), # 获取特殊修饰符
        MethodKeys.CALLED.value: parse_method_called_methods(language, method_node), #方法内的调用信息
        MethodKeys.FULLNAME.value: None,
        MethodKeys.RETURN_TYPE.value: None,
        MethodKeys.RETURN_VALUE.value: None,
        MethodKeys.FILE.value: None,
        MethodKeys.CLASS.value: None,
        MethodKeys.OBJECT.value: None,
        MethodKeys.IS_NATIVE.value: None,
        MethodKeys.METHOD_TYPE.value: None,
    }
    return method_info

def parse_class_methods_node(language, class_node: Node):
    """获取类内部定义的方法节点信息 """
    # body_node:(declaration_list
    # (declaration_list
    # (property_declaration (visibility_modifier) (readonly_modifier) type: (primitive_type) (property_element name: (variable_name (name)) default_value: (integer)))
    # (property_declaration (visibility_modifier) (readonly_modifier) type: (primitive_type) (property_element name: (variable_name (name)) default_value: (integer)))
    # (method_declaration (visibility_modifier) name: (name) parameters: (formal_parameters) body: (compound_statement (echo_statement (encapsed_string (string_content) (escape_sequence)))))
    # (method_declaration (visibility_modifier) name: (name) parameters: (formal_parameters) body: (compound_statement (echo_statement (encapsed_string (string_content) (escape_sequence))))))

    # 获取请求体部分
    body_node = find_first_child_by_field(class_node, "body")
    # 获取方法属性
    method_info = []
    if body_node:
        method_nodes = find_children_by_field(body_node, 'method_declaration')
        for method_node in method_nodes:
            property_info = parse_method_node(language, method_node)
            method_info.append(property_info)
    return method_info


if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.utils_json import print_json

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/class2.php"
    php_file_tree = read_file_to_parse(PARSER, php_file)
    code = analyze_class_infos(php_file_tree, LANGUAGE)
    print_json(code)


