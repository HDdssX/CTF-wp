<?php
class FLAG
{
    private $a;
    protected $b;
    public function __construct($a, $b)
    {
        $this->a = $a;
        $this->b = $b;
        $this->check($a, $b);
        eval ($a . $b);
    }
    public function __destruct()
    {
        $a = (string) $this->a;
        $b = (string) $this->b;
        if ($this->check($a, $b)) {
            $a("", $b);
        } else {
            echo "Try again!";
        }
    }
    private function check($a, $b)
    {
        $blocked_a = ['eval', 'dl', 'ls', 'p', 'escape', 'er', 'str', 'cat', 'flag', 'file', 'ay', 'or', 'ftp', 'dict', '\.\.', 'h', 'w', 'exec', 's', 'open'];
        $blocked_b = ['find', 'filter', 'c', 'pa', 'proc', 'dir', 'regexp', 'n', 'alter', 'load', 'grep', 'o', 'file', 't', 'w', 'insert', 'sort', 'h', 'sy', '\.\.', 'array', 'sh', 'touch', 'e', 'php', 'f'];

        $pattern_a = '/' . implode('|', array_map('preg_quote', $blocked_a, ['/'])) . '/i';
        $pattern_b = '/' . implode('|', array_map('preg_quote', $blocked_b, ['/'])) . '/i';

        if (preg_match($pattern_a, $a) || preg_match($pattern_b, $b)) {
            return false;
        }
        return true;
    }
}


if (isset($_GET['exp'])) {
    $p = unserialize($_GET['exp']);
    var_dump($p);
} else {
    highlight_file("index.php");
}