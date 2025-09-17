<?php
$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];
$blocked_b = ['find', 'filter', 'c', 'pa', 'proc', 'dir', 'regexp', 'n', 'alter', 'load', 'grep', 'o', 'file', 't', 'w', 'insert', 'sort', 'h', 'sy', '\.\.', 'array', 'sh', 'touch', 'e', 'php', 'f'];

$pattern_a = '/' . implode('|', array_map(function ($s) {
    return preg_quote($s, '/'); }, $blocked_a)) . '/i';
$pattern_b = '/' . implode('|', array_map(function ($s) {
    return preg_quote($s, '/'); }, $blocked_b)) . '/i';

echo "寻找可以作为 \$a 的函数（第一个参数任意，第二个参数可控）:\n\n";

$all_functions = get_defined_functions()['internal'];
$candidates = [];

foreach ($all_functions as $func) {
    // 检查是否通过 blocked_a
    if (preg_match($pattern_a, $func)) {
        continue;
    }

    // 获取函数信息
    try {
        $ref = new ReflectionFunction($func);
        $params = $ref->getParameters();

        // 我们需要至少2个参数的函数，第二个参数能让我们执行代码
        if (count($params) >= 2) {
            $candidates[] = [
                'name' => $func,
                'params' => count($params),
                'param_names' => array_map(function ($p) {
                    return $p->getName(); }, $params)
            ];
        }
    } catch (Exception $e) {
        // 跳过
    }
}

echo "找到 " . count($candidates) . " 个候选函数\n\n";

// 显示前20个
echo "前20个候选:\n";
foreach (array_slice($candidates, 0, 20) as $cand) {
    echo sprintf(
        "%-30s (%d params): %s\n",
        $cand['name'],
        $cand['params'],
        implode(', ', $cand['param_names'])
    );
}

// 寻找特别有用的函数
echo "\n\n=== 有用的函数 ===\n";
$useful_keywords = ['create', 'call', 'invoke', 'include', 'require', 'eval', 'assert'];

foreach ($candidates as $cand) {
    foreach ($useful_keywords as $keyword) {
        if (stripos($cand['name'], $keyword) !== false) {
            echo sprintf("%-30s: %s\n", $cand['name'], implode(', ', $cand['param_names']));
            break;
        }
    }
}

// 特别检查 assert
echo "\n\n=== 检查 assert 函数 ===\n";
if (!preg_match($pattern_a, 'assert')) {
    echo "assert 通过 blocked_a 检查！\n";
    echo "assert() 可以执行字符串作为 PHP 代码\n";
    echo "assert('', 'code') - 但是第一个参数是断言，第二个是描述\n";

    $ref = new ReflectionFunction('assert');
    echo "参数: ";
    foreach ($ref->getParameters() as $p) {
        echo $p->getName() . " ";
    }
    echo "\n";
} else {
    echo "assert 被过滤\n";
}

// 检查 create_function
echo "\n=== 检查 create_function ===\n";
if (function_exists('create_function')) {
    if (!preg_match($pattern_a, 'create_function')) {
        echo "create_function 通过检查！\n";
        echo "create_function(\$args, \$code) 可以创建匿名函数\n";
    } else {
        echo "create_function 被过滤\n";
    }
} else {
    echo "create_function 在PHP 8+中已被移除\n";
}
