<?php
namespace MyNamespace;

class ParentClass {
    public function parentMethod() {
        echo "Parent method called";
    }
}

class ChildClass extends ParentClass {
    public function childMethod() {
        $this->parentMethod();
    }
}