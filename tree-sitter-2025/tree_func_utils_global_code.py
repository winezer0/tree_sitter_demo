from typing import Dict

from tree_enums import GB_Code
from tree_func_utils_global_define import query_global_methods_define_infos, query_classes_define_infos, \
    get_node_infos_names_ranges
from tree_sitter_uitls import get_node_text


def line_in_methods_or_classes_ranges(line_num, function_ranges, class_ranges):
    """检查行号是否在函数或类范围内"""
    return any(start <= line_num <= end for start, end in function_ranges) or any(start <= line_num <= end for start, end in class_ranges)


def get_global_code_info(language, root_node,gb_methods_ranges=None,gb_classes_ranges=None) -> Dict:
    """获取所有不在全局函数和类定义内的PHP代码信息"""
    # 获取所有全局函数定义信息 (名称和范围)
    if gb_methods_ranges is None:
        _, gb_methods_ranges = get_node_infos_names_ranges(query_global_methods_define_infos(language, root_node))
    # 获取所有类定义的代码行范围 (名称和范围)，用于排除类方法
    if gb_classes_ranges is None:
        _, gb_classes_ranges = get_node_infos_names_ranges(query_classes_define_infos(language, root_node))

    # 获取源代码的每一行
    source_lines = get_node_text(root_node).split('\n')
    # 存储非函数且非类范围内的代码块
    non_function_non_class_code = []
    # 遍历每一行代码
    for line_num, line_text in enumerate(source_lines):
        # 如果当前行既不在全局函数范围内也不在类范围内，则添加到结果中
        if line_in_methods_or_classes_ranges(line_num, gb_methods_ranges, gb_classes_ranges):
            non_function_non_class_code.append({
                GB_Code.LINE.value: line_num,
                GB_Code.CODE.value: line_text.strip()  # 去除多余空格
            })

    if not non_function_non_class_code:
        return None

    # 返回结果字典
    gb_code_start_line = non_function_non_class_code[0]['line'] if non_function_non_class_code else None
    gb_code_end_line = non_function_non_class_code[-1]['line'] if non_function_non_class_code else None
    return {
        GB_Code.START_LINE.value: gb_code_start_line,
        GB_Code.END_LINE.value: gb_code_end_line,
        GB_Code.TOTAL.value: len(non_function_non_class_code),
        GB_Code.BLOCKS.value: non_function_non_class_code,
    }

def has_global_code(root_node, gb_methods_ranges, gb_classes_ranges):
    """检查是否有(非class和非函数)全局代码的内容"""
    for line_num in range(root_node.start_point[0], root_node.end_point[0] + 1):
        if line_in_methods_or_classes_ranges(line_num, gb_methods_ranges, gb_classes_ranges):
            return False
    return True


def query_global_code_called_methods(language, root_node, classes_names, classes_ranges, gb_methods_names, gb_methods_ranges, object_class_infos):
    """查询全部代码调用的函数信息 并且只保留其中不属于函数和类的部分"""

    # 方案1 获取所有代码信息 然后排除其中的 函数定义范围和类定义范围信息 再进行 代码解析
    # 方案2 解析所有代码结构 然后排除其中的 函数定义范围和类定义范围信息

    # queried = language.query(TREE_SITTER_PHP_METHOD_CALLED_STAT)
    # nf_called_infos = []
    # # 处理对象方法调用
    # for match in queried.matches(root_node):
    #     match_dict = match[1]
    #     if 'member.call' in match_dict or 'static.call' in match_dict:
    #         # 根据静态方法和普通对象方法的语法查询结果关键字进行判断是否是静态方法
    #         is_static_call = 'static.call' in match_dict
    #         method_node = match_dict['static.call'][0] if is_static_call else match_dict['member.call'][0]
    #         start_line = method_node.start_point[0]
    #
    #         if not line_in_methods_or_classes_ranges(start_line, gb_methods_ranges, classes_ranges):
    #             method_name = match_dict['method.name'][0].text.decode('utf-8')
    #             object_node = match_dict['method.object'][0]
    #             args_node = match_dict.get('method.args', [None])[0]
    #
    #             object_name = object_node.text.decode('utf-8')
    #             object_line = object_node.start_point[0]
    #             class_is_native, class_name = guess_called_object_is_native(object_name, object_line, classes_names, object_class_infos)
    #
    #             nf_called_info = res_called_object_method(
    #                 object_node, method_node, args_node, method_name, class_is_native, is_static_call, class_name)
    #             nf_called_infos.append(nf_called_info)
    #
    # # 处理对象创建
    # for match in queried.matches(root_node):
    #     match_dict = match[1]
    #     if 'new_class_name' in match_dict:
    #         class_node = match_dict['new_class_name'][0]
    #         start_line = class_node.start_point[0]
    #
    #         class_name = class_node.text.decode('utf-8')
    #         class_is_native = class_name in classes_names  # 构造方法 可以直接判断
    #
    #         if not line_in_methods_or_classes_ranges(start_line, gb_methods_ranges, classes_ranges):
    #             args_node = match_dict.get('constructor_args', [None])[0]
    #             nf_called_info = res_called_construct_method(class_node, args_node, class_is_native)
    #             nf_called_infos.append(nf_called_info)
    #
    # # 处理普通函数调用
    # for match in queried.matches(root_node):
    #     match_dict = match[1]
    #     if 'function_call' in match_dict:
    #         func_node = match_dict['function_call'][0]
    #         start_line = func_node.start_point[0]
    #
    #         if not line_in_methods_or_classes_ranges(start_line, gb_methods_ranges, classes_ranges):
    #             func_name = func_node.text.decode('utf-8')
    #             args_node = match_dict.get('function_args', [None])[0]
    #
    #             # 分析函数类型
    #             method_is_native = func_name in gb_methods_names
    #             nf_called_info = res_called_general_method(func_node, func_name, args_node, method_is_native)
    #             nf_called_infos.append(nf_called_info)
    #
    # # 判断函数是否有内容, 有的话进行结果返回
    # if nf_called_infos:
    #     nf_name_txt = ClassKeys.NOT_IN_METHOD.value
    #     nf_start_line = root_node.start_point[0]
    #     nf_end_line = root_node.end_point[0]
    #     nf_method_info = {}
    #     return nf_method_info
    # return None
