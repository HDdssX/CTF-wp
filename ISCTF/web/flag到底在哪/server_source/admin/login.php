<?php
session_start();

// 如果已经登录，直接跳转到 upload.php
if (isset($_SESSION['loggedin']) && $_SESSION['loggedin'] === true) {
    header("Location: upload.php");
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';

    if ($username === 'admin' && strpos($password, "' OR '1'='1") !== false) {
        $_SESSION['loggedin'] = true;
        header("Location: /upload.php");
        exit;
    } else {
        $error = "❌ 用户名或密码错误";
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>🔐 Admin Login</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #f0f2f5;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
    }
    .login-box {
      background: white;
      padding: 40px;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      width: 320px;
      text-align: center;
    }
    h2 {
      margin-bottom: 30px;
      color: #333;
    }
    input[type="text"], input[type="password"] {
      width: 100%;
      padding: 12px;
      margin: 8px 0;
      border: 1px solid #ccc;
      border-radius: 4px;
      box-sizing: border-box;
    }
    input[type="submit"] {
      width: 100%;
      padding: 12px;
      background: #007bff;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 16px;
    }
    input[type="submit"]:hover {
      background: #0056b3;
    }
    .hint {
      margin-top: 15px;
      font-size: 12px;
      color: #666;
    }
    .error {
      color: red;
      margin-bottom: 15px;
    }
  </style>
</head>
<body>
  <div class="login-box">
    <h2>🔒 Admin Panel</h2>
    <?php if (isset($error)): ?>
      <div class="error"><?php echo htmlspecialchars($error); ?></div>
    <?php endif; ?>
    <form method="POST">
      <input type="text" name="username" placeholder="Username" value="" required />
      <input type="password" name="password" placeholder="Password" required />
      <input type="submit" value="🚀 Login" />
    </form>
    <div class="hint">
      💡 Hint: Try username <code>admin</code>
    </div>
  </div>
</body>
</html>
