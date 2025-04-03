<?php
if ($_REQUEST['act'] == 'back_list')
{
    /* 检查权限 */
    $result = back_action($back_id, $status_back, $status_refund,  $note = '', $username = null)
}

// 创建类实例
$myClass = new MyClass();
// 调用类方法
$result = $myClass->classMethod("测试调用");
