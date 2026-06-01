<?php
// 测试SplFileObject的行为

// 创建测试文件
file_put_contents('test.txt', "Line 1\nLine 2\nLine 3\n");

// 测试1: SplFileObject的构造函数和open方法
echo "=== Test 1: SplFileObject ===\n";
$file = new SplFileObject('test.txt', 'r');
// 当对象被转换为字符串时
echo "File current line: " . $file->current() . "\n";

// 测试2: SplFileObject遍历
echo "\n=== Test 2: Iterate ===\n";
foreach ($file as $line) {
    echo $line;
}

// 测试3: 研究write方法的行为
echo "\n=== Test 3: Write method simulation ===\n";
function test_write($cla, $file, $cont)
{
    $obj = new $cla();
    $obj->open($file, $cont);
    // SplFileObject在这里已经创建，但是内容如何输出？
    echo "Object created: " . get_class($obj) . "\n";

    // 尝试遍历
    if ($obj instanceof SplFileObject) {
        echo "Reading file:\n";
        while (!$obj->eof()) {
            echo $obj->fgets();
        }
    }
}

test_write('SplFileObject', 'test.txt', 'r');

// 清理
unlink('test.txt');

// 关键问题：write方法在创建SplFileObject后没有返回或输出文件内容
// 但是SplFileObject构造函数会抛出异常如果文件不存在
// 也许错误信息会泄露一些信息？
?>