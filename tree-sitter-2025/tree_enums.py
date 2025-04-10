from enum import Enum
from typing import Dict


class NodeKeys(Enum):
    NAME = "NAME"
    START_LINE = "START"
    END_LINE = "END"
    UNIQ_ID = "UNIQ_ID"

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

    NAMESPACE = "CLASS_NAMESPACE"
    EXTENDS = "CLASS_EXTENDS"
    INTERFACES = "CLASS_INTERFACES"

    VISIBILITY = "CLASS_VISIBILITY"
    MODIFIERS = "CLASS_MODIFIERS"

    PROPERTIES = "CLASS_PROPERTIES"
    METHODS = "CLASS_METHODS"
    NOT_IN_METHOD = "NOT_IN_METHOD"               # 标志函数外的代码键

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
    UNIQ_ID = "UNIQ_ID"
    NAME = "METHOD_NAME"                # 方法名
    FULLNAME = "METHOD_FULLNAME"        # 类名+方法名
    START_LINE = "METHOD_START_LINE"    # 方法开始行
    END_LINE = "METHOD_END_LINE"        # 方法结束行

    VISIBILITY = "METHOD_VISIBILITY"    # 方法的可访问性
    MODIFIERS = "METHOD_MODIFIERS"      # 方法的特殊描述符

    RETURNS = "METHOD_RETURNS"          # 方法的返回信息 存在多个返回语句

    PARAMS = "METHOD_PARAMETERS"        # 方法的参数信息

    FILE = "METHOD_FILE"                 # 方法所处的物理文件路径
    CLASS = "METHOD_CLASS"             # 方法所属的类
    OBJECT = "METHOD_OBJECT"             # 方法所属的对象
    IS_NATIVE = "IS_NATIVE_METHOD"      # 被调用方法是否在本文件中定义 使用bool类型
    METHOD_TYPE = "METHOD_TYPE"         # 方法的类型信息

    CALLED = "CALLED_METHODS"   # 方法内部调用的方法列表
    CALLED_MAY = "CALLED_MAY"           # 方法内部调用的方法列表 可能
    CALLED_BY_MAY = "CALLED_BY_MAY"     # 方法被哪些外部方法调用 可能

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

    CLASS = "CLASS_METHOD"          # 自定义的类方法
    CONSTRUCT = "CONSTRUCT_METHOD"  # 类的构造方法 需要额外处理
    MAGIC = "MAGIC_METHOD"          # 类的魔术方法 直接忽略处理


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

    @classmethod
    def get_type(cls, node, var_name: str, global_vars: Dict, is_global_declaration: bool = False) -> 'VariableType':
        """确定变量类型的类方法"""
        # print(f"Debug - get_type for {var_name}, is_global_declaration: {is_global_declaration}")

        # 超全局变量优先判断
        if var_name in SUPER_GLOBALS:
            # print(f"Debug - {var_name} is superglobal")
            return cls.SUPER_GLOBAL

        # 检查是否是全局声明
        if is_global_declaration:
            # print(f"Debug - {var_name} is global (declared)")
            return cls.GLOBAL

        current_node = node
        while current_node:
            # print(f"Debug - Checking node type: {current_node.type}")
            # 静态变量声明
            if current_node.type == 'static_variable_declaration':
                # print(f"Debug - {var_name} is static")
                return cls.STATIC
            # 在函数内部
            elif current_node.type == 'function_definition':
                if var_name in global_vars:
                    # print(f"Debug - {var_name} is global (used in function)")
                    return cls.GLOBAL
                # print(f"Debug - {var_name} is local")
                return cls.LOCAL
            # 检查是否在文件顶层使用了 global 关键字
            elif current_node.type == 'global_declaration' and current_node.parent.type == 'program':
                # print(f"Debug - {var_name} is global (file level declaration)")
                return cls.GLOBAL
            current_node = current_node.parent

        # 文件顶层直接使用的变量
        if node.parent and node.parent.type == 'program':
            # print(f"Debug - {var_name} is local (file level usage)")
            return cls.LOCAL

        # print(f"Debug - {var_name} is file level")
        return cls.PROGRAM
