<?php
$blocked_b = ['find', 'filter', 'c', 'pa', 'proc', 'dir', 'regexp', 'n', 'alter', 'load', 'grep', 'o', 'file', 't', 'w', 'insert', 'sort', 'h', 'sy', '\.\.', 'array', 'sh', 'touch', 'e', 'php', 'f'];
$pattern_b = '/' . implode('|', array_map(function ($s) {
    return preg_quote($s, '/'); }, $blocked_b)) . '/i';

$tests = [
    ';var_dump(`xxd /?l?g`);die();',
    ';var_dump(`xxd /?l?g`);exit();',
    ';var_dump(`xxd /?l?g`);die;',
    ';var_dump(`xxd /?l?g`);exit;',
];

foreach ($tests as $test) {
    echo "Test: $test\n";
    if (preg_match($pattern_b, $test, $matches)) {
        echo "  被过滤: " . implode(', ', $matches) . "\n";
    } else {
        echo "  ✓ 通过!\n";
    }
    echo "\n";
}
