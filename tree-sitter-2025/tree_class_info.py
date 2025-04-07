from typing import List, Dict, Any

from tree_sitter._binding import Node

from tree_class_info_check import query_namespace_define_infos, find_nearest_namespace
from deprecated_tree_class_info_no_check import parse_method_body_node
from tree_enums import PHPVisibility, PHPModifier, ClassKeys, PropertyKeys, ParameterKeys, MethodKeys, MethodType
from tree_func_info_check import query_general_methods_define_infos, query_classes_define_infos, \
    get_node_names_ranges, query_method_body_called_methods, res_called_object_method, guess_object_is_native, \
    res_called_construct_method, res_called_general_method
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

#
# TREE_SITTER_CLASS_PROPS_QUERY = """
#     ;匹配类属性定义信息
#     (property_declaration
#         (visibility_modifier)? @property_visibility
#         (static_modifier)? @is_static
#         (readonly_modifier)? @is_readonly
#         (property_element
#             name: (variable_name) @property_name
#             (
#                 "="
#                 (_) @property_value
#             )?
#         )+
#     )@property.def
# """


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
            body_node = find_child_by_field(class_node, "body")
            class_properties = parse_body_properties_node(body_node)
            class_info[ClassKeys.PROPERTIES.value] = class_properties
            # 添加类方法信息
            class_methods = parse_body_methods_node(body_node)
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
        class_info[ClassKeys.INTERFACES.value] = implements_nodes

    # 获取类修饰符
    class_info[ClassKeys.MODIFIERS.value] = get_node_modifiers(class_def_node)

    # 获取类的可见性 # 在 PHP 中，类的声明本身没有可见性修饰符
    class_info[ClassKeys.VISIBILITY.value] = get_node_text(class_def_node, 'visibility_modifier')

    # 获取类的起始和结束行号
    class_info[ClassKeys.START_LINE.value] = class_def_node.start_point[0]
    class_info[ClassKeys.END_LINE.value] = class_def_node.end_point[0]
    return class_info


def get_node_text(node, field_name_or_type):
    find_node = find_child_by_field(node, field_name_or_type)
    find_text = find_node.text.decode('utf-8') if find_node else None
    return find_text


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
        print(f"parameters_node:{parameters_node}")
        for param_index,param_node in enumerate(parameters_node.children):
            print(f"param_node.type:{param_node.type}")
            if param_node.type == 'simple_parameter':
                print(f"param_node:{param_node}")
                parameter_info = parse_simple_parameter(param_node, param_index)
                print(f"parameter_info:{parameter_info}")
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
    parameter_info[ParameterKeys.NAME.value] = get_node_text(param_node, 'name')

    # 获取默认值
    default_value_node = find_child_by_field(param_node, 'default_value')
    if default_value_node:
        parameter_info[ParameterKeys.DEFAULT.value] = default_value_node.text.decode('utf-8')
        # 从默认值节点的类型推断参数类型
        parameter_info[ParameterKeys.TYPE.value] = default_value_node.type

    return parameter_info


# def parse_method_body_called_methods(body_node, classes_names, gb_methods_names, object_class_infos):
#     """
#     解析方法体代码内调用的其他方法信息。
#
#     :param body_node: 方法体节点 (Tree-sitter 节点)
#     :param classes_names: 当前文件中的类名集合
#     :param gb_methods_names: 当前文件中的全局方法名集合
#     :param object_class_infos: 对象类型信息
#     :return: 包含所有调用方法信息的列表
#     """
#     called_methods = []
#
#     # 需要使用递归的方法 递归遍历方法体的所有子节点 孙子节点等等 然后提取函数信息,比较麻烦
#     for child_node in body_node.children:
#         # 处理普通函数调用
#         print(f"child_node:{child_node.type} -> {child_node}")
#
#         if child_node.type == 'function_call_expression':
#             func_name_node = child_node.child_by_field_name('name')
#             args_node = child_node.child_by_field_name('arguments')
#
#             if func_name_node:
#                 func_name = func_name_node.text.decode('utf-8')
#                 method_is_native = func_name in gb_methods_names  # 判断是否为本文件函数
#                 called_general_method = res_called_general_method(func_name_node, func_name, args_node, method_is_native)
#                 if called_general_method[MethodKeys.METHOD_TYPE.value] != MethodType.BUILTIN.value:
#                     called_methods.append(called_general_method)
#
#         # 处理对象创建
#         elif child_node.type == 'object_creation_expression':
#             class_name_node = child_node.child_by_field_name('name')
#             args_node = child_node.child_by_field_name('arguments')
#
#             if class_name_node:
#                 class_name = class_name_node.text.decode('utf-8')
#                 class_is_native = class_name in classes_names  # 判断是否为本文件类
#                 called_construct_method = res_called_construct_method(class_name_node, args_node, class_is_native)
#                 called_methods.append(called_construct_method)
#
#         # 处理成员方法调用
#         elif child_node.type == 'member_call_expression':
#             object_node = child_node.child_by_field_name('object')
#             method_name_node = child_node.child_by_field_name('name')
#             args_node = child_node.child_by_field_name('arguments')
#
#             if object_node and method_name_node:
#                 object_name = object_node.text.decode('utf-8')
#                 object_line = object_node.start_point[0]
#                 method_name = method_name_node.text.decode('utf-8')
#
#                 class_is_native, class_name = guess_object_is_native(object_name, object_line, classes_names,object_class_infos)
#                 called_object_method = res_called_object_method(object_node, method_name_node, args_node, method_name, class_is_native, False, class_name)
#                 called_methods.append(called_object_method)
#
#         # 处理静态方法调用
#         elif child_node.type == 'scoped_call_expression':
#             scope_node = child_node.child_by_field_name('scope')
#             method_name_node = child_node.child_by_field_name('name')
#             args_node = child_node.child_by_field_name('arguments')
#
#             if scope_node and method_name_node:
#                 scope_name = scope_node.text.decode('utf-8')
#                 method_name = method_name_node.text.decode('utf-8')
#
#                 class_is_native = scope_name in classes_names  # 判断是否为本文件类
#                 called_static_method = res_called_object_method(scope_node, method_name_node, args_node, method_name, class_is_native, True, scope_name)
#                 called_methods.append(called_static_method)
#
#     return called_methods

def parse_method_called_methods(method_body_node):
    print(f"method_body_node:{method_body_node}")
    # method_body_node:(compound_statement (echo_statement (variable_name (name))))
    body_called_methods = query_method_body_called_methods(LANGUAGE, method_body_node)
    print(f"body_called_methods:{body_called_methods}")
    return body_called_methods

def parse_method_node(method_node):
    method_info = {
        MethodKeys.NAME.value: None,  # 方法名
        MethodKeys.PARAMS.value: [],  # 参数列表
        MethodKeys.VISIBILITY.value: None,  # 默认可见性为 public
        MethodKeys.MODIFIERS.value:[]
    }

    print(f"method_node:{method_node}")
    # 方法名称
    method_info[MethodKeys.NAME.value] = get_node_text(method_node, 'name')
    # 获取可见性修饰符 visibility_modifier
    method_info[MethodKeys.VISIBILITY.value] = get_node_text(method_node, 'visibility_modifier')
    # 获取特殊修饰符
    method_info[MethodKeys.MODIFIERS.value] = get_node_modifiers(method_node)
    # 获取方法信息
    ## 方法参数列表
    method_info[MethodKeys.PARAMS.value] = parse_method_parameters(method_node)
    ## 方法内的调用信息
    method_body_node = find_child_by_field(method_node, 'body')
    method_info[MethodKeys.CALLED.value] = parse_method_called_methods(method_body_node)
    return method_info

def parse_body_methods_node(body_node:Node):
    print(f"body_node:{body_node}")
    # body_node:(declaration_list
    # (declaration_list
    # (property_declaration (visibility_modifier) (readonly_modifier) type: (primitive_type) (property_element name: (variable_name (name)) default_value: (integer)))
    # (property_declaration (visibility_modifier) (readonly_modifier) type: (primitive_type) (property_element name: (variable_name (name)) default_value: (integer)))
    # (method_declaration (visibility_modifier) name: (name) parameters: (formal_parameters) body: (compound_statement (echo_statement (encapsed_string (string_content) (escape_sequence)))))
    # (method_declaration (visibility_modifier) name: (name) parameters: (formal_parameters) body: (compound_statement (echo_statement (encapsed_string (string_content) (escape_sequence))))))

    # 获取方法属性
    method_info = []
    if body_node:
        method_nodes = find_children_by_field(body_node, 'method_declaration')
        for method_node in method_nodes:
            property_info = parse_method_node(method_node)
            method_info.append(property_info)
    return method_info

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




def get_node_modifiers(node):
    modifiers = []
    if find_child_by_field(node, 'abstract_modifier'):
        modifiers.append(PHPModifier.ABSTRACT.value)
    if find_child_by_field(node, 'final_modifier'):
        modifiers.append(PHPModifier.FINAL.value)
    if find_child_by_field(node, 'readonly_modifier'):
        modifiers.append(PHPModifier.READONLY.value)
    if find_child_by_field(node, 'static_modifier'):
        modifiers.append(PHPModifier.STATIC.value)
    return modifiers


def parse_body_properties_node(body_node):
    def parse_property_node(property_node: Node) -> dict:
        """解析单个属性声明节点的信息。 """
        # 初始化属性信息
        prop_info = {
            PropertyKeys.VISIBILITY.value: None,  # 可见性
            PropertyKeys.NAME.value: None,  # 属性名
            PropertyKeys.DEFAULT.value: None,  # 默认值
            PropertyKeys.MODIFIERS.value: None,  # 属性类型
            PropertyKeys.START_LINE.value: None,
            PropertyKeys.END_LINE.value: None,
        }

        # 获取可见性修饰符
        prop_info[PropertyKeys.VISIBILITY.value] = get_node_text(property_node, 'visibility_modifier')

        # 获取类修饰符
        prop_info[PropertyKeys.MODIFIERS.value] = get_node_modifiers(property_node)

        # 获取属性类型修饰符
        prop_info[PropertyKeys.TYPE.value] = get_node_text(property_node, 'primitive_type')

        # 获取属性元素节点
        property_element_node = find_child_by_field(property_node, 'property_element')
        if property_element_node:
            # 获取属性名
            prop_info[PropertyKeys.NAME.value] = get_node_text(property_element_node, 'name')
            # 获取默认值
            prop_info[PropertyKeys.DEFAULT.value] = get_node_text(property_element_node, 'default_value')

        # 添加行属性
        prop_info[PropertyKeys.START_LINE.value] = property_node.start_point[0]
        prop_info[PropertyKeys.END_LINE.value] = property_node.end_point[0]
        return prop_info

    properties = []
    if body_node:
        props_nodes = find_children_by_field(body_node, 'property_declaration')
        for prop_node in props_nodes:
                property_info = parse_property_node(prop_node)
                properties.append(property_info)
    return properties



if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.utils_json import print_json
    from deprecated_tree_func_utils import read_file_to_parse

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/class2.php"
    php_file_tree = read_file_to_parse(PARSER, php_file)
    code = analyze_class_infos(php_file_tree, LANGUAGE)
    print_json(code)


