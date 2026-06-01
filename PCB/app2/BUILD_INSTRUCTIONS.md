# 应用程序打包说明

## 构建项目

运行 `build.bat` 来构建可执行的JAR包：

```bash
build.bat
```

这将会：
1. 下载必要的Tomcat嵌入式依赖
2. 复制所有依赖库到 `dist/lib/`
3. 编译Java源代码
4. 创建可执行的JAR包 `dist/app.jar`

## 运行应用

### 方式1：使用启动脚本（推荐）

```bash
start.bat [端口号]
```

示例：
```bash
start.bat          # 使用默认端口8080
start.bat 9090     # 使用自定义端口9090
```

### 方式2：直接运行JAR

```bash
java -jar dist/app.jar [端口号]
```

示例：
```bash
java -jar dist/app.jar          # 使用默认端口8080
java -jar dist/app.jar 9090     # 使用自定义端口9090
```

## 输出文件

构建完成后，会在 `dist` 目录下生成以下文件：

```
dist/
├── app.jar                           # 主应用程序JAR
└── lib/                              # 依赖库目录
    ├── tomcat-embed-core-9.0.80.jar
    ├── tomcat-annotations-api-9.0.80.jar
    ├── jackson-databind-2.12.6.1.jar
    ├── jackson-core-2.12.6.jar
    ├── jackson-annotations-2.12.6.jar
    ├── jjwt-api-0.11.5.jar
    ├── jjwt-impl-0.11.5.jar
    ├── jjwt-jackson-0.11.5.jar
    ├── json-20240303.jar
    └── tar-1.0.jar
```

## 注意事项

1. **Java版本**：需要Java 17或更高版本
2. **端口占用**：确保所选端口未被其他程序占用
3. **部署**：将整个 `dist` 目录复制到目标服务器即可运行
4. **访问应用**：启动后在浏览器访问 `http://localhost:8080`（或您指定的端口）

## 常见问题

### Q: 如何重新构建？
A: 直接运行 `build.bat` 即可，会自动清理并重新构建

### Q: 启动失败？
A: 检查：
   - Java是否正确安装（java -version）
   - 端口是否被占用
   - dist/lib/ 目录下的依赖是否完整

### Q: 如何在Linux/Mac上运行？
A: 使用命令：`java -jar dist/app.jar [port]`
