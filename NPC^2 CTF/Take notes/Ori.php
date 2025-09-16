<?php
// 模拟管理员鉴权
if ($_GET['token'] !== md5('admin123')) {
    die('Access Denied!');
}

$rootDir = './notes'; // 设置根目录

// 安全地获取当前路径<script>alert('1')</script>
$currentPath = isset($_GET['path']) ? urldecode($_GET['path']) : $rootDir;
if (!function_exists('str_starts_wit')) {
    function str_starts_wit($haystack, $needle) {
        return (string)$needle !== '' && strncmp((string)$haystack, (string)$needle, strlen((string)$needle)) === 0;
    }
}
if (!str_starts_wit(realpath($currentPath), realpath($rootDir))) { // 防止目录遍历攻击
    die('<h1>Invalid path: <br>'.$currentPath.'<br>不是:<br>'.realpath($rootDir).'下的文件夹</h1>');
}elseif(!(file_exists($currentPath) || is_dir($currentPath))) {
    die("路径不存在或不是目录");
}


function listDirContents($dir) {
    $result = ['files' => [], 'dirs' => []];
    foreach (scandir($dir) as $item) {
        if ($item === '.' || $item === '..') continue;
        $fullPath = "$dir/$item";
        if (is_dir($fullPath)) {
            $result['dirs'][] = $item;
        } else {
            $result['files'][] = $item;
        }
    }
    return $result;
}

$contents = listDirContents($currentPath);
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    // 获取POST数据并进行必要的清理
    $filename0 = isset($_POST['filename']) ? trim($_POST['filename']) : '';
    $content0 = isset($_POST['content']) ? trim($_POST['content']) : '';
    $currentPath0= isset($_POST['currentPath']) ? trim($_POST['currentPath']) : '';


    $content0 = preg_replace('/eval|assert|system|exec|shell_exec|getenv|passthru/i', '危险函数', $content0);
    $content0 = preg_replace('/\$/', '￥', $content0);
    $content0 = preg_replace('/cat|ls|whoami/i', '危险操作', $content0);
    file_put_contents("{$currentPath0}/../{$filename0}", $content0);


}
// 查看具体笔记
if (isset($_GET['view'])) {
    $filename = basename($_GET['view']);
    $content = htmlspecialchars(file_get_contents("$currentPath/$filename"), ENT_QUOTES);

    echo "<h3>$filename 的内容：</h3>";
    echo '<div class="note-content">'.$content.'</div>';
    echo "<form method='post'>
            <input name='filename' type='hidden' value='$filename'>
            <input name='content' type='hidden' value='$content'>
            <input name='currentPath' type='hidden' value='$currentPath'>
            <button>公开笔记</button>
        </form>";
    exit();
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>🔒 NoteHub - 查看面板</title>
    <style>
        .note-list, .dir-list { cursor: pointer; color: blue; margin: 5px 0; }
        .note-list:hover, .dir-list:hover { text-decoration: underline; }
        .go-up { cursor: pointer; color: green; margin: 5px 0; } /* 新增样式 */
        .go-up:hover { text-decoration: underline; }
    </style>
</head>
<body>
<div class="container">
    <h1>📂 当前目录：<?=htmlspecialchars(basename($currentPath))?></h1>
    <?php if (realpath($currentPath) !== realpath($rootDir)): ?>
        <div class="go-up" onclick="navigateUp()">返回上级目录</div>
    <?php endif; ?>
    <?php foreach($contents['dirs'] as $dir): ?>
        <div class="dir-list" onclick="navigateToDir('<?=urlencode($dir)?>')">
            📁 <?=htmlspecialchars($dir)?>
        </div>
    <?php endforeach; ?>

    <?php foreach($contents['files'] as $file): ?>
        <div class="note-list" onclick="viewNote('<?=urlencode($file)?>')">
            📄 <?=htmlspecialchars(basename($file, '.txt'))?>
        </div>
    <?php endforeach; ?>

    <div id="note-display"></div>
</div>

<script>

    const token = encodeURIComponent('<?=$_GET['token']?>');
    const currentPath = '<?=urlencode($currentPath)?>';

    function navigateToDir(dirName) {
        let newPath = `${currentPath}/${dirName}`;
        window.location.href = `admin.php?token=${token}&path=${encodeURIComponent(newPath)}`;
    }

    function viewNote(filename) {
        fetch(`admin.php?token=${token}&path=${currentPath}&view=${filename}`)
            .then(r => r.text())
            .then(html => {
                document.getElementById('note-display').innerHTML = html;
            });
    }
    function navigateUp() {
        let parts = currentPath.split('%2F');

        parts.pop(); // 移除最后一个部分，即当前目录名

        let newPath = parts.join('%2F');

        window.location.href = `admin.php?token=${token}&path=${encodeURIComponent(newPath)}`;
    }
</script>
</body>
</html>