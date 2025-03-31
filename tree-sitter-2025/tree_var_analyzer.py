from typing import List, Dict, Any

def format_value(value: str) -> str:
    """格式化提取的值，去除引号等处理"""
    if not value:
        return None
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value

class VariableAnalyzer:
    """PHP变量分析器"""
    
    SUPERGLOBALS = [
        '$_GET', '$_POST', '$_REQUEST', '$_SESSION', 
        '$_COOKIE', '$_SERVER', '$_FILES', '$_ENV', '$GLOBALS'
    ]
    
    def __init__(self, tree, language):
        self.tree = tree
        self.language = language
        self.all_variables = []
        
    def extract_all_variables(self):
        """提取所有变量声明和使用"""
        # 查询所有变量声明和赋值
        query = self.language.query("""
            (function_definition
                name: (name) @function_name
                body: (compound_statement) @function_body
            ) @function
            
            (expression_statement
                (assignment_expression
                    left: (variable_name) @assigned_var
                    right: (_) @var_value
                )
            )
            
            (static_variable_declaration
                (variable_name) @static_var
            )
            
            (global_declaration
                (variable_name) @global_var
            )
            
            (member_access_expression
                (variable_name) @array_name
                (name) @key_name
            )
            
            (subscript_expression
                (variable_name) @array_name
                (_) @key_name
            )
        """)
        
        def _is_superglobal_usage(value_node) -> bool:
            """检查是否使用了超全局变量"""
            if not value_node:
                return False
            value_text = value_node.text.decode('utf-8')
            return any(sg in value_text for sg in self.SUPERGLOBALS)
        
        matches = query.matches(self.tree.root_node)
        current_function = None
        processed_vars = set()  # 用于跟踪已处理的变量
        
        # 先处理文件级变量和全局声明
        for match in matches:
            pattern_index, match_dict = match
            
            if 'function_name' in match_dict:
                current_function = match_dict['function_name'][0].text.decode('utf-8')
            
            for capture_name, nodes in match_dict.items():
                if capture_name in ['assigned_var', 'global_var']:
                    node = nodes[0]
                    var_name = node.text.decode('utf-8')
                    
                    # 只处理文件级变量和全局声明
                    if current_function is None or capture_name == 'global_var':
                        var_key = f"{var_name}:{current_function}"
                        if var_key not in processed_vars:
                            var_info = self._create_variable_info(node, current_function, match_dict)
                            if var_info:
                                self.all_variables.append(var_info)
                                processed_vars.add(var_key)
        
        # 重置函数上下文
        current_function = None
        
        # 处理其他变量
        for match in matches:
            pattern_index, match_dict = match
            
            if 'function_name' in match_dict:
                current_function = match_dict['function_name'][0].text.decode('utf-8')
            
            for capture_name, nodes in match_dict.items():
                if capture_name in ['assigned_var', 'static_var', 'array_name']:
                    node = nodes[0]
                    var_name = node.text.decode('utf-8')
                    
                    # 处理超全局变量使用
                    if capture_name == 'array_name' and var_name in self.SUPERGLOBALS:
                        var_key = f"{var_name}:{current_function}"
                        if var_key not in processed_vars:
                            # 获取访问的键名
                            key_name = None
                            if 'key_name' in match_dict:
                                key_node = match_dict['key_name'][0]
                                key_name = key_node.text.decode('utf-8')
                            
                            self.all_variables.append({
                                'type': 'superglobal',
                                'variable': var_name,
                                'key': key_name,
                                'line': node.start_point[0] + 1,
                                'function': current_function,
                                'value': None
                            })
                            processed_vars.add(var_key)
                            continue
                    
                    # 处理其他变量
                    var_key = f"{var_name}:{current_function}"
                    if var_key not in processed_vars:
                        var_info = self._create_variable_info(node, current_function, match_dict)
                        if var_info:
                            self.all_variables.append(var_info)
                            processed_vars.add(var_key)

    def _create_variable_info(self, node, current_function, match_dict) -> Dict[str, Any]:
        """创建变量信息字典"""
        var_name = node.text.decode('utf-8')
        
        # 基本信息
        var_info = {
            'variable': var_name,
            'line': node.start_point[0] + 1,
            'function': current_function
        }
        
        # 确定变量类型和值
        parent = node.parent
        var_type = self._determine_variable_type(node, parent)
        var_info['type'] = var_type
        
        # 获取变量值
        if 'var_value' in match_dict:
            var_info['value'] = format_value(match_dict['var_value'][0].text.decode('utf-8'))
        else:
            var_info['value'] = None
            
        return var_info
    
    def _determine_variable_type(self, node, parent) -> str:
        """确定变量类型"""
        var_name = node.text.decode('utf-8')
        
        # 检查是否是超全局变量或其使用
        if var_name in self.SUPERGLOBALS:
            return 'superglobal'
        
        # 获取完整的变量上下文
        current_node = node
        while current_node and current_node.type != 'function_definition':
            # 检查静态变量声明
            if current_node.type == 'static_variable_declaration':
                return 'static'
            # 检查全局变量声明
            if current_node.type == 'global_declaration':
                return 'global'
            # 检查是否是超全局变量的使用
            if current_node.type == 'subscript_expression':
                array_name = current_node.child_by_field_name('array')
                if array_name and array_name.text.decode('utf-8') in self.SUPERGLOBALS:
                    return 'superglobal'
            current_node = current_node.parent
        
        # 如果在函数内部
        if current_node and current_node.type == 'function_definition':
            # 确保不是已经被标记为其他类型的变量
            if not any(v['variable'] == var_name and v['type'] in ['static', 'global'] 
                      for v in self.all_variables):
                return 'local'
        
        # 文件级变量
        return 'file_level'

    def get_variables_by_type(self, var_type: str) -> List[Dict[str, Any]]:
        """根据类型获取变量列表"""
        return [var for var in self.all_variables if var['type'] == var_type]

def analyze_php_variables(tree, language) -> Dict[str, List[Dict[str, Any]]]:
    """分析PHP文件中的所有变量"""
    analyzer = VariableAnalyzer(tree, language)
    analyzer.extract_all_variables()
    
    # 使用字典来跟踪变量，允许多次操作记录
    var_dict = {
        'local': {},
        'static': {},
        'superglobal': {},
        'global': []  # 改为列表以记录所有操作
    }
    
    # 处理所有变量
    for var in analyzer.all_variables:
        if var['type'] == 'superglobal':
            var_key = f"{var['variable']}:{var['function']}:{var.get('key', '')}"
            var_dict['superglobal'][var_key] = var
        elif var['type'] == 'static':
            var_key = f"{var['variable']}:{var['function']}"
            var_dict['static'][var_key] = var
        elif var['type'] == 'local':
            var_key = f"{var['variable']}:{var['function']}"
            var_dict['local'][var_key] = var
        elif var['type'] in ['global', 'file_level']:
            # 记录所有全局变量操作
            var_dict['global'].append(var)
    
    # 转换回列表格式，全局变量保持列表形式
    return {
        'local': list(var_dict['local'].values()),
        'static': list(var_dict['static'].values()),
        'superglobal': list(var_dict['superglobal'].values()),
        'global': sorted(var_dict['global'], key=lambda x: x['line'])  # 按行号排序
    }
# 修改输出格式，使其更易读
def print_variable_info(var_list: List[Dict], title: str):
    print(f"\n{title}:")
    for var in var_list:
        print("  变量:", var['variable'])
        print("    行号:", var['line'])
        print("    函数:", var['function'] or '文件级别')
        print("    类型:", var['type'])
        if 'key' in var:
            print("    键名:", var['key'])
        print("    值:", var['value'])
        print()

if __name__ == '__main__':
    from init_tree_sitter import init_php_parser
    from libs_com.file_io import read_file_bytes

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo\globals.php"
    php_file_bytes = read_file_bytes(php_file)
    php_file_tree = PARSER.parse(php_file_bytes)

    # 分析所有变量
    variables = analyze_php_variables(php_file_tree, LANGUAGE)
    

    print_variable_info(variables['local'], "局部变量")
    print_variable_info(variables['global'], "全局变量")
    print_variable_info(variables['static'], "静态变量")
    print_variable_info(variables['superglobal'], "超全局变量")