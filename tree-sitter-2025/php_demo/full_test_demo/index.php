<?php
// 引入自动加载文件
require_once 'autoload.php';

// 使用命名空间中的类
// use DemoProject\Models\User;
use DemoProject\Models\User2;
use DemoProject\Services\Auth;

// 调用工具函数
echo \DemoProject\Utils\greet("World") . "<br>";

// // 实例化 User 类
// $user = new User("John", "john@example.com");
// echo $user->getInfo() . "<br>";

$user2 = new UserDemo();
echo $user2->getInfo() . "<br>";

// 调用 Auth 服务
$auth = new Auth();
echo $auth->login($user) . "<br>";

// 引入数据库配置（演示 require/include）
require 'config/db.php';
echo "DB Host: {$dbConfig['host']}<br>";
?>