"""
Module for analyzing function and method call relationships in PHP code.
This module provides functionality to build and analyze call graphs between functions and methods.
"""

from typing import Dict, Any

from libs_com.utils_json import print_json
from tree_const import (
    CLASS_METHOD,
    LOCAL_METHOD,
    BUILTIN_METHOD,
    CUSTOM_METHOD,
    CONSTRUCTOR,
    METHOD_NAME,
    METHOD_START_LINE,
    METHOD_END_LINE,
    METHOD_OBJECT,
    METHOD_TYPE,
    CALLED_METHODS,
    CLASS_NAME,
    CLASS_EXTENDS,
    CLASS_METHODS,
    CALLS,
    CODE_FILE,
    CALLED_BY, CLASS_INFOS,
    METHOD_FULL_NAME,
    METHOD_VISIBILITY,
    METHOD_MODIFIERS,
    METHOD_RETURN_TYPE,
    METHOD_RETURN_VALUE,
    METHOD_PARAMETERS
)
from tree_enums import FileInfoKeys
from tree_map_utils import (
    init_calls_value,
    build_function_map,
    build_classes_map,
    find_class_infos_by_method
)
from tree_func_utils import is_php_magic_method


class CallRelationBuilder:
    """Class responsible for building call relationships between functions and methods."""
    
    def __init__(self, parsed_infos: Dict[str, Any]):
        self.parsed_infos = parsed_infos
        self.function_map = None
        
    def analyze(self) -> Dict[str, Any]:
        """Main entry point for analyzing function call relationships."""
        print("\n开始分析函数调用关系...")
        
        # Build function and class mappings
        self.function_map = build_function_map(self.parsed_infos)
        print(f"已建立函数映射，共 {len(self.function_map)} 个函数/方法")
        print_json(self.function_map)
        
        # Initialize call relationship fields
        self.parsed_infos = init_calls_value(self.parsed_infos)
        
        # Build call relationships
        self._build_call_relations()
        
        # Build called-by relationships
        print("\n开始建立被调用关系...")
        self._build_called_by_relations()
        
        return self.parsed_infos
    
    def _build_call_relations(self):
        """Build all call relationships."""
        self.parsed_infos = build_calls_func_relation(self.parsed_infos, self.function_map)
        self.parsed_infos = build_calls_class_relation(self.function_map, self.parsed_infos)
    
    def _build_called_by_relations(self):
        """Build all called-by relationships."""
        self.parsed_infos = build_called_by_func_relation(self.parsed_infos, self.function_map)
        self.parsed_infos = build_called_by_class_relation(self.function_map, self.parsed_infos)

def find_local_call_relation(func_info: Dict[str, Any], call_func: Dict[str, Any], 
                           file_path: str, class_name: str = None) -> Dict[str, Any]:
    """Add local function call relationship to function info."""
    if call_func[METHOD_NAME] in call_func:
        call_func_info = {
            **call_func,
            CODE_FILE: file_path,
            CLASS_NAME: class_name if class_name else ''
        }
        func_info[CALLS].append(call_func_info)
    else:
        print(f"在映射列表内没有找到对应 LOCAL_METHOD 函数名称:{call_func[METHOD_NAME]}")
    return func_info

def find_custom_call_relation(func_info: Dict[str, Any], called_func: Dict[str, Any],
                            function_map: Dict[str, Any], class_name: str = None) -> Dict[str, Any]:
    """Add custom function call relationship to function info."""
    if called_func[METHOD_NAME] in function_map:
        probably_func_infos = function_map.get(called_func.get(METHOD_NAME))
        for probably_func_info in probably_func_infos:
            file_path = probably_func_info.get(CODE_FILE)
            call_func_info = {
                **called_func,
                **probably_func_info,
                CODE_FILE: file_path,
                CLASS_NAME: class_name if class_name else ''
            }
            func_info[CALLS].append(call_func_info)
    else:
        print(f"在映射列表内没有找到对应 CUSTOM_METHOD 函数名称:{called_func[METHOD_NAME]}")
    return func_info

def build_called_by_func_relation(parsed_infos: Dict[str, Any], function_map: Dict[str, Any]) -> Dict[str, Any]:
    """Build called-by relationships for functions based on calls information."""
    for file_path, parsed_info in parsed_infos.items():
        for calling_func in parsed_info.get(FileInfoKeys.METHOD_INFOS.value, []):
            for call_info in calling_func.get(CALLS, []):
                caller_info = _build_caller_info(calling_func, file_path)
                _process_called_function(call_info, caller_info, parsed_infos, function_map)
    return parsed_infos

def _build_caller_info(calling_func: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Build caller information dictionary."""
    caller_info = {
        METHOD_NAME: calling_func[METHOD_NAME],
        CODE_FILE: file_path,
        METHOD_START_LINE: calling_func.get(METHOD_START_LINE),
        METHOD_END_LINE: calling_func.get(METHOD_END_LINE),
        METHOD_TYPE: calling_func.get(METHOD_TYPE),
        METHOD_OBJECT: calling_func.get(METHOD_OBJECT),
        METHOD_FULL_NAME: calling_func.get(METHOD_FULL_NAME)
    }
    return caller_info

def _process_called_function(call_info: Dict[str, Any], caller_info: Dict[str, Any],
                           parsed_infos: Dict[str, Any], function_map: Dict[str, Any]):
    """Process a called function and add the caller to its called_by list."""
    called_name = call_info.get(METHOD_NAME)
    called_class = call_info.get(CLASS_NAME)
    
    if called_class:  # Class method
        _process_called_class_method(called_name, called_class, caller_info, parsed_infos, function_map)
    else:  # Regular function
        _process_called_regular_function(called_name, caller_info, parsed_infos, function_map)

def _process_called_class_method(called_name: str, called_class: str, caller_info: Dict[str, Any],
                               parsed_infos: Dict[str, Any], function_map: Dict[str, Any]):
    """Process a called class method and add the caller to its called_by list."""
    full_method_name = f"{called_class}::{called_name}"
    if full_method_name in function_map:
        for func_info in function_map[full_method_name]:
            called_file = func_info[CODE_FILE]
            for class_info in parsed_infos[called_file].get(CLASS_INFOS, []):
                if class_info[CLASS_NAME] == called_class:
                    for method in class_info.get(CLASS_METHODS, []):
                        if method[METHOD_NAME] == called_name:
                            method[CALLED_BY].append(caller_info)

def _process_called_regular_function(called_name: str, caller_info: Dict[str, Any],
                                   parsed_infos: Dict[str, Any], function_map: Dict[str, Any]):
    """Process a called regular function and add the caller to its called_by list."""
    if called_name in function_map:
        for func_info in function_map[called_name]:
            called_file = func_info[CODE_FILE]
            for func in parsed_infos[called_file].get(FileInfoKeys.METHOD_INFOS.value, []):
                if func[METHOD_NAME] == called_name:
                    print(f"Adding called-by relation: {called_name} is called by {caller_info[METHOD_NAME]}")
                    if CALLED_BY not in func:
                        func[CALLED_BY] = []
                    caller_info_copy = caller_info.copy()
                    if caller_info.get(METHOD_TYPE) == CLASS_METHOD:
                        caller_info_copy[CLASS_NAME] = caller_info.get(METHOD_OBJECT)
                    func[CALLED_BY].append(caller_info_copy)

def build_called_by_class_relation(function_map: Dict[str, Any], parsed_infos: Dict[str, Any]) -> Dict[str, Any]:
    """Build called-by relationships for class methods."""
    for file_path, parsed_info in parsed_infos.items():
        for class_info in parsed_info.get(CLASS_INFOS, []):
            class_name = class_info[CLASS_NAME]
            for method in class_info.get(CLASS_METHODS, []):
                for call_info in method.get(CALLS, []):
                    caller_info = _build_class_method_caller_info(method, class_name, file_path)
                    print(f"Processing class method call: {class_name}::{method[METHOD_NAME]} calls {call_info.get(METHOD_NAME)}")
                    _process_called_function(call_info, caller_info, parsed_infos, function_map)
    return parsed_infos

def _build_class_method_caller_info(method: Dict[str, Any], class_name: str, file_path: str) -> Dict[str, Any]:
    """Build caller information for a class method."""
    return {
        METHOD_NAME: method[METHOD_NAME],
        METHOD_OBJECT: class_name,
        CODE_FILE: file_path,
        METHOD_START_LINE: method.get(METHOD_START_LINE),
        METHOD_END_LINE: method.get(METHOD_END_LINE),
        METHOD_TYPE: CLASS_METHOD,
        METHOD_FULL_NAME: f"{class_name}::{method[METHOD_NAME]}",
        CLASS_NAME: class_name
    }

def process_constructor_call(parsed_infos: Dict[str, Any], func_info: Dict[str, Any],
                           called_func: Dict[str, Any]) -> Dict[str, Any]:
    """Process constructor call and add it to function info."""
    class_name = called_func[METHOD_NAME].replace('new ', '')
    func_start_line = called_func.get(METHOD_START_LINE)
    
    print(f"处理构造函数调用...{class_name}")
    class_map = build_classes_map(parsed_infos)
    
    if class_name not in class_map:
        print(f"没有在类映射关系中找到Class:{class_name} -> {class_map.keys()}!!!")
        return func_info
        
    map_find_info = class_map[class_name]
    class_file = map_find_info.get(CODE_FILE)
    
    for class_file_info in parsed_infos[class_file].get(CLASS_INFOS, []):
        if class_file_info[CLASS_NAME] == class_name:
            for method in class_file_info.get(CLASS_METHODS, []):
                if method[METHOD_NAME] == '__construct':
                    call_info = {
                        METHOD_NAME: '__construct',
                        METHOD_TYPE: CONSTRUCTOR,
                        'class': class_name,
                        'func_start_line': func_start_line,
                        'func_file': class_file
                    }
                    func_info['calls'].append(call_info)
    return func_info

def process_object_method_call(parsed_infos: Dict[str, Any], func_info: Dict[str, Any],
                             called_func: Dict[str, Any]) -> Dict[str, Any]:
    """Process object method call and add it to function info."""
    class_name = called_func[METHOD_OBJECT].strip("$")
    method_name = called_func[METHOD_NAME]
    line = called_func.get(METHOD_START_LINE)
    
    class_map = build_classes_map(parsed_infos)
    class_infos = []
    
    if class_name in class_map:
        class_infos = [class_map[class_name]]
    elif not is_php_magic_method(method_name):
        class_infos = find_class_infos_by_method(method_name, class_map)
        
    for map_find_info in class_infos:
        class_file = map_find_info.get(CODE_FILE)
        new_class_name = map_find_info.get(CLASS_NAME)
        
        for class_file_info in parsed_infos[class_file].get(CLASS_INFOS, []):
            if class_file_info[CLASS_NAME] == new_class_name:
                for method in class_file_info.get(CLASS_METHODS, []):
                    if method[METHOD_NAME] == method_name:
                        call_info = {
                            METHOD_NAME: method_name,
                            METHOD_TYPE: CLASS_METHOD,
                            CLASS_NAME: new_class_name,
                            METHOD_START_LINE: line,
                            CODE_FILE: class_file,
                            METHOD_OBJECT: called_func[METHOD_OBJECT],
                            METHOD_FULL_NAME: f"{called_func[METHOD_OBJECT]}->{method_name}",
                            METHOD_VISIBILITY: method.get(METHOD_VISIBILITY, "PUBLIC"),
                            METHOD_MODIFIERS: method.get(METHOD_MODIFIERS, []),
                            METHOD_RETURN_TYPE: method.get(METHOD_RETURN_TYPE),
                            METHOD_RETURN_VALUE: method.get(METHOD_RETURN_VALUE),
                            METHOD_PARAMETERS: called_func.get(METHOD_PARAMETERS, [])
                        }
                        func_info[CALLS].append(call_info)
    return func_info

def build_calls_func_relation(parsed_infos: Dict[str, Any], function_map: Dict[str, Any]) -> Dict[str, Any]:
    """Build call relationships for regular functions."""
    for file_path, parsed_info in parsed_infos.items():
        print(f"\n分析文件 build_calls_func_relation: {file_path}")
        parsed_info_functions = parsed_info.get(FileInfoKeys.METHOD_INFOS.value, [])
        
        for index, func_info in enumerate(parsed_info_functions):
            for called_func in func_info.get(CALLED_METHODS, []):
                func_type = called_func.get(METHOD_TYPE)
                
                if func_type == BUILTIN_METHOD:
                    print("跳过对内置函数函数的寻找调用...")
                    continue
                    
                elif func_type == LOCAL_METHOD:
                    func_info = find_local_call_relation(func_info, called_func, file_path)
                    
                elif func_type == CUSTOM_METHOD:
                    func_info = find_custom_call_relation(func_info, called_func, function_map)
                    
                elif func_type == CONSTRUCTOR:
                    func_info = process_constructor_call(parsed_infos, func_info, called_func)
                    
                elif func_type in [CLASS_METHOD]:
                    func_info = process_object_method_call(parsed_infos, func_info, called_func)
                    
                else:
                    print(f"发现未预期的调用格式 {func_type}, 必须实现 -> {called_func}")
                    print(func_info)
                    continue
                    
                parsed_info_functions[index] = func_info
                
    return parsed_infos

def build_calls_class_relation(function_map: Dict[str, Any], parsed_infos: Dict[str, Any]) -> Dict[str, Any]:
    """Build call relationships for class methods."""
    for file_path, parsed_info in parsed_infos.items():
        print(f"\n分析文件 build_calls_class_relation: {file_path}")
        
        for class_info in parsed_info.get(FileInfoKeys.CLASS_INFOS.value, []):
            class_name = class_info[CLASS_NAME]
            
            for method_info in class_info.get(CLASS_METHODS, []):
                # Process parent constructor call
                if method_info[METHOD_NAME] == '__construct' and class_info.get(CLASS_EXTENDS):
                    _process_parent_constructor(method_info, class_info, function_map, file_path)
                    
                # Process method calls
                for called_func in method_info.get(CALLED_METHODS, []):
                    _process_method_call(method_info, called_func, function_map, file_path, class_name)
                    
    return parsed_infos

def _process_parent_constructor(method_info: Dict[str, Any], class_info: Dict[str, Any],
                              function_map: Dict[str, Any], file_path: str):
    """Process parent constructor call in a constructor method."""
    parent_class = class_info.get(CLASS_EXTENDS)
    if parent_class and isinstance(parent_class, str):
        if parent_class in function_map:
            parent_constructor = {
                METHOD_NAME: '__construct',
                METHOD_TYPE: CONSTRUCTOR,
                METHOD_OBJECT: parent_class,
                METHOD_START_LINE: method_info.get(METHOD_START_LINE)
            }
            method_info = find_local_call_relation(method_info, parent_constructor, file_path, parent_class)
        else:
            print(f"未找到父类构造函数: {parent_class}")
    else:
        print(f"无效的父类名称: {parent_class}")

def _process_method_call(method_info: Dict[str, Any], called_func: Dict[str, Any],
                        function_map: Dict[str, Any], file_path: str, class_name: str):
    """Process a method call in a class method."""
    func_type = called_func.get(METHOD_TYPE)
    
    if func_type == BUILTIN_METHOD:
        print("跳过对内置函数的寻找调用...")
        return
        
    elif func_type == LOCAL_METHOD:
        if called_func[METHOD_NAME] in function_map:
            method_info = find_local_call_relation(method_info, called_func, file_path)
        else:
            print(f"在映射列表内没有找到对应 LOCAL_METHOD 函数名称:{called_func[METHOD_NAME]}")
            
    elif func_type == CUSTOM_METHOD:
        method_info = find_custom_call_relation(method_info, called_func, function_map)
        
    elif func_type == CONSTRUCTOR:
        class_name = called_func['name'].replace('new ', '')
        if class_name in function_map:
            constructor_info = {
                'name': '__construct',
                'type': CONSTRUCTOR,
                'class': class_name,
                'line': called_func.get('line')
            }
            method_info = find_local_call_relation(method_info, constructor_info, file_path, class_name)
            
    elif func_type in [CLASS_METHOD]:
        if 'class' in called_func and called_func['class'] in function_map:
            target_class = called_func['class']
            method_name = called_func['name']
            full_method_name = f"{target_class}::{method_name}"
            
            if full_method_name in function_map:
                method_info = find_local_call_relation(method_info, called_func, file_path, target_class)
            else:
                print(f"在映射列表内没有找到对应方法:{full_method_name}")
                
    else:
        print(f"发现未预期的调用格式 {func_type} -> {called_func}")

def analyze_func_relation(parsed_infos: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for analyzing function relationships."""
    builder = CallRelationBuilder(parsed_infos)
    return builder.analyze()

if __name__ == '__main__':
    # Import required modules
    from init_tree_sitter import init_php_parser
    from libs_com.file_io import read_file_bytes
    import os
    from tree_func_info import analyze_direct_method_infos
    from tree_class_info import analyze_class_infos
    
    # Initialize PHP parser
    PARSER, LANGUAGE = init_php_parser()
    
    # Set test directory
    project_path = r"php_demo/func_call_demo"
    project_path = r"php_demo/class_call_demo"
    
    # Dictionary to store parsed information
    parsed_infos = {}
    
    print("\n=== 开始分析PHP文件调用关系 ===")
    
    # Process each PHP file in the directory
    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith('.php'):
                file_path = os.path.join(root, file)
                print(f"\n处理文件: {file_path}")
                
                # Read and parse the file
                php_file_bytes = read_file_bytes(file_path)
                php_file_tree = PARSER.parse(php_file_bytes)
                
                # Analyze functions and classes
                method_infos = analyze_direct_method_infos(php_file_tree, LANGUAGE)
                class_infos = analyze_class_infos(php_file_tree, LANGUAGE)
                
                # Store results
                parsed_infos[file_path] = {
                    FileInfoKeys.METHOD_INFOS.value: method_infos,
                    FileInfoKeys.CLASS_INFOS.value: class_infos
                }
    
    # Analyze function relationships
    print("\n=== 分析函数调用关系 ===")
    analyzed_infos = analyze_func_relation(parsed_infos)
    
    # Print final results
    print("\n=== 函数调用关系分析结果 ===")
    print("\n1. 函数调用图:")
    print("-" * 50)
    
    # 收集所有函数信息
    all_functions = {}
    for file_path, info in analyzed_infos.items():
        for func in info.get(FileInfoKeys.METHOD_INFOS.value, []):
            func_name = func[METHOD_NAME]
            if func_name not in all_functions:
                all_functions[func_name] = {
                    'file': file_path,
                    'calls': [],
                    'called_by': []
                }
            
            # 收集调用关系
            for call in func.get(CALLS, []):
                call_info = {
                    'name': call.get(METHOD_NAME),
                    'file': call.get(CODE_FILE, 'unknown'),
                    'line': call.get(METHOD_START_LINE, 'unknown')
                }
                all_functions[func_name]['calls'].append(call_info)
            for caller in func.get(CALLED_BY, []):
                caller_info = {
                    'name': caller.get(METHOD_NAME),
                    'file': caller.get(CODE_FILE, 'unknown'),
                    'line': caller.get(METHOD_START_LINE, 'unknown')
                }
                all_functions[func_name]['called_by'].append(caller_info)
    
    # 打印函数调用图
    for func_name, info in all_functions.items():
        print(f"\n函数: {func_name}")
        print(f"定义文件: {info['file']}")
        if info['calls']:
            print("调用:")
            for call in info['calls']:
                print(f"  └─ {call['name']}")
                print(f"    文件: {call['file']}")
                print(f"    行号: {call['line']}")
        if info['called_by']:
            print("被调用:")
            for caller in info['called_by']:
                print(f"  └─ {caller['name']}")
                print(f"    文件: {caller['file']}")
                print(f"    行号: {caller['line']}")
    
    print("\n2. 类方法调用图:")
    print("-" * 50)
    
    # 收集所有类方法信息
    all_methods = {}
    for file_path, info in analyzed_infos.items():
        for class_info in info.get(CLASS_INFOS, []):
            class_name = class_info[CLASS_NAME]
            for method in class_info.get(CLASS_METHODS, []):
                method_name = method[METHOD_NAME]
                full_name = f"{class_name}::{method_name}"
                if full_name not in all_methods:
                    all_methods[full_name] = {
                        'class': class_name,
                        'file': file_path,
                        'calls': [],
                        'called_by': []
                    }
                
                # 收集调用关系
                for call in method.get(CALLS, []):
                    call_info = {
                        'name': call.get(METHOD_NAME),
                        'file': call.get(CODE_FILE, 'unknown'),
                        'line': call.get(METHOD_START_LINE, 'unknown')
                    }
                    all_methods[full_name]['calls'].append(call_info)
                for caller in method.get(CALLED_BY, []):
                    caller_info = {
                        'name': caller.get(METHOD_NAME),
                        'file': caller.get(CODE_FILE, 'unknown'),
                        'line': caller.get(METHOD_START_LINE, 'unknown')
                    }
                    all_methods[full_name]['called_by'].append(caller_info)
    
    # 打印类方法调用图
    for method_name, info in all_methods.items():
        print(f"\n方法: {method_name}")
        print(f"类: {info['class']}")
        print(f"定义文件: {info['file']}")
        if info['calls']:
            print("调用:")
            for call in info['calls']:
                print(f"  └─ {call['name']}")
                print(f"    文件: {call['file']}")
                print(f"    行号: {call['line']}")
        if info['called_by']:
            print("被调用:")
            for caller in info['called_by']:
                print(f"  └─ {caller['name']}")
                print(f"    文件: {caller['file']}")
                print(f"    行号: {caller['line']}")
    
    print("\n=== 分析完成 ===")