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
FUNCTION_TYPE = 'func_type'
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

