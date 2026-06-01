<?php
header('Content-Type: application/json');

$response = [
    "status" => "online",
    "version" => "1.0.4",
    "payment_gateway" => "OK"
];

echo json_encode($response, JSON_PRETTY_PRINT);
?>
