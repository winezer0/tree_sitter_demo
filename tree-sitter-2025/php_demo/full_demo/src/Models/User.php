<?php
namespace DemoProject\Models;

// 引入工具函数（演示跨文件调用）
use function DemoProject\Utils\logMessage;

class User {
    public function __construct(
        private string $name,
        private string $email
    ) {
        logMessage("User {$name} created"); // 调用工具函数
    }

    public function getInfo(): string {
        return "User: {$this->name}, Email: {$this->email}";
    }
}

class UserDemo {
    private string $name="1111"
    private string $email="1111@666.com"
    public static function getInfo(): string {
        return "User: {$this->name}, Email: {$this->email}";
    }
}
?>