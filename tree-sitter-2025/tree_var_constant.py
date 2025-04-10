from typing import List, Dict, Any

from tree_enums import VariableKeys
from tree_sitter_uitls import init_php_parser, get_node_filed_text, find_first_child_by_field, find_children_by_field, \
    get_node_text
from libs_com.file_io import read_file_bytes
from libs_com.utils_json import print_json

def create_var_info_result(name_text, name_type, value_text, value_type, start_line, end_line):
    var_info = {
        VariableKeys.START_LINE.value: start_line,
        VariableKeys.END_LINE.value: end_line,
        VariableKeys.NAME.value: name_text,
        VariableKeys.NAME_TYPE.value: name_type,
        VariableKeys.VALUE.value: value_text,
        VariableKeys.VALUE_TYPE.value: value_type,
    }
    return var_info


def parse_const_node(const_node):
    """ 解析 const_node 函数调用节点的信息。 """
    # (const_declaration (const_element (name) (string (string_content))))
    start_line = const_node.start_point[0]
    end_line = const_node.end_point[0]

    arguments_node = find_first_child_by_field(const_node, 'const_element')
    # (const_element (name) (string (string_content)))

    name_node = find_first_child_by_field(arguments_node, 'name')
    name_text = get_node_text(name_node)
    name_type = name_node.type
    # name_node:CLASS_INT_CONSTANT type:name

    value_node = arguments_node.children[-1]
    value_text = get_node_text(value_node)
    value_type = value_node.type

    var_info = create_var_info_result(name_text, name_type, value_text, value_type, start_line, end_line)
    return var_info


def parse_define_node(define_function_call_node):
    """ 解析 define 函数调用节点的信息。 """
    # 提取参数列表
    arguments_node = find_first_child_by_field(define_function_call_node, 'arguments')
    # (arguments (argument (string (string_content))) (argument (boolean)))

    start_line = define_function_call_node.start_point[0]
    end_line = define_function_call_node.end_point[0]

    # define 提取语法中已经限定,必须有两个参数,如果没有应该报错
    if not arguments_node or len(arguments_node.children) < 2:
        raise ValueError("Invalid arguments for 'define' function.")

    argument_nodes = find_children_by_field(arguments_node, 'argument')
    # [<Node type=argument,>, <Node type=argument, >]
    # 第一个参数：节点名称
    name_node = argument_nodes[0].child(0) # 获取第1个节点
    name_type = name_node.type
    name_text = get_node_filed_text(name_node, 'string_content')
    # print(f"node_name: {name_text} type:{name_type}")
    # node_name: IN_ECS type:string

    # 第二个参数：节点值及其类型
    value_node = argument_nodes[1].child(0)
    value_type = value_node.type
    value_text = get_node_text(value_node)
    # print(f"node_value: {value_text} type {value_type}")
    # node_value: true type boolean

    var_info = create_var_info_result(name_text, name_type, value_text, value_type, start_line, end_line)
    return var_info


def analyze_var_constants(root_node, language) -> List[Dict[str, Any]]:
    """提取 define 常量定义"""
    # 查询 可能的 define函数语法 还需要过滤
    query = language.query("""
        ;define定义信息提取
        (expression_statement
            (function_call_expression
                (name)
                (arguments
                    (argument (string))
                    (argument (_))
                )
            )
        )@define_call
        
        ;const定义信息提取
        (const_declaration)@const_declare
    """)
    matches = query.matches(root_node)

    constants = []
    # 提取define常量信息
    for match in matches:
        pattern_index, match_dict = match
        if 'define_call' in match_dict:
            define_call_node = match_dict['define_call'][0]
            # (expression_statement (function_call_expression function: (name) arguments: (arguments (argument (string (string_content))) (argument (boolean)))))
            function_call_node = find_first_child_by_field(define_call_node, 'function_call_expression')
            function_name = get_node_filed_text(function_call_node, 'name')
            if function_name == "define":
                define_info = parse_define_node(function_call_node)
                constants.append(define_info)

    # 提取const常量信息
    for match in matches:
        pattern_index, match_dict = match
        if 'const_declare' in match_dict:
            const_declare_node = match_dict['const_declare'][0]
            # (const_declaration (const_element (name) (string (string_content))))
            const_info = parse_const_node(const_declare_node)
            constants.append(const_info)
    return sorted(constants, key=lambda x: x[VariableKeys.START_LINE.value])


if __name__ == '__main__':
    php_file = r"php_demo\var_const.php"
    PARSER, LANGUAGE = init_php_parser()
    php_file_bytes = read_file_bytes(php_file)
    php_file_tree = PARSER.parse(php_file_bytes)
    constants = analyze_var_constants(php_file_tree.root_node, LANGUAGE)
    print_json(constants)
