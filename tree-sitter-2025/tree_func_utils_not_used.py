from typing import Optional, Dict

from tree_class_info import parse_method_parameters
from tree_enums import MethodKeys
from tree_func_utils import query_global_methods_define_infos
from tree_sitter_uitls import get_node_filed_text, get_node_text


def get_global_method_name_by_line(language, root_node, line_number: int) -> Optional[Dict]:
    """获取指定行号所在的函数信息"""
    query = language.query("""
        (function_definition
            ;name: (name) @function_name
            ;parameters: (formal_parameters) @params
            ;body: (compound_statement) @body
        ) @function.def
    """)

    for match in query.matches(root_node):
        match_dict = match[1]
        if 'function.def' in match_dict:
            method_node = match_dict['function.def'][0]
            start_line = method_node.start_point[0]
            end_line = method_node.end_point[0]

            if start_line <= line_number <= end_line:
                return {
                    MethodKeys.NAME.value: get_node_filed_text(method_node, 'name'),
                    MethodKeys.START_LINE.value: start_line,
                    MethodKeys.END_LINE.value: end_line,
                    MethodKeys.PARAMS.value: parse_method_parameters(method_node),
                    'code_line': line_number,
                }
    return None


def get_global_method_content(language, root_node, function_name: str) -> Optional[Dict]:
    """获取指定函数名的代码内容
    :param root_node:
    """
    query = language.query("""
        (function_definition
            name: (name) @function_name
            ;body: (compound_statement) @body
        ) 
    """)

    for match in query.matches(root_node):
        match_dict = match[1]
        if 'function_name' in match_dict:
            func_name_node = match_dict['function_name'][0]
            func_name_text = get_node_filed_text(func_name_node, 'name')
            if func_name_text == function_name:
                func_def_node = func_name_node.parent
                return {
                    MethodKeys.NAME.value: function_name,
                    MethodKeys.START_LINE.value: func_def_node.start_point[0],
                    MethodKeys.END_LINE.value: func_def_node.end_point[0],
                    'func_code': func_def_node.text.decode('utf-8'),
                }
    return None


def get_global_code(language, root_node) -> Dict:
    """获取所有不在全局函数内的PHP代码 TODO 可能存在问题 没有排除类范围"""
    # 获取所有全局函数定义信息
    function_names, function_ranges = query_global_methods_define_infos(language, root_node)
    source_lines = get_node_text(root_node).split('\n')
    non_function_code = []
    for line_num, line_text in enumerate(source_lines):
        if not any(start <= line_num <= end for start, end in function_ranges):
            non_function_code.append({
                'line': line_num,
                'code': line_text
            })

    return {
        MethodKeys.START_LINE.value: non_function_code[0]['line'] if non_function_code else None,
        MethodKeys.END_LINE.value: non_function_code[-1]['line'] if non_function_code else None,
        'total_lines': len(non_function_code),
        'code_blocks': non_function_code,
    }
