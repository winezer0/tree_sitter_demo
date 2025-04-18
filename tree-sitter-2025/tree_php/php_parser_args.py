import argparse
import os


def parse_php_parser_args():
    parser = argparse.ArgumentParser(description='分析php项目代码语法结构 用于静态分析时补充代码信息')
    parser.add_argument('-p', '--project-path', default=None, help='需要扫描的目标项目地址')
    parser.add_argument('-n', '--project-name', default='default_project', help='项目名称 影响输出分析结果文件名')
    # 性能配置 os.cpu_count()
    parser.add_argument('-w', '--workers', type=int, default=1, help='线程数 (默认: CPU 核心数)')
    parser.add_argument('-o', '--output', default=None, help='分析结果文件路径 (默认: {project}_result.json)')
    # 性能配置
    parser.add_argument('-s', '--save-cache', action='store_false', default=True, help='缓存分析结果 (默认: True)!!!')
    # 过滤配置
    parser.add_argument('-e', '--exclude-dir', nargs='+', default=[], help='排除目录路径关键字列表, 支持部分路径和完整路径 (例如: test/ build/)')
    args = parser.parse_args()
    return args