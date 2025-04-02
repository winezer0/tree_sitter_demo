## 普通函数分析结果的格式设计 # 文件的方法列表 不包含类的方法
```
[  
	    {
	      "METHOD_NAME": "__CONSTRUCT",           #方法名
	      "METHOD_START_LINE": 17,   #方法开始行号
	      "METHOD_END_LINE": 21,     #方法结束行号#

	      "METHOD_OBJECT": "CLASS_NAME",   # 方法对应的类对象 对于类方法而言就是自身
	      "METHOD_FULL_NAME": "CLASS_NAME->__CONSTRUCT",  #调用的完整方法名
	      "METHOD_VISIBILITY": "PUBLIC",  #方法的访问修饰符
	      "METHOD_MODIFIERS": [],         #方法的特殊修饰符
	      "METHOD_RETURN_TYPE": NULL,     #方法的返回值类型
	      "METHOD_RETURN_VALUE": NULL,    #方法的实际返回值

	      "METHOD_TYPE": "CLASS_METHOD",  #方法的类型 自己定义的描述符号,对于类方法而言,都是类方法
	      "METHOD_PARAMETERS": [          #方法的参数列表
	        {
	          "PARAMETER_INDEX":0,    			#参数索引
	          "PARAMETER_NAME": "$USERNAME",    #参数名
	          "PARAMETER_TYPE": NULL,          #参数类型
	          "PARAMETER_DEFAULT": NULL,       #参数默认值
	          "PARAMETER_VALUE": NULL,         #参数值
	        }
      ],
      "CALLED_METHODS": [                   #方法内调用的其他方法列表
	    {
	      "METHOD_NAME": "__CONSTRUCT",    #方法名
	      "METHOD_START_LINE": 17,         #方法开始行号
	      "METHOD_END_LINE": 21,           #方法结束行号  

	      "METHOD_OBJECT": "",    #方法对应的类对象 //对于类方法而言就是自身
	      "METHOD_FULL_NAME": "", # 调用的完整方法名
	      "METHOD_VISIBILITY": "PUBLIC",  # 方法的访问修饰符
	      "METHOD_MODIFIERS": [],         # 方法的特殊修饰符

	      "METHOD_RETURN_TYPE": NULL,     # 方法的返回值类型
	      "METHOD_RETURN_VALUE": NULL,    # 方法的实际返回值

	      "METHOD_TYPE": "CLASS_METHOD",   # 方法的类型//自己定义的描述符号,对于类方法而言,都是类方法
	      "METHOD_PARAMETERS": [           # 方法的参数列表
	        {
			  "PARAMETER_INDEX":0,    			#参数索引
	          "PARAMETER_NAME": "$USERNAME",  # 参数名
	          "PARAMETER_TYPE": NULL,          # 参数类型
	          "PARAMETER_DEFAULT": NULL,       # 参数默认值
	          "PARAMETER_VALUE": NULL,         #参数值
	        }
      ]
    }
  ]
```