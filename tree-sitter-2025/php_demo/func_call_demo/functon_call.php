<?php
if ($_REQUEST['act'] == 'back_list')
{
    /* 检查权限 */
    $result = back_action($back_id, $status_back, $status_refund,  $note = '', $username = null)
}
