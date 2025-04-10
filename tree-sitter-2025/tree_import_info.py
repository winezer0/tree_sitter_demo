from libs_com.utils_json import print_json
from tree_enums import ImportType, ImportKey



def get_use_declarations(root_node, language):
    use_query = language.query("""
        (namespace_use_declaration) @use_declaration
    """)

    use_infos = []
    matches = use_query.matches(root_node)
    
    for _, match_dict in matches:
        node = match_dict['use_declaration'][0]
        node_text = node.text.decode('utf-8')

        # 处理 group use 语句
        if '{' in node_text and '}' in node_text:
            # 提取 group use 的前缀
            group_prefix = node_text.split('{')[0].strip()
            group_prefix = group_prefix.replace('use', '').strip()
            
            # 提取 group use 的内容
            group_content = node_text.split('{')[1].split('}')[0].strip()
            items = [item.strip() for item in group_content.split(',')]
            
            # 处理每个 item
            for item in items:
                # 确定导入类型
                import_type = ImportType.USE_CLASS.value
                if item.startswith('function '):
                    import_type = ImportType.USE_FUNCTION.value
                    item = item.replace('function ', '')
                elif item.startswith('const '):
                    import_type = ImportType.USE_CONST.value
                    item = item.replace('const ', '')

                use_info = create_import_result(start_line=node.start_point[0], end_line=node.end_point[0],
                                                namespace=group_prefix, import_type=import_type,
                                                file_path=None, use_from=f"{group_prefix}\\{item}", alias=None)
                use_infos.append(use_info)
        else:
            # 处理普通 use 语句
            import_type = ImportType.USE_CLASS.value
            if node_text.startswith('use '):
                node_text = node_text.replace('use ', '').strip()

            if node_text.startswith('function '):
                import_type = ImportType.USE_FUNCTION.value
                node_text = node_text.replace('function ', '').strip()
            elif node_text.startswith('const '):
                import_type = ImportType.USE_CONST.value
                node_text = node_text.replace('const ', '').strip()
            elif 'SomeTrait' in node_text:
                import_type = ImportType.USE_TRAIT.value

            # 提取路径和别名
            use_content = node_text.rstrip(';')
            if ' as ' in use_content:
                use_from, alias = use_content.split(' as ')
                use_from = use_from.strip()
                alias = alias.strip()
            else:
                use_from = use_content
                alias = None
            # 处理命名空间
            namespace = '\\'.join(use_from.split('\\')[:-1]) if '\\' in use_from else None

            use_info = create_import_result(start_line=node.start_point[0], end_line=node.end_point[0],
                                            namespace=namespace, import_type=import_type,
                                            file_path=None, use_from=use_from, alias=alias)
            use_infos.append(use_info)

    return use_infos


def create_import_result(start_line, end_line, namespace, import_type, file_path, use_from, alias):
    import_info = {
        ImportKey.TYPE.value: import_type,
        ImportKey.PATH.value: file_path,
        ImportKey.START_LINE.value: start_line,
        ImportKey.END_LINE.value: end_line,
        ImportKey.NAMESPACE.value: namespace,
        ImportKey.USE_FROM.value: use_from,
        ImportKey.ALIAS.value: alias
    }
    return import_info


def get_include_require_info(root_node, language):
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
    matches = include_query.matches(root_node)
    
    for _, match_dict in matches:
        # 处理 include 语句
        if 'include_right' in match_dict:
            node = match_dict['include_right'][0]
            path_text = get_node_text(node).strip('"\'')
            if 'dirname(__FILE__)' in path_text:  # 处理相对路径
                path_text = path_text.replace('dirname(__FILE__) . ', 'dirname(__FILE__) . ')
            
            import_info.append({
                ImportKey.TYPE.value: ImportType.INCLUDE.value,
                ImportKey.PATH.value: path_text,
                ImportKey.START_LINE.value: node.start_point[0],
                ImportKey.NAMESPACE.value: None,
                ImportKey.USE_FROM.value: None,
                ImportKey.ALIAS.value: None
            })
        
        # 处理 include_once 语句
        if 'include_once_right' in match_dict:
            node = match_dict['include_once_right'][0]

            import_info.append({
                ImportKey.TYPE.value: ImportType.INCLUDE_ONCE.value,
                ImportKey.PATH.value: get_node_text(node).strip('"\''),
                ImportKey.START_LINE.value: node.start_point[0],
                ImportKey.NAMESPACE.value: None,
                ImportKey.USE_FROM.value: None,
                ImportKey.ALIAS.value: None  # 新增
            })
            
        # 处理 require 语句
        if 'require_right' in match_dict:
            node = match_dict['require_right'][0]

            import_info.append({
                ImportKey.TYPE.value: ImportType.REQUIRE.value,
                ImportKey.PATH.value: get_node_text(node).strip('"\''),
                ImportKey.START_LINE.value: node.start_point[0],
                ImportKey.NAMESPACE.value: None,
                ImportKey.USE_FROM.value: None,
                ImportKey.ALIAS.value: None  # 新增
            })
        
        # 处理 require_once 语句
        if 'require_once_right' in match_dict:
            node = match_dict['require_once_right'][0]

            import_info.append({
                ImportKey.TYPE.value: ImportType.REQUIRE_ONCE.value,
                ImportKey.PATH.value: get_node_text(node).strip('"\''),
                ImportKey.START_LINE.value: node.start_point[0],
                ImportKey.NAMESPACE.value: None,
                ImportKey.USE_FROM.value: None,  # 修正拼写错误
                ImportKey.ALIAS.value: None
            })
    
    return import_info


def format_import_paths(import_info):
    """格式化导入路径中的反斜杠"""
    for item in import_info:
        if item.get(ImportKey.NAMESPACE.value):
            item[ImportKey.NAMESPACE.value] = item[ImportKey.NAMESPACE.value].replace('\\\\', '\\').rstrip('\\')   
        if item.get(ImportKey.USE_FROM.value):
            item[ImportKey.USE_FROM.value] = item[ImportKey.USE_FROM.value].replace('\\\\', '\\').rstrip('\\')   
        if item.get(ImportKey.PATH.value):
            item[ImportKey.PATH.value] = item[ImportKey.PATH.value].replace('\\\\', '/').rstrip('/')
    return import_info

def parse_import_info(language, root_node):
    """获取PHP文件中的所有导入信息"""
    import_info = []
    import_info.extend(get_use_declarations(root_node, language))
    import_info.extend(get_include_require_info(root_node, language))
    
    # 在返回前格式化路径
    return format_import_paths(import_info)


if __name__ == '__main__':
    # 解析tree
    from tree_sitter_uitls import init_php_parser, get_node_text
    from libs_com.file_io import read_file_bytes

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo\depends.php"
    php_file_bytes = read_file_bytes(php_file)
    # print(f"read_file_bytes:->{php_file}")
    php_file_tree = PARSER.parse(php_file_bytes)
    code = parse_import_info(LANGUAGE, php_file_tree.root_node)
    print_json(code)
