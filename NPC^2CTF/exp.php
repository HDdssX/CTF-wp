<?php

class A
{
    public $a;
    public $b;
    function __construct(){
        $this->a = &$this->b;
    }
}
echo serialize(new A());