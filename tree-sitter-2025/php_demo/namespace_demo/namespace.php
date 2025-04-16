<?php
namespace MyApp\\Controllers1 {
    use MyApp\\Models\\User;
    class UserController {
        public function index() {
            $user = new User();
        }
    }
}

namespace MyApp\\Services;
    use MyApp\\Utils\\Logger;
    function logMessage($message) {
        Logger::log($message);
    }

namespace MyApp\\Services2;

namespace MyApp\\Controllers2 {
    use MyApp\\Models\\User;
    class UserController {
        public function index() {
            $user = new User();
        }
    }
}


namespace MyApp\\Controllers3 {}