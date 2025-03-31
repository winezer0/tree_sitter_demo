from libs_com.file_io import write_string
from libs_com.utils_json import dumps_json


def save_cache_if_needed(cache_file, cache_data, cache_time, last_cache_time, save_interval, force_store) -> tuple:
    """检查是否需要保存缓存"""
    total_seconds = (cache_time - last_cache_time).total_seconds()
    if force_store or (0 < save_interval <= total_seconds):
        try:
            # 根据数据类型分别处理
            if isinstance(cache_data, (dict, list)):
                # dump_status, dump_error = dump_json(cache_file, cache_data)
                # 尝试copy看有没有缓存报错 没有用
                # cache_copy = copy.deepcopy(cache_data)  # dictionary changed size during iteration
                # 转换为json再进行写入
                json_str, dump_error = dumps_json(cache_data)  # dictionary changed size during iteration
                if dump_error:
                    raise dump_error
                if json_str:
                    dump_status, dump_error = write_string(cache_file, json_str)
                    if dump_error:
                        raise dump_error
            elif isinstance(cache_data, str):
                dump_status, dump_error = write_string(cache_file, cache_data)
                if dump_error:
                    raise dump_error
            else:
                dump_error = TypeError(f"非预期的缓存格式类型:{type(cache_data)}")
                if dump_error:
                    raise dump_error
            return True, None
        except Exception as error:
            print(f"\n保存缓存失败: {error}")
            return False, error
    else:
        return False, None
