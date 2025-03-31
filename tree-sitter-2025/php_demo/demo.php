<?php

// 全局变量
$globalCounter = 0;

// 全局辅助函数
function globalHelper($value) {
    global $globalCounter;
    $globalCounter++;
    return "Helper processed: " . $value;
}

function formatData($data) {
    return strtoupper(globalHelper($data));
}

// 基础工具类
class BaseUtils {
    protected static $instanceCount = 0;
    
    public function __construct() {
        self::$instanceCount++;
    }
    
    protected function getInstanceCount() {
        return self::$instanceCount;
    }
}

// 工具类
class Utils extends BaseUtils {
    private $prefix;
    
    public function __construct($prefix = '') {
        parent::__construct();
        $this->prefix = $prefix;
    }
    
    public function processString($str) {
        // 调用全局函数
        $processed = globalHelper($str);
        // 调用父类方法
        $count = $this->getInstanceCount();
        return $this->prefix . $processed . "#" . $count;
    }
    
    public static function staticProcess($data) {
        // 调用全局函数
        return formatData($data);
    }
}