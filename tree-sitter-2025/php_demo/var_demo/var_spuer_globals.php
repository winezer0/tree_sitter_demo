<?php
$user_agent = $_SERVER;
$user_agent = $_SERVER[1111];
$user_agent = $_SERVER['aaa'];
$user_agent = $_SERVER[$bbb];
echo $user_agent;

function test_local_vars() {
    $post_data = $_POST['data'];
    echo $_POST['data'];
}

class MyClass {
    public $cookie_value = $_COOKIE['user'];

    function class_method() {
        // 使用超全局变量
        $env_path = $_ENV['PATH'];
        echo $env_path;
    }
}
