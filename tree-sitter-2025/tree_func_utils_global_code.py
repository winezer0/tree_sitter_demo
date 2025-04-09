from typing import Dict

from guess import guess_called_object_is_native
from tree_enums import MethodKeys, ClassKeys
from tree_func_utils import TREE_SITTER_PHP_METHOD_CALLED_STAT, create_method_result
from tree_func_utils_global_define import query_global_methods_define_infos
from tree_sitter_uitls import get_node_text


def get_global_code(language, root_node) -> Dict:
    """获取所有不在全局函数内的PHP代码 TODO 可能存在问题 没有排除类范围"""
    # 获取所有全局函数定义信息
    function_names, function_ranges = query_global_methods_define_infos(language, root_node)
    source_lines = get_node_text(root_node).split('\n')
    non_function_code = []
    for line_num, line_text in enumerate(source_lines):
        if not any(start <= line_num <= end for start, end in function_ranges):
            non_function_code.append({
                'line': line_num,
                'code': line_text
            })

    return {
        MethodKeys.START_LINE.value: non_function_code[0]['line'] if non_function_code else None,
        MethodKeys.END_LINE.value: non_function_code[-1]['line'] if non_function_code else None,
        'total_lines': len(non_function_code),
        'code_blocks': non_function_code,
    }


def has_global_code(root_node, class_ranges, function_ranges):
    """检查是否有(非class和非函数)全局代码的内容"""
    root_start = root_node.start_point[0]
    root_end = root_node.end_point[0]
    for i in range(root_start, root_end + 1):
        if (not any(start <= i <= end for start, end in function_ranges) and
            not any(start <= i <= end for start, end in class_ranges)):
            return True
    return False


def line_in_methods_or_classes_ranges(line_num, function_ranges, class_ranges):
    """检查行号是否在函数或类范围内"""
    return any(start <= line_num <= end for start, end in function_ranges) or any(start <= line_num <= end for start, end in class_ranges)


def query_global_code_called_methods(language, root_node, classes_names, classes_ranges, gb_methods_names,
                                     gb_methods_ranges, object_class_infos):
    """查询全部代码调用的函数信息 并且只保留其中不属于函数和类的部分"""
    queried = language.query(TREE_SITTER_PHP_METHOD_CALLED_STAT)

    nf_called_infos = []

    # 处理对象方法调用
    for match in queried.matches(root_node):
        match_dict = match[1]
        if 'member.call' in match_dict or 'static.call' in match_dict:
            # 根据静态方法和普通对象方法的语法查询结果关键字进行判断是否是静态方法
            is_static_call = 'static.call' in match_dict
            method_node = match_dict['static.call'][0] if is_static_call else match_dict['member.call'][0]
            start_line = method_node.start_point[0]

            if not line_in_methods_or_classes_ranges(start_line, gb_methods_ranges, classes_ranges):
                method_name = match_dict['method.name'][0].text.decode('utf-8')
                object_node = match_dict['method.object'][0]
                args_node = match_dict.get('method.args', [None])[0]

                object_name = object_node.text.decode('utf-8')
                object_line = object_node.start_point[0]
                class_is_native, class_name = guess_called_object_is_native(object_name, object_line, classes_names, object_class_infos)

                nf_called_info = res_called_object_method(
                    object_node, method_node, args_node, method_name, class_is_native, is_static_call, class_name)
                nf_called_infos.append(nf_called_info)

    # 处理对象创建
    for match in queried.matches(root_node):
        match_dict = match[1]
        if 'new_class_name' in match_dict:
            class_node = match_dict['new_class_name'][0]
            start_line = class_node.start_point[0]

            class_name = class_node.text.decode('utf-8')
            class_is_native = class_name in classes_names  # 构造方法 可以直接判断

            if not line_in_methods_or_classes_ranges(start_line, gb_methods_ranges, classes_ranges):
                args_node = match_dict.get('constructor_args', [None])[0]
                nf_called_info = res_called_construct_method(class_node, args_node, class_is_native)
                nf_called_infos.append(nf_called_info)

    # 处理普通函数调用
    for match in queried.matches(root_node):
        match_dict = match[1]
        if 'function_call' in match_dict:
            func_node = match_dict['function_call'][0]
            start_line = func_node.start_point[0]

            if not line_in_methods_or_classes_ranges(start_line, gb_methods_ranges, classes_ranges):
                func_name = func_node.text.decode('utf-8')
                args_node = match_dict.get('function_args', [None])[0]

                # 分析函数类型
                method_is_native = func_name in gb_methods_names
                nf_called_info = res_called_general_method(func_node, func_name, args_node, method_is_native)
                nf_called_infos.append(nf_called_info)

    # 判断函数是否有内容, 有的话进行结果返回
    if nf_called_infos:
        nf_name_txt = ClassKeys.NOT_IN_METHOD.value
        nf_start_line = root_node.start_point[0]
        nf_end_line = root_node.end_point[0]
        nf_method_info = {}
        return nf_method_info
    return None
