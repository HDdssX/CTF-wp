<?php
error_reporting(0);
require_once 'init.php';

function safe_str($str)
{
    if (preg_match('/[ \t\r\n]/', $str) || preg_match('/\/\*|#|--[ \t\r\n]/', $str)) {
        return false;
    }
    return true;
}

if (!isset($_GET['info']) || !isset($_GET['key'])) {
    highlight_file(__FILE__);
    die('');
}

$info = str_replace('`', '``', base64_decode($_GET['info']));
$key = base64_decode($_GET['key']);

if (!safe_str($info) || !safe_str($key)) {
    die('Invalid input');
}

$sql = "SELECT `$info` FROM users WHERE username = ?";

$stmt = $pdo->prepare($sql);
$stmt->execute([$key]);
print_r($stmt->fetchAll());