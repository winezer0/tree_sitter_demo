<?php

namespace App\Test;

class TypeTest
{
    // 基本类型参数
    public function testBasicTypes(
        string $name,
        int $age,
        float $height,
        bool $isActive,
        array $hobbies
    ) {
        return $name;
    }

    // 可空类型参数
    public function testNullableTypes(
        ?string $name,
        ?int $age,
        ?float $height
    ) {
        return $name;
    }

    // 带默认值的参数
    public function testDefaultValues(
        string $name = "default",
        int $age = 18,
        float $height = 1.75,
        bool $active = true,
        array $items = [],
        ?string $nickname = null
    ) {
        return $name;
    }

    // 类类型参数
    public function testClassTypes(
        \DateTime $date,
        self $selfType,
        \App\Test\TypeTest $typeTest,
        ?\DateTime $nullableDate
    ) {
        return $date;
    }

    // 构造函数参数
    public function __construct(
        private string $name,
        protected ?int $age = null,
        public \DateTime $createdAt = new \DateTime()
    ) {
    }

    // 方法调用和对象创建
    public function testMethodCalls()
    {
        $obj = new self("test", 20);
        $date = new \DateTime("now");
        $this->testClassTypes($date, $obj, $this, null);
        $this->testBasicTypes("John", 25, 1.80, true, ["reading"]);
    }
}

// 接口参数测试
interface TestInterface
{
    public function interfaceMethod(
        string $name,
        ?int $age,
        \DateTime $date
    ): string;
}

// 抽象类参数测试
abstract class AbstractTest
{
    abstract public function abstractMethod(
        string $name,
        ?self $parent = null,
        array $config = []
    ): void;
}