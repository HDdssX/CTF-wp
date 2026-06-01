<?php
$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];
$pattern_a = '/' . implode('|', array_map(function ($s) {
    return preg_quote($s, '/'); }, $blocked_a)) . '/i';

echo "测试 'var_dump':\n";
if (preg_match($pattern_a, 'var_dump', $matches)) {
    echo "被过滤，匹配到: " . implode(', ', $matches) . "\n";
} else {
    echo "未被过滤\n";
}

echo "\n测试 'var':\n";
if (preg_match($pattern_a, 'var', $matches)) {
    echo "被过滤，匹配到: " . implode(', ', $matches) . "\n";
} else {
    echo "未被过滤\n";
}

echo "\n测试 'dump':\n";
if (preg_match($pattern_a, 'dump', $matches)) {
    echo "被过滤，匹配到: " . implode(', ', $matches) . "\n";
} else {
    echo "未被过滤\n";
}

// 原来 'd' 'u' 'm' 'p' 中，'p' 单独存在所以被过滤了！

echo "\n\n让我找真正不包含这些字母的函数:\n";
echo "不能包含: p, s, h, w, (还有 eval, dl, ls, escape, er, str, cat, flag, file, ay, or, ftp, dict, exec, open)\n\n";

// 找出完全不包含这些字母的函数
$all_funcs = get_defined_functions()['internal'];
$safe_funcs = [];

foreach ($all_funcs as $func) {
    if (!preg_match($pattern_a, $func)) {
        // 双重检查：确保不包含这些字母
        if (!preg_match('/[pshw]/i', $func)) {
            $safe_funcs[] = $func;
        }
    }
}

echo "完全安全的函数 (前30个):\n";
foreach (array_slice($safe_funcs, 0, 30) as $func) {
    echo "  $func\n";
}

echo "\n总共 " . count($safe_funcs) . " 个\n";

// 在这些函数中找有用的
echo "\n可能有用的:\n";
foreach ($safe_funcs as $func) {
    if (
        stripos($func, 'call') !== false ||
        stripos($func, 'exec') !== false ||
        stripos($func, 'eval') !== false ||
        stripos($func, 'run') !== false ||
        stripos($func, 'invoke') !== false
    ) {
        echo "  $func\n";
    }
}
