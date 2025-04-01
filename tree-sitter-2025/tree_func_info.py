from logging import NOTSET

from libs_com.utils_json import print_json
from tree_const import *


# 修改函数类型判断逻辑
def analyze_direct_method_infos(tree, language):
    """获取所有函数信息，包括函数内部和非函数部分"""
    # 首先定义所有需要的查询

    class_ranges = get_class_ranges(language, tree)

    file_funcs_calls, in_funcs_info, in_funcs_ranges = query_functions_info(tree, language, class_ranges)

    # 获取文件级函数调用
    if has_non_func_content(tree, class_ranges, in_funcs_ranges):
        # 获取非函数部分的调用
        non_funcs_calls = [call for call in _get_function_calls(tree.root_node, language, file_funcs_calls)
                            if not any(start <= call[FUNC_START_LINE] <= end for start, end in in_funcs_ranges)
                            and not any(start <= call[FUNC_START_LINE] <= end for start, end in class_ranges)
        ]

        # 获取文件级调用并去重
        file_level_calls = get_file_level_calls(tree, language, file_funcs_calls, non_funcs_calls)

        # 合并所有文件级调用到 non_functions，确保不重复
        file_level_calls = [call for call in file_level_calls if (call[FUNC_NAME], call[FUNC_START_LINE]) not in {(c[FUNC_NAME], c[FUNC_START_LINE]) for c in non_funcs_calls}]
        non_func_all_calls = non_funcs_calls + file_level_calls
        if non_func_all_calls:  # 只在有函数调用时添加

            non_function_info = {
                FUNC_NAME: NOT_IN_FUNCS,
                FUNC_PARAMS: [],
                FUNC_RETURN_TYPE: None,
                FUNC_START_LINE: tree.root_node.start_point[0] + 1,
                FUNC_END_LINE: tree.root_node.end_point[0] + 1,
                CALLED_FUNCTIONS: non_func_all_calls
            }
            in_funcs_info.append(non_function_info)

    return in_funcs_info


def query_functions_info(tree, language, class_ranges):
    # 获取函数定义
    function_query = language.query("""
        (function_definition
            name: (name) @function.name
            parameters: (formal_parameters
                (simple_parameter
                    name: (variable_name) @param.name
                    type: (_)? @param.type
                    default_value: (_)? @param.default
                )*
            ) @function.params
            body: (compound_statement) @function.body
        ) @function.def
    """)
    # 获取所有函数名称
    file_function_calls = set()
    # 获取函数信息
    functions_info = []
    function_ranges = []
    matches = function_query.matches(tree.root_node)
    for _, match_dict in matches:
        if 'function.name' in match_dict:
            name_node = match_dict['function.name'][0]
            if name_node:
                file_function_calls.add(name_node.text.decode('utf8'))

    for _, match_dict in matches:
        if 'function.def' in match_dict:
            function_node = match_dict['function.def'][0]
            # 检查函数是否在类定义范围内
            func_start = function_node.start_point[0] + 1
            func_end = function_node.end_point[0] + 1

            # 如果函数不在任何类的范围内，才添加到函数列表中
            if not any(class_start <= func_start <= class_end for class_start, class_end in class_ranges):
                name_node = match_dict.get('function.name', [None])[0]
                params_node = match_dict.get('function.params', [None])[0]
                body_node = match_dict.get('function.body', [None])[0]

                current_function = {
                    FUNC_NAME: name_node.text.decode('utf8') if name_node else '',
                    FUNC_START_LINE: func_start,
                    FUNC_END_LINE: func_end,
                    FUNC_PARAMS: _parse_parameters(params_node) if params_node else [],
                    CALLED_FUNCTIONS: _get_function_calls(body_node, language, file_function_calls) if body_node else []
                }
                functions_info.append(current_function)
                function_ranges.append((func_start, func_end))
    return file_function_calls, functions_info, function_ranges


def get_file_level_calls(tree, language, file_functions, non_function_calls):
    # 获取文件级调用
    file_level_query = language.query("""
            (program
                (expression_statement
                    [(function_call_expression
                        function: (name) @function_name
                        arguments: (arguments) @function_args
                    )
                    (object_creation_expression
                        (name) @class_name
                    )
                    (member_call_expression
                        object: (_) @object
                        name: (name) @method_name
                    )
                    (scoped_call_expression
                        scope: (name) @class_scope
                        name: (name) @static_method_name
                    )
                    (binary_expression
                        (function_call_expression
                            function: (name) @concat_func_name
                        )
                    )]
                )
            )
        """)

    seen_calls = {(call[FUNC_NAME], call[FUNC_START_LINE]) for call in non_function_calls}

    file_level_calls = []
    file_level_query_matches = file_level_query.matches(tree.root_node)
    for match in file_level_query_matches:
        if 'function_name' in match[1] or 'concat_func_name' in match[1]:
            func_node = match[1].get('function_name', [None])[0] or match[1]['concat_func_name'][0]
            func_name = func_node.text.decode('utf8')
            start_line_num = func_node.start_point[0] + 1

            # 检查是否已经记录过这个调用
            if (func_name, start_line_num) not in seen_calls:
                func_type = CUSTOM_METHOD
                if func_name in file_functions:
                    func_type = LOCAL_METHOD
                elif func_name in PHP_BUILTIN_FUNCTIONS:
                    func_type = BUILTIN_METHOD
                elif func_name.startswith('$'):
                    func_type = DYNAMIC_METHOD  # 动态函数调用

                if func_type != BUILTIN_METHOD:
                    called_func_info = {
                        FUNC_NAME: func_name,
                        FUNC_START_LINE: start_line_num,
                        FUNC_TYPE: func_type,
                    }

                    file_level_calls.append(called_func_info)
                    seen_calls.add((func_name, start_line_num))
        elif 'class_name' in match[1]:
            class_node = match[1]['class_name'][0]
            file_level_calls.append({
                FUNC_START_LINE: class_node.start_point[0] + 1,
                FUNC_NAME: f"new {class_node.text.decode('utf8')}",
                FUNC_TYPE: CONSTRUCTOR,
            })
        elif 'method_name' in match[1]:
            object_node = match[1]['object'][0]
            method_node = match[1]['method_name'][0]
            file_level_calls.append({
                FUNC_START_LINE: method_node.start_point[0] + 1,
                FUNC_NAME: f"{object_node.text.decode('utf8')}->{method_node.text.decode('utf8')}",
                FUNC_TYPE: OBJECT_METHOD,

            })
        elif 'static_method_name' in match[1]:
            class_node = match[1]['class_scope'][0]
            method_node = match[1]['static_method_name'][0]
            file_level_calls.append({
                FUNC_START_LINE: method_node.start_point[0] + 1,
                FUNC_NAME: f"{class_node.text.decode('utf8')}::{method_node.text.decode('utf8')}",
                FUNC_TYPE: STATIC_METHOD,
            })
    return file_level_calls


def has_non_func_content(tree, class_ranges, function_ranges):
    root_start = tree.root_node.start_point[0] + 1
    root_end = tree.root_node.end_point[0] + 1
    has_non_function_content = False
    for i in range(root_start, root_end + 1):
        if (not any(start <= i <= end for start, end in function_ranges) and
                not any(start <= i <= end for start, end in class_ranges)):
            has_non_function_content = True
            break
    return has_non_function_content


def get_class_ranges(language, tree):
    """获取所有类定义的范围"""
    class_query = language.query("""
        (class_declaration) @class.def
    """)
    class_ranges = []
    for match in class_query.matches(tree.root_node):
        class_node = match[1]['class.def'][0]
        class_ranges.append((
            class_node.start_point[0] + 1,
            class_node.end_point[0] + 1
        ))
    return class_ranges


def _parse_parameters(params_node):
    """解析函数参数"""
    parameters = []
    if not params_node:
        return parameters

    # 遍历所有参数节点
    for child in params_node.children:
        if child.type == 'simple_parameter':
            param = {}
            # 获取参数名
            for sub_child in child.children:

                if sub_child.type == 'variable_name':
                    param[PARAM_NAME] = sub_child.text.decode('utf8')
                elif sub_child.type == 'null':
                    param[PARAM_VALUE_DEFAULT] = 'null'
                elif sub_child.type == 'string':
                    # 去掉字符串两端的引号
                    default_value = sub_child.text.decode('utf8')
                    param[PARAM_VALUE_DEFAULT] = default_value.strip('\'\"')
            if param:
                parameters.append(param)

    return parameters


def _get_function_calls(body_node, language, file_functions):
    """获取函数体内的函数调用信息"""
    if not body_node:
        return []

    query = language.query("""
        [
            (function_call_expression 
                function: (name) @func_name
            ) @func_call
            
            (object_creation_expression
                (name) @class_name
            ) @new_object
            
            (member_call_expression
                object: (variable_name) @obj_name
                name: (name) @method_name
            ) @method_call
            
            (scoped_call_expression
                scope: (name) @class_scope
                name: (name) @static_method_name
            ) @static_call
        ]
    """)

    called_functions = []
    seen = set()  # 修改为使用 (name, line) 元组作为唯一标识
    matches = query.matches(body_node)

    for _, match_dict in matches:
        # 处理普通函数调用
        if 'func_name' in match_dict:
            node = match_dict['func_name'][0]
            func_name = node.text.decode('utf-8')
            line_num = node.start_point[0] + 1
            call_id = (func_name, line_num)  # 新增：使用函数名和行号组合作为唯一标识
            
            if call_id not in seen:  # 修改：使用新的唯一标识判断
                func_type = CUSTOM_METHOD
                if func_name in file_functions:
                    func_type = LOCAL_METHOD
                elif func_name in PHP_BUILTIN_FUNCTIONS:
                    func_type = BUILTIN_METHOD
                elif func_name.startswith('$'):
                    func_type = DYNAMIC_METHOD  # 动态函数调用

                # 排除内置函数
                if func_type != BUILTIN_METHOD:
                    called_func_info = {
                        FUNC_START_LINE: line_num,
                        FUNC_NAME: func_name,
                        FUNC_TYPE: func_type,
                    }

                    called_functions.append(called_func_info)
                    seen.add(call_id)  # 修改：记录新的唯一标识

        # 处理对象创建
        elif 'class_name' in match_dict:
            node = match_dict['class_name'][0]
            class_name = node.text.decode('utf-8')
            line_num = node.start_point[0] + 1
            full_name = f"new {class_name}"
            call_id = (full_name, line_num)  # 新增：使用完整名称和行号组合
            
            if call_id not in seen:  # 修改：使用新的唯一标识判断
                called_functions.append({
                    FUNC_START_LINE: line_num,
                    FUNC_NAME: full_name,
                    FUNC_TYPE: CONSTRUCTOR,
                })
                seen.add(call_id)
        
        # 处理方法调用
        elif 'method_name' in match_dict and 'obj_name' in match_dict:
            obj_node = match_dict['obj_name'][0]
            method_node = match_dict['method_name'][0]
            full_name = f"{obj_node.text.decode('utf-8')}->{method_node.text.decode('utf-8')}"
            line_num = method_node.start_point[0] + 1
            call_id = (full_name, line_num)  # 添加行号到唯一标识
            
            if call_id not in seen:  # 使用新的唯一标识判断
                called_functions.append({
                    FUNC_START_LINE: line_num,
                    FUNC_NAME: full_name,
                    FUNC_TYPE: OBJECT_METHOD,
                })
                seen.add(call_id)
            
            # 处理静态方法调用
            elif 'static_method_name' in match_dict:
                class_node = match_dict['class_scope'][0]
                method_node = match_dict['static_method_name'][0]
                full_name = f"{class_node.text.decode('utf-8')}::{method_node.text.decode('utf-8')}"
                line_num = method_node.start_point[0] + 1
                call_id = (full_name, line_num)  # 添加行号到唯一标识
                
                if call_id not in seen:  # 使用新的唯一标识判断
                    called_functions.append({
                        FUNC_START_LINE: line_num,
                        FUNC_NAME: full_name,
                        FUNC_TYPE: STATIC_METHOD,
                    })
                    seen.add(call_id)

    return called_functions


if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.file_io import read_file_bytes


    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/function_none.php"
    php_file_bytes = read_file_bytes(php_file)
    print(f"read_file_bytes:->{php_file}")
    php_file_tree = PARSER.parse(php_file_bytes)
    code = analyze_direct_method_infos(php_file_tree, LANGUAGE)
    print_json(code)