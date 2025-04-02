import os

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

# 存储文件对应的信息的键
METHOD_INFOS = "METHOD_INFOS"
IMPORT_INFOS = "IMPORT_INFOS"
VARIABLE_INFOS = 'VARIABLE_INFOS'
CONSTANT_INFOS = 'CONSTANT_INFOS'
CLASS_INFOS = 'CLASS_INFOS'
NOT_IN_FUNCS = 'NOT_IN_FUNCS'  # 作为非函数外的代码调用的键名称

# 整理调用关系时使用的键值对
CALLS = 'CALLS'
CALLED_BY = 'CALLED_BY'
CODE_FILE = 'CODE_FILE'


# 类方法解析解析结果键和默认值选项
# "CLASS_NAME|类名": "UserManager",
CLASS_NAME = 'CLASS_NAME'
# "class_start_line|类开始行号": 11,
CLASS_START_LINE = 'CLASS_START_LINE'
# "class_end_line|类结束行号": 25,
CLASS_END_LINE = 'CLASS_END_LINE'
# "class_extends|类继承的父类": {父类名称: 文件路径},
CLASS_EXTENDS = 'CLASS_EXTENDS'
# "class_interfaces|类实现的接口列表": [{抽象类名称: 文件路径}, ],
CLASS_INTERFACES = "CLASS_INTERFACES"
# CLASS_NAMESPACE|类所处的命名空间
CLASS_NAMESPACE = 'CLASS_NAMESPACE'
# CLASS_VISIBILITY|类的可见性修饰符  # public, private, protected
CLASS_VISIBILITY = 'CLASS_VISIBILITY'
# CLASS_MODIFIERS| 类的特殊修饰符列表  # abstract, final, interface 等
CLASS_MODIFIERS = 'CLASS_MODIFIERS'

# "CLASS_PROPERTIES|类的属性列表":
CLASS_PROPERTIES = 'CLASS_PROPERTIES'

# 类属性的具体信息
# "PROPERTY_NAME|类属性名": "$username",
PROPERTY_NAME = 'PROPERTY_NAME'
# "PROPERTY_LINE|类属性所在行号": 13,
PROPERTY_LINE = 'PROPERTY_LINE'
# "PROPERTY_INITIAL_VALUE|属性的初始值": null
PROPERTY_INITIAL_VALUE = 'PROPERTY_INITIAL_VALUE'
# "PROPERTY_VISIBILITY|属性的访问修饰符": "private",
PROPERTY_VISIBILITY = 'PROPERTY_VISIBILITY'
# "PROPERTY_MODIFIERS|属性的特殊性质": ["static"],
PROPERTY_MODIFIERS = "PROPERTY_MODIFIERS"

# 类方法列表
CLASS_METHODS = 'CLASS_METHODS'
# 类方法的具体信息
# "METHOD_NAME|方法名": "__construct",
METHOD_NAME = 'METHOD_NAME'
# "METHOD_START_LINE|方法开始行号": 17,
METHOD_START_LINE = 'METHOD_START_LINE'
# "METHOD_END_LINE|方法结束行号": 21,
METHOD_END_LINE = 'METHOD_END_LINE'
# "METHOD_OBJECT|方法对应的类对象": "class_name", // 对于类方法而言就是自身
METHOD_OBJECT = 'METHOD_OBJECT'
# METHOD_FULL_NAME|类方法的完整名 object->方法名
METHOD_FULL_NAME = 'METHOD_FULL_NAME'
# "METHOD_VISIBILITY|方法的访问修饰符": "public",
METHOD_VISIBILITY = 'METHOD_VISIBILITY'
# "METHOD_MODIFIERS|方法的特殊性质": ["static", "abstract", "final"],
METHOD_MODIFIERS = 'METHOD_MODIFIERS'
# "METHOD_RETURN_TYPE|方法的返回值类型": null,
METHOD_RETURN_TYPE = 'METHOD_RETURN_TYPE'
# "METHOD_RETURN_VALUE|方法的返回值": null,
METHOD_RETURN_VALUE = 'METHOD_RETURN_VALUE'

# "METHOD_TYPE方法|调用方法的类型": "local_method",
METHOD_TYPE = 'METHOD_TYPE'
# METHOD_TYPE 允许的值类型
BUILTIN_METHOD = 'BUILTIN_METHOD'
LOCAL_METHOD = 'LOCAL_METHOD'
DYNAMIC_METHOD = 'DYNAMIC_METHOD'
CONSTRUCTOR = 'CONSTRUCTOR'
CUSTOM_METHOD = 'CUSTOM_METHOD'
CLASS_METHOD = 'CLASS_METHOD'

# "METHOD_PARAMETERS|方法的参数列表":
METHOD_PARAMETERS = 'METHOD_PARAMETERS'
# "PARAMETER_NAME|参数名": "$username",
PARAMETER_NAME = 'PARAMETER_NAME'
# "PARAMETER_TYPE|参数类型": null,
PARAMETER_TYPE = 'PARAMETER_TYPE'
# "PARAMETER_DEFAULT|参数默认值": null
PARAMETER_DEFAULT = 'PARAMETER_DEFAULT'
# "PARAMETER_VALUE|实际调用的参数值": null
PARAMETER_VALUE = 'PARAMETER_VALUE'

# "CALLED_METHODS|方法内部调用的其他方法或函数": //方法信息和方法内的参数信息就和上面类的方法格式完全相同了
CALLED_METHODS = 'CALLED_METHODS'
