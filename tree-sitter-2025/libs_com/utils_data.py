from libs_com.constant import *


def to_lower_list(lis):
    # 格式化过滤条件
    return [x.lower() for x in lis] if lis else None


def init_cacha_dict():
    return {CACHE_RESULT: {}, CACHE_UPDATE: None}


