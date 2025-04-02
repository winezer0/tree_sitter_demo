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
NOT_IN_FUNCS = 'not_functions'  # 作为非函数外的代码调用的键名称

# 整理调用关系时使用的键值对
CALLS = 'calls'
CALLED_BY = 'called_by'
CODE_FILE = 'code_file'


# 类方法解析解析结果键和默认值选项
# "class_name|类名": "UserManager",
CLASS_NAME = 'class_name'
# "class_start_line|类开始行号": 11,
CLASS_START_LINE = 'class_start_line'
# "class_end_line|类结束行号": 25,
CLASS_END_LINE = 'class_end_line'
# "class_extends|类继承的父类": {父类名称: 文件路径},
CLASS_EXTENDS = 'class_extends'
# "class_interfaces|类实现的接口列表": [{抽象类名称: 文件路径}, ],  //暂时没有实现
CLASS_INTERFACES = "class_interfaces"
# "class_properties|类的属性列表":
CLASS_PROPS = 'class_properties'
# CLASS_NAMESPACE|类所处的命名空间
CLASS_NAMESPACE = "CLASS_NAMESPACE"

# "class_type|类的特殊属性": "normal", // 可选 普通类、抽象类、最终类、静态类(php好像没有静态类)等,后面改成 class_modifiers 和 class_visibility
CLASS_TYPE = 'class_type'
# 类的类型可选的值   # 需要删除合并到其他选项中去
TYPE_CLASS = 'type_class'           # 需要删除,没什么用
TYPE_INTERFACE = 'type_interface'   # 需要把值合并到 CLASS_INTERFACES
TYPE_NAMESPACE = 'type_namespace'   # 需要把值合并到 CLASS_NAMESPACE


# 类属性的具体信息
# "property_name|属性名": "$username",
PROP_NAME = 'prop_name'
# "property_line|属性所在行号": 13,
PROP_LINE = 'prop_line'
# "property_initial_value|属性的初始值": null
PROP_VALUE = 'prop_value'
# "property_visibility|属性的访问修饰符": "private",  //暂时没有实现
PROPERTY_VISIBILITY = 'property_visibility'
# "property_modifiers|属性的特殊性质": ["normal"],   //暂时没有实现
PROPERTY_MODIFIERS = "property_modifiers"
PROP_IS_STATIC = 'prop_is_static'  # 需要删除 合并到 PROPERTY_MODIFIERS中去

# 类方法列表
CLASS_METHODS = 'class_methods'
# 类方法的具体信息
# "method_name|方法名": "__construct",
METHOD_NAME = 'method_name'
# "method_start_line|方法开始行号": 17,
METHOD_START_LINE = 'method_start_line'
# "method_end_line|方法结束行号": 21,
METHOD_END_LINE = 'method_end_line'
# "method_object|方法对应的类对象": "class_name", // 对于类方法而言就是自身
METHOD_OBJECT = 'method_object'
# 类方法的完整名 object->方法名
METHOD_FULL_NAME = 'method_full_name'
# "method_visibility|方法的访问修饰符": "public",
METHOD_VISIBILITY = 'method_visibility'
# "method_modifiers|方法的特殊性质": ["normal"], //暂未实现
METHOD_MODIFIERS = "method_modifiers"
METHOD_IS_STATIC = 'method_is_static' # 需要弃用, 然后替换到 METHOD_MODIFIERS 中
# "method_return_type|方法的返回值类型": null,
METHOD_RETURN_TYPE = 'METHOD_RETURN_TYPE'
# "METHOD_TYPE|方法|调用方法的类型": "local_method",
METHOD_TYPE = 'METHOD_TYPE'
# METHOD_TYPE 允许的值类型
BUILTIN_METHOD = 'builtin_method'
LOCAL_METHOD = 'local_method'
DYNAMIC_METHOD = 'dynamic_method'
CONSTRUCTOR = 'constructor'
STATIC_METHOD = 'static_method'   # 需要删除、合并到call_method_modifiers中去
CUSTOM_METHOD = 'custom_method'
CLASS_METHOD = 'class_method'
OBJECT_METHOD = 'object_method'  # 需要删除、等于 class_method

# "method_parameters|方法或者调用方法的参数列表":
METHOD_PARAMS = 'method_parameters'
# "parameter_name|参数名": "$username",
PARAM_NAME = 'param_name'
# "parameter_type|参数类型": null,
PARAM_TYPE = 'param_type'
# "parameter_default_value|参数默认值": null
PARAM_DEFAULT_VALUE = 'param_default'

# "called_methods|方法内部调用的其他方法或函数": //方法信息和方法内的参数信息就和上面类的方法格式完全相同了
CALLED_METHODS = 'called_methods'

# "class_dependencies|类的所有依赖项": { //这个可以在最后进行分析,避免代码混乱 //考虑删除
CLASS_DEPENDS = 'class_depends'
