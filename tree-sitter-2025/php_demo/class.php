<?php

// 引入其他命名空间的类
use App\Services\EmailService;
use App\Utils\Logger;
use App\Interfaces\UserInterface;

class UserManager implements UserInterface {
    // trait 的使用
    use \App\Traits\Loggable;
    use \App\Traits\Validatable {
        Validatable::validate insteadof Loggable;
        Loggable::validate as validateLog;
    }
    
    private $username;
    private $email;
    private static $userCount = 0;
    private $emailService;
    private $logger;
    
    public function __construct($username, $email) {
        $this->username = $username;
        $this->email = $email;
        self::$userCount++;
        
        // 使用导入的类
        $this->emailService = new EmailService();
        $this->logger = new Logger();
    }
    
    // 获取用户名
    public function getUsername() {
        return $this->username;
    }
    
    // 设置用户名
    public function setUsername($username) {
        $this->username = $username;
    }
    
    // 获取邮箱
    public function getEmail() {
        return $this->email;
    }
    
    // 设置邮箱
    public function setEmail($email) {
        $this->email = $email;
    }
    
    // 静态方法：获取用户总数
    public static function getUserCount() {
        return self::$userCount;
    }
    
    // 实例方法：显示用户信息
    public function displayInfo() {
        return "用户名: " . $this->username . ", 邮箱: " . $this->email;
    }
    
    public function sendNotification($message) {
        $this->emailService->send($this->email, $message);
        $this->logger->info("Notification sent to {$this->username}");
    }
}

// 使用示例
$user1 = new UserManager("张三", "zhangsan@example.com");
$user2 = new UserManager("李四", "lisi@example.com");

echo $user1->displayInfo() . "\n";
echo $user2->displayInfo() . "\n";
echo "总用户数: " . UserManager::getUserCount() . "\n";