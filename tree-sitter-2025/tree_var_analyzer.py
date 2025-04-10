from typing import List, Dict, Any

from tree_sitter._binding import Node

from libs_com.utils_json import print_json
from tree_enums import VariableType, ClassKeys, OtherName
from tree_func_utils import get_global_code_info, get_global_code_string
from tree_var_constant import create_var_info_result


def parse_static_node(static_node):
    """解析常规的变量赋值节点"""
    # (function_static_declaration (static_variable_declaration name: (variable_name (name)) value: (integer)))
    start_line = static_node.start_point[0]
    end_line = static_node.end_point[0]
    variable_text = get_node_text(static_node)

    static_node = find_first_child_by_field(static_node, "static_variable_declaration")
    variable_node = find_first_child_by_field(static_node, 'variable_name')
    name_text = get_node_text(variable_node)
    name_type = get_node_type(variable_node)

    # 获取代表 value 的内容
    value_node = static_node.children[2]
    value_text = get_node_text(value_node)
    value_type = get_node_type(value_node)


    var_info = create_var_info_result(name_text=name_text, name_type=name_type, value_text=value_text,
                                      value_type=value_type, start_line=start_line, end_line=end_line,
                                      full_text=variable_text, function=None)
    return var_info


def parse_variable_node(language, any_node, node_name):
    """解析常规的函数体中的变量赋值节点"""
    def parse_assignment_node(assignment_node, function):
        """解析常规的变量赋值节点"""
        # (assignment_expression left: (variable_name (name)) right: (integer))
        start_line = assignment_node.start_point[0]
        end_line = assignment_node.end_point[0]
        variable_text = get_node_text(assignment_node)

        left_node = find_first_child_by_field(assignment_node, 'left')
        right_node = find_first_child_by_field(assignment_node, 'right')
        variable_name = get_node_text(left_node)
        variable_type = get_node_type(left_node)
        value_name = get_node_text(right_node)
        value_type = get_node_type(right_node)

        var_info = create_var_info_result(name_text=variable_name, name_type=variable_type, value_text=value_name,
                                          value_type=value_type, start_line=start_line, end_line=end_line,
                                          full_text=variable_text, function=function)
        return var_info

    query = language.query("""
        ;常规变量赋值 比如 $localVar = 42;
        (assignment_expression
            (variable_name)
            (_) @var_value
        )@variables
    """)
    matches = query.matches(any_node)
    variable_infos = []
    for match in matches:
        pattern_index, match_dict = match
        if 'variables' in match_dict:
            variable_node = match_dict['variables'][0]
            variable_info = parse_assignment_node(variable_node, node_name)
            variable_infos.append(variable_info)
    return variable_infos

def parse_global_node(global_node):
    # (global_declaration (variable_name (name)))
    start_line = global_node.start_point[0]
    end_line = global_node.end_point[0]
    global_text = get_node_text(global_node)

    global_node = find_first_child_by_field(global_node, 'variable_name')
    variable_name = get_node_text(global_node)
    variable_type = get_node_type(global_node)

    var_info = create_var_info_result(name_text=variable_name, name_type=variable_type, value_text=None,
                                      value_type=None, start_line=start_line, end_line=end_line, full_text=global_text,
                                      function=None)
    return var_info

def parse_super_global_node(super_global_node: Node):
    start_line = super_global_node.start_point[0]
    end_line = super_global_node.end_point[0]

    # (subscript_expression (variable_name (name)) (string (string_content)))
    super_global_text = get_node_text(super_global_node)
    # print(f"super_global_text:{super_global_text}")  # $_SERVER[1111]

    super_var_node = find_first_child_by_field(super_global_node, 'variable_name')
    super_var_name = get_node_text(super_var_node)
    super_var_type = get_node_type(super_var_node)
    # print(super_var_name, super_var_type)  # $_COOKIE variable_name

    # 获取代表key的内容
    super_key_node = super_global_node.children[2]
    # print(super_key_node)  # (string (string_content))
    super_key_name = get_node_text(super_key_node)
    super_key_type = get_node_type(super_key_node)
    # print(super_key_name, super_key_type)  # PATH string

    var_info = create_var_info_result(name_text=super_var_name, name_type=super_var_type, value_text=super_key_name,
                                      value_type=super_key_type, start_line=start_line, end_line=end_line,
                                      full_text=super_global_text, function=None)
    return var_info

def analyze_php_variables(parser, language, root_node) -> Dict[str, List[Dict[str, Any]]]:
    """分析PHP文件中的所有变量"""
    # # 初始化变量字典
    var_infos = {var_type.value: [] for var_type in VariableType}

    query = language.query("""
        ;匹配超全局变量访问 比如 $_SERVER['REQUEST_METHOD']
        (subscript_expression)@super_global_call
        
        ;全局变量声明 比如 global $globalVar;
        (global_declaration)@global_declare
        
        ;静态变量声明 比如 static $staticVar = 0;
        (function_static_declaration)@static_declare
    """)
    matches = query.matches(root_node)

    # SUPER_GLOBAL = 'superglobal'  超全局变量调用信息
    # PHP 中的超全局变量（Superglobals）是内置的预定义变量，在脚本的任何作用域中都可以直接访问
    # 提取文件中的 super global 信息
    super_global_infos = []
    for match in matches:
        pattern_index, match_dict = match
        if 'super_global_call' in match_dict:
            variable_node = match_dict['super_global_call'][0]
            variable_info = parse_super_global_node(variable_node)
            super_global_infos.append(variable_info)
    var_infos[VariableType.SUPER_GLOBAL.value] = super_global_infos

    # GLOBAL = 'global'  声明全局的变量信息
    # (global_declaration (variable_name (name)))
    global_infos = []
    for match in matches:
        pattern_index, match_dict = match
        if 'global_declare' in match_dict:
            variable_node = match_dict['global_declare'][0]
            variable_info = parse_global_node(variable_node)
            global_infos.append(variable_info)
    var_infos[VariableType.GLOBAL.value] = global_infos


    # STATIC = 'static' 静态变量只能在函数或方法内部声明
    # (function_static_declaration (static_variable_declaration name: (variable_name (name)) value: (encapsed_string (string_content))))
    static_variable_infos = []
    for match in matches:
        pattern_index, match_dict = match
        if 'static_declare' in match_dict:
            static_node = match_dict['static_declare'][0]
            variable_info = parse_static_node(static_node)
            static_variable_infos.append(variable_info)
    var_infos[VariableType.STATIC.value] = static_variable_infos


    # PROGRAM = 'program'  全局代码内的变量信息
    program_code_info = get_global_code_info(language, root_node, None, None)
    nf_code_tree = load_str_to_parse(parser, get_global_code_string(program_code_info))
    nf_code_node = nf_code_tree.root_node
    program_variable_infos = parse_variable_node(language, nf_code_node, OtherName.NOT_IN_METHOD.value)
    var_infos[VariableType.PROGRAM.value] = program_variable_infos

    # LOCAL = 'local' 函数内的变量信息
    # 先获取所有函数节点，再分别解析其中的每个节点
    function_query = language.query("""
        ; 查询全局函数定义
        (function_definition) @function.def
        ; 查询类方法定义
        (method_declaration) @method.def
        ; 匹配闭包定义
        (anonymous_function) @anonymous.def
    """)
    matches = function_query.matches(root_node)
    locale_variable_infos = []
    for match in matches:
        pattern_index, match_dict = match
        # 处理全局函数和类函数
        if 'function.def' in match_dict or 'method.def' in match_dict:
            function_node = match_dict['function.def'][0] if 'function.def' in match_dict else match_dict['method.def'][0]
            method_name = get_node_filed_text(function_node, 'name')
            body_node = find_first_child_by_field(function_node, 'body')
            variable_info = parse_variable_node(language, body_node, method_name)
            locale_variable_infos.append(variable_info)
        # 处理匿名函数
        if 'anonymous.def' in match_dict:
            function_node = match_dict['anonymous.def'][0]
            body_node = find_first_child_by_field(function_node,'body')
            variable_info = parse_variable_node(language, body_node, OtherName.ANONYMOUS.value)
            locale_variable_infos.append(variable_info)
    var_infos[VariableType.LOCAL.value] = locale_variable_infos

    # TODO 进一步通过行号信息 判断变量的真实信息
    # TODO 进一步通过行号信息 判断变量所处的类和函数
    return var_infos



if __name__ == '__main__':
    from tree_sitter_uitls import init_php_parser, read_file_to_parse, find_first_child_by_field, get_node_text, \
    get_node_type, load_str_to_parse, get_node_filed_text

    PARSER, LANGUAGE = init_php_parser()
    # php_file = r"php_demo/var_spuer_globals.php"
    # php_file = r"php_demo/var_globals.php"
    # php_file = r"php_demo/var_static.php"
    php_file = r"php_demo/var_local.php"
    # php_file = r"php_demo\class.php"
    php_file_tree = read_file_to_parse(PARSER, php_file)
    # 分析所有变量
    variables = analyze_php_variables(PARSER, LANGUAGE, php_file_tree.root_node)
    # 打印分析结果
    # print_json(variables)