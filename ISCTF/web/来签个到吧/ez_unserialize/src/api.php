<?php
require_once "./config.php";
require_once "./classes.php";

$id = $_GET["id"] ?? '喵喵喵?';

$s = $db->prepare("SELECT content FROM notes WHERE id = ?");
$s->execute([$id]);
$row = $s->fetch(PDO::FETCH_ASSOC);

if (! $row) {
    die("喵喵喵?");
}

$cfg = unserialize($row["content"]);

if ($cfg instanceof ShitMountant) {
    $r = $cfg->fetch();
    echo "ok!" . "<br>";
    echo nl2br(htmlspecialchars($r));
}
else {
    echo "喵喵喵?";
}
?>
