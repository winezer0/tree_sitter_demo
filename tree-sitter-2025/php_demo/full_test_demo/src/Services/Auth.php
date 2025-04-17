<?php

function login(User $user) {
    return $user->getInfo();
}


namespace DemoProject\Services;

// 引入模型（演示类依赖）
use DemoProject\Models\User;

class Auth {
    public function login(User $user): string {
        return "Logging in user: " . $user->getInfo();
    }
}
?>