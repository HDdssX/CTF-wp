# 迷宫 WP

## 题目类型

Misc / 多层压缩包还原

## 题目分析

题目提示说明：

- 攻击者将关键凭证以“迷宫”形式隐藏在多个压缩包中
- 需要逐层解压
- 提取最内层数据后还原原始凭证

拿到附件后，先从 `layer1/data2.zip` 开始查看。

第一层 ZIP 中包含：

```text
secret3/hidden4.zip
```

继续解压 `hidden4.zip`，可以得到：

```text
.config/user/backup5/vault.bin
```

这说明题目的“迷宫”主要体现在层层嵌套的路径和压缩包中，核心数据最终落在 `vault.bin`。

## 最内层数据分析

查看 `vault.bin` 内容：

```text
Mjg3NzEwOTg0ZjAwNmEwNGQ5YmYzMTUwZDkwNGI0YmE=67
```

可以发现：

- 前半部分很像 Base64
- 最后的 `67` 更像干扰字符

将可解码的 Base64 部分：

```text
Mjg3NzEwOTg0ZjAwNmEwNGQ5YmYzMTUwZDkwNGI0YmE=
```

进行 Base64 解码，得到：

```text
287710984f006a04d9bf3150d904b4ba
```

这是一个 32 位十六进制字符串，也就是题目中隐藏的“原始凭证”。

## 最终 Flag

按题目要求包装为 flag 格式：

```text
flag{287710984f006a04d9bf3150d904b4ba}
```

## 复现过程

### 1. 查看第一层压缩包

```powershell
tar -tf .\layer1\data2.zip
```

输出可见内部还有 `secret3/hidden4.zip`。

### 2. 继续解压第二层

解压后得到：

```text
.config/user/backup5/vault.bin
```

### 3. 读取最内层文件

```powershell
Get-Content .\vault.bin
```

得到：

```text
Mjg3NzEwOTg0ZjAwNmEwNGQ5YmYzMTUwZDkwNGI0YmE=67
```

### 4. Base64 解码

将前面的 Base64 字符串解码即可还原真实凭证。

## 总结

这题本身不复杂，关键点在于：

- 不要被多层目录和压缩包绕晕
- 一层层解到最内层即可
- 最终数据并不是复杂加密，而是简单的 Base64 包装

所以这题的核心是文件递归解包和对最终落点文件的格式识别。
