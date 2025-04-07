from typing import List, Dict, Any

from tree_sitter._binding import Node

from tree_class_info_check import query_namespace_define_infos, find_nearest_namespace
from tree_enums import PHPVisibility, PHPModifier, ClassKeys, PropertyKeys
from tree_func_info_check import query_general_methods_define_infos, query_classes_define_infos, \
    get_node_names_ranges
from tree_sitter_uitls import find_child_by_field, find_children_by_field

TREE_SITTER_CLASS_DEFINE_QUERY = """
    ;匹配类定义信息 含abstract类和final类
    (class_declaration
        ;(visibility_modifier)? @class_visibility
        ;(abstract_modifier)? @is_abstract_class
        ;(final_modifier)? @is_final_class
        ;(readonly_modifier)? @is_readonly_class
        ;(static_modifier)? @is_static_class
        ;name: (name) @class_name
        ;(base_clause (name) @extends)? @base_clause
        ;(class_interface_clause (name) @implements)? @class_interface_clause
        ;body: (declaration_list) @class_body
    ) @class.def

    ;匹配接口定义
    (interface_declaration
        ;name: (name) @interface_name
        ;捕获继承的父类
        ;(base_clause (name) @extends)? @base_clause
        ;body: (declaration_list) @interface_body
    ) @interface.def
"""

#     ;匹配类方法定义信息
#     (method_declaration
#         (visibility_modifier)? @method_visibility
#         (static_modifier)? @is_static_method
#         (abstract_modifier)? @is_abstract_method
#         (final_modifier)? @is_final_method
#         name: (name) @method_name
#         parameters: (formal_parameters) @method_params
#         return_type: (_)? @method_return_type
#         body: (compound_statement) @method_body
#     )@method.def


TREE_SITTER_CLASS_PROPS_QUERY = """
    ;匹配类属性定义信息
    (property_declaration
        (visibility_modifier)? @property_visibility
        (static_modifier)? @is_static
        (readonly_modifier)? @is_readonly
        (property_element
            name: (variable_name) @property_name
            (
                "="
                (_) @property_value
            )?
        )+
    )@property.def
"""


def analyze_class_infos(tree, language) -> List[Dict[str, Any]]:
    """提取所有类定义信息"""
    # 获取所有本地函数名称
    gb_methods_names,gb_methods_ranges=get_node_names_ranges(query_general_methods_define_infos(tree, language))
    print(f"gb_methods_names:{gb_methods_names}")
    # gb_methods_names:{'call_class'}

    # 获取所有类定义的代码行范围，以排除类方法 本文件不处理类方法
    classes_names, classes_ranges= get_node_names_ranges(query_classes_define_infos(tree, language))
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
                find_namespace = find_nearest_namespace(class_info[ClassKeys.START_LINE.value], namespaces_infos)
                class_info[ClassKeys.NAMESPACE.value] = find_namespace if find_namespace else ""
                class_info[ClassKeys.IS_INTERFACE.value] = is_interface

            # 添加类属性信息
            print(f"class_node:{class_node}")
            current_property = parse_class_properties_info(class_node)
            print("Added property:", current_property[PropertyKeys.NAME.value])
            class_info[ClassKeys.PROPERTIES.value].append(current_property)
            # 添加类方法信息

            # # 处理类方法信息
            # if 'method_name' in match_dict:
            #     parse_class_method_info(match_dict, current_class_info, gb_methods_names)
            #     print("Added method:", match_dict['method_name'][0].text.decode('utf-8'))

            class_infos.append(class_info)
            print(f"Added class: {class_info} in namespace:[{find_namespace}]")

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
    base_clause_node = find_child_by_field(class_def_node, 'base_clause')
    if base_clause_node:
        extends_nodes = find_children_by_field(base_clause_node, "name")
        extends_nodes = [{node.text.decode('utf-8'): None} for node in extends_nodes]
        # extends_nodes:[{'MyAbstractClassA': None}, {'MyAbstractClassB': None}]
        class_info[ClassKeys.EXTENDS.value] = extends_nodes

    # 获取接口信息
    interface_clause_node = find_child_by_field(class_def_node, 'class_interface_clause')
    if interface_clause_node:
        implements_nodes = find_children_by_field(interface_clause_node, "name")
        implements_nodes= [{node.text.decode('utf-8'): None} for node in implements_nodes]
        # implements_nodes:[{'MyInterface': None}, {'MyInterfaceB': None}]
        class_info[ClassKeys.INTERFACES.value] =implements_nodes

    # 获取类修饰符
    modifiers = []
    if find_child_by_field(class_def_node, 'abstract_modifier'):
        modifiers.append(PHPModifier.ABSTRACT.value)
    if find_child_by_field(class_def_node, 'final_modifier'):
        modifiers.append(PHPModifier.FINAL.value)
    if find_child_by_field(class_def_node, 'readonly_modifier'):
        modifiers.append(PHPModifier.READONLY.value)
    if find_child_by_field(class_def_node, 'static_modifier'):
        modifiers.append(PHPModifier.STATIC.value)
    class_info[ClassKeys.MODIFIERS.value] = modifiers

    # 获取类的可见性 # 在 PHP 中，类的声明本身没有可见性修饰符
    visibility_node = find_child_by_field(class_def_node, 'visibility_modifier')
    if visibility_node:
        class_info[ClassKeys.VISIBILITY.value] = visibility_node.text.decode('utf-8')

    # 获取类的起始和结束行号
    class_info[ClassKeys.START_LINE.value] = class_def_node.start_point[0]
    class_info[ClassKeys.END_LINE.value] = class_def_node.end_point[0]
    return class_info


# def parse_class_method_info(match_dict, current_class, file_functions):
#     if not (current_class and 'method_name' in match_dict):
#         return
#     method_node = match_dict['method.def'][0]
#     method_name = match_dict['method_name'][0]
#     method_name_txt = method_name.text.decode('utf-8')
#
#     # 获取返回类型
#     return_type = None
#     if 'method_return_type' in match_dict and match_dict['method_return_type'][0]:
#         return_type_node = match_dict['method_return_type'][0]
#         if return_type_node.type == 'qualified_name':
#             return_type = return_type_node.text.decode('utf-8')
#             if not return_type.startswith('\\'):
#                 return_type = '\\' + return_type
#         elif return_type_node.type == 'nullable_type':
#             for child in return_type_node.children:
#                 if child.type != '?':
#                     base_type = child.text.decode('utf-8')
#                     return_type = f"?{base_type}"
#                     break
#         else:
#             return_type = return_type_node.text.decode('utf-8')
#
#     # 获取方法可见性和修饰符
#     visibility = PHPVisibility.PUBLIC.value
#     if 'method_visibility' in match_dict and match_dict['method_visibility'][0]:
#         visibility = match_dict['method_visibility'][0].text.decode('utf-8')
#
#     method_modifiers = []
#     if 'is_static_method' in match_dict and match_dict['is_static_method'][0]:
#         method_modifiers.append(PHPModifier.STATIC.value)
#     if 'is_abstract_method' in match_dict and match_dict['is_abstract_method'][0]:
#         method_modifiers.append(PHPModifier.ABSTRACT.value)
#     if 'is_final_method' in match_dict and match_dict['is_final_method'][0]:
#         method_modifiers.append(PHPModifier.FINAL.value)
#
#     # 获取方法参数（只处理一次）
#     method_params = []
#     if 'method_params' in match_dict and match_dict['method_params'][0]:
#         params_node = match_dict['method_params'][0]
#         print(f"Debug - Processing method parameters for {method_name_txt}")
#         print(f"Debug - Parameter node types: {[child.type for child in params_node.children]}")
#
#         param_index = 0
#         for child in params_node.children:
#             if child.type == 'simple_parameter':
#                 param_info = process_parameter_node(child, current_class, param_index)  # 传入索引
#                 if param_info:
#                     method_params.append(param_info)
#                     print(f"Debug - Added parameter: {param_info}")
#                     param_index += 1
#
#     concat = "::" if 'static' in method_modifiers else "->"
#     current_method_info = {
#         MethodKeys.NAME.value: method_name_txt,
#         MethodKeys.METHOD_TYPE.value: MethodType.CLASS.value,
#         MethodKeys.START_LINE.value: method_node.start_point[0],
#         MethodKeys.END_LINE.value: method_node.end_point[0],
#
#         MethodKeys.VISIBILITY.value: visibility,
#         MethodKeys.MODIFIERS.value: method_modifiers,
#         MethodKeys.OBJECT.value: current_class[ClassKeys.NAME.value],
#         MethodKeys.FULLNAME.value: f"{current_class[ClassKeys.NAME.value]}{concat}{method_name_txt}",
#
#         MethodKeys.RETURN_TYPE.value: return_type,
#         MethodKeys.RETURN_VALUE.value: None,
#         MethodKeys.PARAMS.value: method_params,
#         MethodKeys.CALLED.value: []
#     }
#
#     # 处理方法体中的函数调用
#     if 'method_body' in match_dict:
#         body_node = match_dict['method_body'][0]
#         # seen_called_functions = set()
#         # print(f"Debug - Processing method body for {current_method_info[MethodKeys.NAME.value]}")
#         #
#         # def traverse_method_body(node):
#         #     parse_method_body_node(node, seen_called_functions, file_functions, current_method_info, current_class)
#         #     for _child in node.children:
#         #         traverse_method_body(_child)
#         # traverse_method_body(body_node)
#
#         query_method_body_called_methods(language, body_node, classes_names, gb_methods_names, object_class_infos)
#         print(f"Debug - Found {len(current_method_info[MethodKeys.CALLED.value])} called methods")
#
#     current_class[ClassKeys.METHODS.value].append(current_method_info)


def parse_property_declaration(property_node: Node) -> dict:
    """解析单个属性声明节点的信息。 """
    # 初始化属性信息
    property_info = {
        'visibility': None,  # 可见性
        'name': None,  # 属性名
        'default_value': None,  # 默认值
        'type': None,  # 属性类型
    }

    # 获取可见性修饰符
    visibility_node = find_child_by_field(property_node,'visibility_modifier')
    if visibility_node:
        property_info['visibility'] = visibility_node.text.decode('utf-8')
        print("Visibility:", property_info['visibility'])

    # 获取属性类型修饰符
    primitive_node = find_child_by_field(property_node,'primitive_type')
    if primitive_node:
        property_info['type'] = primitive_node.text.decode('utf-8')
        print("type:", property_info['type'])

    # 获取类修饰符
    modifiers = []
    if find_child_by_field(property_node, 'abstract_modifier'):
        modifiers.append(PHPModifier.ABSTRACT.value)
    if find_child_by_field(property_node, 'final_modifier'):
        modifiers.append(PHPModifier.FINAL.value)
    if find_child_by_field(property_node, 'readonly_modifier'):
        modifiers.append(PHPModifier.READONLY.value)
    if find_child_by_field(property_node, 'static_modifier'):
        modifiers.append(PHPModifier.STATIC.value)
    property_info[PropertyKeys.MODIFIERS.value] = modifiers


    # 获取属性元素节点
    property_element_node =find_child_by_field(property_node,'property_element')
    if property_element_node:
        # 获取属性名
        name_node = find_child_by_field(property_element_node,'name')
        print("name_node:", name_node)
        if name_node:
            property_info['name'] = name_node.text.decode('utf-8')

        # 获取默认值
        default_value_node = find_child_by_field(property_element_node, 'default_value')
        print("default_value_node:", default_value_node)
        if default_value_node:
            property_info['default_value'] = default_value_node.text.decode('utf-8')

    return property_info

def parse_class_properties_info(class_node):
    # class_node:
    # (class_declaration name: (name) (base_clause (name) (name))
    # body: (declaration_list (property_declaration (visibility_modifier) (property_element name: (variable_name (name)) default_value: (integer)))
    # (method_declaration (visibility_modifier) name: (name) parameters: (formal_parameters) body: (compound_statement (echo_statement (encapsed_string (string_content) (escape_sequence)))))))
    properties = []
    body_node = find_child_by_field(class_node, "body")
    if body_node:
        print(f"body_node:{body_node}")
        props_nodes = find_children_by_field(body_node, 'property_declaration')
        for prop_node in props_nodes:
                print(f"declaration:{prop_node}")
                property_info = parse_property_declaration(prop_node)
                print(f"property_info:{property_info}")
                properties.append(property_info)
    print(f"properties:{properties}")
    exit()
    # property_visibility = match_dict.get('property_visibility', [None])[0]
    # visibility = property_visibility.text.decode('utf-8') if property_visibility else PHPVisibility.PUBLIC.value
    #
    # is_static = 'is_static' in match_dict and match_dict['is_static'][0] is not None
    # is_readonly = 'is_readonly' in match_dict and match_dict['is_readonly'][0] is not None
    #
    # property_info = match_dict['property_name'][0]
    # property_modifiers = []
    # if is_static:
    #     property_modifiers.append(PHPModifier.STATIC.value)
    # if is_readonly:
    #     property_modifiers.append(PHPModifier.READONLY.value)
    # # 获取属性初始值
    # property_value = match_dict['property_value'][0].text.decode('utf-8') if 'property_value' in match_dict else None
    #
    # current_property = {
    #     PropertyKeys.NAME.value: property_info.text.decode('utf-8'),
    #     PropertyKeys.LINE.value: property_info.start_point[0],
    #     PropertyKeys.VISIBILITY.value: visibility,
    #     PropertyKeys.MODIFIERS.value: property_modifiers,
    #     PropertyKeys.DEFAULT.value: property_value,
    #     PropertyKeys.TYPE.value: None,
    # }

    print("Debug - Final property:", current_property)
    return current_property



if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.utils_json import print_json
    from tree_func_utils import read_file_to_parse

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/class2.php"
    php_file_tree = read_file_to_parse(PARSER, php_file)
    code = analyze_class_infos(php_file_tree, LANGUAGE)
    print_json(code)


