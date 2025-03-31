<?php

function back_action($back_id, $status_back, $status_refund,  $note = '', $username = null)
{
    if (is_null($username))
    {
        $username = $_SESSION['admin_name'];
    }

    $sql = 'INSERT INTO ' . $GLOBALS['ecs']->table('back_action') .
                ' (back_id, action_user, status_back, status_refund,  action_note, log_time) ' .
            'SELECT ' .
                "$back_id, '$username', '$status_back', '$status_refund',  '$note', '" .gmtime() . "' " .
            'FROM ' . $GLOBALS['ecs']->table('back_order') . " WHERE back_id = '$back_id'";
    $GLOBALS['db']->query($sql);
}
