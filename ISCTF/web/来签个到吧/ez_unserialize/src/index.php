<?php
require_once "./config.php";
require_once "./classes.php";

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $s = $_POST["shark"] ?? '喵喵喵?';

    if (str_starts_with($s, "blueshark:")) {
        $ss = substr($s, strlen("blueshark:"));

        $o = @unserialize($ss);

        $p = $db->prepare("INSERT INTO notes (content) VALUES (?)");
        $p->execute([$ss]);

        echo "save sucess!";
        exit(0);
    } else {
        echo "喵喵喵?";
        exit(1);
    }
}

$q = $db->query("SELECT id, content FROM notes ORDER BY id DESC LIMIT 10");
$rows = $q->fetchAll(PDO::FETCH_ASSOC);
?>

<!doctype html>
<html>
<head>
    <meta charset="utf-8" />
    <title>宝宝你是一只猫猫</title>
    <style>
        body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; padding: 24px; }
        textarea { width: 100%; max-width: 800px; height: 120px; font-family: monospace; }
        .recent { margin-top: 20px; max-width: 900px; }
        .note { background:#f7f7f8; padding:10px; border-radius:6px; margin-bottom:8px; font-family: monospace; white-space:pre-wrap; }
        .meta { color:#666; font-size:90%; margin-bottom:6px; }
        .btn { padding:8px 14px; border-radius:6px; border:1px solid #ccc; background:#fff; cursor:pointer; }
    </style>
</head>
<body>
<h1>SharkHub</h1>

<form method="POST" style="max-width:900px; margin-bottom:18px;">
    <p>你喜欢小蓝鲨吗？</p>
    <br/>
    <!--
    <textarea id="s" name="shark" placeholder=""></textarea><br/>
    <br/>
    <button class="btn" type="submit">commit</button>
    -->
</form>

<div class="recent">
    <h2>Recent</h2>
    <?php foreach ($rows as $r): ?>
        <div class="note">
            <div class="meta">#<?= htmlspecialchars($r['id'], ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8') ?></div>
            <div><?= htmlspecialchars($r['content'], ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8') ?></div>
        </div>
    <?php endforeach; ?>
</div>
</body>
</html>
