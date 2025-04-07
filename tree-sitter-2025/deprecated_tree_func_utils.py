from typing import Dict, Optional

from libs_com.file_io import read_file_bytes
from libs_com.utils_json import print_json
from tree_enums import MethodKeys
from tree_func_info_check import parse_node_params_info, query_general_methods_define_infos


def read_file_to_parse(parser, php_file: str):
    """解析PHP文件"""
    php_bytes = read_file_bytes(php_file)
    return parser.parse(php_bytes)

def get_function_by_line(php_file: str, parser, language, line_number: int) -> Optional[Dict]:
    """获取指定行号所在的函数信息"""
    tree = read_file_to_parse(parser, php_file)
    query = language.query("""
        (function_definition
            name: (name) @function_name
            parameters: (formal_parameters) @params
            body: (compound_statement) @body
        ) @function
    """)

    for match in query.matches(tree.root_node):
        if 'function' in match[1]:
            node = match[1]['function'][0]
            start_line = node.start_point[0]
            end_line = node.end_point[0]

            if start_line <= line_number <= end_line:
                params_node = node.child_by_field_name('parameters')
                return {
                    MethodKeys.NAME.value: node.child_by_field_name('name').text.decode('utf-8'),
                    MethodKeys.START_LINE.value: start_line,
                    MethodKeys.END_LINE.value: end_line,
                    MethodKeys.PARAMS.value: parse_node_params_info(params_node),
                    'code_line': line_number,
                }
    return None

def get_function_code(php_file: str, parser, language, function_name: str) -> Optional[Dict]:
    """获取指定函数名的代码内容"""
    tree = read_file_to_parse(parser, php_file)
    query = language.query("""
        (function_definition
            name: (name) @function_name
            body: (compound_statement) @body
        ) @function
    """)

    for match in query.matches(tree.root_node):
        if 'function_name' in match[1]:
            node = match[1]['function_name'][0]
            if node.text.decode('utf-8') == function_name:
                function_node = node.parent
                return {
                    MethodKeys.NAME.value: function_name,
                    MethodKeys.START_LINE.value: function_node.start_point[0],
                    MethodKeys.END_LINE.value: function_node.end_point[0],
                    'code': function_node.text.decode('utf-8'),
                }
    return None

def get_not_in_func_code(php_file: str, parser, language) -> Dict:
    """获取所有不在函数内的PHP代码"""
    tree = read_file_to_parse(parser, php_file)
    function_names, function_ranges = query_general_methods_define_infos(tree, language)
    source_lines = tree.root_node.text.decode('utf-8').split('\n')
    
    non_function_code = []
    for line_num, line in enumerate(source_lines):
        if not any(start <= line_num <= end for start, end in function_ranges):
            non_function_code.append({
                'line_number': line_num,
                'code': line
            })
            
    return {
        MethodKeys.START_LINE.value: non_function_code[0]['line_number'] if non_function_code else None,
        MethodKeys.END_LINE.value: non_function_code[-1]['line_number'] if non_function_code else None,
        'total_lines': len(non_function_code),
        'code_blocks': non_function_code,
    }



def guess_method_is_static(object_name, classes_names, source_code):
    """判断方法是不是静态方法 目前已弃用,可以直接查询静态调用预计"""
    # method_code = method_node.text.decode('utf-8')
    # 如果在对象名在本地的类名内部,说明就是本地类直接静态调用的
    if object_name in classes_names:
        return True
    # 如果是通过::进行调用的,说明也是静态调用的
    if source_code and f"{object_name}::" in source_code:
        return True
    return False


if __name__ == '__main__':
    from init_tree_sitter import init_php_parser

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/function_none.php"

    # 测试各个功能
    print("=== 通过行号获取函数 ===")
    result = get_function_by_line(php_file, PARSER, LANGUAGE, 5)
    print_json(result)

    print("\n=== 通过函数名获取代码 ===")
    result = get_function_code(php_file, PARSER, LANGUAGE, "back_action")
    print_json(result)

    print("\n=== 获取非函数代码 ===")
    result = get_not_in_func_code(php_file, PARSER, LANGUAGE)
    print_json(result)
