<?php

namespace App\Test;

class MultiParamTest {
    private string $name;
    private int $age;
    private ?float $score;

    public function __construct(string $name, int $age = 18, ?float $score = null) {
        $this->name = $name;
        $this->age = $age;
        $this->score = $score;
    }

    public function testMultiParams(
        string $name,
        int $age,
        ?float $score = null,
        array $data = [],
        bool $isActive = true,
        \DateTime $date = null
    ) {
        $user = new self($name, $age, $score);
        $this->processData($data, $isActive);
        return $user;
    }

    private function processData(array $data, bool $flag) {
        if ($flag) {
            echo "Processing data...";
        }
    }
}

$test = new MultiParamTest("John", 25, 98.5);
$test->testMultiParams("Alice", 20, 95.5, ["test" => "value"], true, new \DateTime());