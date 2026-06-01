<?php
// 让我仔细分析 blocked_a 的每一个词
$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];

echo "blocked_a 分析：\n";
foreach ($blocked_a as $item) {
    echo "  '$item'\n";
}

echo "\n这意味着包含以下子字符串的都会被过滤（不区分大小写）：\n";
echo "- p: passthru, proc_open, popen等\n";
echo "- s: system, shell_exec, show_source等\n";
echo "- h: shell, chmod等\n";
echo "- w: passthru, fwrite等\n";
echo "- er: error, preg_filter等\n";
echo "- str: str_replace, strpos等\n";
echo "- or: error, ignore等\n";
echo "- ay: array等\n";
echo "\n";

echo "等等！'p', 's', 'h', 'w' 这些单个字母也被过滤了？\n";
echo "这意味着任何包含这些字母的函数名都不行！\n\n";

// 测试一些函数
$test_funcs = [
    'print', // 有 p
    'echo', // 有 h  
    'system', // 有 s
    'passthru', // 有 p, s, h
    'phpinfo', // 有 p, h
    'var_dump', // 没有 p, s, h, w, er, str, or, ay
    'print_r', // 有 p, r (但 'r' 不在 blocked_a 中，只有 'or')
    'die', // 没有
    'exit', // 没有
];

$pattern_a = '/' . implode('|', array_map(function ($s) {
    return preg_quote($s, '/'); }, $blocked_a)) . '/i';

echo "测试函数：\n";
foreach ($test_funcs as $func) {
    $status = preg_match($pattern_a, $func) ? '✗' : '✓';
    echo "  $status $func\n";
}

echo "\n哇！var_dump, die, exit 都可以通过！\n";
echo "但问题是它们不能帮我们执行命令...\n\n";

// 继续寻找...
echo "让我找所有不包含 p,s,h,w,er,str,or,ay 且能执行代码的函数:\n\n";

$危险函数 = [
    'eval' => 'BLOCKED (eval)',
    'assert' => 'BLOCKED (er)',
    'system' => 'BLOCKED (s)',
    'exec' => 'BLOCKED (exec)',
    'shell_exec' => 'BLOCKED (s,h,exec)',
    'passthru' => 'BLOCKED (p,s,h)',
    'proc_open' => 'BLOCKED (p,or,open)',
    'popen' => 'BLOCKED (p,open)',
    'pcntl_exec' => 'BLOCKED (p,exec)',
    'call_user_func' => 'BLOCKED (or)',
    'create_function' => 'BLOCKED (er)',
    'preg_replace' => 'BLOCKED (p,er)',
    'mb_ereg_replace' => 'BLOCKED (er)',
    'array_map' => 'BLOCKED (ay)',
    'array_filter' => 'BLOCKED (ay)',
    'usort' => 'BLOCKED (s,or)',
    '`cmd`' => 'Backtick - 需要在 eval 中',
];

foreach ($危险函数 as $func => $reason) {
    echo "  $func: $reason\n";
}

echo "\n结论：几乎所有能执行代码的方式都被blocked_a过滤了！\n";
echo "唯一的希望是反引号，但它需要在eval上下文中\n";
echo "而 __destruct 中是直接函数调用，不是 eval\n\n";

echo "========== 关键insight ==========\n";
echo "等等！让我重新看 __construct 中的 eval:\n";
echo "  eval(\$a . \$b);\n";
echo "如果 \$a 为空，就是 eval(\$b)\n";
echo "那么 \$b 可以是任何PHP代码，包括反引号命令！\n\n";

echo "但问题是：反序列化不会调用 __construct！\n\n";

echo "UNLESS... 我们想办法在反序列化过程中触发一个新对象的创建！\n\n";

echo "方法1：在对象属性中嵌套一个需要 __construct 的对象\n";
echo "  -> 但反序列化不会调用 __construct\n\n";

echo "方法2：通过 __wakeup 或 __destruct 创建新对象\n";
echo "  -> 没有 __wakeup，__destruct 需要合法的函数名\n\n";

echo "方法3：找到一个PHP内置类，它的反序列化会触发代码执行\n";
echo "  -> 这是典型的 PHP 反序列化漏洞，但需要知道具体的类\n\n";

echo "方法4：也许题目环境有其他可利用的类？\n";
echo "  -> 我们看不到完整的代码\n\n";

// 最后的尝试
echo "========== 最后尝试 ==========\n";
echo "让我尝试一些不太常见但可能有用的PHP特性:\n\n";

// 测试一些不常见的函数
$uncommon = ['forward_static_call', 'forward_static_call_array', 'iterator_apply', 'spl_autoload_call'];

foreach ($uncommon as $func) {
    if (function_exists($func) && !preg_match($pattern_a, $func)) {
        echo "✓ $func 可用且未被过滤！\n";
        $ref = new ReflectionFunction($func);
        echo "  参数: ";
        foreach ($ref->getParameters() as $p) {
            echo $p->getName() . ', ';
        }
        echo "\n";
    }
}
