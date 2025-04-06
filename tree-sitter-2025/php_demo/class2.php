<?php
function call_class($message='message') {
    $myClass = new MyClass("xxxx");
    $result = MyClass::classMethod2("测试调用");

}

namespace App\Namespace1{
    // 1. 定义一个简单的接口
    interface MyInterface extends MyInterfaceA,MyInterfaceB{
        public function interfaceMethod();
    }

    // 2. 定义一个简单的抽象类
    abstract class MyAbstractClass extends MyAbstractClassA,MyAbstractClassB{
        // 抽象方法
        abstract public function abstractMethod();

        // 普通方法
        public function commonMethod() {
            echo "This is a common method in the abstract class.\n";
        }
    }

    // 3. 定义一个普通类，包含类属性和类方法
    class MyClass {
        // 类属性
        public static $classProperty = "I am a class property";

        // 静态方法
        public static function staticMethod() {
            echo "This is a static method. Class property value: " . self::$classProperty . "\n";
        }

        // 普通方法
        public function instanceMethod() {
          call_class($message='message');
        }
    }

}


namespace App\Namespace2;
// 4. 实现抽象类
class ConcreteClass extends MyAbstractClass {
    public function abstractMethod() {
        echo "Implemented abstractMethod in ConcreteClass.\n";
    }
}

// 5. 实现接口
class InterfaceImplementation implements MyInterface {
    public function interfaceMethod() {
        echo "Implemented interfaceMethod in InterfaceImplementation.\n";
    }
}
