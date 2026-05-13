<?php
$url = "http://challenge.bluesharkinfo.com:29023/";

// 测试1: 访问基础页面
echo "===== 测试1: 基础页面 =====\n";
$response = file_get_contents($url);
echo substr($response, 0, 500) . "\n\n";

// 测试2: 用一个简单的payload看报错
echo "===== 测试2: 简单payload =====\n";
$简单payload = 'O:4:"FLAG":2:{s:1:"a";s:0:"";s:1:"b";s:4:"test";}';
$encoded = urlencode($简单payload);
$test_url = $url . "?exp=" . $encoded;
echo "URL: $test_url\n";
$response = @file_get_contents($test_url);
echo "响应:\n" . $response . "\n\n";

// 测试3: 看看是否可以通过某种方式绕过 flag 检查
echo "===== 测试3: 尝试不同的类名变体 =====\n";

// 也许题目环境中还有其他类？
// 或者我们可以利用PHP的动态特性？

echo "由于 'FLAG' 被过滤，让我们想想是否有其他办法引用这个类...\n";
echo "在PHP中，类名可以通过字符串动态引用\n";
echo "但在 __destruct 中，\$a 已经是字符串了，直接调用\n\n";

echo "======== 关键发现 ========\n";
echo "等一下！让我重新看代码:\n";
echo "在 __destruct 中:\n";
echo "  \$a = (string) \$this->a;\n";
echo "  \$b = (string) \$this->b;\n";
echo "  if (\$this->check(\$a, \$b)) {\n";
echo "      \$a('', \$b);\n";
echo "  }\n\n";

echo "注意！check 方法是 private 的，它不是静态方法！\n";
echo "所以 \$this->check(\$a, \$b) 是在对象的上下文中调用的\n\n";

echo "这意味着什么？也许我们可以利用 \$this ？\n";
echo "不，在字符串化后，\$a 和 \$b 就是纯字符串了\n\n";

echo "========我想到了另一个角度！========\n";
echo "也许题目确实无解？\n";
echo "或者需要找到服务器上存在的其他类？\n";
echo "或者... 题目描述中有提示？\n\n";

// 让我尝试一个完全不同的方法
echo "=== 尝试利用 PHP 的 autoload ===\n";
echo "如果服务器配置了 autoload，当我们引用一个不存在的类时\n";
echo "autoload 函数会被调用\n";
echo "但这需要 spl_autoload_register，而且我们无法控制 autoload 逻辑\n\n";

echo "=== 最后的最后 ===\n";
echo "让我检查一下是否我对 'flag' 过滤的理解有误...\n";
$pattern = '/flag/i';
$tests = ['FLAG', 'FLaG', 'fLAG', 'flAG'];
foreach ($tests as $test) {
    echo "$test => " . (preg_match($pattern, $test) ? "MATCH" : "NO") . "\n";
}

echo "\n确实，/flag/i 会匹配所有大小写组合\n";
echo "所以 'FLAG' 无法绕过\n\n";

echo "========== 结论 ==========\n";
echo "基于当前的分析，你的思路是正确的！\n";
echo "通过 \$a = '类名'，让 __destruct 调用 类名('', \$b)\n";
echo "从而触发 __construct，执行 eval(\$b)\n\n";
echo "但是 'FLAG' 被 '/flag/i' 过滤了\n\n";
echo "可能的解决方案:\n";
echo "1. 题目环境中有其他可利用的类（但我们不知道）\n";
echo "2. 我遗漏了某个可以绕过过滤的技巧\n";
echo "3. 有其他完全不同的解法\n\n";

echo "让我再尝试访问目标看看有没有其他线索...\n";
