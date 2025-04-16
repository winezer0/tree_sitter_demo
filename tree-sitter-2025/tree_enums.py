from enum import Enum
from typing import Dict


class DefineKeys(Enum):
    UNIQ_ID = "UNIQ_ID"
    NAME = "NAME"
    START_LINE = "START"
    END_LINE = "END"

class FileInfoKeys(Enum):
    """文件信息相关的键"""
    METHOD_INFOS = "METHOD_INFOS"
    CLASS_INFOS = "CLASS_INFOS"
    IMPORT_INFOS = "IMPORT_INFOS"
    VARIABLE_INFOS = "VARIABLE_INFOS"

class ClassKeys(Enum):
    """类信息相关的键"""
    UNIQ_ID = "UNIQ_ID"                 # 综合属性计算出来的一个ID
    FILE = "FILE"                 # 所处的物理文件路径

    NAME = "CLASS_NAME"
    START_LINE = "CLASS_START_LINE"
    END_LINE = "CLASS_END_LINE"

    NAMESPACE = "CLASS_NAMESPACE"
    EXTENDS = "CLASS_EXTENDS"
    INTERFACES = "CLASS_INTERFACES"

    VISIBILITY = "CLASS_VISIBILITY"
    MODIFIERS = "CLASS_MODIFIERS"

    PROPERTIES = "CLASS_PROPERTIES"
    METHODS = "CLASS_METHODS"

    IS_INTERFACE = "IS_INTERFACE"

class PHPVisibility(Enum):
    """PHP访问修饰符枚举"""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"

    @classmethod
    def from_value(cls, value):
        """根据值查找对应的枚举元素，忽略大小写。"""
        search_value = value.lower()  # 将输入值转为小写
        for item in cls:
            if item.value.lower() == search_value:  # 比较时也转为小写
                return item
        raise ValueError(f"No enum member found with value '{value}'")

class PHPModifier(Enum):
    """PHP特殊修饰符枚举"""
    STATIC = "static"
    ABSTRACT = "abstract"
    FINAL = "final"
    READONLY = "readonly"
    INTERFACE = "interface"

class PropertyKeys(Enum):
    """属性信息相关的键"""
    NAME = "PROPERTY_NAME"
    DEFAULT = "PROPERTY_DEFAULT"
    VISIBILITY = "PROPERTY_VISIBILITY"
    MODIFIERS = "PROPERTY_MODIFIERS"
    TYPE = "PROPERTY_TYPE"
    START_LINE = "START_LINE"
    END_LINE = "END_LINE"

class MethodKeys(Enum):
    """方法信息相关的键"""
    UNIQ_ID = "UNIQ_ID"                 # 综合属性计算出来的一个ID
    FILE = "METHOD_FILE"                 # 所处的物理文件路径
    NAMESPACE = "METHOD_NAMESPACE"       # 方法所在的命名空间信息

    NAME = "METHOD_NAME"                # 方法名
    FULLNAME = "METHOD_FULLNAME"        # 类名+方法名
    START_LINE = "METHOD_START_LINE"    # 方法开始行
    END_LINE = "METHOD_END_LINE"        # 方法结束行

    VISIBILITY = "METHOD_VISIBILITY"    # 方法的可访问性
    MODIFIERS = "METHOD_MODIFIERS"      # 方法的特殊描述符

    RETURNS = "METHOD_RETURNS"          # 方法的返回信息 存在多个返回语句

    PARAMS = "METHOD_PARAMETERS"        # 方法的参数信息

    METHOD_CLASS = "METHOD_CLASS"             # 方法所属的类
    OBJECT = "METHOD_OBJECT"             # 方法所属的对象
    IS_NATIVE = "IS_NATIVE_METHOD"      # 被调用方法是否在本文件中定义 使用bool类型
    METHOD_TYPE = "METHOD_TYPE"         # 方法的类型信息

    CALLED = "CALLED_METHODS"   # 方法内部调用的方法列表
    CALLED_POSSIBLE = "CALLED_POSSIBLE"           # 方法内部调用的方法列表 可能
    # CALLED_BY_MAY = "CALLED_BY_MAY"     # 方法被哪些外部方法调用 可能

class ParameterKeys(Enum):
    """参数信息相关的键"""
    NAME = "PARAM_NAME"
    TYPE = "PARAM_TYPE"
    DEFAULT = "PARAM_DEFAULT"
    VALUE = "PARAM_VALUE"
    INDEX = "PARAM_INDEX"


class ReturnKeys(Enum):
    """方法类型"""
    NAME = "RETURN_NAME"
    TYPE = "RETURN_TYPE"
    VALUE = "RETURN_VALUE"
    START = "START_LINE"
    END = "END_LINE"


class GlobalCode(Enum):
    """方法类型"""
    START = "START_LINE"
    END = "END_LINE"
    TOTAL = "TOTAL"
    BLOCKS = "BLOCKS"
    LINE = "LINE"
    CODE = "CODE"


class MethodType(Enum):
    """方法类型"""
    GENERAL = "GENERAL_METHOD"      # 自定义的普通方法
    BUILTIN = "BUILTIN_METHOD"      # PHP内置方法
    DYNAMIC = "DYNAMIC_METHOD"      # 动态方法 （使用变量作为函数名）

    CONSTRUCT = "CONSTRUCT_METHOD"  # 类的构造方法 需要额外处理
    MAGIC_METHOD = "MAGIC_METHOD"          # 类的魔术方法 直接忽略处理
    CLASS_METHOD = "CLASS_METHOD"          # 自定义的类方法


# 常量定义
SUPER_GLOBALS = [
    '$_GET', '$_POST', '$_REQUEST', '$_SESSION',
    '$_COOKIE', '$_SERVER', '$_FILES', '$_ENV', '$GLOBALS'
]

class VariableType(Enum):
    """变量类型枚举"""
    LOCAL = 'local'
    STATIC = 'static'
    GLOBAL = 'global'
    PROGRAM = 'program'
    SUPER_GLOBAL = 'superglobal'
    CONSTANT = 'CONSTANT'



class VariableKeys(Enum):
    """信息字典相关的键"""
    NAME = "name"
    VALUE = "value"
    NAME_TYPE = "name_type"
    VALUE_TYPE = "value_type"
    START_LINE = "start_line"
    END_LINE = "end_line"
    FULL_TEXT = "full_text"
    FUNCTION = "function"

class OtherName(Enum):
    NOT_IN_METHOD = "GLOBAL_CODE"               # 标志函数外的代码键
    ANONYMOUS = "ANONYMOUS"


class ImportType(Enum):
    BASE_IMPORT = "BASE_IMPORT" # 大分类 标准的导入方法
    AUTO_IMPORT = "AUTO_IMPORT" # 大分类 自动导入规则

    INCLUDE = 'include'
    INCLUDE_ONCE = 'include_once'
    REQUIRE = 'require'
    REQUIRE_ONCE = 'require_once'

    USE_CLASS = 'use_class'
    USE_FUNCTION = 'use_function'
    USE_CONST = 'use_const'
    USE_TRAIT = 'use_trait'
    USE_OTHER = 'use_other'
    # USE_GROUP = 'use_group'  # 新增
    # USE_ALIAS = 'use_alias'  # 新增


class ImportKey(Enum):
    TYPE = 'import_type'
    PATH = 'import_path'
    NAMESPACE = 'namespace'
    USE_FROM = 'use_from'
    ALIAS = 'alias'
    START_LINE = 'start_line'
    END_LINE = 'end_line'
    FULL_TEXT = 'full_text'
