from enum import Enum
from libs_com.utils_json import print_json

# 新增导入类型枚举
class ImportType(Enum):
    INCLUDE = 'include'
    INCLUDE_ONCE = 'include_once'
    REQUIRE = 'require'
    REQUIRE_ONCE = 'require_once'
    USE_CLASS = 'use_class'
    USE_FUNCTION = 'use_function'
    USE_CONST = 'use_const'
    USE_TRAIT = 'use_trait'  # 新增
    USE_GROUP = 'use_group'  # 新增
    USE_ALIAS = 'use_alias'  # 新增

# 新增键名枚举
# 修改ImportKey枚举类
class ImportKey(Enum):
    IMPORT_TYPE = 'import_type'
    PATH = 'path'
    LINE = 'line'
    NAMESPACE = 'namespace'
    USE_FROM = 'use'
    ALIAS = 'alias'  # 新增别名字段

def get_use_declarations(tree, language):
    use_query = language.query("""
        (namespace_use_declaration) @use_declaration
    """)

    use_info = []
    matches = use_query.matches(tree.root_node)
    
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
                import_type = ImportType.USE_CLASS
                if item.startswith('function '):
                    import_type = ImportType.USE_FUNCTION
                    item = item.replace('function ', '')
                elif item.startswith('const '):
                    import_type = ImportType.USE_CONST
                    item = item.replace('const ', '')
                
                use_info.append({
                    ImportKey.IMPORT_TYPE.value: import_type.value,
                    ImportKey.PATH.value: None,
                    ImportKey.LINE.value: node.start_point[0] + 1,
                    ImportKey.NAMESPACE.value: group_prefix,
                    ImportKey.USE_FROM.value: item,  # 仅保留类名、函数名或常量名
                    ImportKey.ALIAS.value: None
                })
        else:
            # 处理普通 use 语句
            import_type = ImportType.USE_CLASS
            if node_text.startswith('use '):
                node_text = node_text.replace('use ', '').strip()

            if node_text.startswith('function '):
                import_type = ImportType.USE_FUNCTION
                node_text = node_text.replace('function ', '').strip()
            elif node_text.startswith('const '):
                import_type = ImportType.USE_CONST
                node_text = node_text.replace('const ', '').strip()
            elif 'SomeTrait' in node_text:
                import_type = ImportType.USE_TRAIT

            # 提取路径和别名
            use_content = node_text.rstrip(';')
            if ' as ' in use_content:
                path, alias = use_content.split(' as ')
                path = path.strip()
                alias = alias.strip()
            else:
                path = use_content
                alias = None

            # 处理命名空间
            namespace = '\\'.join(path.split('\\')[:-1]) if '\\' in path else None
            use_from = path.split('\\')[-1] if '\\' in path else path
            
            use_info.append({
                ImportKey.IMPORT_TYPE.value: import_type.value,
                ImportKey.PATH.value: None,
                ImportKey.LINE.value: node.start_point[0] + 1,
                ImportKey.NAMESPACE.value: namespace,
                ImportKey.USE_FROM.value: use_from,
                ImportKey.ALIAS.value: alias
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
            if 'dirname(__FILE__)' in path_text:  # 处理相对路径
                path_text = path_text.replace('dirname(__FILE__) . ', 'dirname(__FILE__) . ')
            
            import_info.append({
                ImportKey.IMPORT_TYPE.value: ImportType.INCLUDE.value,
                ImportKey.PATH.value: path_text,
                ImportKey.LINE.value: node.start_point[0] + 1,
                ImportKey.NAMESPACE.value: None,
                ImportKey.USE_FROM.value: None,
                ImportKey.ALIAS.value: None
            })
        
        # 处理 include_once 语句
        if 'include_once_right' in match_dict:
            node = match_dict['include_once_right'][0]
            path_text = node.text.decode('utf8').strip('"\'')
            
            import_info.append({
                ImportKey.IMPORT_TYPE.value: ImportType.INCLUDE_ONCE.value,
                ImportKey.PATH.value: path_text,
                ImportKey.LINE.value: node.start_point[0] + 1,
                ImportKey.NAMESPACE.value: None,
                ImportKey.USE_FROM.value: None,
                ImportKey.ALIAS.value: None  # 新增
            })
            
        # 处理 require 语句
        if 'require_right' in match_dict:
            node = match_dict['require_right'][0]
            path_text = node.text.decode('utf8').strip('"\'')
            
            import_info.append({
                ImportKey.IMPORT_TYPE.value: ImportType.REQUIRE.value,
                ImportKey.PATH.value: path_text,
                ImportKey.LINE.value: node.start_point[0] + 1,
                ImportKey.NAMESPACE.value: None,
                ImportKey.USE_FROM.value: None,
                ImportKey.ALIAS.value: None  # 新增
            })
        
        # 处理 require_once 语句
        if 'require_once_right' in match_dict:
            node = match_dict['require_once_right'][0]
            path_text = node.text.decode('utf8').strip('"\'')
            
            import_info.append({
                ImportKey.IMPORT_TYPE.value: ImportType.REQUIRE_ONCE.value,
                ImportKey.PATH.value: path_text,
                ImportKey.LINE.value: node.start_point[0] + 1,
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

def get_import_info(tree, language):
    """获取PHP文件中的所有导入信息"""
    import_info = []
    import_info.extend(get_use_declarations(tree, language))
    import_info.extend(get_include_require_info(tree, language))
    
    # 在返回前格式化路径
    return format_import_paths(import_info)


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
