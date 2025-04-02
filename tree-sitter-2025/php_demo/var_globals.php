<?php
// 文件级变量
$global_user_id = 100;
$global_user_name = "admin";

// 文件级全局变量
global $file_level_count;
global $file_level_status;
$file_level_count = 0;
$file_level_status = true;

function test_local_vars() {
    // 局部变量
    $local_var1 = "local value 1";
    $local_var2 = 42;
    $local_array = array(1, 2, 3);
    
    // 静态变量声明和使用
    static $static_counter = 0;
    static $static_flag = false;
    $static_counter++;  // 增加计数器
    
    if ($static_counter > 5) {
        $static_flag = true;  // 修改静态标志
    }
    
    // 使用静态变量
    echo "Counter: " . $static_counter . "\n";
    echo "Flag: " . ($static_flag ? "true" : "false") . "\n";
    
    // 全局变量声明
    global $file_level_count, $file_level_status;
    
    // 使用超全局变量
    $user_agent = $_SERVER['HTTP_USER_AGENT'];
    $request_method = $_SERVER['REQUEST_METHOD'];
    $session_id = $_SESSION['id'];
    $get_param = $_GET['param'];
    $post_data = $_POST['data'];
}

function another_function() {
    // 静态变量声明和使用
    static $another_static = "static value";
    static $call_count = 0;
    
    $call_count++;  // 记录函数调用次数
    $another_static .= " - Call #" . $call_count;  // 修改静态字符串
    
    echo "Static value: " . $another_static . "\n";
    echo "This function has been called " . $call_count . " times\n";
    
    // 全局变量声明
    global $file_level_count;
    $file_level_count = 10;
    
    // 使用超全局变量
    $cookie_value = $_COOKIE['user'];
    $env_path = $_ENV['PATH'];
    $files_info = $_FILES['upload'];
}

// 更新文件级变量
$file_level_status = false;
$file_level_count = 10;

// 使用 REQUEST 超全局变量
$request_data = $_REQUEST['data'];

// 测试静态变量的效果
test_local_vars();  // 第一次调用
test_local_vars();  // 第二次调用
another_function(); // 第一次调用
another_function(); // 第二次调用

?>