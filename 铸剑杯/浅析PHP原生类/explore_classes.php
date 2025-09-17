<?php
// SimpleXMLElement可以用来进行XXE攻击读取文件！
// 构造函数：__construct(string $data, int $options = 0, bool $dataIsURL = false)
// 但问题是write方法是先new再open，SimpleXMLElement没有open方法

// 让我重新思考...也许可以利用Error/Exception类？
// Error::__construct(string $message = "", int $code = 0)
// Exception也类似
// 它们没有open方法

// 或者尝试SoapClient?
// SoapClient可以进行SSRF
// 但它也需要构造函数参数

// 让我尝试另一个思路：
// GlobIterator、FilesystemIterator等迭代器
// 但它们都需要构造参数

// 还有PDO - 但需要构造参数

// 让我尝试SplFileInfo
echo "Checking SplFileInfo...\n";
if (class_exists('SplFileInfo')) {
    $reflection = new ReflectionClass('SplFileInfo');
    echo "Constructor params: " . count($reflection->getConstructor()->getParameters()) . "\n";
    if ($reflection->hasMethod('open')) {
        echo "Has open method!\n";
    } else {
        echo "No open method\n";
    }
}

// 让我尝试finfo
echo "\nChecking finfo...\n";
if (class_exists('finfo')) {
    $reflection = new ReflectionClass('finfo');
    $constructor = $reflection->getConstructor();
    if ($constructor) {
        $params = $constructor->getParameters();
        $required = array_filter($params, function ($p) {
            return !$p->isOptional(); });
        echo "Required constructor params: " . count($required) . "\n";
    }
    if ($reflection->hasMethod('open')) {
        echo "Has open method!\n";
    }
}

// 关键问题：我们需要一个类：
// 1. 可以无参构造
// 2. 有open方法
// 3. open方法被调用后能输出文件内容或者报错泄露信息

// 已知可以用的：XMLReader, ZipArchive
// 但它们不会自动输出内容...

// 等等！也许我们可以通过异常/错误来泄露信息？
// 或者通过destruct时的副作用？

// 让我想想另一个方法 - 也许flag不在文件里，而是在环境变量或者其他地方？
// 或者我们需要触发一个会读取并显示文件的操作？

echo "\n\nLet me think about SimpleXMLElement with XXE...\n";
// SimpleXMLElement构造时可以解析XML
// 如果我们能让它解析一个恶意XML，可能能读取文件
// 但问题是没有open方法...

// 等等！让我查看一下是否有其他read相关的方法
echo "\nChecking XMLReader methods...\n";
if (class_exists('XMLReader')) {
    $reflection = new ReflectionClass('XMLReader');
    $methods = $reflection->getMethods(ReflectionMethod::IS_PUBLIC);
    echo "Public methods:\n";
    foreach ($methods as $method) {
        if (!$method->isStatic() && strpos($method->getName(), '__') !== 0) {
            echo "  - " . $method->getName() . "\n";
        }
    }
}
?>