from enum import Enum
from typing import List, Dict, Any

from libs_com.utils_json import print_json


class VariableType(Enum):
    """变量类型枚举"""
    LOCAL = 'local'
    STATIC = 'static'
    GLOBAL = 'global'
    PROGRAM = 'program'
    SUPERGLOBAL = 'superglobal'

    @classmethod
    def get_type(cls, node, var_name: str, global_vars: Dict, is_global_declaration: bool = False) -> 'VariableType':
        """确定变量类型的类方法"""
        print(f"Debug - get_type for {var_name}, is_global_declaration: {is_global_declaration}")

        # 超全局变量优先判断
        if var_name in SUPERGLOBALS:
            print(f"Debug - {var_name} is superglobal")
            return cls.SUPERGLOBAL

        # 检查是否是全局声明
        if is_global_declaration:
            print(f"Debug - {var_name} is global (declared)")
            return cls.GLOBAL

        current_node = node
        while current_node:
            print(f"Debug - Checking node type: {current_node.type}")
            # 静态变量声明
            if current_node.type == 'static_variable_declaration':
                print(f"Debug - {var_name} is static")
                return cls.STATIC
            # 在函数内部
            elif current_node.type == 'function_definition':
                if var_name in global_vars:
                    print(f"Debug - {var_name} is global (used in function)")
                    return cls.GLOBAL
                print(f"Debug - {var_name} is local")
                return cls.LOCAL
            # 检查是否在文件顶层使用了 global 关键字
            elif current_node.type == 'global_declaration' and current_node.parent.type == 'program':
                print(f"Debug - {var_name} is global (file level declaration)")
                return cls.GLOBAL
            current_node = current_node.parent

        # 文件顶层直接使用的变量
        if node.parent and node.parent.type == 'program':
            print(f"Debug - {var_name} is local (file level usage)")
            return cls.LOCAL

        print(f"Debug - {var_name} is file level")
        return cls.PROGRAM

# 常量定义
SUPERGLOBALS = [
    '$_GET', '$_POST', '$_REQUEST', '$_SESSION', 
    '$_COOKIE', '$_SERVER', '$_FILES', '$_ENV', '$GLOBALS'
]

def format_value(value: str) -> str:
    """格式化提取的值，去除引号等处理"""
    if not value:
        return None
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value

def create_variable_info(node, current_function, match_dict, global_vars) -> Dict[str, Any]:
    """创建变量信息字典"""
    var_name = node.text.decode('utf-8')
    
    # 检查是否是全局声明
    is_global_declaration = False
    if 'global_var' in match_dict:
        for global_node in match_dict['global_var']:
            if global_node.text.decode('utf-8') == var_name:
                # 检查是否在函数内声明
                current_node = node
                while current_node:
                    if current_node.type == 'function_definition':
                        is_global_declaration = True
                        break
                    current_node = current_node.parent
    
    var_info = {
        'variable': var_name,
        'start_line': node.start_point[0],
        'function': current_function,
        'value': None
    }
    
    # 获取变量类型，传入全局声明标志
    var_type = VariableType.get_type(node, var_name, global_vars, is_global_declaration)
    var_info['type'] = var_type.value
    
    # 处理变量值
    if 'var_value' in match_dict:
        value_node = match_dict['var_value'][0]
        var_info['value'] = format_value(value_node.text.decode('utf-8'))
    elif var_type == VariableType.STATIC and 'static_value' in match_dict:
        var_info['value'] = format_value(match_dict['static_value'][0].text.decode('utf-8'))
    elif var_type == VariableType.GLOBAL and var_name in global_vars:
        var_info['value'] = global_vars[var_name]
    
    return var_info

def analyze_php_variables(tree, language) -> Dict[str, List[Dict[str, Any]]]:
    """分析PHP文件中的所有变量"""
    query = language.query("""
        ; 函数定义
        (function_definition
            name: (name) @function_name
            body: (compound_statement) @function_body
        ) @function
        
        ; 变量赋值和声明
        [
            (expression_statement
                (assignment_expression
                    left: (variable_name) @assigned_var
                    right: (_) @var_value
                )
            )
            (global_declaration
                (variable_name) @global_var
            )
            (static_variable_declaration
                (variable_name) @static_var
                value: (_) @static_value
            )
        ]
        
        ; 超全局变量访问
        (subscript_expression
            (variable_name) @array_name
            (_) @key_name
        )
    """)

    matches = query.matches(tree.root_node)
    processed_vars = set()
    global_vars = {}
    all_variables = []
    function_context = {}

    # 初始化变量字典 - 这行代码需要在处理变量之前添加
    var_dict = {var_type.value: {} for var_type in VariableType}

    # 修改全局变量收集逻辑
    global_vars_set = set()
    for match in matches:
        _, match_dict = match
        if 'global_var' in match_dict:
            for node in match_dict['global_var']:
                var_name = node.text.decode('utf-8')
                # 检查是否在函数内声明的全局变量
                current_node = node
                while current_node:
                    if current_node.type == 'function_definition':
                        global_vars_set.add(var_name)
                        global_vars[var_name] = None
                        break
                    current_node = current_node.parent

    # 添加调试语句来跟踪全局变量集合
    print("Debug - Global vars set:", global_vars_set)

    # 处理函数定义和变量
    for match in matches:
        pattern_index, match_dict = match
        
        # 添加调试语句来跟踪匹配的模式
        if 'global_var' in match_dict:
            print("Debug - Found global declaration:", [n.text.decode('utf-8') for n in match_dict['global_var']])

        if 'function_name' in match_dict:
            current_function = match_dict['function_name'][0].text.decode('utf-8')
            function_node = match_dict['function'][0]
            function_context[current_function] = {
                'start': function_node.start_point[0],
                'end': function_node.end_point[0]
            }
        
        for capture_name, nodes in match_dict.items():
            if capture_name in ['assigned_var', 'static_var', 'array_name']:
                node = nodes[0]
                node_line = node.start_point[0]
                
                # 确定当前函数上下文
                current_function = None
                for func_name, context in function_context.items():
                    if context['start'] <= node_line <= context['end']:
                        current_function = func_name
                        break
                
                var_name = node.text.decode('utf-8')
                var_key = f"{var_name}:{current_function}"
                
                if var_key not in processed_vars:
                    var_info = create_variable_info(node, current_function, match_dict, global_vars)
                    if var_info:
                        all_variables.append(var_info)
                        processed_vars.add(var_key)

    # 处理变量时添加调试语句
    for var in all_variables:
        var_name = var['variable']
        var_type = var['type']
        
        # 添加调试语句来跟踪变量分类
        print(f"Debug - Processing variable: {var_name}, type: {var_type}")
        
        # 构造变量键
        if var_type == VariableType.SUPERGLOBAL.value:
            var_key = f"{var_name}:{var.get('key', '')}"
        elif var_type in [VariableType.STATIC.value, VariableType.LOCAL.value]:
            var_key = f"{var_name}:{var['function']}"
        else:  # GLOBAL 和 FILE_LEVEL
            var_key = var_name
            var['function'] = None
        
        # 存储变量信息前添加调试语句
        print(f"Debug - Storing variable {var_name} with key {var_key} as type {var_type}")
        var_dict[var_type][var_key] = var

    # 在返回结果前添加最终的变量分类统计
    for var_type in VariableType:
        print(f"Debug - Final count for {var_type.value}: {len(var_dict[var_type.value])}")

    # 第二步：专门查询 global 声明
    global_query = language.query("""
        (function_definition
            body: (compound_statement 
                (global_declaration
                    (variable_name) @global_var
                )
            )
        )
    """)
    
    # 收集所有在函数内使用 global 关键字声明的变量
    global_declarations = set()
    for match in global_query.matches(tree.root_node):
        _, match_dict = match
        if 'global_var' in match_dict:
            for node in match_dict['global_var']:
                var_name = node.text.decode('utf-8')
                global_declarations.add(var_name)
    
    print("Debug - Global declarations in functions:", global_declarations)
    
    # 修正变量分类
    corrected_vars = {var_type.value: [] for var_type in VariableType}
    processed_vars = set()  # 用于跟踪已处理的变量
    
    # 处理每个类别的变量
    for var_type in VariableType:
        for var in var_dict[var_type.value].values():
            var_name = var['variable']
            
            # 跳过已处理的变量
            if var_name in processed_vars:
                continue
            
            # 如果变量在函数内使用了 global 关键字声明，将其移动到 global 类别
            if var_name in global_declarations:
                var['type'] = VariableType.GLOBAL.value
                corrected_vars[VariableType.GLOBAL.value].append(var)
            else:
                corrected_vars[var_type.value].append(var)
            
            processed_vars.add(var_name)
    
    # 添加调试信息
    print("\nDebug - Final corrected counts:")
    for var_type in VariableType:
        print(f"Debug - {var_type.value}: {len(corrected_vars[var_type.value])}")
    
    return corrected_vars

if __name__ == '__main__':
    from init_tree_sitter import init_php_parser
    from libs_com.file_io import read_file_bytes

    PARSER, LANGUAGE = init_php_parser()
    # php_file = r"php_demo\var_globals.php"
    php_file = r"php_demo\class.php"
    php_file_bytes = read_file_bytes(php_file)
    php_file_tree = PARSER.parse(php_file_bytes)

    # 分析所有变量
    variables = analyze_php_variables(php_file_tree, LANGUAGE)
    

    # 打印分析结果
    print_json(variables)