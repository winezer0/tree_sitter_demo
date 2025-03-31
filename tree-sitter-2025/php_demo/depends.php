<?php
require(dirname(__FILE__) . '/includes/init.php');
require_once(ROOT_PATH . 'includes/lib_order.php');
include(ROOT_PATH . 'includes/lib_goods.php');
include_once(ROOT_PATH . 'includes/lib_users.php');

use function think\Container;
use core\util\Snowflake;
