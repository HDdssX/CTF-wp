# Coordinates

## 结论

- 最终 flag：`flag{6b9393b6318a70a56b19c34ded696b5f}`

## 题目观察

附件只有一个 [secret.pth](/F:/CTF/CTF-wp/红明谷/Coordinates/secret.pth)。

先看文件头：

```text
50 4B 03 04
```

说明它其实是一个 zip 格式的 PyTorch 权重文件，不是普通图片或压缩包伪装题。

继续看 `data.pkl` 里的参数名，可以确认它外壳上是一个标准 `ResNet50` 的 `state_dict`，但是真正的数据都塞在 `secret/data/0` 里。

## 关键异常

直接统计 `secret/data/0` 里的 4 字节浮点，可以发现一个值重复得非常离谱：

```text
0.5201314091682434
```

对应原始 4 字节是：

```text
55 27 05 3f
```

把这个值在整个浮点流中的位置取出来，能看到一个很明显的规律：

- 前面的大部分出现位置都落在 `600, 700, 1000, 1100, ...`
- 也就是都在 `100` 的整数倍槽位上
- 主要集中在前 `30800` 个浮点内
- 后面只有两个零散噪声点，可以忽略

这说明它不是随机重复，而是在用“是否出现该特殊值”编码二进制。

## 提取思路

做法很直接：

1. 读取 `secret/data/0`，按 `float32` 拆分。
2. 找出所有等于 `0.5201314091682434` 的位置。
3. 只取前一段有效区域，把位置除以 `100`，得到 bit 槽编号。
4. 从槽位 `5` 开始取，到槽位 `308` 结束。
5. 某个槽位出现特殊值记为 `1`，否则记为 `0`。
6. 按 `MSB-first` 每 `8` 位打包成一个字节，直接得到 ASCII 文本。

这里前 `5` 位是对齐噪声，丢掉后就能直接对齐出 `flag{`。

## 复现脚本

```python
import zipfile
import struct

zf = zipfile.ZipFile("secret.pth")
raw = zf.read("secret/data/0")

target = 0.5201314091682434
positions = []

for i in range(0, len(raw), 4):
    v = struct.unpack("<f", raw[i:i+4])[0]
    if v == target:
        positions.append(i // 4)

# 主要有效区域都在前面，后面两个是噪声点
slots = {p // 100 for p in positions if p < 100000}

bits = [1 if i in slots else 0 for i in range(5, 309)]

out = bytearray()
for i in range(0, len(bits), 8):
    b = 0
    for bit in bits[i:i+8]:
        b = (b << 1) | bit
    out.append(b)

print(out.decode())
```

输出：

```text
flag{6b9393b6318a70a56b19c34ded696b5f}
```

## Flag

```text
flag{6b9393b6318a70a56b19c34ded696b5f}
```
