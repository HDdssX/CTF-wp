<?php
session_start();
include 'config.php';
header('Content-Type: application/json');

if (!isset($_SESSION['user_id'])) {
    die(json_encode(["error" => "Authentication required"]));
}

$item = $_POST['item'] ?? '';

if ($item === '') {
    die(json_encode(["error" => "Missing item parameter"]));
}

$items = [
    'basic_vip' => 10,
    'premium_vip' => 50,
    'flag' => 99999
];

if (!array_key_exists($item, $items)) {
    die(json_encode(["error" => "Invalid item."]));
}

$price = $items[$item];

if ($_SESSION['balance'] < $price) {
    die(json_encode(["error" => "Insufficient funds! You only have " . intval($_SESSION['balance']) . " 金币."]));
}

$_SESSION['balance'] -= $price;

if ($item === 'flag') {
    $flag = "flag{da91f6ee9d5cceef4705fd4f8af9e3f3}";
    if (file_exists('/var/www/flag.php')) {
        include '/var/www/flag.php';
        if (isset($FLAG)) $flag = $FLAG;
    }
    echo json_encode(["success" => true, "message" => "购买 successful! Your Flag is [ " . $flag . " ]", "balance" => $_SESSION['balance']]);
} else {
    echo json_encode(["success" => true, "message" => "购买 successful! Enjoy your " . htmlspecialchars($item) . ".", "balance" => $_SESSION['balance']]);
}
?>
