<?php

function function() {
    $call_count=1;  // 记录函数调用次数
    $another= "another";  // 修改静态字符串
}

$staticGreet = static function($name) {
    $name = "Hello";
    return $name;
};

class Myclass{
    function another() {
        $call_count=1;  // 记录函数调用次数
        $another= "another";  // 修改静态字符串
    }
}
