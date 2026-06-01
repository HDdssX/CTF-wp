<?php
session_start();
include '../config.php';
include '../models.php';
header('Content-Type: application/json');

if (!isset($_SESSION['user_id'])) {
    die(json_encode(["error" => "Authentication required"]));
}

$couponData = $_POST['coupon'] ?? '';

if ($couponData === '') {
    die(json_encode(["error" => "Empty coupon code"]));
}

$decoded = base64_decode($couponData);
if ($decoded === false) {
    die(json_encode(["error" => "Invalid coupon format. Must be base64."]));
}

try {
    $promo = @unserialize($decoded);
    if ($promo === false) {
        die(json_encode(["error" => "Failed to apply coupon."]));
    }
} catch (Exception $e) {
    die(json_encode(["error" => "Coupon parsing error."]));
}

echo json_encode(["success" => true, "message" => "Coupon processed."]);
?>
