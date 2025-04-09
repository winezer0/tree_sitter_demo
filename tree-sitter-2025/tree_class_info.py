from typing import List, Dict, Any

from tree_class_uitls import query_namespace_define_infos
from tree_class_parse_sub import parse_class_properties_node, parse_class_methods_node
from guess import find_nearest_namespace
from tree_enums import PHPVisibility, ClassKeys
from tree_func_utils_sub_parse import get_node_modifiers
from tree_func_utils_global_define import query_gb_methods_define_infos, query_gb_classes_define_infos, \
    get_node_infos_names_ranges
from tree_sitter_uitls import find_first_child_by_field, find_children_by_field, get_node_filed_text, \
    read_file_to_parse

def analyze_class_infos(tree, language) -> List[Dict[str, Any]]:
    """提取所有类定义信息"""
    root_node = tree.root_node
    # 获取所有本地函数名称
    gb_methods_define_infos = query_gb_methods_define_infos(language, root_node)
    gb_methods_names,gb_methods_ranges=get_node_infos_names_ranges(gb_methods_define_infos)
    print(f"gb_methods_names:{gb_methods_names}")
    # 获取所有类定义的代码行范围，以排除类方法 本文件不处理类方法
    classes_define_infos = query_gb_classes_define_infos(language, root_node)
    gb_classes_names, gb_classes_ranges= get_node_infos_names_ranges(classes_define_infos)
    print(f"gb_classes_names:{gb_classes_names}")
    # gb_classes_names:{'InterfaceImplementation', 'MyAbstractClass', 'ConcreteClass', 'MyInterface', 'MyClass'}
    # 获取所有命名空间信息
    namespaces_infos = query_namespace_define_infos(language, root_node)
    print(namespaces_infos)
    # [{'NAME': 'App\\Namespace1', 'START': 7, 'END': 41, 'UNIQ': 'App\\Namespace1|7,41'},

    TREE_SITTER_CLASS_DEFINE_QUERY = """
        ;匹配类定义信息 含abstract类和final类
        (class_declaration) @class.def
        ;匹配接口定义
        (interface_declaration) @class.def
    """
    class_info_query = language.query(TREE_SITTER_CLASS_DEFINE_QUERY)
    class_info_matches = class_info_query.matches(root_node)

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
            class_info = parse_class_define_info(language, class_node, is_interface, namespaces_infos)
            class_infos.append(class_info)
    return class_infos


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


if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.utils_json import print_json

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/class2.php"
    php_file_tree = read_file_to_parse(PARSER, php_file)
    code = analyze_class_infos(php_file_tree, LANGUAGE)
    print_json(code)


