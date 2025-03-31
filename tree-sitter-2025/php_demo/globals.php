<?php

// 全局变量声明
$global_user_id = 100;
$global_user_name = "admin";

// 文件级变量
$file_level_count = 0;
$file_level_status = true;

function test_globals() {
    // 声明使用全局变量
    global $global_user_id, $global_user_name;
    
    // 使用全局变量
    echo $global_user_id;
    $global_user_name = "new_admin";
    
    // 使用超全局变量
    $_SESSION['user_id'] = 1;
    $user_agent = $_SERVER['HTTP_USER_AGENT'];
    $post_data = $_POST['data'];
    $get_param = $_GET['id'];
    $cookie_value = $_COOKIE['token'];
    
    // 文件级变量需要 global 关键字才能在函数内使用
    global $file_level_count;
    $file_level_count++;
}

function another_function() {
    // 另一个函数中使用全局变量
    global $global_user_id;
    $global_user_id += 1;
    
    // 使用 $GLOBALS 数组访问全局变量
    $GLOBALS['global_user_name'] = "super_admin";
    
    // 使用其他超全局变量
    $_FILES['upload']['name'];
    $_ENV['PATH'];
    $_REQUEST['param'];
}

// 文件级变量的使用
$file_level_status = false;
$file_level_count = 10;