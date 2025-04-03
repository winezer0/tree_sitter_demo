from enum import Enum

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


class FileInfoKeys(Enum):
    """文件信息相关的键"""
    METHOD_INFOS = "METHOD_INFOS"
    IMPORT_INFOS = "IMPORT_INFOS"
    VARIABLE_INFOS = "VARIABLE_INFOS"
    CONSTANT_INFOS = "CONSTANT_INFOS"
    CLASS_INFOS = "CLASS_INFOS"


class ClassKeys(Enum):
    """类信息相关的键"""
    NAME = "CLASS_NAME"
    START_LINE = "CLASS_START_LINE"
    END_LINE = "CLASS_END_LINE"
    EXTENDS = "CLASS_EXTENDS"
    INTERFACES = "CLASS_INTERFACES"
    NAMESPACE = "CLASS_NAMESPACE"
    VISIBILITY = "CLASS_VISIBILITY"
    MODIFIERS = "CLASS_MODIFIERS"
    PROPERTIES = "CLASS_PROPERTIES"
    METHODS = "CLASS_METHODS"
    NOT_IN_METHOD = "NOT_IN_METHOD"               # 标志函数外的代码键


class PropertyKeys(Enum):
    """属性信息相关的键"""
    NAME = "PROPERTY_NAME"
    LINE = "PROPERTY_LINE"
    INITIAL_VALUE = "PROPERTY_INITIAL_VALUE"
    VISIBILITY = "PROPERTY_VISIBILITY"
    MODIFIERS = "PROPERTY_MODIFIERS"
    TYPE = "PROPERTY_TYPE"


class MethodKeys(Enum):
    """方法信息相关的键"""
    NAME = "METHOD_NAME"
    START_LINE = "METHOD_START_LINE"
    END_LINE = "METHOD_END_LINE"
    OBJECT = "METHOD_OBJECT"
    FULL_NAME = "METHOD_FULL_NAME"
    VISIBILITY = "METHOD_VISIBILITY"
    MODIFIERS = "METHOD_MODIFIERS"
    RETURN_TYPE = "METHOD_RETURN_TYPE"
    RETURN_VALUE = "METHOD_RETURN_VALUE"
    METHOD_TYPE = "METHOD_TYPE"
    PARAMS = "METHOD_PARAMETERS"
    CALLED = "CALLED_METHODS"
    CALLED_BY = "CALLED_BY_METHODS"     # 方法被哪些方法调用
    FILE = "METHOD_FILE"                 # 方法所处的物理文件路径
    CLASS = "METHOD_CLASS"               # 方法所属的类

class ParameterKeys(Enum):
    """参数信息相关的键"""
    PARAM_NAME = "PARAM_NAME"
    PARAM_TYPE = "PARAM_TYPE"
    PARAM_DEFAULT = "PARAM_DEFAULT"
    PARAM_VALUE = "PARAM_VALUE"
    PARAM_INDEX = "PARAM_INDEX"

class MethodType(Enum):
    """方法类型"""
    BUILTIN = "BUILTIN_METHOD"      # PHP内置方法
    DYNAMIC = "DYNAMIC_METHOD"      # 动态方法 （使用变量作为函数名）
    CLASS = "CLASS_METHOD"          # 自定义的类方法
    GLOBAL = "GLOBAL_METHOD"        # 自定义的普通方法
    CONSTRUCT = "CONSTRUCT_METHOD"  # 类的构造方法 需要额外处理
    IS_NATIVE = "IS_NATIVE_METHOD"  # 表示是否在本文件中定义 使用bool类型
