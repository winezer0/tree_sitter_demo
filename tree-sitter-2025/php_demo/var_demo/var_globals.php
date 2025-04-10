<?php
// Global 全局变量
global $file_level_count;
global $file_level_status;
$file_level_count = 0;
$file_level_status = true;

function test_local_vars() {
    // 全局变量声明
    global $file_level_count;
    $file_level_count = 10;
}

class MyClass {
    // 全局变量声明
    global $file_level_count2;
    function class_method() {
        // 全局变量声明
        global $file_level_status2;
    }
}
