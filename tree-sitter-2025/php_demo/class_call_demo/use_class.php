<?php
require_once 'MyClass.php';


// 创建类实例
$myClass = new MyClass();
// 调用类方法
$result = $myClass->classMethod("测试调用");

function call_class($message='message') {
    $myClass = new MyClass("xxxx");
    $myClass->classMethod("yyyy");
}
call_class('xxxxxxxx');


class MyClass {
    public $aaa;
    public function __construct($aaa) {
        $this->aaa = $aaa;
    }
    public function classMethod($bbb) {
         echo $bbb;
    }
}
