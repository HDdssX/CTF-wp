# 幻影 WP

## 题目类型

Misc / 文件分析 / 简单编码还原

## 题目内容

题目描述提到：

- 一共截获了 10 个看似相同的加密文件
- 它们使用了相同的隐藏手法
- 每个文件内容略有差异
- 需要从每个文件中提取真正的 flag

这类描述通常意味着需要先找出统一的隐藏规则，再批量处理所有文件。

## 初步分析

拿到样本后，目录中实际看到的是一个 `data.bin` 文件。  
对文件做十六进制查看，可以直接发现里面混有可读字符串：

```text
REMEMBER: FLAG IS HIDDEN IN BASE64 PLUS XOR!
FAKE FLAG: flag{00000000-0000-0000-0000-000000000000}
DO NOT TRUST THIS ONE.
GBIfGQVPR0tLTh8dHFMdSxhOU0ocSRpTHEZNTFNJS0ZHThpHSRpIHBsD
```

这里已经把思路提示得很明显了：

1. 文件里给了一个假的 flag
2. 真正的 flag 隐藏在一段 Base64 字符串里
3. Base64 解码后还要再经过 XOR 还原

## 解题思路

先提取最后那段可疑字符串：

```text
GBIfGQVPR0tLTh8dHFMdSxhOU0ocSRpTHEZNTFNJS0ZHThpHSRpIHBsD
```

对其进行 Base64 解码，得到一串不可读字节。  
接着对结果爆破单字节 XOR，筛选出包含 `flag{}` 结构的明文即可。

爆破后得到：

```text
flag{19550acb-c5f0-4b7d-b832-75890d97d6be}
```

对应的 XOR key 为：

```text
0x7e
```

## 自动化脚本

由于题目说一共有 10 个同类文件，因此最合适的做法是直接写批量脚本。  
当前目录下的 `solve.py` 会：

- 扫描目录中的 `.bin` / `.dat` / `.txt` 文件
- 提取其中可能的 Base64 长串
- 先 Base64 解码
- 再爆破 0-255 的单字节 XOR
- 自动寻找符合 `flag{...}` 格式的结果

运行方式：

```powershell
& 'C:\Users\29703\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\solve.py
```

如果后续把 10 个文件都放进同一目录，脚本会逐个输出结果。

## 样本结果

对当前样本 `data.bin` 提取出的真实 flag 为：

```text
flag{19550acb-c5f0-4b7d-b832-75890d97d6be}
```

## 总结

这题本质上不是复杂隐写，而是一个“伪装 + 编码提示”的批量还原题：

- 文件头伪装成了看起来像压缩文件的数据
- 中间故意塞了假的 flag 干扰分析
- 真正内容是 `Base64 + 单字节 XOR`

一旦从第一个样本里总结出规则，其余 9 个文件都可以同法秒出。
