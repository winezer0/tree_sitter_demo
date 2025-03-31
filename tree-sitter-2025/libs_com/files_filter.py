import os
from typing import List


def get_php_files(file_path, skip_dirs=['temp/compiled', 'vendor', 'node_modules']):
    """获取指定目录下的PHP文件"""
    php_files = []

    # 如果指定了单个文件
    if os.path.isfile(file_path):
        return [file_path]

    # 递归扫描目录
    for root, _, files in os.walk(file_path):
        # 跳过特定目录
        if any(skip_dir in root.replace('\\', '/') for skip_dir in skip_dirs):
            continue

        for file in files:
            if file.endswith('.php'):
                php_files.append(os.path.join(root, file))
    return php_files


def get_files_with_filter(directory: str, exclude_suffixes: List[str], exclude_keys: List[str] = None) -> List[str]:
    """
    获取目录下的所有文件，并根据排除后缀和关键字排除不需要的文件和目录。
    参数:
        directory (str): 要遍历的根目录。
        exclude_suffixes (List[str]): 需要排除的文件后缀列表。
        exclude_keys (List[str]): 需要排除的目录关键字列表。
    返回:
        List[str]: 符合条件的所有文件路径列表。
    """

    def _format_path(path: str):
        if path:
            path = str(path).replace("\\", "/").replace("//", "/")
        return path

    exclude_keys = [_format_path(x) for x in (exclude_keys or [])]
    files = []
    for root, dirs, filenames in os.walk(directory):
        # 检查当前目录路径是否包含任何需要排除的关键字
        if any(key in _format_path(root) for key in exclude_keys):
            # 忽略包含关键字的目录及其子目录
            continue
        # 过滤掉需要排除的目录
        dirs[:] = [d for d in dirs if not any(key in _format_path(os.path.join(root, d)) for key in exclude_keys)]
        # 进行后缀排除
        for filename in filenames:
            if not any(filename.endswith(suffix) for suffix in exclude_suffixes):
                files.append(os.path.join(root, filename))
    return files


def file_is_larger(file_path, limit=1):
    """判断指定路径的文件大小是否超过1MB。 """
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        mb_in_bytes = 1024 * 1024 * limit
        return file_size > mb_in_bytes
    else:
        print(f"Error: 文件 {file_path} 不存在,返回False")
    return False


def in_allowed_suffixes(filename: str, suffixes: str) -> bool:
    """检查文件是否需要根据规则进行处理"""
    if suffixes == '*':
        return True
    if isinstance(suffixes, str):
        suffixes = suffixes.split("|")
    if any(filename.endswith(suffix) for suffix in suffixes):
        return True
    return False
