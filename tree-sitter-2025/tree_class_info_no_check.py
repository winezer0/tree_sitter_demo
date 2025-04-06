from tree_sitter import Language, Parser

from tree_const import PHP_BUILTIN_FUNCTIONS
from tree_enums import MethodKeys, ParameterKeys, MethodType, ClassKeys

TREE_SITTER_CLASS_INFO_QUERY = """
    ;匹配命名空间定义信息
    (namespace_definition
        name: (namespace_name) @namespace_name
        body: (declaration_list)? @namespace_body
    ) @namespace.def

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

    ; 查询函数调用匹配
    (function_call_expression
        function: (name) @function_call
        arguments: (arguments) @function_args
    ) @function_call_expr

    ; 查询对象方法调用
    (member_call_expression
        object: (_) @object
        name: (name) @method_call
        arguments: (arguments) @method_args
    ) @member_call_expr

    ; 查询 new 表达式匹配语法
    (object_creation_expression
        (name) @new_class_name
        (arguments) @constructor_args
    )@new_class_expr
"""



def parse_method_body_node(node, seen_called_functions, file_functions, current_method, current_class):
    # 首先处理当前节点
    if node.type == 'function_call_expression':
        func_node = node.child_by_field_name('function')
        if func_node:
            func_name = func_node.text.decode('utf-8')
            call_key = f"{func_name}:{node.start_point[0]}"
            if call_key not in seen_called_functions:
                seen_called_functions.add(call_key)
                # 修改函数类型判断逻辑
                func_type = MethodType.GENERAL.value
                if func_name in PHP_BUILTIN_FUNCTIONS:
                    func_type = MethodType.BUILTIN.value
                elif func_name in file_functions:
                    func_type = MethodType.IS_NATIVE.value
                elif func_name.startswith('$'):
                    func_type = MethodType.DYNAMIC.value

                # 处理参数
                args_node = node.child_by_field_name('arguments')
                call_params = []
                if args_node:
                    param_index = 0
                    for arg in args_node.children:
                        # 跳过括号和逗号
                        if arg.type not in [',', '(', ')']:
                            arg_value = arg.text.decode('utf-8')
                            # 检查是否有显式的参数名指定
                            param_name = None
                            if arg.type == 'named_argument':
                                name_node = arg.child_by_field_name('name')
                                if name_node:
                                    param_name = name_node.text.decode('utf-8')
                                value_node = arg.child_by_field_name('value')
                                if value_node:
                                    arg_value = value_node.text.decode('utf-8')

                            # 处理参数值，去掉字符串的引号
                            if arg_value.startswith('"') and arg_value.endswith('"'):
                                arg_value = arg_value[1:-1]
                            elif arg_value.startswith("'") and arg_value.endswith("'"):
                                arg_value = arg_value[1:-1]

                            call_params.append({
                                ParameterKeys.PARAM_NAME.value: param_name if param_name else f"$arg{param_index}",
                                ParameterKeys.PARAM_TYPE.value: None,
                                ParameterKeys.PARAM_DEFAULT.value: None,
                                ParameterKeys.PARAM_VALUE.value: arg_value,
                                ParameterKeys.PARAM_INDEX.value: param_index  # 添加参数索引
                            })
                            param_index += 1
                call_info = {
                    MethodKeys.NAME.value: func_name,
                    MethodKeys.START_LINE.value: node.start_point[0],
                    MethodKeys.END_LINE.value: node.end_point[0],
                    MethodKeys.OBJECT.value: None,  # 函数调用没有对象
                    MethodKeys.FULLNAME.value: func_name,
                    MethodKeys.METHOD_TYPE.value: func_type,
                    MethodKeys.MODIFIERS.value: [],
                    MethodKeys.RETURN_TYPE.value: None,
                    MethodKeys.RETURN_VALUE.value: None,
                    MethodKeys.PARAMS.value: call_params
                }
                current_method[MethodKeys.CALLED.value].append(call_info)

    elif node.type == 'member_call_expression':
        object_node = node.child_by_field_name('object')
        name_node = node.child_by_field_name('name')
        if object_node and name_node:
            object_name = object_node.text.decode('utf-8')
            method_name = name_node.text.decode('utf-8')

            # 处理参数
            args_node = node.child_by_field_name('arguments')
            call_params = []
            if args_node:
                param_index = 0
                for arg in args_node.children:
                    # 跳过括号和逗号
                    if arg.type not in [',', '(', ')']:
                        arg_value = arg.text.decode('utf-8')
                        call_params.append({
                            ParameterKeys.PARAM_NAME.value: arg_value,
                            ParameterKeys.PARAM_TYPE.value: None,
                            ParameterKeys.PARAM_DEFAULT.value: None,
                            ParameterKeys.PARAM_VALUE.value: arg_value,
                            ParameterKeys.PARAM_INDEX.value: param_index
                        })
                        param_index += 1

            call_info = {
                MethodKeys.OBJECT.value: object_name,
                MethodKeys.NAME.value: method_name,
                MethodKeys.FULLNAME.value: f"{object_name}->{method_name}",
                MethodKeys.START_LINE.value: name_node.start_point[0],
                MethodKeys.END_LINE.value: name_node.end_point[0],
                MethodKeys.METHOD_TYPE.value: MethodType.CLASS.value,
                MethodKeys.MODIFIERS.value: [],
                MethodKeys.RETURN_TYPE.value: None,
                MethodKeys.RETURN_VALUE.value: None,
                MethodKeys.PARAMS.value: call_params
            }
            current_method[MethodKeys.CALLED.value].append(call_info)


    elif node.type == 'object_creation_expression':
        print(f"Debug - Processing object creation at line {node.start_point[0]}")
        call_key = f"new_{node.start_point[0]}"
        if call_key not in seen_called_functions:
            seen_called_functions.add(call_key)

            # 获取类名节点
            class_name_node = None
            for child in node.children:
                if child.type in ['qualified_name', 'name']:
                    class_name_node = child
                    break

            if class_name_node:
                class_name = class_name_node.text.decode('utf-8')
                print(f"Debug - Found class name: {class_name}")

                # 处理命名空间
                if not class_name.startswith('\\'):
                    if current_class and current_class[ClassKeys.NAMESPACE.value]:
                        class_name = f"\\{current_class[ClassKeys.NAMESPACE.value]}\\{class_name}"
                    else:
                        class_name = '\\' + class_name
                print(f"Debug - Normalized class name: {class_name}")

                # 处理构造函数参数
                constructor_params = []
                param_index = 0
                for child in node.children:
                    if child.type == 'arguments':
                        print(f"Debug - Processing constructor arguments")
                        for arg in child.children:
                            if arg.type not in ['(', ')', ',']:
                                print(f"Debug - Processing argument: {arg.type} - {arg.text.decode('utf-8')}")
                                arg_value = arg.text.decode('utf-8')
                                param_type = 'mixed'

                                # 根据参数类型设置类型信息
                                if arg.type == 'string':
                                    param_type = 'string'
                                    arg_value = arg_value.strip('"\'')
                                elif arg.type == 'integer':
                                    param_type = 'int'
                                elif arg.type == 'variable_name':
                                    # 尝试从当前方法的参数中获取类型
                                    for param in current_method[MethodKeys.PARAMS.value]:
                                        if param[ParameterKeys.PARAM_NAME.value] == arg_value:
                                            param_type = param[ParameterKeys.PARAM_TYPE.value]
                                            break

                                constructor_params.append({
                                    ParameterKeys.PARAM_NAME.value: f"$arg{len(constructor_params)}",
                                    ParameterKeys.PARAM_TYPE.value: param_type,
                                    ParameterKeys.PARAM_DEFAULT.value: None,
                                    ParameterKeys.PARAM_VALUE.value: arg_value,
                                    ParameterKeys.PARAM_INDEX.value: param_index  # 添加参数索引
                                })
                                param_index += 1
                                print(f"Debug - Added constructor parameter: {constructor_params[-1]}")

                print(f"Debug - Creating constructor call info with {len(constructor_params)} parameters")
                call_info = {
                    MethodKeys.NAME.value: "__construct",
                    MethodKeys.START_LINE.value: node.start_point[0],
                    MethodKeys.END_LINE.value: node.end_point[0],
                    MethodKeys.OBJECT.value: class_name,
                    MethodKeys.FULLNAME.value: f"{class_name}->__construct",
                    MethodKeys.METHOD_TYPE.value: MethodType.CONSTRUCT.value,
                    MethodKeys.MODIFIERS.value: [],
                    MethodKeys.RETURN_TYPE.value: class_name,
                    MethodKeys.RETURN_VALUE.value: None,
                    MethodKeys.PARAMS.value: constructor_params
                }
                current_method[MethodKeys.CALLED.value].append(call_info)
                print(f"Debug - Added constructor call with parameters: {constructor_params}")


def process_parameter_node(param_node, current_class=None, param_index=0):
    """处理参数节点，提取完整的参数信息"""
    param_name = None
    param_default = None
    param_value = None

    print(f"Debug - Processing parameter node: {param_node.type}")
    print(f"Debug - Parameter children types: {[child.type for child in param_node.children]}")

    for child in param_node.children:
        if child.type == 'variable_name':
            param_name = child.text.decode('utf-8')
        elif child.type == 'default_value':
            value_node = child.children[1] if len(child.children) > 1 else child.children[0]
            param_default = value_node.text.decode('utf-8')
            param_value = param_default

    # 使用新的类型推断函数
    param_type = guess_parameter_type(param_node, current_class)

    if param_name:
        return {
            ParameterKeys.PARAM_NAME.value: param_name,
            ParameterKeys.PARAM_TYPE.value: param_type,
            ParameterKeys.PARAM_DEFAULT.value: param_default,
            ParameterKeys.PARAM_VALUE.value: param_value,
            ParameterKeys.PARAM_INDEX.value: param_index  # 添加参数索引
        }

    return None


def guess_parameter_type(param_node, current_class=None):
    """
    推断参数类型
    param_node: 参数节点
    current_class: 当前类的信息
    """
    param_type = None

    # 遍历参数节点的子节点
    for child in param_node.children:
        # 处理显式类型声明
        if child.type in ['primitive_type', 'name', 'qualified_name']:
            param_type = child.text.decode('utf-8')
            # 处理完整的命名空间
            if not param_type.startswith('\\') and '\\' in param_type:
                param_type = '\\' + param_type
            elif not param_type.startswith('\\') and current_class and current_class[ClassKeys.NAMESPACE.value]:
                # 如果是类类型且没有命名空间，添加当前类的命名空间
                param_type = f"\\{current_class[ClassKeys.NAMESPACE.value]}\\{param_type}"
            return param_type

        # 处理可空类型
        elif child.type == 'nullable_type':
            for type_child in child.children:
                if type_child.type != '?':
                    base_type = type_child.text.decode('utf-8')
                    if not base_type.startswith('\\') and current_class and current_class[ClassKeys.NAMESPACE.value]:
                        base_type = f"\\{current_class[ClassKeys.NAMESPACE.value]}\\{base_type}"
                    return f"?{base_type}"

        # 处理默认值
        elif child.type == 'default_value':
            # 获取值节点
            value_node = child.children[1] if len(child.children) > 1 else child.children[0]
            # # 根据默认值推断类型
            # 类型映射字典
            TYPE_MAPPING = {'string': 'string', 'integer': 'int', 'float': 'float', 'boolean': 'bool',
                            'array': 'array', 'null': 'mixed'}
            # 根据类型推断 param_type
            param_type = TYPE_MAPPING.get(value_node.type)
            # 如果是对象创建表达式
            if param_type is None and value_node.type == 'object_creation_expression':
                for new_child in value_node.children:
                    if new_child.type in ['qualified_name', 'name']:
                        class_name = new_child.text.decode('utf-8')
                        if not class_name.startswith('\\'):
                            if current_class and current_class[ClassKeys.NAMESPACE.value]:
                                class_name = f"\\{current_class[ClassKeys.NAMESPACE.value]}\\{class_name}"
                            else:
                                class_name = '\\' + class_name
                        param_type = class_name
                        break
            # 如果仍然没有匹配到类型，默认设置为 mixed
            param_type = param_type or 'mixed'
    return param_type or 'mixed'



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

# def parse_interface_define_info(match_dict):
#     # 获取继承信息 并格式化为{"继承信息":"php文件"}  # TODO 继承信息没有验证  # TODO 添加继承类信息的PHP文件路径
#     class_extends = None
#     if 'extends' in match_dict:
#         class_extends = [match_dict['extends'][0].text.decode('utf-8')]
#         class_extends = [{x: None} for x in class_extends]
#
#     # 获取类名信息
#     if 'interface_name' in match_dict:
#         interface_node = match_dict['interface.def'][0]
#         interface_name = match_dict['interface_name'][0]
#
#         return {
#             ClassKeys.NAME.value: interface_name.text.decode('utf-8'),
#             ClassKeys.NAMESPACE.value: None,
#             ClassKeys.START_LINE.value: interface_node.start_point[0],
#             ClassKeys.END_LINE.value: interface_node.end_point[0],
#             ClassKeys.EXTENDS.value: class_extends,
#             ClassKeys.IS_INTERFACE.value: True,
#         }
#     return None

if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.utils_json import print_json

    PARSER, LANGUAGE = init_php_parser()

    # 示例 PHP 代码
    php_code = """
    <?php
    class MyClass implements MyInterface {
    }
    """
    # 解析代码并打印语法树
    tree = PARSER.parse(bytes(php_code, "utf8"))
    root_node = tree.root_node
    print(root_node)
