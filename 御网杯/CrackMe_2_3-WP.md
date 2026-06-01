# CrackMe_2_3 WP

## 题目信息

- 附件：`./CrackMe_2_3/CrackMe_2_3.apk`
- 类型：Android / Native CrackMe
- 最终 flag：`flag{2023326077889096380}`

## 题目分析

这题目录里只有一个 APK，所以思路很直接：先看 APK 里有没有明显的 Java 层校验逻辑，如果没有，就继续盯 native。

对 APK 做字符串检索后，很快能看到几个关键符号：

- `com/cr/crackme2/MainActivity`
- `Java_com_cr_crackme2_MainActivity_stringFromJNI`
- `verifyFlag`
- `lib/x86/libcrackme2.so`

说明题目的核心校验逻辑大概率在 `libcrackme2.so` 里。

### 1. native 层入口

把 APK 解开后，可以直接定位到：

```text
lib/x86/libcrackme2.so
```

继续看导出符号：

```text
Java_com_cr_crackme2_MainActivity_stringFromJNI
verifyFlag(_JNIEnv*, _jclass*, _jstring*)
des_encrypt
des_decrypt
des_ecb_encrypt
des_ecb_decrypt
bytesToHex
JNI_OnLoad
```

这里最值得看的就是 `verifyFlag`。函数名已经很诚实了，基本就是“正确答案在这儿”。

### 2. verifyFlag 的核心逻辑

把 `verifyFlag` 反汇编后，能整理出一条比较清晰的校验链：

1. `GetStringUTFChars()` 取出用户输入
2. 计算输入长度
3. 调用一个辅助函数，把输入补齐到 `8` 字节倍数
4. 使用固定 key 调用 `des_ecb_encrypt`
5. 把结果转成 hex 字符串
6. 和内置的目标字符串比较

从逻辑上看，这题像是在做一层 DES-ECB 校验。

其中补位函数很好认，本质上就是按 `8` 字节分组做 PKCS 风格补位。举个例子，如果明文长度是 `25`，那么会补 `7` 个 `0x07`。

### 3. 关键常量

继续看 `.rodata`，能拿到两个非常关键的字符串。

#### DES key

在 `.rodata` 里可以找到：

```text
12345678
```

也就是校验时使用的 key。

#### 目标 hex 串

还可以找到真正参与比较的目标字符串：

```text
666c61677b323032333332363037373838393039363338307d07070707070707
```

这串东西一眼就有点不对劲，因为前半段非常像 ASCII 的十六进制。

### 4. 直接还原 flag

把上面的 hex 串直接转回字节：

```python
from binascii import unhexlify

data = unhexlify("666c61677b323032333332363037373838393039363338307d07070707070707")
print(data)
```

结果为：

```text
b'flag{2023326077889096380}\x07\x07\x07\x07\x07\x07\x07'
```

去掉末尾 `7` 个 `0x07` padding 后，明文就是：

```text
flag{2023326077889096380}
```

也就是说，这题虽然表面上走了一套 `DES -> hex -> compare` 的流程，但真正拿 flag 并不需要把整套 DES 实现完全啃完。因为比较目标本身已经把补位后的明文暴露出来了。

## 复现脚本

最短恢复脚本如下：

```python
from binascii import unhexlify

hex_data = "666c61677b323032333332363037373838393039363338307d07070707070707"
raw = unhexlify(hex_data)
pad = raw[-1]
flag = raw[:-pad].decode()
print(flag)
```

输出：

```text
flag{2023326077889096380}
```

## 总结

这题的关键不是把 APK 整体跑起来，而是尽快定位真正的校验点：

- APK 中存在 native 库 `libcrackme2.so`
- `verifyFlag` 明确承担校验逻辑
- `.rodata` 里直接藏着目标 hex 串
- 该 hex 串解码后就是补位后的 flag 明文

所以这题的最短路径其实是：

1. 定位 `verifyFlag`
2. 找到内置比较字符串
3. hex 解码
4. 去 padding
5. 拿到 flag

最终 flag：

```text
flag{2023326077889096380}
```
