from enum import Enum, auto

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
    NOT_IN_FUNCS = "NOT_IN_FUNCS"
    CALLS = "CALLS"
    CALLED_BY = "CALLED_BY"
    CODE_FILE = "CODE_FILE"


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
    TYPE = "METHOD_TYPE"
    PARAMETERS = "METHOD_PARAMETERS"
    CALLED_METHODS = "CALLED_METHODS"


class ParameterKeys(Enum):
    """参数信息相关的键"""
    NAME = "PARAMETER_NAME"
    TYPE = "PARAMETER_TYPE"
    DEFAULT = "PARAMETER_DEFAULT"
    VALUE = "PARAMETER_VALUE"
    INDEX = "PARAMETER_INDEX"

class MethodType(Enum):
    """方法类型"""
    CLASS_METHOD = "CLASS_METHOD"     # 类方法
    LOCAL_METHOD = "LOCAL_METHOD"     # 本地方法
    BUILTIN_METHOD = "BUILTIN_METHOD" # 内置方法
    CUSTOM_METHOD = "CUSTOM_METHOD"   # 自定义方法
    DYNAMIC_METHOD = "DYNAMIC_METHOD" # 动态方法
    CONSTRUCTOR = "CONSTRUCTOR"         # 类的构造方法 需要额外处理
    OBJECT_METHOD = "OBJECT_METHOD"
    STATIC_METHOD = "STATIC_METHOD"
    FILES_METHOD = "FILES_METHOD"
    METHOD_CLASS = "METHOD_CLASS"     # 方法所属的类
