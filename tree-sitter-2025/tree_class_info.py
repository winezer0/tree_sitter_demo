from typing import List, Dict, Any

from tree_class_info_check import query_namespace_define_infos, find_nearest_namespace
from tree_enums import PHPVisibility, PHPModifier, ClassKeys, PropertyKeys
from tree_func_info_check import query_general_methods_define_infos, query_classes_define_infos, \
    get_node_names_ranges
from tree_sitter_uitls import find_child_by_field_type, find_child_by_field, find_children_by_field

TREE_SITTER_CLASS_DEFINE_QUERY = """
    ;匹配类定义信息 含abstract类和final类
    (class_declaration
        (visibility_modifier)? @class_visibility
        (abstract_modifier)? @is_abstract_class
        (final_modifier)? @is_final_class
        name: (name) @class_name
        (base_clause (name) @extends)? @base_clause
        (class_interface_clause (name) @implements)? @class_interface_clause
        body: (declaration_list) @class_body
    ) @class.def

    ;匹配接口定义
    (interface_declaration
        name: (name) @interface_name
        ;捕获继承的父类
        (base_clause (name) @extends)? @base_clause
        body: (declaration_list) @interface_body
    ) @interface.def

    ;匹配类方法定义信息
    (method_declaration
        (visibility_modifier)? @method_visibility
        (static_modifier)? @is_static_method
        (abstract_modifier)? @is_abstract_method
        (final_modifier)? @is_final_method
        name: (name) @method_name
        parameters: (formal_parameters) @method_params
        return_type: (_)? @method_return_type
        body: (compound_statement) @method_body
    )@method.def
"""

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
        # 解析类信息
        if 'class.def' in match_dict:
            # 处理类信息时使用当前命名空间 # 如果命名空间栈非空，使用栈顶命名空间
            class_node = match_dict['class.def'][0]
            print(f"class_node:{class_node}")
            class_info = parse_class_define_info(class_node)
            print(class_info)
            if class_info:
                # 反向查询命名空间信息
                find_namespace = find_nearest_namespace(class_info[ClassKeys.START_LINE.value], namespaces_infos)
                class_info[ClassKeys.NAMESPACE.value] = find_namespace if find_namespace else ""
                class_infos.append(class_info)
                print(f"Added class: {class_info[ClassKeys.NAME.value]} in namespace:[{find_namespace}]")

            exit()
        # 解析接口信息
        if 'interface.def' in match_dict:
            interface_node = match_dict['interface.def'][0]
            print(f"interface_node:{interface_node}")
            interface_info = parse_interface_define_info(match_dict)
            if interface_info:
                find_namespace = find_nearest_namespace(interface_info[ClassKeys.START_LINE.value], namespaces_infos)
                interface_info[ClassKeys.NAMESPACE.value] = find_namespace
                class_infos.append(interface_info)
                print(f"Added interface: {interface_info[ClassKeys.NAME.value]} in namespace:[{find_namespace}]")

        # if current_class_info:
        #     # 添加类属性信息
        #     if 'property_name' in match_dict:
        #         current_property = process_class_property_info(match_dict)
        #         print("Added property:", current_property[PropertyKeys.NAME.value])
        #         current_class_info[ClassKeys.PROPERTIES.value].append(current_property)

            # # 处理类方法信息
            # if 'method_name' in match_dict:
            #     parse_class_method_info(match_dict, current_class_info, gb_methods_names)
            #     print("Added method:", match_dict['method_name'][0].text.decode('utf-8'))

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
        ClassKeys.VISIBILITY.value: PHPVisibility.PUBLIC.value,  # 默认可见性
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
    print(f"class_def_node:{class_def_node}")
    interface_clause_node = find_child_by_field(class_def_node, 'class_interface_clause')
    print(f"interface_clause_node:{interface_clause_node}")
    if interface_clause_node:
        implements_nodes = [node.text.decode('utf-8') for node in interface_clause_node.children if node.type == 'name']
        class_info[ClassKeys.INTERFACES.value] = [
            {node.text.decode('utf-8'): None} for node in implements_nodes
        ]
        exit()
    # 获取类修饰符
    modifiers = []
    if class_def_node.child_by_field_name('abstract_modifier'):
        modifiers.append(PHPModifier.ABSTRACT.value)
    if class_def_node.child_by_field_name('final_modifier'):
        modifiers.append(PHPModifier.FINAL.value)
    class_info[ClassKeys.MODIFIERS.value] = modifiers

    # 获取类的可见性
    visibility_node = class_def_node.child_by_field_name('visibility_modifier')
    if visibility_node:
        class_info[ClassKeys.VISIBILITY.value] = visibility_node.text.decode('utf-8')

    # 获取类的起始和结束行号
    class_info[ClassKeys.START_LINE.value] = class_def_node.start_point[0] + 1  # 转换为 1-based 行号
    class_info[ClassKeys.END_LINE.value] = class_def_node.end_point[0] + 1  # 转换为 1-based 行号

    return class_info

# def parse_class_define_info(match_dict):
#     # 获取继承信息 并格式化为{"继承信息":"php文件"}  # TODO 继承信息没有验证  # TODO 添加继承类信息的PHP文件路径
#     class_extends = None
#     if 'extends' in match_dict:
#         # TODO 当前版本的 tree-sitter 的索引号都是0 需要合并多继承的情只能在最后面进行分析
#         class_extends = [match_dict['extends'][0].text.decode('utf-8')]
#         class_extends = [{x: None} for x in class_extends]
#
#     # 获取接口信息 # TODO 接口信息没有验证  # TODO 添加接口类信息的PHP文件路径
#     class_implements = None
#     if 'implements' in match_dict:
#         class_implements = [match_dict['implements'][0].text.decode('utf-8')]
#         class_implements = [{x: None} for x in class_implements]
#
#     # 获取类的修饰符
#     class_modifiers = []
#     if 'is_abstract_class' in match_dict and match_dict['is_abstract_class'][0]:
#         class_modifiers.append(PHPModifier.ABSTRACT.value)
#     if 'is_final_class' in match_dict and match_dict['is_final_class'][0]:
#         class_modifiers.append(PHPModifier.FINAL.value)
#
#     # 获取类的可见性
#     visibility = PHPVisibility.PUBLIC.value  # 默认可见性
#     if 'class_visibility' in match_dict and match_dict['class_visibility'][0]:
#         visibility = match_dict['class_visibility'][0].text.decode('utf-8')
#
#     # 获取类名信息
#     if 'class_name' in match_dict:
#         class_node = match_dict['class.def'][0]
#         class_name = match_dict['class_name'][0]
#
#         return {
#             ClassKeys.NAME.value: class_name.text.decode('utf-8'),
#             ClassKeys.NAMESPACE.value: None,
#             ClassKeys.VISIBILITY.value: visibility,
#             ClassKeys.MODIFIERS.value: class_modifiers,
#             ClassKeys.START_LINE.value: class_node.start_point[0],
#             ClassKeys.END_LINE.value: class_node.end_point[0],  # 使用类体的结束行号
#             ClassKeys.EXTENDS.value: class_extends,
#             ClassKeys.INTERFACES.value: class_implements,
#             ClassKeys.METHODS.value: [],
#             ClassKeys.PROPERTIES.value: [],
#             ClassKeys.IS_INTERFACE.value: False,
#         }
#     return None

def parse_interface_define_info(match_dict):
    # 获取继承信息 并格式化为{"继承信息":"php文件"}  # TODO 继承信息没有验证  # TODO 添加继承类信息的PHP文件路径
    class_extends = None
    if 'extends' in match_dict:
        class_extends = [match_dict['extends'][0].text.decode('utf-8')]
        class_extends = [{x: None} for x in class_extends]

    # 获取类名信息
    if 'interface_name' in match_dict:
        interface_node = match_dict['interface.def'][0]
        interface_name = match_dict['interface_name'][0]

        return {
            ClassKeys.NAME.value: interface_name.text.decode('utf-8'),
            ClassKeys.NAMESPACE.value: None,
            ClassKeys.START_LINE.value: interface_node.start_point[0],
            ClassKeys.END_LINE.value: interface_node.end_point[0],
            ClassKeys.EXTENDS.value: class_extends,
            ClassKeys.IS_INTERFACE.value: True,
        }
    return None

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

def process_class_property_info(match_dict):
    if not ('property_name' in match_dict):
        return None

    property_visibility = match_dict.get('property_visibility', [None])[0]
    visibility = property_visibility.text.decode('utf-8') if property_visibility else PHPVisibility.PUBLIC.value
    
    is_static = 'is_static' in match_dict and match_dict['is_static'][0] is not None
    is_readonly = 'is_readonly' in match_dict and match_dict['is_readonly'][0] is not None

    property_info = match_dict['property_name'][0]
    property_modifiers = []
    if is_static:
        property_modifiers.append(PHPModifier.STATIC.value)
    if is_readonly:
        property_modifiers.append(PHPModifier.READONLY.value)
    # 获取属性初始值
    property_value = match_dict['property_value'][0].text.decode('utf-8') if 'property_value' in match_dict else None
    current_property = {
        PropertyKeys.NAME.value: property_info.text.decode('utf-8'),
        PropertyKeys.LINE.value: property_info.start_point[0],
        PropertyKeys.VISIBILITY.value: visibility,
        PropertyKeys.MODIFIERS.value: property_modifiers,
        PropertyKeys.DEFAULT.value: property_value,
        PropertyKeys.TYPE.value: None,
    }

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


