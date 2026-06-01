
<?php
#flag在/flag中
highlight_file(__FILE__);
error_reporting(1);
$wakeup='asleep';
class phone{
    public $a;
    public function test(){
        global $wakeup;
        if($wakeup!='wakeup'){
            echo('I am sleeping');
        }
        if(!preg_match("/[a-z0-9]+/i", $this->a)){
            eval($this->a);
        }else{
            echo("I am sleeping");
        }
    }
}

class please{
    public $a;
    public function __wakeup(){
        ($this->a)();
    }
    public function __destruct(){
        echo('I am sleeping');
    }
}
class wake{
    public function __call($hs,$cs){
        ($cs[0])[strlen($hs)]();
    }
}
class up{
    public $a;
    public $b;
    public $c;
    public function __call($hs,$cs){
        global $wakeup;
        $this->a=mt_rand();
        if($this->b==$this->a){
            $wakeup=$cs[strlen($hs)-$this->c];
        }
    }
}
class me{
    public $a;
    public $b;
    public $c;
    public $d;
    public function __invoke(){
        $this->a->oh($this->c);

    }
    public function __wakeup(){
        $this->b->ho($this->d);
    }

}

unserialize($_GET['mobile']);