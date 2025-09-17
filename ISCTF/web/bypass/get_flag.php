<?php
$url = trim(file_get_contents('correct_url.txt'));

echo "正在访问: $url\n\n";

$ctx = stream_context_create(['http' => ['timeout' => 10]]);
$response = @file_get_contents($url, false, $ctx);

if ($response === false) {
    echo "请求失败\n";
} else {
    echo "响应:\n";
    echo $response . "\n\n";

    // 查找 flag
    if (preg_match('/ISCTF\{[^}]+\}/', $response, $matches)) {
        echo "\n========= FLAG =========\n";
        echo $matches[0] . "\n";
        echo "========================\n";
    } else {
        echo "未找到 flag 格式，查看完整响应...\n";
    }
}
