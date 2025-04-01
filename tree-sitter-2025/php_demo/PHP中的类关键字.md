在 PHP 中，namespace 是用来组织代码的一种机制，类似于文件夹的作用。它可以帮助避免类、接口、函数或常量之间的命名冲突，特别是在大型项目或使用第三方库时非常有用。

## 1. Namespace 的基本用法
namespace 用于声明一个命名空间。
命名空间的定义必须出现在文件的顶部（除了 <?php 标记和可能的 declare 语句之外）。
示例：
```
<?php
namespace MyApp;

class User {
    public function greet() {
        echo "Hello from User!";
    }
}

$user = new User();
$user->greet();
```
如果需要在另一个文件中使用 MyApp\User 类，可以使用 use 关键字导入命名空间：
```
<?php
namespace AnotherApp;

use MyApp\User;

$user = new User();
$user->greet();
```

## 2. extends 和 namespace 的结合
extends 是用来实现类继承的关键字。命名空间中的类可以继承同一个命名空间或其他命名空间中的类。

示例：
```
<?php
namespace MyApp;

class ParentClass {
    public function sayHello() {
        echo "Hello from ParentClass!";
    }
}

class ChildClass extends ParentClass {
    public function sayWorld() {
        echo " World!";
    }
}

$child = new ChildClass();
$child->sayHello(); // 输出: Hello from ParentClass!
$child->sayWorld(); // 输出: World!
```
## 3. Interface 和 namespace 的结合
interface 是用来定义接口的关键字。接口可以定义在一个命名空间中，并且可以在其他命名空间中被实现。

```
<?php
namespace MyApp;

interface MyInterface {
    public function doSomething();
}

class MyClass implements MyInterface {
    public function doSomething() {
        echo "Doing something!";
    }
}
$obj = new MyClass();
$obj->doSomething(); // 输出: Doing something!
```

## 4. extends、namespace 和 interface 结合在一起
你可以在一个命名空间中定义接口，并在另一个命名空间中通过继承和实现来使用它们。

文件: MyApp/Interfaces.php
```
<?php
namespace MyApp;

interface MyInterface {
    public function doSomething();
}

abstract class AbstractClass {
    abstract public function sayHello();
}
```

文件: AnotherApp/ConcreteClass.php
```
namespace AnotherApp;

use MyApp\MyInterface;
use MyApp\AbstractClass;

class ConcreteClass extends AbstractClass implements MyInterface {
    public function sayHello() {
        echo "Hello from ConcreteClass!";
    }

    public function doSomething() {
        echo " Doing something!";
    }
}

$obj = new ConcreteClass();
$obj->sayHello();    // 输出: Hello from ConcreteClass!
$obj->doSomething(); // 输出: Doing something!
```

## 总结
namespace 可以很好地组织代码，避免命名冲突。

extends 可以继承同一个命名空间或其他命名空间中的类。

interface 可以定义在命名空间中，并在其他命名空间中实现。

extends 和 implements 可以同时使用，结合命名空间的功能， 构建复杂的类继承和接口实现结构。

希望这些例子能帮助你更好地理解 namespace 的用法！
