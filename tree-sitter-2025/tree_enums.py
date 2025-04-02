from enum import Enum, auto

class MethodType(Enum):
    """方法类型枚举"""
    CLASS_METHOD = "CLASS_METHOD"     # 类方法
    LOCAL_METHOD = "LOCAL_METHOD"     # 本地方法
    BUILTIN_METHOD = "BUILTIN_METHOD" # 内置方法
    CUSTOM_METHOD = "CUSTOM_METHOD"   # 自定义方法
    DYNAMIC_METHOD = "DYNAMIC_METHOD" # 动态方法

class PHPVisibility(Enum):
    """PHP访问修饰符枚举"""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"

class PHPModifier(Enum):
    """PHP特殊修饰符枚举"""
    STATIC = "static"
    ABSTRACT = "abstract"
    FINAL = "final"
    READONLY = "readonly"
    INTERFACE = "interface"


class PHPParameterType(Enum):
    """PHP参数类型枚举"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"
    MIXED = "mixed"


class PHPPropertyType(Enum):
    """PHP属性类型枚举"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"