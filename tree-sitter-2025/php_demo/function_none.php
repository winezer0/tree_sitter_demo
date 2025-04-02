<?php
$back_type_arr=array('0'=>'退货-退回', '1'=>'换货-退回', '2'=>'换货-换出', '4'=>'退款-无需退货');
back_list_6666666();
function back_action($back_id, $status_back, $status_refund,  $note = 'note', $username = 'admin')
{
    $username = $_SESSION['admin_name'];
    return $username;
}

if ($_REQUEST['act'] == 'back_list')
{
    /* 检查权限 */
    back_action($back_id, $status_back, $status_refund,  $note = '', $username = null)
    /* 查询 */
    $result = back_list($_REQUEST['act']);
}
