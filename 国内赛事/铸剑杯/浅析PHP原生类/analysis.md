# PHP反序列化题目分析

## 源代码分析

### 关键类

1. **install 类**
   - `__wakeup()`: 输出 "Hello," + username
   - `__toString()`: 执行 `($this->username)()`，将username当作函数调用
   - `__destruct()`: 检查install.lock，不存在则创建config.php和install.lock

2. **Until 类**
   - `__invoke()`: 调用 `write($a, $b, $c)`
   - `__toString()`: 返回 "HappyUnserialize"
   - `write($cla, $file, $cont)`: 创建 `$cla` 类的实例，调用其 `open($file, $cont)` 方法

### 入口点
```php
@unserialize($_GET['data']);
```

## 漏洞利用思路

### POP链构造

从 `write()` 方法可以看出，它会实例化一个类并调用其 `open()` 方法。这里可以利用PHP原生类。

常用的PHP原生类：
- **SplFileObject**: 文件操作类，可以用于读写文件
- **SimpleXMLElement**: XML处理类
- **ZipArchive**: ZIP文件操作类

### 利用链

1. **目标**: 读取flag文件或执行命令
2. **可能的链路**:
   - install->__destruct() -> 触发某个对象的__toString()
   - Until->__invoke() -> write() -> 实例化原生类 -> open()

### SplFileObject 利用

SplFileObject 的构造函数就是 open 方法：
```php
$obj = new SplFileObject($file, $cont);
```

这里 `$file` 是文件路径，`$cont` 是打开模式（如 'r', 'w' 等）

### 完整利用链

```
install::__destruct() 
  -> 如果 install.lock 不存在
  -> file_put_contents('config.php', serialize($config))
  -> $config['username'] 触发 __toString()
```

或者：

```
install::__toString()
  -> ($this->username)()
  -> 触发 Until::__invoke()
  -> write($a, $b, $c)
  -> new $cla()->open($file, $cont)
  -> new SplFileObject('/flag', 'r')
```

## 利用方法

### 方案1: 读取文件

构造链：
1. install->username = Until对象
2. Until->a = 'SplFileObject'
3. Until->b = '/flag' (或其他可能的flag路径)
4. Until->c = 'r'

触发: install对象在某处被当作字符串使用，触发__toString()

### 方案2: 写入文件（如果需要）

可以写入webshell或其他恶意代码。

## 注意事项

1. 私有属性序列化需要特殊处理：`\x00类名\x00属性名`
2. flag可能在 `/flag`, `/var/www/html/flag.php` 等位置
3. 需要考虑如何触发反序列化和魔术方法
