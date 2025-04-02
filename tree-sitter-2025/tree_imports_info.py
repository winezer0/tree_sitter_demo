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
        (namespace_use_declaration
            (namespace_use_clause
                (qualified_name) @full_name
            )
        )
    """)

    use_info = []  # 初始化 use_info 列表
    matches = use_query.matches(tree.root_node)
    
    for _, match_dict in matches:
        if 'full_name' in match_dict:
            # 处理普通 use 语句
            node = match_dict['full_name'][0]
            import_type = ImportType.USE_CLASS
            parent = node.parent
            if parent and parent.parent:
                parent_text = parent.parent.text.decode('utf-8')
                if parent_text.startswith('use function'):
                    import_type = ImportType.USE_FUNCTION
                elif parent_text.startswith('use const'):
                    import_type = ImportType.USE_CONST
                elif 'SomeTrait' in parent_text:
                    import_type = ImportType.USE_TRAIT

            path = node.text.decode('utf-8')
            namespace = '\\'.join(path.split('\\')[:-1])
            alias = None
            if ' as ' in parent_text:
                alias = parent_text.split(' as ')[1].strip().rstrip(';')  # 去除末尾分号

            use_info.append({
                ImportKey.IMPORT_TYPE.value: import_type.value,
                ImportKey.PATH.value: None,
                ImportKey.LINE.value: node.start_point[0] + 1,
                ImportKey.NAMESPACE.value: namespace,
                ImportKey.USE_FROM.value: path,
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
