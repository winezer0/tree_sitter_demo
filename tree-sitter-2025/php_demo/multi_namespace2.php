<?php

namespace App\Controller;

class UserController {
    public function index() {
        echo "User Controller";
    }
}

namespace App\Model;

class User {
    private $name;
    
    public function __construct($name) {
        $this->name = $name;
    }
}

namespace App\Service;

class UserService {
    public static function create($name) {
        return new \App\Model\User($name);
    }
}