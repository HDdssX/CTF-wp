<?php
$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];

$pattern_a = '/' . implode('|', array_map(function ($s) {
    return preg_quote($s, '/'); }, $blocked_a)) . '/i';

$tests = ['FLAG', 'flag', 'Flag', 'fLaG'];

foreach ($tests as $test) {
    echo "Test '$test': ";
    if (preg_match($pattern_a, $test)) {
        echo "BLOCKED\n";
    } else {
        echo "OK\n";
    }
}
