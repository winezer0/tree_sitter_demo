<?php
namespace MyNamespace;

interface MyInterface {
    public function interfaceMethod();
}

class MyClass implements MyInterface {
    public function interfaceMethod() {
        echo "Interface method implemented";
    }
}