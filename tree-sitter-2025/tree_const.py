import os

from tree_enums import FileInfoKeys, ClassKeys, PropertyKeys, MethodKeys, ParameterKeys, MethodType


# 保持原有的函数加载内置函数列表
def load_php_builtin_functions():
    functions = set()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'PHP_BUILTIN_FUNCTIONS.txt')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    functions.add(line)
        return functions
    except FileNotFoundError:
        print(f"警告: 未找到函数列表文件 {file_path}")
        return set()

PHP_BUILTIN_FUNCTIONS = load_php_builtin_functions()
PHP_MAGIC_METHODS = [
    '__construct',   # 构造函数，在对象创建时调用
    '__destruct',    # 析构函数，在对象销毁时调用
    '__call',        # 在调用不可访问的方法时触发
    '__callStatic',  # 在调用不可访问的静态方法时触发
    '__get',         # 在尝试读取不可访问的属性时触发
    '__set',         # 在尝试设置不可访问的属性时触发
    '__isset',       # 在对不可访问的属性调用 isset() 或 empty() 时触发
    '__unset',       # 在对不可访问的属性调用 unset() 时触发
    '__toString',    # 在将对象当作字符串使用时触发
    '__invoke',      # 在尝试将对象当作函数调用时触发
    '__clone',       # 在克隆对象时触发
    '__sleep',       # 在序列化对象前触发
    '__wakeup',      # 在反序列化对象后触发
    '__serialize',   # 在序列化对象时触发（PHP 7.4+）
    '__unserialize', # 在反序列化对象时触发（PHP 7.4+）
    '__set_state',   # 在调用 var_export() 导出对象时触发
    '__debugInfo',   # 在使用 var_dump() 输出对象时触发
    '__autoload',    # 自动加载类（已弃用，推荐使用 spl_autoload_register）
]


# 文件相关常量映射
METHOD_INFOS = FileInfoKeys.METHOD_INFOS.value
CLASS_INFOS = FileInfoKeys.CLASS_INFOS.value
IMPORT_INFOS = FileInfoKeys.IMPORT_INFOS.value
VARIABLE_INFOS = FileInfoKeys.VARIABLE_INFOS.value
CONSTANT_INFOS = FileInfoKeys.CONSTANT_INFOS.value

# 类相关常量映射
CLASS_NAME = ClassKeys.NAME.value
CLASS_START_LINE = ClassKeys.START_LINE.value
CLASS_END_LINE = ClassKeys.END_LINE.value
CLASS_EXTENDS = ClassKeys.EXTENDS.value
CLASS_INTERFACES = ClassKeys.INTERFACES.value
CLASS_NAMESPACE = ClassKeys.NAMESPACE.value
CLASS_VISIBILITY = ClassKeys.VISIBILITY.value
CLASS_MODIFIERS = ClassKeys.MODIFIERS.value
CLASS_PROPERTIES = ClassKeys.PROPERTIES.value
CLASS_METHODS = ClassKeys.METHODS.value

# 类属性相关常量映射
PROPERTY_NAME = PropertyKeys.NAME.value
PROPERTY_LINE = PropertyKeys.LINE.value
PROPERTY_INITIAL_VALUE = PropertyKeys.INITIAL_VALUE.value
PROPERTY_VISIBILITY = PropertyKeys.VISIBILITY.value
PROPERTY_MODIFIERS = PropertyKeys.MODIFIERS.value
PROPERTY_TYPE = PropertyKeys.TYPE.value

# 类方法|普通方法相关常量映射
METHOD_NAME = MethodKeys.NAME.value
METHOD_START_LINE = MethodKeys.START_LINE.value
METHOD_END_LINE = MethodKeys.END_LINE.value
METHOD_OBJECT = MethodKeys.OBJECT.value
METHOD_FULL_NAME = MethodKeys.FULL_NAME.value
METHOD_VISIBILITY = MethodKeys.VISIBILITY.value
METHOD_MODIFIERS = MethodKeys.MODIFIERS.value
METHOD_RETURN_TYPE = MethodKeys.RETURN_TYPE.value
METHOD_RETURN_VALUE = MethodKeys.RETURN_VALUE.value
METHOD_TYPE = MethodKeys.TYPE.value
METHOD_PARAMETERS = MethodKeys.PARAMETERS.value
CALLED_METHODS = MethodKeys.CALLED_METHODS.value
CALLED_BY_METHODS = MethodKeys.CALLED_BY_METHODS.value
METHOD_FILE = MethodKeys.METHOD_FILE.value
NOT_IN_FUNCS = MethodKeys.NOT_IN_FUNCS.value

# 类方法|普通方法类型常量映射
BUILTIN_METHOD = MethodType.BUILTIN_METHOD.value
LOCAL_METHOD = MethodType.LOCAL_METHOD.value
DYNAMIC_METHOD = MethodType.DYNAMIC_METHOD.value
CONSTRUCTOR = MethodType.CONSTRUCTOR.value
CUSTOM_METHOD = MethodType.CUSTOM_METHOD.value
CLASS_METHOD = MethodType.CLASS_METHOD.value

# 方法参数相关常量映射
PARAMETER_NAME = ParameterKeys.NAME.value
PARAMETER_TYPE = ParameterKeys.TYPE.value
PARAMETER_DEFAULT = ParameterKeys.DEFAULT.value
PARAMETER_VALUE = ParameterKeys.VALUE.value
PARAMETER_INDEX = ParameterKeys.INDEX.value