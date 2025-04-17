import os


def get_now_dir_file_path(path):
    return os.path.join(os.path.dirname(__file__), path)


def get_abspath(config_file):
    if config_file != os.path.abspath(config_file):
        config_file = os.path.join(os.path.dirname(__file__), config_file)
    return config_file


def get_root_dir(project_path):
    return os.path.abspath(project_path if os.path.isdir(project_path) else os.path.dirname(project_path))


def get_relative_path(absolute_path: str, project_root: str) -> str:
    """将绝对路径转换为相对于项目根目录的路径"""
    if not project_root:
        return absolute_path
    try:
        rel_path = os.path.relpath(absolute_path, project_root)
        return rel_path.replace('\\', '/')  # 统一使用正斜杠
    except ValueError:
        return absolute_path


def get_base_dir():
    return os.path.dirname(os.path.abspath(__file__))


def path_is_exist(file_path):
    # 判断文件是否存在
    return os.path.exists(file_path)


def file_is_empty(file_path):
    # 判断一个文件是否为空
    return not os.path.exists(file_path) or not os.path.getsize(file_path)
