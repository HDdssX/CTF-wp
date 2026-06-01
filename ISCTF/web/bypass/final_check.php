<?php
$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];
$pattern_a = '/' . implode('|', array_map(function ($s) {
    return preg_quote($s, '/'); }, $blocked_a)) . '/i';

// 我需要找一个函数满足：
// 1. 不包含 blocked_a 的字符
// 2. 接受2个参数，第二个参数可以让我们RCE

// 关键insight: 也许我应该用 __destruct 的原始意图不是创建新对象
// 而是直接执行一个PHP的内置功能

echo "======== 核心问题 ========\n";
echo "我们需要: \$a('', \$b) 能够执行命令\n";
echo "其中 \$a 和 \$b 都要通过过滤\n\n";

echo "想法1: \$a 是一个会执行 \$b 作为代码的函数\n";
echo "  -> 没有这样的函数通过了过滤\n\n";

echo "想法2: \$a 是类名 'FLAG'，new FLAG('', \$b) 触发 __construct\n";
echo "  -> 'FLAG' 被过滤了\n\n";

echo "想法3: 利用PHP的某个内置类\n";
echo "  -> 让我检查...\n\n";

// 检查一些可能有用的PHP内置类
$classes = get_declared_classes();
$safe_classes = [];

foreach ($classes as $class) {
    if (!preg_match($pattern_a, $class)) {
        // 检查这个类的构造函数
        try {
            $ref = new ReflectionClass($class);
            if ($ref->isInternal()) {  // 只看内置类
                $constructor = $ref->getConstructor();
                if ($constructor) {
                    $params = $constructor->getParameters();
                    if (count($params) >= 2) {
                        $safe_classes[] = $class;
                    }
                }
            }
        } catch (Exception $e) {
        }
    }
}

echo "可用的内置类 (有2+参数的构造函数):\n";
foreach ($safe_classes as $class) {
    echo "  $class\n";
    try {
        $ref = new ReflectionClass($class);
        $constructor = $ref->getConstructor();
        echo "    构造函数: ";
        foreach ($constructor->getParameters() as $p) {
            echo $p->getName() . ($p->isOptional() ? '?' : '') . ', ';
        }
        echo "\n";
    } catch (Exception $e) {
    }
}

echo "\n\n======== 重新思考 ========\n";
echo "也许我理解错了题目？\n";
echo "让我重新看看 eval(\$a . \$b) 这一行\n";
echo "如果 \$a = '' 并且 \$b = 'var_dump(\`xxd /?l?g\`);'\n";
echo "那么 eval('var_dump(\`xxd /?l?g\`);') 会执行命令并输出\n\n";

echo "问题是：如何触发 __construct？\n";
echo "答案：通过 __destruct 中的 \$a('', \$b)!\n\n";

echo "但是 'FLAG' 被过滤了...\n";
echo "等等！也许我们可以用完全限定的命名空间？\n";
echo "比如 '\\FLAG' 或者 'namespace\\FLAG'？\n\n";

// 测试命名空间变体
$ns_tests = ['\\FLAG', 'FLAG', '\\\\FLAG'];
foreach ($ns_tests as $test) {
    echo "测试 '$test': ";
    if (preg_match($pattern_a, $test)) {
        echo "BLOCKED\n";
    } else {
        echo "OK\n";
    }
}

echo "\n还是不行，都包含 'FLAG'\n\n";

echo "======== 最后的想法 ========\n";
echo "也许题目的答案根本不是通过 __destruct？\n";
echo "也许有其他我没想到的利用方式？\n\n";

echo "或者... 也许 blocked 列表中有什么我理解错的？\n";
echo "让我再看一遍 preg_quote 的行为:\n\n";

$pattern_detail = '/';
foreach ($blocked_a as $item) {
    $quoted = preg_quote($item, '/');
    $pattern_detail .= $quoted;
    if ($item !== end($blocked_a)) {
        $pattern_detail .= '|';
    }
}
$pattern_detail .= '/i';

echo "完整正则: $pattern_detail\n\n";

// 测试边界情况
echo "边界测试:\n";
$边界 = [
    'XFLAG' => '前面加X',
    'FLAGX' => '后面加X',
    'F' => '只有F',
    'fag' => '去掉L',
    'flg' => '去掉A',
];

foreach ($边界 as $test => $desc) {
    $result = preg_match($pattern_a, $test) ? 'BLOCKED' : 'OK';
    echo "  $test ($desc): $result\n";
}
