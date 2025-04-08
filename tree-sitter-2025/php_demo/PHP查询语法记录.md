```
    ;匹配命名空间定义信息
    (namespace_definition
        name: (namespace_name) @namespace_name
        body: (declaration_list)? @namespace_body
    ) @namespace.def

    ;匹配类定义信息 含abstract类和final类
    (class_declaration
        (visibility_modifier)? @class_visibility
        (abstract_modifier)? @is_abstract_class
        (final_modifier)? @is_final_class
        name: (name) @class_name
        (base_clause (name) @extends)? @base_clause
        (class_interface_clause (name) @implements)? @class_interface_clause
        body: (declaration_list) @class_body
    ) @class.def

    ;匹配类定义信息 含abstract类和final类 简化版本,需要自己判断其中的类型
    (class_declaration) @class.def

    ;匹配接口定义
    (interface_declaration
        name: (name) @interface_name
        ;捕获继承的父类
        (base_clause (name) @extends)? @base_clause
        body: (declaration_list) @interface_body
    ) @interface.def

    ;匹配接口定义 简化版本,需要自己判断其中的类型
    (interface_declaration) @interface.def
    
    ;匹配类方法定义信息
    (method_declaration
        (visibility_modifier)? @method_visibility
        (static_modifier)? @is_static_method
        (abstract_modifier)? @is_abstract_method
        (final_modifier)? @is_final_method
        name: (name) @method_name
        parameters: (formal_parameters) @method_params
        return_type: (_)? @method_return_type
        body: (compound_statement) @method_body
    )@method.def

    ;匹配类属性定义信息
    (property_declaration
        (visibility_modifier)? @property_visibility
        (static_modifier)? @is_static
        (readonly_modifier)? @is_readonly
        (property_element
            name: (variable_name) @property_name
            (
                "="
                (_) @property_value
            )?
        )+
    )@property.def

    ; 查询函数调用匹配
    (function_call_expression
        function: (name) @function_call
        arguments: (arguments) @function_args
    ) @function_call_expr

    ; 查询对象方法调用
    (member_call_expression
        object: (_) @object
        name: (name) @method_call
        arguments: (arguments) @method_args
    ) @member_call_expr

    ; 查询 new 表达式匹配语法
    (object_creation_expression
        (name) @new_class_name
        (arguments) @constructor_args
    )@new_class_expr
    

    ; 全局函数定义
    (function_definition
        name: (name) @function.name
        parameters: (formal_parameters) @function.params
        body: (compound_statement) @function.body
    ) @function.def
```