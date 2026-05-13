<?php
// SimpleXMLElement XXE利用

// SimpleXMLElement构造函数：
// __construct(string $data, int $options = 0, bool $dataIsURL = false, string $namespace_or_prefix = "", bool $is_prefix = false)

// 关键问题：write()方法是先new $cla()再调用open()
// SimpleXMLElement需要构造参数，所以不能直接new
// 但如果它有open方法，也许我们可以...

echo "Checking SimpleXMLElement...\n";
if (class_exists('SimpleXMLElement')) {
    $reflection = new ReflectionClass('SimpleXMLElement');

    // 检查构造函数
    $constructor = $reflection->getConstructor();
    $params = $constructor->getParameters();
    $required = array_filter($params, function ($p) {
        return !$p->isOptional(); });
    echo "Required constructor params: " . count($required) . "\n";

    // 检查open方法
    if ($reflection->hasMethod('open')) {
        echo "Has open() method!\n";
    } else {
        echo "No open() method\n";
    }

    // 列出所有方法
    echo "\nAll methods:\n";
    foreach ($reflection->getMethods(ReflectionMethod::IS_PUBLIC) as $method) {
        if (!$method->isStatic()) {
            echo "  - " . $method->getName() . "\n";
        }
    }
}

echo "\n\n=== 关键发现 ===\n";
echo "我们需要的类必须满足：\n";
echo "1. 可以无参数构造（new \$cla()）\n";
echo "2. 有open(\$file, \$cont)方法\n";
echo "3. open方法调用后能产生可见的副作用（输出、报错、写文件等）\n\n";

echo "已知符合1和2的类：XMLReader, ZipArchive\n";
echo "但它们的open方法只是打开文件，不输出内容\n\n";

echo "=== 新思路 ===\n";
echo "也许flag就藏在报错信息中？\n";
echo "让我们尝试触发一些错误...\n";
?>