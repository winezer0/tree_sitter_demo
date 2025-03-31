
def get_function_by_line(tree, language, line_number):
    """获取指定行号所在的函数信息"""
    query = language.query("""
        (function_definition
            name: (name) @function_name
            parameters: (formal_parameters) @params
            body: (compound_statement) @body
        ) @function
    """)

    captures = query.captures(tree.root_node)
    for node, capture_name in captures:
        if capture_name == 'function':
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1

            if start_line <= line_number <= end_line:
                function_info = {
                    'name': node.child_by_field_name('name').text.decode('utf-8'),
                    'start_line': start_line,
                    'end_line': end_line,
                    'code_line': line_number,
                    'parameters': []
                }

                # 获取参数信息
                params_node = node.child_by_field_name('parameters')
                if params_node:
                    for param in params_node.children:
                        if param.type == 'parameter':
                            param_info = {
                                'name': '',
                                'type': None
                            }
                            # 获取参数类型
                            type_node = param.child_by_field_name('type')
                            if type_node:
                                param_info['type'] = type_node.text.decode('utf-8')
                            # 获取参数名
                            name_node = param.child_by_field_name('name')
                            if name_node:
                                param_info['name'] = name_node.text.decode('utf-8')
                            function_info['parameters'].append(param_info)

                return function_info

    return None


def get_function_code(tree, language, function_name):
    """获取指定函数名的代码内容"""
    query = language.query("""
        (function_definition
            name: (name) @function_name
            body: (compound_statement) @body
        ) @function
    """)

    captures = query.captures(tree.root_node)
    for node, capture_name in captures:
        if capture_name == 'function_name':
            if node.text.decode('utf-8') == function_name:
                function_node = node.parent
                # 获取函数的完整文本内容
                return {
                    'name': function_name,
                    'code': function_node.text.decode('utf-8'),
                    'start_line': function_node.start_point[0] + 1,
                    'end_line': function_node.end_point[0] + 1
                }
    return None
