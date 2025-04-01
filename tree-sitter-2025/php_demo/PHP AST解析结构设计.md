## 类分析结果的格式设计
{
  "class_name|类名": "UserManager",
  "class_start_line|类开始行": 11,
  "class_end_line|类结束行": 11,
  "class_type": "type_class" -> 需要修改为 normal普通类|abstract抽象类|final最终类|静态类？
  "class_extends": null, -> 需要修改为继承|实现的源类
  "class_props|类的属性列表": [
    {
      "prop_name|属性名": "$username",
      "prop_line|属性行": 13,
      "prop_visibility|属性访问性质": "private",
      "prop_is_static|属性特殊性质": false, -> 需要修改 final|Static|const|normal
      "prop_value|属性值": null
    }, {
      "prop_name|属性名": "$userCount",
      "prop_line|属性行": 14,
      "prop_visibility|属性访问性质": "private",
      "prop_is_static|属性特殊性质": true, -> 需要修改 final|Static|const|normal
      "prop_value|属性值": null
    }
  ],
  "class_methods|类的方法列表": [
    {
      "method_name|方法名": "__construct",
      "method_start_line|方法开始行": 17,
      "method_end_line|方法结束行": 17,
      "method_visibility|方法的可访问性": "public",
      "method_is_static|方法特殊性质": false, -> 需要修改 final|Static|const|normal
      "method_params|方法的参数列表": [
        {
          "param_name|方法的参数名": "$username",
          "param_value|方法的参数值": null,
          "param_type|方法的参数类型": null, ->这个可能分析不出来
        }
      ],
      "called_functions|方法内部调用的方法": [
        {
          "call_func_name|调用的方法名": "test_function",
          "call_start_line|调用方法所在的行": 21,
          "call_end_line|调用方法所在的行": 21,
          "call_func_type|调用方法的类型": "local_method", -> 本文件方法|php内置方法|类的实例方法|类的静态方法等 ->这里最好把静态方法拆出来,作为一个新的属性名称
          "call_func_params|调用方法的参数列表": [ ->暂时没有实现,需要实现
              "param_name|方法的参数名": "$username",
              "param_value|方法的参数值": null,
              "param_type|方法的参数类型": null, ->这个可能分析不出
            ]
        }
      ]
    }
  ],
  "class_depends|整个类中所有依赖的外部函数": [ ->在最后进行统计即可,不需要也可以
    {
      "function_name": "test_function",
      "func_type": "local_method"
    }
  ],
}


## 函数分析结果的格式设计
  "file_methods|文件的方法列表": [
    {
      "method_name|方法名": "test",
      "method_start_line|方法开始行": 17,
      "method_end_line|方法结束行": 17,
      "method_visibility|方法的可访问性": "public", -> 默认都是空的
      "method_params|方法的参数列表": [
        {
          "param_name|方法的参数名": "$username",
          "param_value|方法的参数值": null,
          "param_type|方法的参数类型": null, ->这个可能分析不出来
        }
      ],
      "called_functions|方法内部调用的方法": [
        {
          "call_func_name|调用的方法名": "test_function",
          "call_start_line|调用方法所在的行": 21,
          "call_end_line|调用方法所在的行": 21,
          "call_func_type|调用方法的类型": "local_method", -> 本文件方法|php内置方法|类的实例方法|类的静态方法等 ->这里最好把静态方法拆出来,作为一个新的属性名称
          "call_func_params|调用方法的参数列表": [ ->暂时没有实现,需要实现
              "param_name|方法的参数名": "$username",
              "param_value|方法的参数值": null,
              "param_type|方法的参数类型": null, ->这个可能分析不出
            ]
        }
      ]
    }
  ]
  
## 可以用类方法的解析格式来存储普通函数方法

