import hashlib
import json
import os
from typing import Dict

from libs_com.constant import *


def get_rule_hash(rule: Dict) -> str:
    # 计算扫描规则的哈希值
    return hashlib.md5(json.dumps(sorted(rule.get(PATTERNS, []))).encode()).hexdigest()


def get_path_hash(rules_path):
    return hashlib.md5(f"{os.path.abspath(rules_path)}".encode()).hexdigest()[:8]


def get_vuln_hash(vuln_info: dict) -> str:
    # 计算漏洞信息的哈希值
    key_data = {
        FILE_S: vuln_info.get(FILE_S),
        VULNERABILITY: vuln_info.get(VULNERABILITY),
        LINE_NUMBER: vuln_info.get(LINE_NUMBER),
    }
    return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()


def get_strs_hash(*args):
    # 计算传入的任意个字符串的MD5哈希值，并返回前8个字符。
    if not args:
        raise ValueError("至少需要提供一个字符串参数")
    # 将所有字符串连接成一个单一的字符串
    concatenated_string = ''.join(str(arg) for arg in args)
    # 计算并返回哈希值的前8个字符
    hash_object = hashlib.md5(concatenated_string.encode('utf-8'))
    return hash_object.hexdigest()[:8]
