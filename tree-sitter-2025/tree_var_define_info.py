from typing import List, Dict, Any
from tree_sitter_uitls import init_php_parser, get_node_filed_text, find_first_child_by_field, find_children_by_field, \
    get_node_text
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


def parse_define_node(function_call_node):
    """ 解析 define 函数调用节点的信息。 """
    # 提取参数列表
    arguments_node = find_first_child_by_field(function_call_node, 'arguments')
    print(f"arguments_node:{arguments_node}")
    if not arguments_node or len(arguments_node.children) < 2:
        # define 提取语法中已经限定了,必须有两个参数,如果没有应该报错
        raise ValueError("Invalid arguments for 'define' function.")

    argument_nodes = find_children_by_field(arguments_node, 'argument')
    print("argument_nodes:", argument_nodes)

    # 第一个参数：节点名称
    name_argument = argument_nodes[0]
    if name_argument.type != 'argument':
        raise ValueError("First argument of 'define' must be an argument.")

    name_argument = name_argument.child(0)
    node_name = get_node_filed_text(name_argument, 'string_content')
    node_type = name_argument.type
    print(f"node_name: {node_name} type:{node_type}")

    # 第二个参数：节点值及其类型
    value_node = argument_nodes[1]
    if value_node.type != 'argument':
        raise ValueError("Second argument of 'define' must be an argument.")
    # 提取 argument 的 value 子节点
    value_node = value_node.child(0)
    node_value = get_node_text(value_node)
    node_type = value_node.type
    print(f"node_value: {node_value} type {node_type}")


    info = {
        'node_name': node_name,
        'node_value': node_value,
        'node_type': node_type,
        'node_line': function_call_node.start_point[0],
    }
    print('info: ', info)
    return info

def analyze_php_constants(root_node, language) -> List[Dict[str, Any]]:
    """
    提取所有常量定义
    # define('DEBUG_MODE', false);
    # const DATABASE_HOST = 'localhost';
    """
    # print(root_node)
    # (expression_statement (function_call_expression function: (name) arguments: (arguments (argument (string (string_content))) (argument (boolean)))))
    # (expression_statement (function_call_expression function: (name) arguments: (arguments (argument (string (string_content))) (argument (string (string_content))))))
    # (expression_statement (function_call_expression function: (name) arguments: (arguments (argument (string (string_content)))  (argument (array_creation_expression

    # 查询define常量定义
    query = language.query("""
        (expression_statement
            (function_call_expression
                function: (name)
                arguments: (arguments
                    (argument (string))
                    (argument (_))
                )
            )
        )@define_call
    """)

    matches = query.matches(root_node)

    constants = []
    for match in matches:
        pattern_index, match_dict = match
        if 'define_call' in match_dict:
            # print(f'define_call:{match_dict}')
            # define_call:{'define_call': [<Node type=expression_statement, start_point=(2, 0), end_point=(2, 23)>]}
            define_call_node = match_dict['define_call'][0]
            # print("define_call_node:", define_call_node)
            #  define_call_node: (expression_statement (function_call_expression function: (name) arguments: (arguments (argument (string (string_content))) (argument (boolean)))))
            function_call_node = find_first_child_by_field(define_call_node, 'function_call_expression')
            function_name = get_node_filed_text(function_call_node, 'name')
            #  function_call_node name:define
            if function_name == "define":
                define_info = parse_define_node(function_call_node)
                constants.append(define_info)
    return sorted(constants, key=lambda x: x['node_line'])

    
if __name__ == '__main__':
    php_file = r"php_demo\var_const.php"
    PARSER, LANGUAGE = init_php_parser()
    php_file_bytes = read_file_bytes(php_file)
    php_file_tree = PARSER.parse(php_file_bytes)
    constants = analyze_php_constants(php_file_tree.root_node, LANGUAGE)
    print_json(constants)