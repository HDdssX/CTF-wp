from flask import Flask, request, render_template, render_template_string
from io import BytesIO
import os
import json
import httpx

app = Flask(__name__)

API_KEY = os.urandom(32).hex()
HOST = '127.0.0.1:5000'

@app.route('/admin', methods=['GET'])
def admin():
    token = request.headers.get("Authorization", "")
    if token != API_KEY:
        return 'unauth', 403

    tmpl = request.values.get('tmpl', 'index.html')
    tmpl_path = os.path.join('./templates', tmpl)

    if not os.path.exists(tmpl_path):
        return 'Not Found', 404

    tmpl_content = open(tmpl_path, 'r').read()
    return render_template_string(tmpl_content), 200

@app.route('/action', methods=['POST'])
def action():
    ip = request.remote_addr
    if ip != '127.0.0.1':
        return 'only localhost', 403

    token = request.headers.get("X-Token", "")
    if token != API_KEY:
        return 'unauth', 403
    
    file = request.files.get('content')
    content = file.stream.read().decode()
    print(f"[+] Content: {content}")
    action = request.files.get("action")
    act = json.loads(action.stream.read().decode())

    if act["type"] == "echo":
        print("[+] Echo Action Triggered")
        return content, 200
    elif act["type"] == "debug":
        print("[+] Debug Action Triggered")
        return content.format(app), 200
    else:
        print("[-] Unknown Action")
        return 'unkown action', 400

@app.route('/heartbeat', methods=['GET', 'POST'])
def heartbeat():
    text = request.values.get('text', "default")
    client = request.values.get('client', "default")
    token = request.values.get('token', "")

    if len(text) > 300:
        return "text too large", 400

    action = json.dumps({"type" : "echo"})

    form_data = {
        'content': ('content', BytesIO(text.encode()), 'text/plain'),
        'action' : ('action', BytesIO(action.encode()), 'text/json')
    }

    headers = {
        "X-Token" : API_KEY,
    }
    headers[client] = token

    response = httpx.post(f"http://{HOST}/action", headers=headers, files=form_data, timeout=10.0)
    if response.status_code == 200:
        return response.text, 200
    else:
        return f'action failed', 500

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)