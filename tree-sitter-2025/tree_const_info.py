from typing import List, Dict, Any
from init_tree_sitter import init_php_parser
from libs_com.file_io import read_file_bytes
from libs_com.utils_json import print_json


def format_value(value: str) -> Any:
    """格式化常量值"""
    if not value:
        return None
        
    # 处理布尔值
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    
    # 处理数字
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    
    # 处理字符串（去除引号）
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    
    return value

def analyze_php_constants(tree, language) -> List[Dict[str, Any]]:
    """提取所有常量定义"""
    constants = []
    
    # 查询常量定义
    query = language.query("""
        (expression_statement
            (function_call_expression
                function: (name) @func_name
                arguments: (arguments
                    (argument (string) @const_name)
                    (argument (_) @const_value)
                )
            )
        )
    """)
    
    matches = query.matches(tree.root_node)
    
    for match in matches:
        pattern_index, match_dict = match
        
        # 处理 define() 函数调用
        if 'func_name' in match_dict and match_dict['func_name'][0].text.decode('utf-8') == 'define':
            if 'const_name' in match_dict and 'const_value' in match_dict:
                name_node = match_dict['const_name'][0]
                value_node = match_dict['const_value'][0]
                
                constants.append({
                    'name': format_value(name_node.text.decode('utf-8')),
                    'value': format_value(value_node.text.decode('utf-8')),
                    'type': 'define',
                    'line': name_node.start_point[0]
                })
    
    return sorted(constants, key=lambda x: x['line'])

    
if __name__ == '__main__':
    php_file = r"php_demo\var_const.php"
    PARSER, LANGUAGE = init_php_parser()
    php_file_bytes = read_file_bytes(php_file)
    php_file_tree = PARSER.parse(php_file_bytes)
    constants = analyze_php_constants(php_file_tree, LANGUAGE)
    print_json(constants)