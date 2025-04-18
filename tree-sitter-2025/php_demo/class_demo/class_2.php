<?php

namespace App\Test;

class SimpleTest {
    // 测试不同可见性和修饰符的属性
    private $name;
    protected static $count = 0;
    public readonly $id;
    private $value = "test";
    protected $number = 3.14;
    private $isActive = true;
    public $data = null;

    // 测试构造函数和参数
    public function __construct(string $name) {
        $this->name = $name;
        self::$count++;
    }

    // 测试静态方法
    public static function getCount(): int {
        test_function();
        return self::$count;
    }

    // 测试普通方法和内置函数调用
    public function display(): void {
        echo $this->name;
        imap_open();
        test_function();
    }
}

function test_function() {
    echo "test";
}