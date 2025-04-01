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

FUNCTIONS = "functions"
IMPORTS = "imports"

# 变量和常量相关的键名
VARIABLES = 'variables'
CONSTANTS = 'constants'

# 类相关的键名
CLASSES = 'classes'

# 函数类型
FUNC_TYPE = 'func_type'
BUILTIN_METHOD = 'builtin_method'
LOCAL_METHOD = 'local_method'
DYNAMIC_METHOD = 'DYNAMIC_METHOD'
CONSTRUCTOR = 'constructor'
OBJECT_METHOD = 'object_method'
STATIC_METHOD = 'static_method'
CUSTOM_METHOD = 'custom_method'

FUNCTION = 'function'
CLASS_METHOD = 'class_method'

#调用函数的键
CALLED_FUNCTIONS = 'called_functions'
CLASS_INFO = 'classes'

php_magic_methods = [
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
CLASS_TYPE = 'class_type'
CLASS_PROPS = 'class_props'
CLASS_METHODS = 'class_methods'
CLASS_DEPENDS = 'class_depends'
CLASS_EXTENDS = 'class_extends'
TYPE_CLASS = 'type_class'
TYPE_INTERFACE = 'type_interface'
TYPE_NAMESPACE = 'type_namespace'
METHOD_IS_STATIC = 'method_is_static'
METHOD_VISIBILITY = 'method_visibility'
METHOD_PARAMS = 'method_params'
PROP_VISIBILITY = 'prop_visibility'
PROP_IS_STATIC = 'prop_is_static'
CLASS_NAME = 'class_name'
CLASS_START_LINE = 'class_start_line'
CLASS_END_LINE = 'class_end_line'
METHOD_NAME = 'method_name'
METHOD_START_LINE = 'method_start_line'
METHOD_END_LINE = 'method_end_line'
METHOD_FULL_NAME = 'method_full_name'
METHOD_OBJECT = 'method_object'
PARAM_NAME = 'param_name'
PARAM_TYPE = 'param_type'
PROP_NAME = 'prop_name'
PROP_VALUE = 'prop_value'
PROP_LINE = 'prop_line'
FUNC_NAME = 'func_name'
FUNC_START_LINE = 'func_start_line'
FUNC_END_LINE= 'func_end_line'


FUNC_NAME = 'function_name'
FUNC_LINE = 'function_line'
NOT_IN_FUNCS = 'not_functions'
FUNC_PARAMS = 'parameters'
FUNC_RETURN_TYPE = 'return_type'
FUNC_START_LINE = 'start_line'
FUNC_END_LINE = 'end_line'
PARAM_NAME = 'name'
PARAM_VALUE_DEFAULT = 'default'


# 整理调用关系
CALLS = 'calls'
CALLED_BY = 'called_by'
CODE_FILE = 'code_file'
