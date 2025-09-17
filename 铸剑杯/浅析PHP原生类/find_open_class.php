<?php
// 寻找有open方法的PHP原生类

// 已知的类
$classes = [
    'SplFileObject',  // 需要参数构造
    'DirectoryIterator',  // 需要参数构造
    'XMLReader',  // 可以无参构造!
    'ZipArchive',  // 可以无参构造且有open方法!
    'mysqli',  // 可以无参构造
];

foreach ($classes as $class) {
    if (class_exists($class)) {
        echo "\n=== $class ===\n";
        $reflection = new ReflectionClass($class);

        // 检查构造函数
        $constructor = $reflection->getConstructor();
        if ($constructor) {
            $params = $constructor->getParameters();
            $requiredParams = array_filter($params, function ($p) {
                return !$p->isOptional(); });
            echo "Required constructor params: " . count($requiredParams) . "\n";
        } else {
            echo "No constructor\n";
        }

        // 检查是否有open方法
        if ($reflection->hasMethod('open')) {
            echo "Has open() method: YES\n";
            $method = $reflection->getMethod('open');
            $params = $method->getParameters();
            echo "open() parameters: " . count($params) . "\n";
            foreach ($params as $param) {
                echo "  - " . $param->getName() . ($param->isOptional() ? " (optional)" : " (required)") . "\n";
            }
        } else {
            echo "Has open() method: NO\n";
        }
    }
}

// 重点测试 XMLReader
echo "\n\n=== Testing XMLReader ===\n";
if (class_exists('XMLReader')) {
    $xml = new XMLReader();
    echo "XMLReader created without params!\n";
    // XMLReader::open(string $uri, ?string $encoding = null, int $options = 0)
    // 可以用来读取文件!
}

// 重点测试 ZipArchive  
echo "\n=== Testing ZipArchive ===\n";
if (class_exists('ZipArchive')) {
    $zip = new ZipArchive();
    echo "ZipArchive created without params!\n";
    // ZipArchive::open(string $filename, int $flags = 0)
}
?>