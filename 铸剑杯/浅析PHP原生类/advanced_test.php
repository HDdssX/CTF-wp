<?php
// 寻找可能执行命令或有其他副作用的原生类

// 1. SplFileObject - 虽然需要构造参数，但让我看看是否有其他方法
echo "=== SplFileObject ===\n";
if (class_exists('SplFileObject')) {
    $reflection = new ReflectionClass('SplFileObject');
    $methods = $reflection->getMethods(ReflectionMethod::IS_PUBLIC);
    echo "Public methods:\n";
    foreach ($methods as $method) {
        if (!$method->isStatic() && $method->getName()[0] != '_') {
            echo "  - " . $method->getName() . "\n";
        }
    }
}

//  2. Error/Exception - 看看构造时是否能leak信息
echo "\n=== Error/Exception ===\n";
if (class_exists('Error')) {
    $reflection = new ReflectionClass('Error');
    if ($reflection->hasMethod('open')) {
        echo "Error has open method!\n";
    }
}

// 3. 让我想想XMLReader读取文件后的状态
echo "\n=== Testing XMLReader behavior ===\n";
$xml = new XMLReader();
echo "Created XMLReader\n";

// 创建测试文件
file_put_contents('test.xml', '<root><data>test content</data></root>');
$result = $xml->open('test.xml');
echo "Open result: " . var_export($result, true) . "\n";

// XMLReader对象的状态
echo "XMLReader properties:\n";
$reflection = new ReflectionClass('XMLReader');
$props = $reflection->getProperties();
echo "Properties count: " . count($props) . "\n";

// 尝试读取
if ($xml->read()) {
    echo "Read success!\n";
    echo "Node type: " . $xml->nodeType . "\n";
    echo "Name: " . $xml->name . "\n";
}

unlink('test.xml');

// 4. 关键问题：open()后对象的__toString会返回什么？
echo "\n=== Testing __toString ===\n";
$xml2 = new XMLReader();
file_put_contents('test2.xml', '<root>FLAG_TEST_123</root>');
$xml2->open('test2.xml');

try {
    $str = (string) $xml2;
    echo "XMLReader as string: " . $str . "\n";
} catch (Exception $e) {
    echo "Error converting to string: " . $e->getMessage() . "\n";
}

unlink('test2.xml');

// 5. 也许我们应该寻找在析构时会输出内容的类？
echo "\n=== Thinking about __destruct ===\n";
echo "Maybe some class outputs content in __destruct?\n";
echo "Or leaks information when serialized?\n";

//  6. PHP Wrapper?
echo "\n=== PHP Wrappers ===\n";
echo "Can we use php://filter to read files?\n";
$xml3 = new XMLReader();
try {
    // 尝试使用PHP filter wrapper
    $result = $xml3->open('php://filter/read=convert.base64-encode/resource=explore_classes.php');
    echo "Opened with php://filter: " . var_export($result, true) . "\n";
    if ($xml3->read()) {
        echo "Content: " . $xml3->readString() . "\n";
    }
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>