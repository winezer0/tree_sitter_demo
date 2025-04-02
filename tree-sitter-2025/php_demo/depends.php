<?php
require(dirname(__FILE__) . '/includes/init.php');
require_once(ROOT_PATH . 'includes/lib_order.php');
include(ROOT_PATH . 'includes/lib_goods.php');
include_once(ROOT_PATH . 'includes/lib_users.php');

use function think\Container\helper;
use core\util\Snowflake;
use const App\Config\MAX_USERS;

// 新增示例
use SomeNamespace\SomeTrait;  // Trait 导入
use LongNamespace\LongClassName as ShortName;  // 别名导入
use AnotherNamespace\{ClassA, ClassB, function someFunction, const SOME_CONST};  // Group Use 导入
