<?php
$cmd = base64_encode("cat /flag");
$reversed_cmd = strrev($cmd);
$decoded_key = md5($reversed_cmd);
$key = base64_encode($decoded_key);

echo "cmd=$cmd&key=$key";

function decrypt_request($cmd, $key) {
    $decoded_key = base64_decode($key);
    $reversed_cmd = '';
    for ($i = strlen($cmd) - 1; $i >= 0; $i--) {
        $reversed_cmd .= $cmd[$i];
    }
    $hashed_reversed_cmd = md5($reversed_cmd);
    if ($hashed_reversed_cmd !== $decoded_key) {
        die("Invalid key");
    }
    $decrypted_cmd = base64_decode($cmd);
    return $decrypted_cmd;
}

echo "\n";
echo decrypt_request($cmd, $key);