# CTF Writeup - PHP原生类反序列化题目

## 题目信息
- **URL**: http://f7c8a2a3.clsadp.com/
- **题目描述**: 金融科技公司的日志聚合微服务使用unserialize处理序列化数据
- **关键词**: PHP反序列化、PHP原生类

## 源代码分析

### 可用类
1. **install** 类
   - `__wakeup()`: echo "Hello,".$this->username;
   - `__toString()`: ($this->username)(); return "Guest";
   - `__destruct()`: 检查install.lock，不存在则写入config.php

2. **Until** 类
   - `__invoke()`: $this->write($this->a, $this->b, $this->c);
   - `__toString()`: return "HappyUnserialize";
   - `write($cla, $file, $cont)`: **关键方法**
     ```php
     $obj = new $cla();
     $obj->open($file, $cont);
     ```

### 入口点
```php
@unserialize($_GET['data']);
```

## 利用思路

### POP链构造
```
外层install->__wakeup()
→ echo触发内层install->__toString()
→ 内层install->__toString()调用Until->__invoke()
→ Until->write($a, $b, $c)
→ new $a()->open($b, $c)
```

### 可用的PHP原生类
经过测试，找到以下可用原生类（无参构造 + 有open方法）：
1. **XMLReader**
   - `XMLReader::open(string $uri, ?string $encoding = null, int $options = 0)`
   - 可以打开文件，但不自动输出内容

2. **ZipArchive**
   - `ZipArchive::open(string $filename, int $flags = 0)`
   - 可以打开ZIP文件，但不自动输出内容

## 已尝试的方法

### 1. 基础利用链
```php
$until = new Until('XMLReader', '/flag', null);
$inner_install = new install($until, 'pass2');
$outer_install = new install($inner_install, 'pass1');
```
**结果**: 触发了`__wakeup`，输出"Hello,HappyUnserializeHello,GuestAlready installed"

### 2. 绕过__wakeup
通过修改序列化字符串中的属性数量来绕过__wakeup：
- 将`O:7:"install":2:`改为`O:7:"install":3:`

**结果**: 成功绕过__wakeup，响应中不再有"Hello,"等输出

### 3. 尝试多种文件路径
- /flag
- flag
- flag.php
- /var/www/html/flag
- /tmp/flag
- ../flag等

**结果**: 所有测试返回相同长度的响应(7418字节)，无明显差异

## 当前困境

### 核心问题
1. XMLReader和ZipArchive的`open()`方法只打开文件，不会自动输出内容
2. `write()`方法在调用`open()`后就返回了，没有后续操作
3. install.lock文件已存在，导致`__destruct`提前退出

### 缺失的环节
需要找到一个方法能够：
- 在`open()`调用后读取并输出文件内容
- 或者通过错误信息泄露flag
- 或者通过某种副作用让flag可见

## 下一步思路

### 可能的方向
1. **Error-based**: 触发包含文件内容的错误信息
2. **盲注技术**: 通过响应的细微差异判断文件内容
3. **其他PHP原生类**: 继续寻找更合适的原生类
4. **XXE攻击**: 如果有XML处理相关的方法
5. **重新审视题目**: 是否遗漏了重要信息

### 待测试
- [ ] 检查XMLReader打开文件后的对象状态
- [ ] 尝试触发XMLReader/ZipArchive的错误
- [ ] 搜索其他可能的PHP原生类
- [ ] 尝试SSRF或其他攻击向量
- [ ] 检查是否有其他可访问的端点

## 技术细节

### PHP原生类特点
1. **无参构造的类**: XMLReader, ZipArchive, finfo等
2. **有open方法的类**: XMLReader, ZipArchive
3. **绕过__wakeup**: 修改序列化字符串中的属性数量

### 序列化格式
```
O:类名长度:"类名":属性数量:{属性定义}
s:长度:"字符串"
i:整数
N = NULL
```

### 私有属性序列化
```
s:17:"\x00类名\x00属性名"
```

## 总结
目前已成功构造POP链并绕过__wakeup，但卡在如何从XMLReader/ZipArchive获取文件内容的问题上。需要重新思考利用方式或寻找新的突破点。
