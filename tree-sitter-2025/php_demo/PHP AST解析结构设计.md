## 类分析结果的格式设计
{
  "class_name|类名": "UserManager",
  "class_start_line|类开始行号": 11,
  "class_end_line|类结束行号": 25,   
  "class_type|类的类型": "normal", //可选 普通类、抽象类、最终类、静态类等等
  "class_extends|类继承的父类": {父类名称:文件路径},
  "class_interfaces|类实现的接口列表": [{抽象类名称:文件路径},],
  "class_properties|类的属性列表": [
    {
      "property_name|属性名": "$username",
      "property_line|属性所在行号": 13,
      "property_visibility|属性的访问修饰符": "private", 
      "property_modifiers|属性的特殊性质": ["normal"], 
      "property_initial_value|属性的初始值": null
    },
    {
      "property_name|属性名": "$userCount",
      "property_line|属性所在行号": 14,
      "property_visibility|属性的访问修饰符": "private",
      "property_modifiers|属性的特殊性质": ["static"],
      "property_initial_value|属性的初始值": null
    }
  ],
  "class_methods|类的方法列表": [
    {
      "method_object|方法对应的类对象": "class_name", //对于类方法而言就是自身
      "method_name|方法名": "__construct",
      "method_fullname|调用的完整方法名": "class_name->__construct",
      "method_start_line|方法开始行号": 17,
      "method_end_line|方法结束行号": 21,
      "method_visibility|方法的访问修饰符": "public",
      "method_return_type|方法的返回值类型": null,
      "method_return_value|方法的返回值类型": null,
      "method_modifiers|方法的特殊性质": ["normal"],
      "method_type|方法的类型": "class_method", //自己定义的描述符号,对于类方法而言,都是类方法
      "method_parameters|方法的参数列表": [
        {
          "parameter_name|参数名": "$username",
          "parameter_type|参数类型": null,
          "parameter_default_value|参数默认值": null
        }
      ],
      "called_methods|方法内部调用的其他方法或函数": [
        {
          "method_object|调用的目标对象": null, //有值表示是类方法
          "method_name|调用的方法名": "test_function",
          "method_fullname|调用的完整方法名": "myclass->test_function",
          "method_start_line|调用开始行号": 20,
          "method_end_line|调用结束行号": 20,
          "method_return_type|调用方法的返回值": null,
          "method_return_value|调用方方法的返回值类型": null,
          "method_modifiers|方法的特殊性质": ["static"],
          "method_parameters|调用方法的参数列表": [
                {
                  "parameter_name|参数名": "$username",
                  "parameter_type|参数类型": null,
                  "parameter_default_value|参数默认值": null
                }
            ],
          "method_type|调用方法的类型": "local_method",
        }
      ]
    }
  ]
}

## 考虑扩展的信息
  "class_dependencies|类的所有依赖项": { //这个可以在最后进行分析,避免代码混乱
    "dependent_functions|依赖的外部函数列表": [
      {
        "method_name|函数名": "test_function",
        "function_type|函数类型": "local_method"
      }
    ],
    "dependent_classes|依赖的外部类列表": []
  }

## 函数分析结果的格式设计 可完全拷贝类的方法属性
 
## 可以用类方法的解析格式来存储普通函数方法

