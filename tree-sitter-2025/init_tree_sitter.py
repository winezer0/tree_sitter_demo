import tree_sitter_php
from tree_sitter import Language, Parser

def init_php_parser():
    """
    初始化 tree-sitter PHP 解析器
    tree_sitter>0.21.3 （test on 0.24.0 0.23.2）
    """
    PHP_LANGUAGE = Language(tree_sitter_php.language_php())
    php_parser = Parser(PHP_LANGUAGE)
    return php_parser, PHP_LANGUAGE
