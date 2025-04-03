from typing import List, Dict, Any

from init_tree_sitter import init_php_parser
from libs_com.file_io import read_file_bytes
from libs_com.utils_json import print_json
from tree_const import *
from tree_enums import MethodType, PHPVisibility, PHPModifier
from tree_func_info import get_file_funcs


def analyze_class_infos(tree, language) -> List[Dict[str, Any]]:
    """提取所有类定义信息"""
    # 获取所有本地函数名称
    file_functions = get_file_funcs(tree, language)

    class_infos = []
    class_info_query = language.query("""
        (class_declaration
            (visibility_modifier)? @class_visibility
            (abstract_modifier)? @is_abstract_class
            (final_modifier)? @is_final_class
            name: (name) @class_name
            (base_clause (name) @extends)? @base_clause
            body: (declaration_list) @class_body
        )
        
        (namespace_definition
            name: (namespace_name) @namespace_name
            body: (declaration_list)? @namespace_body
        )
        
        (method_declaration
            (visibility_modifier)? @method_visibility
            (static_modifier)? @is_static_method
            (abstract_modifier)? @is_abstract_method
            (final_modifier)? @is_final_method
            name: (name) @method_name
            parameters: (formal_parameters) @method_params
            return_type: (_)? @method_return_type
            body: (compound_statement) @method_body
        )

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
        )

        ; 修改函数调用匹配
        ((function_call_expression
            function: (name) @function_call
            arguments: (arguments) @function_args
        ) @function_call_expr
        (#not-eq? @function_call "echo"))

        ; 修改方法调用匹配
        (member_call_expression
            object: (_) @object
            name: (name) @method_call
            arguments: (arguments) @method_args
        ) @method_call_expr
        
        ; 修改 new 表达式匹配语法，不使用字段名而是直接匹配子节点
        (object_creation_expression
            (_) @new_class_name
            (arguments) @constructor_args
        )
    """)
    class_info_matches = class_info_query.matches(tree.root_node)

    # 修改函数调用解析部分
    current_class = None
    current_method = None
    current_namespace = None
    namespace_stack = []  # 添加命名空间栈
    
    for pattern_index, match_dict in class_info_matches:
        # 添加调试信息
        print("Pattern match type:", [key for key in match_dict.keys()])
        
        # 获取命名空间信息
        if 'namespace_name' in match_dict:
            current_namespace = match_dict['namespace_name'][0].text.decode('utf-8')
            print("Found namespace:", current_namespace)
            
            # 检查是否有命名空间体
            if 'namespace_body' in match_dict and match_dict['namespace_body'][0]:
                # 大括号语法
                namespace_stack.append(current_namespace)
            continue
            
        # 处理类信息时使用当前命名空间
        if 'class_name' in match_dict:
            # 如果命名空间栈非空，使用栈顶命名空间
            active_namespace = namespace_stack[-1] if namespace_stack else current_namespace
            current_class = process_class_interface_info(match_dict, active_namespace)
            if current_class:
                class_infos.append(current_class)
                print("Added class:", current_class[CLASS_NAME], "in namespace:", active_namespace)
        
        # 处理方法和属性
        if current_class:
            if 'method_name' in match_dict:
                process_method_info(match_dict, current_class, file_functions)
                print("Added method:", match_dict['method_name'][0].text.decode('utf-8'))
            
            if 'property_name' in match_dict:
                process_property_info(match_dict, current_class)
                print("Added property:", match_dict['property_name'][0].text.decode('utf-8'))
        
    return class_infos

def process_class_interface_info(match_dict, current_namespace):
    # 添加调试信息
    print("Processing class/interface info:", match_dict.keys())

    # 获取继承信息 并格式化为{"继承信息":"php文件"}  # TODO 继承信息没有验证  # TODO 添加继承类信息的PHP文件路径
    class_extends = match_dict['extends'][0].text.decode('utf-8') if 'extends' in match_dict else None
    class_extends = [{class_extends: None}] if class_extends else []

    # 获取接口信息 # TODO 接口信息没有验证  # TODO 添加接口类信息的PHP文件路径
    class_interface = match_dict['interface'][0].text.decode('utf-8') if 'interface' in match_dict else None
    class_interface = [{class_interface: None}] if class_interface else []

    if 'class_name' in match_dict:
        class_name = match_dict['class_name'][0]
        class_body = match_dict['class_body'][0]  # 获取类体节点
        # 获取类的可见性
        visibility = PHPVisibility.PUBLIC.value  # 默认可见性
        if 'class_visibility' in match_dict and match_dict['class_visibility'][0]:
            visibility = match_dict['class_visibility'][0].text.decode('utf-8')

        # 获取类的修饰符
        class_modifiers = []
        if 'is_abstract_class' in match_dict and match_dict['is_abstract_class'][0]:
            class_modifiers.append(PHPModifier.ABSTRACT.value)
        if 'is_final_class' in match_dict and match_dict['is_final_class'][0]:
            class_modifiers.append(PHPModifier.FINAL.value)

        return {
            CLASS_NAME: class_name.text.decode('utf-8'),
            CLASS_NAMESPACE: current_namespace if current_namespace else "",
            CLASS_VISIBILITY: visibility,
            CLASS_MODIFIERS: class_modifiers,
            CLASS_START_LINE: class_name.start_point[0] + 1,
            CLASS_END_LINE: class_body.end_point[0] + 1,  # 使用类体的结束行号
            CLASS_EXTENDS: class_extends,
            CLASS_INTERFACES: class_interface,
            CLASS_METHODS: [],
            CLASS_PROPERTIES: [],
        }

    elif 'interface_name' in match_dict:
        interface_info = match_dict['interface_name'][0]
        return {
            CLASS_NAME: interface_info.text.decode('utf-8'),
            CLASS_NAMESPACE: current_namespace,
            CLASS_VISIBILITY: 'public',
            CLASS_MODIFIERS: [PHPModifier.INTERFACE.value],
            CLASS_START_LINE: interface_info.start_point[0] + 1,
            CLASS_END_LINE: interface_info.end_point[0] + 1,
            CLASS_EXTENDS: class_extends,
            CLASS_INTERFACES: class_interface,
            CLASS_PROPERTIES: [],
            CLASS_METHODS: [],
        }

    return None

def process_method_info(match_dict, current_class, file_functions):
    if not (current_class and 'method_name' in match_dict):
        return
        
    method_info = match_dict['method_name'][0]
    method_body = match_dict['method_body'][0] if 'method_body' in match_dict else method_info
    method_name = method_info.text.decode('utf-8')
    
    # 获取返回类型
    return_type = None
    if 'method_return_type' in match_dict and match_dict['method_return_type'][0]:
        return_type_node = match_dict['method_return_type'][0]
        if return_type_node.type == 'qualified_name':
            return_type = return_type_node.text.decode('utf-8')
            if not return_type.startswith('\\'):
                return_type = '\\' + return_type
        elif return_type_node.type == 'nullable_type':
            for child in return_type_node.children:
                if child.type != '?':
                    base_type = child.text.decode('utf-8')
                    return_type = f"?{base_type}"
                    break
        else:
            return_type = return_type_node.text.decode('utf-8')
    
    # 获取方法可见性和修饰符
    visibility = PHPVisibility.PUBLIC.value
    if 'method_visibility' in match_dict and match_dict['method_visibility'][0]:
        visibility = match_dict['method_visibility'][0].text.decode('utf-8')

    method_modifiers = []
    if 'is_static_method' in match_dict and match_dict['is_static_method'][0]:
        method_modifiers.append(PHPModifier.STATIC.value)
    if 'is_abstract_method' in match_dict and match_dict['is_abstract_method'][0]:
        method_modifiers.append(PHPModifier.ABSTRACT.value)
    if 'is_final_method' in match_dict and match_dict['is_final_method'][0]:
        method_modifiers.append(PHPModifier.FINAL.value)
    
    # 获取方法参数（只处理一次）
    method_params = []
    if 'method_params' in match_dict and match_dict['method_params'][0]:
        params_node = match_dict['method_params'][0]
        print(f"Debug - Processing method parameters for {method_name}")
        print(f"Debug - Parameter node types: {[child.type for child in params_node.children]}")
        
        param_index = 0
        for child in params_node.children:
            if child.type == 'simple_parameter':
                param_info = process_parameter_node(child, current_class, param_index)  # 传入索引
                if param_info:
                    method_params.append(param_info)
                    print(f"Debug - Added parameter: {param_info}")
                    param_index += 1

    current_method = {
        METHOD_NAME: method_name,
        METHOD_TYPE: MethodType.CLASS_METHOD.value,
        METHOD_START_LINE: method_info.start_point[0] + 1,
        METHOD_END_LINE: method_body.end_point[0] + 1,
        METHOD_VISIBILITY: visibility,
        METHOD_MODIFIERS: method_modifiers,
        METHOD_OBJECT: current_class[CLASS_NAME],
        METHOD_FULL_NAME: f"{current_class[CLASS_NAME]}->{method_name}",
        METHOD_RETURN_TYPE: return_type,
        METHOD_RETURN_VALUE: return_type,
        METHOD_PARAMETERS: method_params,
        CALLED_METHODS: []
    }
    
    # 处理方法体中的函数调用
    if 'method_body' in match_dict:
        body_node = match_dict['method_body'][0]
        seen_called_functions = set()
        print(f"Debug - Processing method body for {current_method[METHOD_NAME]}")
        
        def traverse_method_body(node):
            process_method_body_node(node, seen_called_functions, file_functions, current_method, current_class)
            for child in node.children:
                traverse_method_body(child)
        
        traverse_method_body(body_node)
        print(f"Debug - Found {len(current_method[CALLED_METHODS])} called methods")
    
    current_class[CLASS_METHODS].append(current_method)

def process_property_info(match_dict, current_class):
    if not (current_class and 'property_name' in match_dict):
        return
        
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

    current_property = {
        PROPERTY_NAME: property_info.text.decode('utf-8'),
        PROPERTY_LINE: property_info.start_point[0] + 1,
        PROPERTY_TYPE: None,
        PROPERTY_VISIBILITY: visibility,
        PROPERTY_MODIFIERS: property_modifiers,
        PROPERTY_INITIAL_VALUE: None
    }

    if 'property_value' in match_dict and match_dict['property_value'][0]:
        property_value = match_dict['property_value'][0]
        print("Debug - Property value node:", {
            'type': property_value.type,
            'text': property_value.text.decode('utf-8'),
            'start_point': property_value.start_point,
            'end_point': property_value.end_point,
            'children_types': [child.type for child in property_value.children]
        })
        
        if property_value.type == 'integer':
            print("Debug - Processing integer value")
            current_property[PROPERTY_INITIAL_VALUE] = int(property_value.text.decode('utf-8'))
            current_property[PROPERTY_TYPE] = 'integer'
        elif property_value.type == 'string':
            print("Debug - Processing string value")
            value = property_value.text.decode('utf-8').strip('"\'')
            current_property[PROPERTY_INITIAL_VALUE] = value
            current_property[PROPERTY_TYPE] = 'string'
        elif property_value.type == 'float':
            print("Debug - Processing float value")
            current_property[PROPERTY_INITIAL_VALUE] = float(property_value.text.decode('utf-8'))
            current_property[PROPERTY_TYPE] = 'float'
        elif property_value.type == 'null':
            print("Debug - Processing null value")
            current_property[PROPERTY_INITIAL_VALUE] = None
            current_property[PROPERTY_TYPE] = 'null'
        elif property_value.type == 'boolean':
            print("Debug - Processing boolean value")
            value = property_value.text.decode('utf-8').lower()
            current_property[PROPERTY_INITIAL_VALUE] = value == 'true'
            current_property[PROPERTY_TYPE] = 'boolean'
        else:
            print("Debug - Processing unknown type:", property_value.type)
            current_property[PROPERTY_INITIAL_VALUE] = property_value.text.decode('utf-8')
            current_property[PROPERTY_TYPE] = property_value.type
    else:
        print("Debug - No property value found in match_dict")

    print("Debug - Final property:", current_property)
    current_class[CLASS_PROPERTIES].append(current_property)

def process_method_body_node(node, seen_called_functions, file_functions, current_method, current_class):
    # 首先处理当前节点
    if node.type == 'function_call_expression':
        func_node = node.child_by_field_name('function')
        if func_node:
            func_name = func_node.text.decode('utf-8')
            call_key = f"{func_name}:{node.start_point[0]}"
            if call_key not in seen_called_functions:
                seen_called_functions.add(call_key)
                # 修改函数类型判断逻辑
                func_type = MethodType.CUSTOM_METHOD.value
                if func_name in PHP_BUILTIN_FUNCTIONS:
                    func_type = MethodType.BUILTIN_METHOD.value
                elif func_name in file_functions:
                    func_type = MethodType.LOCAL_METHOD.value
                elif func_name.startswith('$'):
                    func_type = MethodType.DYNAMIC_METHOD.value

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
                                PARAMETER_NAME: param_name if param_name else f"$arg{param_index}",
                                PARAMETER_TYPE: None,
                                PARAMETER_DEFAULT: None,
                                PARAMETER_VALUE: arg_value,
                                PARAMETER_INDEX: param_index  # 添加参数索引
                            })
                            param_index += 1
                call_info = {
                    METHOD_NAME: func_name,
                    METHOD_START_LINE: node.start_point[0] + 1,
                    METHOD_END_LINE: node.end_point[0] + 1,
                    METHOD_OBJECT: None,  # 函数调用没有对象
                    METHOD_FULL_NAME: func_name,
                    METHOD_TYPE: func_type,
                    METHOD_MODIFIERS: [],
                    METHOD_RETURN_TYPE: None,
                    METHOD_RETURN_VALUE: None,
                    METHOD_PARAMETERS: call_params
                }
                current_method[CALLED_METHODS].append(call_info)

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
                            PARAMETER_NAME: arg_value,
                            PARAMETER_TYPE: None,
                            PARAMETER_DEFAULT: None,
                            PARAMETER_VALUE: arg_value,
                            PARAMETER_INDEX: param_index
                        })
                        param_index += 1
                    
            call_info = {
                METHOD_OBJECT: object_name,
                METHOD_NAME: method_name,
                METHOD_FULL_NAME: f"{object_name}->{method_name}",
                METHOD_START_LINE: name_node.start_point[0] + 1,
                METHOD_END_LINE: name_node.end_point[0] + 1,
                METHOD_TYPE: MethodType.CLASS_METHOD.value,
                METHOD_MODIFIERS: [],
                METHOD_RETURN_TYPE: None,
                METHOD_RETURN_VALUE: None,
                METHOD_PARAMETERS: call_params
            }
            current_method[CALLED_METHODS].append(call_info)


    elif node.type == 'object_creation_expression':
        print(f"Debug - Processing object creation at line {node.start_point[0] + 1}")
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
                    if current_class and current_class[CLASS_NAMESPACE]:
                        class_name = f"\\{current_class[CLASS_NAMESPACE]}\\{class_name}"
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
                                    for param in current_method[METHOD_PARAMETERS]:
                                        if param[PARAMETER_NAME] == arg_value:
                                            param_type = param[PARAMETER_TYPE]
                                            break
                                
                                constructor_params.append({
                                    PARAMETER_NAME: f"$arg{len(constructor_params)}",
                                    PARAMETER_TYPE: param_type,
                                    PARAMETER_DEFAULT: None,
                                    PARAMETER_VALUE: arg_value,
                                    PARAMETER_INDEX: param_index  # 添加参数索引
                                })
                                param_index += 1
                                print(f"Debug - Added constructor parameter: {constructor_params[-1]}")

                print(f"Debug - Creating constructor call info with {len(constructor_params)} parameters")
                call_info = {
                    METHOD_NAME: "__construct",
                    METHOD_START_LINE: node.start_point[0] + 1,
                    METHOD_END_LINE: node.end_point[0] + 1,
                    METHOD_OBJECT: class_name,
                    METHOD_FULL_NAME: f"{class_name}->__construct",
                    METHOD_TYPE: MethodType.CONSTRUCTOR.value,
                    METHOD_MODIFIERS: [],
                    METHOD_RETURN_TYPE: class_name,
                    METHOD_RETURN_VALUE: None,
                    METHOD_PARAMETERS: constructor_params
                }
                current_method[CALLED_METHODS].append(call_info)
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
    param_type = infer_parameter_type(param_node, current_class)
    
    if param_name:
        return {
            PARAMETER_NAME: param_name,
            PARAMETER_TYPE: param_type,
            PARAMETER_DEFAULT: param_default,
            PARAMETER_VALUE: param_value,
            PARAMETER_INDEX: param_index  # 添加参数索引
        }
    
    return None

def infer_parameter_type(param_node, current_class=None):
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
            elif not param_type.startswith('\\') and current_class and current_class[CLASS_NAMESPACE]:
                # 如果是类类型且没有命名空间，添加当前类的命名空间
                param_type = f"\\{current_class[CLASS_NAMESPACE]}\\{param_type}"
            return param_type
            
        # 处理可空类型
        elif child.type == 'nullable_type':
            for type_child in child.children:
                if type_child.type != '?':
                    base_type = type_child.text.decode('utf-8')
                    if not base_type.startswith('\\') and current_class and current_class[CLASS_NAMESPACE]:
                        base_type = f"\\{current_class[CLASS_NAMESPACE]}\\{base_type}"
                    return f"?{base_type}"
                    
        # 处理默认值
        elif child.type == 'default_value':
            # 获取值节点
            value_node = child.children[1] if len(child.children) > 1 else child.children[0]
            # # 根据默认值推断类型
            # 类型映射字典
            TYPE_MAPPING = {'string': 'string','integer': 'int', 'float': 'float', 'boolean': 'bool',
                            'array': 'array', 'null': 'mixed'}
            # 根据类型推断 param_type
            param_type = TYPE_MAPPING.get(value_node.type)
            # 如果是对象创建表达式
            if param_type is None and value_node.type == 'object_creation_expression':
                for new_child in value_node.children:
                    if new_child.type in ['qualified_name', 'name']:
                        class_name = new_child.text.decode('utf-8')
                        if not class_name.startswith('\\'):
                            if current_class and current_class[CLASS_NAMESPACE]:
                                class_name = f"\\{current_class[CLASS_NAMESPACE]}\\{class_name}"
                            else:
                                class_name = '\\' + class_name
                        param_type = class_name
                        break
            # 如果仍然没有匹配到类型，默认设置为 mixed
            param_type = param_type or 'mixed'
    return param_type or 'mixed'


if __name__ == '__main__':
    php_file = r"php_demo\multi_namespace.php"
    # php_file = r"php_demo\class.new.php"
    # php_file = r"php_demo\extends.php"
    # php_file = r"php_demo\interface.php"
    # php_file = r"php_demo\class.多参数.php"
    PARSER, LANGUAGE = init_php_parser()
    php_file_bytes = read_file_bytes(php_file)
    php_file_tree = PARSER.parse(php_file_bytes)
    # print(php_file_tree.root_node)
    classes = analyze_class_infos(php_file_tree, LANGUAGE)
    for class_info in classes:
        print("=" * 50)
        print_json(class_info)
        print("=" * 50)
