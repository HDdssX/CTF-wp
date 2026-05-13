<?php
// 检查finfo类
if (class_exists('finfo')) {
    echo "finfo class exists!\n";
    $reflection = new ReflectionClass('finfo');

    // 检查open方法
    if ($reflection->hasMethod('open')) {
        echo "finfo has open() method!\n\n";
        $method = $reflection->getMethod('open');
        echo "Method signature:\n";
        $params = $method->getParameters();
        foreach ($params as $param) {
            echo "  - " . $param->getName();
            if ($param->isOptional()) {
                echo " (optional, default: " . var_export($param->getDefaultValue(), true) . ")";
            } else {
                echo " (required)";
            }
            echo "\n";
        }

        // 测试finfo
        echo "\n=== Testing finfo ===\n";
        $finfo = new finfo();
        echo "finfo created without params!\n";

        // 尝试调用open
        // finfo::open(int $flags = FILEINFO_NONE, ?string $magic_database = null)
        try {
            $result = $finfo->open(FILEINFO_MIME_TYPE);
            echo "finfo->open() result: " . var_export($result, true) . "\n";

            // 现在尝试用file方法读取文件信息
            if (method_exists($finfo, 'file')) {
                $file_info = $finfo->file('explore_classes.php');
                echo "File info: " . $file_info . "\n";
            }
        } catch (Exception $e) {
            echo "Error: " . $e->getMessage() . "\n";
        }
    } else {
        echo "finfo does NOT have open() method\n";
    }

    // 列出所有方法
    echo "\nAll public methods:\n";
    foreach ($reflection->getMethods(ReflectionMethod::IS_PUBLIC) as $method) {
        echo "  - " . $method->getName() . "\n";
    }
}
?>