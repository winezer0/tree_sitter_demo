from tree_enums import DefineKeys
from tree_sitter_uitls import find_first_child_by_field, get_strs_hash


def query_namespace_define_infos(language, root_node):
    """获取所有本地命名空间的定义 返回node字典格式"""
    namespace_define_query = language.query("""
    ;匹配命名空间定义信息
    (namespace_definition
        name: (namespace_name) @namespace_name
    ) @namespace.def
    """)
    # 提取命名空间信息
    namespace_infos = extract_namespace_node_define_infos(root_node, namespace_define_query, 'namespace.def', need_node_field='name')
    return namespace_infos


def extract_namespace_node_define_infos(root_node, query, node_field, need_node_field='name'):
    """获取namespace_node节点的名称和行信息 返回字典格式"""
    infos = []
    for match in query.matches(root_node):
        match_dict = match[1]
        if node_field in match_dict:
            total_node = match_dict[node_field][0]
            if total_node:
                # 提取命名空间名称
                need_node = find_first_child_by_field(total_node, need_node_field)
                need_text = need_node.text.decode('utf8')

                # 获取命名空间的起始行号
                start_point = total_node.start_point[0]
                end_point = None

                # 检查是否有显式代码块
                has_explicit_body = False
                for child in total_node.children:
                    if child.type == 'declaration_list':  # 显式代码块
                        has_explicit_body = True
                        end_point = child.end_point[0]
                        break

                # 如果没有显式代码块，则查找后续代码的范围
                if not has_explicit_body:
                    next_sibling = total_node.next_named_sibling
                    while next_sibling:
                        if next_sibling.type in ['namespace_definition', 'program']:
                            # 遇到下一个命名空间或文件末尾时停止
                            break
                        end_point = next_sibling.end_point[0]
                        next_sibling = next_sibling.next_named_sibling

                # 如果仍然没有找到结束行号，则使用命名空间声明的结束行号
                if not end_point:
                    end_point = total_node.end_point[0]

                # 构造命名空间信息
                node_info = {
                    DefineKeys.NAME.value: need_text,
                    DefineKeys.START.value: start_point,
                    DefineKeys.END.value: end_point,
                    DefineKeys.UNIQ_ID.value: get_strs_hash(need_text, start_point, end_point),
                }
                infos.append(node_info)
    return infos


if __name__ == '__main__':
    # 解析tree
    from tree_sitter_uitls import init_php_parser, read_file_to_root
    from libs_com.utils_json import print_json

    PARSER, LANGUAGE = init_php_parser()
    php_file = r"php_demo/namespace_demo/namespace.php"
    root_node = read_file_to_root(PARSER, php_file)
    namespace_infos = query_namespace_define_infos(LANGUAGE, root_node)
    print_json(namespace_infos)