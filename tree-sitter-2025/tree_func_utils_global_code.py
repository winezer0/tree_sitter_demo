from typing import Dict

from tree_enums import ClassKeys, GlobalCode
from tree_func_utils import query_method_called_methods
from tree_func_utils_sub_parse import create_method_result
from tree_func_utils_global_define import query_gb_methods_define_infos, query_gb_classes_define_infos, \
    get_node_infos_names_ranges
from tree_sitter_uitls import get_node_text, load_str_to_parse


def line_in_methods_or_classes_ranges(line_num, function_ranges, class_ranges):
    """检查行号是否在函数或类范围内"""
    return any(start <= line_num <= end for start, end in function_ranges) or any(start <= line_num <= end for start, end in class_ranges)


def has_global_code(root_node, gb_methods_ranges, gb_classes_ranges):
    """检查是否有(非class和非函数)全局代码的内容"""
    for line_num in range(root_node.start_point[0], root_node.end_point[0] + 1):
        if not line_in_methods_or_classes_ranges(line_num, gb_methods_ranges, gb_classes_ranges):
            return True
    return False

def get_global_code_info(language, root_node,gb_methods_ranges,gb_classes_ranges) -> Dict:
    """获取所有不在全局函数和类定义内的PHP代码信息"""
    # 获取所有全局函数定义信息 (名称和范围)
    if gb_methods_ranges is None:
        _, gb_methods_ranges = get_node_infos_names_ranges(query_gb_methods_define_infos(language, root_node))
    # 获取所有类定义的代码行范围 (名称和范围)，用于排除类方法
    if gb_classes_ranges is None:
        _, gb_classes_ranges = get_node_infos_names_ranges(query_gb_classes_define_infos(language, root_node))

    # 获取源代码的每一行
    source_lines = get_node_text(root_node).split('\n')
    # 存储非函数且非类范围内的代码块
    non_function_non_class_code = []
    # 遍历每一行代码
    for line_num, line_text in enumerate(source_lines):
        # 如果当前行既不在全局函数范围内也不在类范围内，则添加到结果中
        if not line_in_methods_or_classes_ranges(line_num, gb_methods_ranges, gb_classes_ranges):
            code_info = {
                GlobalCode.LINE.value: line_num,
                GlobalCode.CODE.value: line_text.strip()  # 去除多余空格
            }
            non_function_non_class_code.append(code_info)

    if not non_function_non_class_code:
        return None

    # 返回结果字典
    gb_code_start_line = non_function_non_class_code[0][GlobalCode.LINE.value] if non_function_non_class_code else None
    gb_code_end_line = non_function_non_class_code[-1][GlobalCode.LINE.value] if non_function_non_class_code else None
    global_code_info = {
        GlobalCode.START.value: gb_code_start_line,
        GlobalCode.END.value: gb_code_end_line,
        GlobalCode.TOTAL.value: len(non_function_non_class_code),
        GlobalCode.BLOCKS.value: non_function_non_class_code,
    }
    return global_code_info

def get_global_code_string(global_code_info):
    if not global_code_info:
        return None

    # 提取 START 和 END 行号
    nf_start_line = global_code_info[GlobalCode.START.value]
    nf_end_line = global_code_info[GlobalCode.END.value]

    # 提取 BLOCKS 并按 LINE 排序
    code_blocks = global_code_info[GlobalCode.BLOCKS.value]
    sorted_blocks = sorted(code_blocks, key=lambda x: x[GlobalCode.LINE.value])

    # 构建完整的行号空代码
    codes = ["" for _ in range(nf_start_line, nf_end_line + 1)]
    # 填充代码数据
    for block in sorted_blocks:
        line_num = block[GlobalCode.LINE.value]
        codes[line_num] = block[GlobalCode.CODE.value]

    # 将所有代码拼接成字符串
    return "\n".join(codes)

def query_global_code_called_methods(parser, language, root_node, gb_classes_names, gb_classes_ranges,
                                     gb_methods_names, gb_methods_ranges, gb_object_class_infos):
    """查询全部代码调用的函数信息 并且只保留其中不属于函数和类的部分"""
    if not has_global_code(root_node, gb_methods_ranges, gb_classes_ranges):
        print("文件中不存在全局性代码...")
        return None

    print("开始进行全局性代码额外处理...")
    # 方案1 获取所有代码信息 然后排除其中的 函数定义范围和类定义范围信息 再进行 代码解析
    # TODO 存在一个问题, gb_object_class_infos 中的行索引信息不匹配了
    global_code_info = get_global_code_info(language, root_node, gb_methods_ranges, gb_classes_ranges)
    print(f"global_code_info:{global_code_info}")

    nf_name_txt = ClassKeys.NOT_IN_METHOD.value
    nf_start_line = global_code_info[GlobalCode.START.value]
    nf_end_line = global_code_info[GlobalCode.END.value]

    # 解析全局代码数据
    nf_global_code = get_global_code_string(global_code_info)
    if not nf_global_code:
        return None

    nf_code_tree = load_str_to_parse(parser, nf_global_code)
    nf_code_node = nf_code_tree.root_node
    nf_code_called_methods = query_method_called_methods(language, nf_code_node, gb_classes_names, gb_methods_names, gb_object_class_infos)

    return create_method_result(uniq_id=None, method_name=nf_name_txt, start_line=nf_start_line, end_line=nf_end_line,
                            object_name=None, class_name=None, fullname=nf_name_txt, method_file=None,
                            visibility=None, modifiers=None, method_type=None, params_info=None,
                            return_infos=None, is_native=None, called_methods=nf_code_called_methods)
