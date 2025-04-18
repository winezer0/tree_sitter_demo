<?php
// 这是一个单行注释
# 这是另一个单行注释
/*
这是一个多行注释
可以跨越多行
*/
namespace MyApp; //xxxxxxxxxx

/**
 * 这是一个文档注释
 */
class MyClass {
    public /**/ function sayHello() {//xxxxxxxxxx
        echo "Hello, World!";//xxxxxxxxxx
    }
}

// (program (php_tag) (comment) (comment) (comment) (namespace_definition name: (namespace_name (name))) (comment) (comment) (class_declaration name: (name) body: (declaration_list (method_declaration (visibility_modifier) (comment) name: (name) parameters: (formal_parameters) body: (compound_statement (comment) (echo_statement (encapsed_string (string_content))) (comment))))))
