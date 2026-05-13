<?php

error_reporting(0);
highlight_file(__FILE__);

class A {
    public $first;
    public $step;
    public $next;

    public function __construct() {
        $this->first = "继续加油！";
    }

    public function start() {
        echo $this->next;
    }
}

class E {
    private $you;
    public $found;
    private $secret = "admin123";

    public function __get($name){
        if($name === "secret") {
            echo "<br>".$name." maybe is here!</br>";
            $this->found->check();
        }
    }
}

class F {
    public $fifth;
    public $step;
    public $finalstep;

    public function check() {
        if(preg_match("/U/",$this->finalstep)) {
            echo "仔细想想！";
        }
        else {
            $this->step = new $this->finalstep();
            ($this->step)();
        }
    }
}

class H {
    public $who;
    public $are;
    public $you;

    public function __construct() {
        $this->you = "nobody";
    }

    public function __destruct() {
        $this->who->start();
    }
}

class N {
    public $congratulation;
    public $yougotit;

    public function __call(string $func_name, array $args) {
        return call_user_func($func_name,$args[0]);
    }
}

class U {
    public $almost;
    public $there;
    public $cmd;

    public function __construct() {
        $this->there = new N();
        $this->cmd = $_POST['cmd'];
    }

    public function __invoke() {
        return $this->there->system($this->cmd);
    }
}

class V {
    public $good;
    public $keep;
    public $dowhat;
    public $go;

    public function __toString() {
        $abc = $this->dowhat;
        $this->go->$abc;
        return "<br>Win!!!</br>";
    }
}

unserialize($_POST['payload']);

?>