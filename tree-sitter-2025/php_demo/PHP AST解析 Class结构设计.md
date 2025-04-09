## 类分析结果的格式设计
```
{
  "CLASS_NAME": "USERMANAGER",  #类名
  "CLASS_START_LINE": 11,   #类开始行号
  "CLASS_END_LINE": 25,     #类结束行号
  "CLASS_NAMESPACE": "",    #类的命名空间
  "CLASS_VISIBILITY": [],   #类的访问修饰符
  "CLASS_MODIFIERS": [],    #类的特殊修饰符
  "CLASS_EXTENDS": [{父类名称:文件路径}], # 类继承的父类列表
  "CLASS_INTERFACES": [{抽象类名称:文件路径}], # 类实现的接口列表
  "CLASS_PROPERTIES": [       #类的属性列表
	    {
	      "PROPERTY_NAME": "$USERNAME",   #属性名
	      "PROPERTY_LINE": 13,            #属性行号
	      "PROPERTY_TYPE": NULL,          #属性类型
	      "PROPERTY_VISIBILITY": "PRIVATE",   #属性的访问修饰符
	      "PROPERTY_MODIFIERS": [],       #属性的特殊修饰符
	      "PROPERTY_INITIAL_VALUE": NULL,  #属性的初始值
	    }
  ],
  "CLASS_METHODS|类的方法列表": [
	    {
	      "METHOD_NAME": "__CONSTRUCT",           #方法名
	      "METHOD_START_LINE": 17,   #方法开始行号
	      "METHOD_END_LINE": 21,     #方法结束行号#

	      "METHOD_OBJECT": "CLASS_NAME",   # 方法对应的类对象 对于类方法而言就是自身
	      "METHOD_CLASS": "CLASS_NAME",   # 方法对应的类
	      "METHOD_FULL_NAME": "CLASS_NAME->__CONSTRUCT",  #调用的完整方法名
	      "METHOD_VISIBILITY": "PUBLIC",  #方法的访问修饰符
	      "METHOD_MODIFIERS": [],         #方法的特殊修饰符
	      "METHOD_RETURN": [],            #方法的返回信息

	      "METHOD_TYPE": "CLASS_METHOD",  #方法的类型 自己定义的描述符号,对于类方法而言,都是类方法
	      "METHOD_PARAMETERS": [          #方法的参数列表
	        {
	          "PARAMETER_INDEX":0,    			#参数索引
	          "PARAMETER_NAME": "$USERNAME",    #参数名
	          "PARAMETER_TYPE": NULL,          #参数类型
	          "PARAMETER_DEFAULT": NULL,       #参数默认值
	          "PARAMETER_VALUE": NULL,         #参数值
	        },
	        "IS_NATIVE": None,   # 被调用方法是否在本文件内
      ],
      "CALLED_METHODS": [                   #方法内调用的其他方法列表
	    {
	      "METHOD_NAME": "__CONSTRUCT",    #方法名
	      "METHOD_START_LINE": 17,         #方法开始行号
	      "METHOD_END_LINE": 21,           #方法结束行号  

	      "METHOD_OBJECT": "CLASS_NAME",   # 方法对应的类对象 对于类方法而言就是自身
	      "METHOD_CLASS": "CLASS_NAME",   # 方法对应的类
	      "METHOD_FULL_NAME": "", # 调用的完整方法名
	      "METHOD_VISIBILITY": "PUBLIC",  # 方法的访问修饰符
	      "METHOD_MODIFIERS": [],         # 方法的特殊修饰符

	      "METHOD_RETURN": [],            #方法的返回信息

	      "METHOD_TYPE": "CLASS_METHOD",   # 方法的类型//自己定义的描述符号,对于类方法而言,都是类方法
	      "METHOD_PARAMETERS": [           # 方法的参数列表
	        {
			  "PARAMETER_INDEX":0,    			#参数索引
	          "PARAMETER_NAME": "$USERNAME",  # 参数名
	          "PARAMETER_TYPE": NULL,          # 参数类型
	          "PARAMETER_DEFAULT": NULL,       # 参数默认值
	          "PARAMETER_VALUE": NULL,         #参数值
	        },
	        "IS_NATIVE": None,   # 被调用方法是否在本文件内
      ]
    }
  ]
}
```

## 函数分析结果的格式设计 可完全拷贝类的方法属性
 

