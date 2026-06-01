# 损坏的压缩包

## 题目信息

- 分类：Misc
- 题目提示：提交形式为 `flag{*****}`

## 解题过程

先检查原始文件 [压缩包.zip](C:/Users/29703/Downloads/压缩包.zip)。

观察压缩包结构可以发现，它实际上并没有真的损坏，压缩包内只有一个文件：

```text
data.txt
```

提取后得到 `data.txt`，内容为：

```text
bmR0Zw==
```

这个字符串一眼可以看出是 Base64。对其进行解码：

```text
bmR0Zw== -> ndtg
```

结合题目要求的提交格式，最终得到 flag：

```text
flag{ndtg}
```

## 最终答案

`flag{ndtg}`
