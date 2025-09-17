<?php
$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];

$pattern_a = '/' . implode('|', array_map(function ($s) {
    return preg_quote($s, '/'); }, $blocked_a)) . '/i';

// 直接测试一些可能有用的函数
$test_functions = [
    'define',
    'call_user_func',
    'call_user_func_array',
    'usort',
    'uasort',
    'uksort',
    'array_walk',
    'array_walk_recursive',
    'array_reduce',
    'array_map',
    'array_filter',
    'preg_replace_callback',
    'ob_start',
    'register_shutdown_function',
    'register_tick_function',
    'sqlite_create_function',
    'mb_ereg_replace_callback'
];

echo "测试可能有用的函数:\n\n";

foreach ($test_functions as $func) {
    $status = preg_match($pattern_a, $func) ? 'BLOCKED' : 'OK';
    $exists = function_exists($func) ? 'EXISTS' : 'N/A';

    echo sprintf("%-35s [%s] %s\n", $func, $status, $exists);

    if ($status == 'OK' && $exists == 'EXISTS') {
        try {
            $ref = new ReflectionFunction($func);
            $params = $ref->getParameters();
            echo "    参数: ";
            foreach ($params as $p) {
                echo $p->getName() . ($p->isOptional() ? '?' : '') . ', ';
            }
            echo "\n";
        } catch (Exception $e) {
        }
    }
}

// 特别关注的：uasort, usort, uksort 这些可以调用回调函数
echo "\n\n=== 关键发现 ===\n";
echo "usort 系列函数可以接受回调函数！\n";
echo "如果 \$a = 'usort'，那么 usort('', \$b) 会怎样？\n";
echo "usort 需要一个数组和一个回调函数\n";
echo "第一个参数是空字符串，不是数组，会报错但可能会先执行回调？\n\n";

// 测试 call 相关
echo "=== call_user_func 系列 ===\n";
echo "这些函数可以动态调用其他函数\n";
echo "但是它们都包含被过滤的字符...\n\n";

// 我们需要的是：第二个参数会被当作代码执行的函数
echo "=== 重新思考 ===\n";
echo "我们的目标是找到一个函数 f，使得 f('', \$b) 能执行 \$b\n";
echo "或者 \$b 能控制函数的行为以执行任意代码\n\n";

// 测试一个关键发现
echo "关键想法：某些函数的第二个参数是 callback\n";
$callback_funcs = ['uasort', 'uksort', 'usort', 'array_walk', 'array_reduce', 'array_map', 'array_filter'];

foreach ($callback_funcs as $func) {
    if (!preg_match($pattern_a, $func) && function_exists($func)) {
        echo "✓ $func 可用！\n";
    }
}
