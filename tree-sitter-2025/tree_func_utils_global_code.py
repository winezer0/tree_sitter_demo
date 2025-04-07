from typing import Dict

from tree_enums import MethodKeys
from tree_func_utils import query_global_methods_define_infos
from tree_sitter_uitls import get_node_text


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
