<?php

define('IN_ECS', true);

// 使用 define() 函数定义常量
define('MAX_USERS', 100);
define('PI', 3.14159);
define('SITE_NAME', 'My Website');
define('DEBUG_MODE', false);

// 使用 const 关键字定义常量
const DATABASE_HOST = 'localhost';
const DATABASE_PORT = 3306;
const API_VERSION = '1.0.0';
const ENABLE_CACHE = true;

// 定义数组常量
define('ALLOWED_TYPES', [
    'jpg',
    'png',
    'gif'
]);

// 类中的常量定义
class Config {
    const DEFAULT_TIMEZONE = 'Asia/Shanghai';
    const MAX_UPLOAD_SIZE = 5242880;  // 5MB
    const CACHE_EXPIRE = 3600;        // 1小时
}