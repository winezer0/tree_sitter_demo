<?php
static $static_counter = 0;

function test_local_vars() {
    // 静态变量声明和使用
    static $static_counter = 0;
    static $static_flag = false;
    $static_counter++;  // 增加计数器
    
    if ($static_counter > 5) {
        $static_flag = true;  // 修改静态标志
    }
}

class Myclass{
function another_function() {
    // 静态变量声明和使用
    static $another_static = "static value";
    static $call_count = 0;

    $call_count++;  // 记录函数调用次数
    $another_static .= " - Call #" . $call_count;  // 修改静态字符串
}
}
