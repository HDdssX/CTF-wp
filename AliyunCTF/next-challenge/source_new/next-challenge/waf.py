#!/usr/bin/env python3
"""
Next-WAF 下一代应用防火墙
"""

from flask import Flask, request, Response
import requests
import json

app = Flask(__name__)

BACKEND_URL = "http://127.0.0.1:3000"

# 允许的 headers（小写）
ALLOWED_HEADERS = {
    "host",
    "user-agent",
    "accept",
    "accept-language",
    "accept-encoding",
    "cookie",
    "connection",
    "cache-control",
    "pragma",
    "next-action",
}

# 禁止的关键字（小写）
FORBIDDEN_KEYWORDS = ["__proto__", "constructor", "prototype", "\\u"]


def check_forbidden(value):
    """
    递归检查值是否包含禁止的关键字
    对所有 string 类型进行检查，不区分大小写
    如果字符串是合法的 JSON，则解析并递归检查
    """
    if isinstance(value, str):
        lower_value = value.lower()
        for keyword in FORBIDDEN_KEYWORDS:
            if keyword in lower_value:
                return False
        # 尝试解析为 JSON，如果成功则递归检查
        try:
            parsed = json.loads(value.strip())
            # 只有当解析结果是 dict 或 list 时才递归检查
            if isinstance(parsed, (dict, list, str)):
                if not check_forbidden(parsed):
                    return False
        except (json.JSONDecodeError, TypeError):
            # 不是有效的 JSON，已经通过了字符串检查，放行
            pass
        return True
    elif isinstance(value, dict):
        for k, v in value.items():
            # 检查 key（如果是字符串）
            if isinstance(k, str):
                lower_k = k.lower()
                for keyword in FORBIDDEN_KEYWORDS:
                    if keyword in lower_k:
                        return False
            # 递归检查 value
            if not check_forbidden(v):
                return False
        return True
    elif isinstance(value, list):
        for item in value:
            if not check_forbidden(item):
                return False
        return True
    else:
        # 其他类型（int, float, bool, None）直接放行
        return True


def filter_headers(headers):
    """过滤 headers，只保留允许的"""
    filtered = {}
    for key, value in headers.items():
        if key.lower() in ALLOWED_HEADERS:
            # 不转发 host，让 requests 自己设置
            if key.lower() != "host":
                filtered[key] = value
    return filtered


@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def proxy(path):
    # 过滤 headers
    headers = filter_headers(request.headers)

    # 构建目标 URL
    url = f"{BACKEND_URL}/{path}"
    # if request.query_string:
    #     url += f"?{request.query_string.decode()}"

    try:
        if request.method == "GET":
            resp = requests.get(url, headers=headers, timeout=30)

        elif request.method == "POST":
            content_type = request.content_type or ""
            if "multipart/form-data" in content_type:
                # 准备表单字段
                files = {}
                for key in request.form:
                    if not check_forbidden(key):
                        return Response("Forbidden", status=403)
                    for value in request.form.getlist(key):
                        try:
                            data = json.loads(value)
                            if not check_forbidden(data):
                                return Response("Forbidden", status=403)
                            files[key] = (None, json.dumps(data))
                        except Exception:
                            return Response("Forbidden", status=403)

                # 发送 multipart 请求
                resp = requests.post(url, headers=headers, files=files, timeout=30)

            elif "text/plain" in content_type:
                # Text/plain - 尝试解析为 JSON 并验证
                body = request.get_data(as_text=True)
                try:
                    parsed = json.loads(body)
                    if not check_forbidden(parsed):
                        return Response("Forbidden", status=403)
                except Exception:
                    # 不是有效的 JSON，拒绝
                    return Response("Invalid JSON", status=400)

                # 转发原始请求体
                headers["Content-Type"] = "text/plain"
                resp = requests.post(url, headers=headers, data=body, timeout=30)

            else:
                return Response("Unsupported Content-Type", status=400)
        else:
            return Response("Method Not Allowed", status=405)

    except requests.exceptions.RequestException as e:
        return Response(f"Backend Error: {str(e)}", status=502)

    # 构建响应，排除某些 hop-by-hop headers
    excluded_headers = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    response_headers = [(name, value) for name, value in resp.headers.items() if name.lower() not in excluded_headers]

    return Response(resp.content, resp.status_code, response_headers)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
