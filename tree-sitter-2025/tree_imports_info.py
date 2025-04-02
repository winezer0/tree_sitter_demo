from libs_com.utils_json import print_json


def get_use_declarations(tree, language):
    """获取PHP文件中的use声明信息"""
    # import_type 是用来标识 PHP 中 use 语句导入的类型，在 PHP 中主要有三种导入类型：
    # 1. class （默认类型）：导入类、接口或 trait use App\Models\User;  // 导入类
    # 2. function ：导入函数 use function App\Helpers\format_date;  // 导入函数
    # 3. constant ：导入常量 use const App\Config\MAX_USERS;  // 导入常量
    use_info = []
    use_query = language.query("""
        (namespace_use_declaration
            (namespace_use_clause
                (qualified_name
                    prefix: (namespace_name) @prefix
                    (name) @name
                ) @full_name
            )
        )
    """)

    matches = use_query.matches(tree.root_node)
    
    for _, match_dict in matches:
        if 'full_name' in match_dict:
            node = match_dict['full_name'][0]
            import_type = 'class'  # 默认类型为类导入
            parent = node.parent
            if parent and parent.parent:
                parent_text = parent.parent.text.decode('utf-8')
                if 'function' in parent_text:
                    import_type = 'function'
                elif 'const' in parent_text:
                    import_type = 'constant'

            use_info.append({
                'type': 'use',
                'import_type': import_type,
                'path': node.text.decode('utf-8'),
                'line': node.start_point[0] + 1
            })

    return use_info


def get_include_require_info(tree, language):
    """获取 include/require 信息"""
    include_query = language.query("""
        [
            (include_expression
                (parenthesized_expression
                    (binary_expression
                        left: (name) @include_left
                        right: (string) @include_right)
                )
            ) @include
            (include_once_expression
                (parenthesized_expression
                    (binary_expression
                        left: (name) @include_once_left
                        right: (string) @include_once_right)
                )
            ) @include_once
            (require_expression
                (parenthesized_expression
                    (binary_expression
                        left: (_) @require_left
                        right: (string) @require_right)
                )
            ) @require
            (require_once_expression
                (parenthesized_expression
                    (binary_expression
                        left: (_) @require_once_left
                        right: (string) @require_once_right)
                )
            ) @require_once
        ]
    """)
    
    import_info = []
    matches = include_query.matches(tree.root_node)
    
    for _, match_dict in matches:
        # 处理 include 语句
        if 'include_right' in match_dict:
            node = match_dict['include_right'][0]
            path_text = node.text.decode('utf8').strip('"\'')
            import_info.append({
                'type': 'include',
                'path': path_text,
                'line': node.start_point[0] + 1
            })
        
        # 处理 include_once 语句
        if 'include_once_right' in match_dict:
            node = match_dict['include_once_right'][0]
            path_text = node.text.decode('utf8').strip('"\'')
            import_info.append({
                'type': 'include_once',
                'path': path_text,
                'line': node.start_point[0] + 1
            })
            
        # 处理 require 语句
        if 'require_right' in match_dict:
            node = match_dict['require_right'][0]
            path_text = node.text.decode('utf8').strip('"\'')
            import_info.append({
                'type': 'require',
                'path': path_text,
                'line': node.start_point[0] + 1
            })
        
        # 处理 require_once 语句
        if 'require_once_right' in match_dict:
            node = match_dict['require_once_right'][0]
            path_text = node.text.decode('utf8').strip('"\'')
            import_info.append({
                'type': 'require_once',
                'path': path_text,
                'line': node.start_point[0] + 1
            })
    
    return import_info


def get_import_info(tree, language):
    """获取PHP文件中的所有导入信息"""
    import_info = []
    import_info.extend(get_use_declarations(tree, language))
    import_info.extend(get_include_require_info(tree, language))
    return import_info


if __name__ == '__main__':
    # 解析tree
    from init_tree_sitter import init_php_parser
    from libs_com.file_io import read_file_bytes

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo\depends.php"
    php_file_bytes = read_file_bytes(php_file)
    print(f"read_file_bytes:->{php_file}")
    php_file_tree = PARSER.parse(php_file_bytes)
    code = get_import_info(php_file_tree, LANGUAGE)
    print_json(code)
