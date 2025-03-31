from libs_com.file_path import file_is_exist
from PHPParser import PHPParser

if __name__ == '__main__':
    # project_path = r"php_demo\d_include.php"
    # OK  import_info:->[{'type': 'require', 'path': '/includes/init.php', 'line': 2}, {'type': 'require_once', 'path': 'includes/lib_order.php', 'line': 3}]

    # project_path = r"php_demo\d_require.php"
    # OK import_info:->[{'type': 'include', 'path': 'includes/lib_goods.php', 'line': 2}, {'type': 'include_once', 'path': 'includes/lib_users.php', 'line': 3}]

    project_path = r"php_demo\d_use.php"
    # OK import_info:->[{'type': 'use', 'import_type': 'class', 'path': 'think\\Container', 'line': 2}, {'type': 'use', 'import_type': 'function', 'path': 'core\\util\\Snowflake', 'line': 3}, {'type': 'use', 'import_type': 'constant', 'path': 'app\\service\\core\\upload\\CoreImageService', 'line': 4}]
    project_path = r"php_demo\depends.php"
    # import_info:->[
    # {'type': 'use', 'import_type': 'function', 'path': 'think\\Container', 'line': 7},
    # {'type': 'use', 'import_type': 'class', 'path': 'core\\util\\Snowflake', 'line': 8},
    # {'type': 'require', 'path': '/includes/init.php', 'line': 2},
    # {'type': 'require_once', 'path': 'includes/lib_order.php', 'line': 3},
    # {'type': 'include', 'path': 'includes/lib_goods.php', 'line': 4},
    # {'type': 'include_once', 'path': 'includes/lib_users.php', 'line': 5}]

    # project_path = r"php_demo\function.php"
    # project_path = r"php_demo/functon_none.php"
    # project_path = r"php_demo/allinone.php"
    # project_path = r"php_demo/class.php"
    project_path = r"php_demo/demo.php"
    if not file_is_exist(project_path):
        print(f"输入的文件项目路径不存在 {project_path}")
        exit()
    parser = PHPParser(project_name="default_project", project_path=project_path)
    analyse_result = parser.analyse(save_cache=True)
    print(analyse_result)
