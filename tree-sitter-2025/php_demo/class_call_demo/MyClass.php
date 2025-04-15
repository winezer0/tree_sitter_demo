<?php
require_once 'call_func.php';

class MyClass {
   public $property;
    // 构造函数
    public function __construct($value='666') {
        $this->property = $value;
    }

    public static function classMethod($input) {
        // 在类方法中调用普通函数
        return call_func("来自类方法: " . $input);
    }
}