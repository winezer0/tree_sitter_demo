<?php
include_once(ROOT_PATH . 'includes/lib_users.php');
use function think\Container;
// 定义一个测试函数
function test_function($param) {
    return "测试函数输出: " . $param;
}

class UserManager {
    // 类属性
    private $username;
    private static $userCount = 0;
    
    // 构造函数
    public function __construct($username) {
        $this->username = $username;
        self::$userCount++;
        // 在方法内调用函数
        echo test_function("在构造函数中调用");
    }
    
    // 实例方法
    public function displayInfo() {
        // 在方法内调用函数
        $test_result = test_function($this->username);
        return "用户名: " . $test_result;
    }
    
    // 静态方法
    public static function getUserCount() {
        // 在静态方法中调用函数
        echo test_function("获取用户数");
        return self::$userCount;
    }
}

// 在类外调用函数
echo test_function("类外调用") . "\n";

// 使用示例
$user = new UserManager("张三");
echo $user->displayInfo() . "\n";
echo "总用户数: " . UserManager::getUserCount() . "\n";