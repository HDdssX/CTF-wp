<?php
// 最终思路：我们需要一个不包含 blocked_a 字符的字符串作为 $a
// 并且这个字符串作为函数名调用时，第二个参数能让我们RCE

// 经过前面的分析，几乎所有有用的函数都被过滤了
// 让我们尝试一个完全不同的思路

// 如果 $a 为空字符串，check 会通过（空字符串不匹配任何pattern）
// 但是 $a("", $b) 会报错

// 如果 $a 是一个数字字符串呢？比如 "123"
$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];
$pattern_a = '/' . implode('|', array_map(function ($s) {
    return preg_quote($s, '/'); }, $blocked_a)) . '/i';

echo "测试特殊字符串:\n";
$tests = ['', '123', 'abc', 'xyz', 'md5', 'abs', 'min', 'max', 'defined', 'define'];

foreach ($tests as $test) {
    $status = preg_match($pattern_a, $test) ? 'BLOCKED' : 'OK';
    $callable = is_callable($test) ? 'CALLABLE' : 'NOT CALLABLE';
    echo sprintf("'%-10s' => %s, %s\n", $test, $status, $callable);
}

echo "\n我们可以用 'define' !\n";
echo "define(\$name, \$value) - 定义常量\n";
echo "define('', \$b) - 定义一个空名称的常量，这会失败但可能不影响执行\n\n";

echo "但这不能帮我们RCE...\n\n";

echo "========== 重新审视题目 ==========\n";
echo "问题的核心：\n";
echo "1. 我们可以控制 \$this->a 和 \$this->b\n";
echo "2. 在 __destruct 中，会调用 \$a('', \$b)\n";
echo "3. \$a 必须不包含 blocked_a 的字符\n";
echo "4. \$b 必须不包含 blocked_b 的字符\n";
echo "5. 我们需要通过这个机制RCE\n\n";

echo "重要发现：blocked_b 过滤了 'e'，所以我们不能用 eval、exec、shell_exec等\n";
echo "但是我们可以用反引号执行命令！\n";
echo "问题是反引号需要在 eval 上下文中，而 __destruct 直接调用函数\n\n";

echo "等等！也许题目的意图不是通过 __destruct！\n";
echo "让我重新看看 __construct:\n";
echo "  \$this->check(\$a, \$b);\n";
echo "  eval(\$a . \$b);\n";
echo "这里 eval 是直接执行的！\n\n";

echo "但是反序列化不会调用 __construct...\n";
echo "除非... 我们在 PHP 中有一个技巧！\n\n";

// PHP反序列化的技巧
echo "=== PHP 反序列化技巧 ===\n";
echo "当对象的属性是另一个对象时，反序列化会递归处理\n";
echo "但这还是不会调用 __construct\n\n";

echo "真正的技巧：使用 Phar 反序列化！\n";
echo "但这需要文件操作权限...\n\n";

echo "或者：如果存在 __wakeup 或 __unserialize 会在反序列化时调用\n";
echo "但题目代码中没有定义这些\n\n";

echo "========== 最后的想法 ==========\n";
echo "回到你的原始想法：让 \$a = 'XXX'（某个类名或函数名）\n";
echo "在 __destruct 中调用 XXX('', \$b)\n\n";

echo "如果我们找不到合适的函数，那么也许...\n";
echo "题目的意图是让我们找到一个不明显的PHP内置函数？\n\n";

// 让我搜索所有2参数且第一个参数无关紧要的函数
echo "寻找形如 func(any, code/callback) 的函数:\n\n";

$all_funcs = get_defined_functions()['internal'];
foreach ($all_funcs as $func) {
    if (preg_match($pattern_a, $func))
        continue;
    if (!function_exists($func))
        continue;

    try {
        $ref = new ReflectionFunction($func);
        $params = $ref->getParameters();

        if (count($params) >= 2) {
            // 检查第二个参数的名称是否暗示回调或代码
            $param2_name = $params[1]->getName();
            if (preg_match('/(callback|function|code|command|script)/i', $param2_name)) {
                echo "$func: " . $param2_name . "\n";
            }
        }
    } catch (Exception $e) {
    }
}
