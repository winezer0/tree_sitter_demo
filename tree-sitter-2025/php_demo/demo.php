<?php

// 全局函数定义
function globalHelper($param) {
    echo "Global helper function\n";
    return $param * 2;
}

// 全局变量
$globalVar = 100;

// 定义一个工具类
class Utils {
    private static $counter = 0;
    
    public static function increment() {
        self::$counter++;
        return self::$counter;
    }
    
    public function formatString($str) {
        // 调用全局函数
        $value = globalHelper(10);
        return strtoupper($str) . $value;
    }
}

// 定义主要的业务类
class BusinessService {
    private $utils;
    private $name;
    
    public function __construct($name) {
        $this->name = $name;
        $this->utils = new Utils();  // 构造函数调用
    }
    
    public function processData($data) {
        // 调用实例方法
        $formatted = $this->utils->formatString($data);
        
        // 调用静态方法
        $count = Utils::increment();
        
        // 调用全局函数
        $result = globalHelper($count);
        
        return $this->finalizeResult($formatted, $result);
    }
    
    private function finalizeResult($str, $num) {
        global $globalVar;
        return "{$this->name}: {$str} ({$num}) - {$globalVar}";
    }
}

// 定义一个使用这些类的函数
function processUserData($userName, $userData) {
    // 创建服务实例
    $service = new BusinessService($userName);
    
    // 调用实例方法
    $result = $service->processData($userData);
    
    // 调用全局函数
    return globalHelper(strlen($result));
}

// 使用示例
$service = new BusinessService("TestUser");
$result = $service->processData("test data");
echo $result . "\n";

// 直接调用处理函数
$finalResult = processUserData("John", "sample data");
echo $finalResult . "\n"; 