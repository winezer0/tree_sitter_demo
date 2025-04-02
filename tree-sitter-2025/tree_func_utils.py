from typing import Dict, List, Optional, Tuple
from libs_com.utils_json import print_json
from libs_com.file_io import read_file_bytes
from tree_const import *
from tree_func_info import process_parameters

def parse_php_file(parser, php_file: str):
    """解析PHP文件"""
    php_bytes = read_file_bytes(php_file)
    return parser.parse(php_bytes)

def get_function_by_line(php_file: str, parser, language, line_number: int) -> Optional[Dict]:
    """获取指定行号所在的函数信息"""
    tree = parse_php_file(parser, php_file)
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
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1

            if start_line <= line_number <= end_line:
                params_node = node.child_by_field_name('parameters')
                return {
                    METHOD_NAME: node.child_by_field_name('name').text.decode('utf-8'),
                    METHOD_START_LINE: start_line,
                    METHOD_END_LINE: end_line,
                    METHOD_PARAMETERS: process_parameters(params_node),
                    'code_line': line_number,
                }
    return None

def get_function_code(php_file: str, parser, language, function_name: str) -> Optional[Dict]:
    """获取指定函数名的代码内容"""
    tree = parse_php_file(parser, php_file)
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
                    METHOD_NAME: function_name,
                    METHOD_START_LINE: function_node.start_point[0] + 1,
                    METHOD_END_LINE: function_node.end_point[0] + 1,
                    'code': function_node.text.decode('utf-8'),
                }
    return None

def get_function_ranges(tree, language) -> List[Tuple[int, int]]:
    """获取所有函数的范围"""
    ranges = []
    query = language.query("(function_definition) @function")

    
    for match in query.matches(tree.root_node):
        if 'function' in match[1]:
            node = match[1]['function'][0]
            ranges.append((node.start_point[0], node.end_point[0]))
    return ranges

def get_not_in_func_code(php_file: str, parser, language) -> Dict:
    """获取所有不在函数内的PHP代码"""
    tree = parse_php_file(parser, php_file)
    function_ranges = get_function_ranges(tree, language)
    source_lines = tree.root_node.text.decode('utf-8').split('\n')
    
    non_function_code = []
    for line_num, line in enumerate(source_lines):
        if not any(start <= line_num <= end for start, end in function_ranges):
            non_function_code.append({
                'line_number': line_num + 1,
                'code': line
            })
            
    return {
        METHOD_START_LINE: non_function_code[0]['line_number'] if non_function_code else None,
        METHOD_END_LINE: non_function_code[-1]['line_number'] if non_function_code else None,
        'total_lines': len(non_function_code),
        'code_blocks': non_function_code,
    }

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