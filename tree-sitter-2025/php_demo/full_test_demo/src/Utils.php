<?php
namespace DemoProject\Utils;

// 工具函数（演示函数调用）
function greet(string $name): string {
    return "Hello, " . $name . "!";
}

// 另一个工具函数（会被其他文件调用）
function logMessage(string $message): void {
    file_put_contents('log.txt', date('Y-m-d H:i:s') . " - " . $message . PHP_EOL, FILE_APPEND);
}
?>