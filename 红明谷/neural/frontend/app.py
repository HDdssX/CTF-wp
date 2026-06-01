"""
NeuralChat Frontend - Flask web application for NeuralChat LLM service.
Proxies requests to the C backend engine via Unix socket.
"""

import os
import sys
import json
import struct
import socket
import base64
import time
from flask import Flask, request, jsonify, send_file, render_template, abort

app = Flask(__name__)


ENGINE_SOCKET = "/opt/neuralchat/run/engine.sock"
DOWNLOAD_DIR  = "/opt/neuralchat/downloads"
KNOWLEDGE_DIR = "/opt/neuralchat/data/knowledge"

CMD_NEW_SESSION   = 0x01
CMD_CHAT          = 0x02
CMD_LIST_SESSIONS = 0x03
CMD_EXPORT        = 0x04
CMD_IMPORT        = 0x05
CMD_UPLOAD_KNOW   = 0x06
CMD_LIST_KNOW     = 0x07
CMD_MODEL_INFO    = 0x08
CMD_STATUS        = 0x09
CMD_ADMIN         = 0xFF


def send_to_engine(command, payload=b''):
    """Send a command to the C backend engine via Unix socket."""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(ENGINE_SOCKET)

        total_len = 5 + len(payload)
        msg = struct.pack('<I', total_len) + bytes([command]) + payload
        sock.sendall(msg)

        header = b''
        while len(header) < 4:
            chunk = sock.recv(4 - len(header))
            if not chunk:
                break
            header += chunk

        if len(header) < 4:
            sock.close()
            return None, "Connection error"

        resp_len = struct.unpack('<I', header)[0]
        body = b''
        remaining = resp_len - 4
        while len(body) < remaining:
            chunk = sock.recv(remaining - len(body))
            if not chunk:
                break
            body += chunk

        sock.close()

        if len(body) < 1:
            return None, "Empty response"

        status = body[0]
        data = body[1:]
        return status, data

    except Exception as e:
        return None, str(e)



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Get engine status - exposes PID for monitoring."""
    status, data = send_to_engine(CMD_STATUS)
    if status == 0x00:
        return jsonify(json.loads(data.decode('utf-8', errors='replace')))
    return jsonify({"error": "Engine unavailable"}), 503


@app.route('/api/session/new', methods=['POST'])
def new_session():
    status, data = send_to_engine(CMD_NEW_SESSION)
    if status == 0x00 and len(data) >= 4:
        sid = struct.unpack('<I', data[:4])[0]
        return jsonify({"session_id": sid})
    return jsonify({"error": "Failed to create session"}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    body = request.get_json()
    if not body or 'session_id' not in body or 'message' not in body:
        return jsonify({"error": "Missing session_id or message"}), 400

    sid = int(body['session_id'])
    msg = body['message'].encode('utf-8')

    payload = struct.pack('<I', sid) + msg
    status, data = send_to_engine(CMD_CHAT, payload)

    if status == 0x00:
        return jsonify({"response": data.decode('utf-8', errors='replace')})
    return jsonify({"error": data.decode('utf-8', errors='replace')}), 400


@app.route('/api/sessions')
def list_sessions():
    status, data = send_to_engine(CMD_LIST_SESSIONS)
    if status == 0x00:
        return jsonify(json.loads(data.decode('utf-8', errors='replace')))
    return jsonify([])


@app.route('/api/export', methods=['POST'])
def export_session():
    body = request.get_json()
    if not body or 'session_id' not in body:
        return jsonify({"error": "Missing session_id"}), 400

    sid = int(body['session_id'])
    payload = struct.pack('<I', sid)
    status, data = send_to_engine(CMD_EXPORT, payload)

    if status == 0x00:
        filename = data.decode('utf-8', errors='replace')
        return jsonify({"download_url": f"/api/download?file={filename}"})
    return jsonify({"error": "Export failed"}), 500


@app.route('/api/download')
def download_file():
    filename = request.args.get('file', '')
    if not filename:
        return "Missing file parameter", 400

    filepath = os.path.join(DOWNLOAD_DIR, filename)

    if not filepath.startswith(DOWNLOAD_DIR):
        return "Access denied", 403

    if not os.path.exists(filepath):
        return "File not found", 404

    return send_file(filepath)


@app.route('/api/knowledge/upload', methods=['POST'])
def upload_knowledge():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files['file']
    filename = f.filename
    content = f.read()

    name_bytes = filename.encode('utf-8')
    payload = struct.pack('<H', len(name_bytes)) + name_bytes
    payload += struct.pack('<I', len(content)) + content

    status, data = send_to_engine(CMD_UPLOAD_KNOW, payload)
    if status == 0x00:
        path = data.decode('utf-8', errors='replace')
        return jsonify({"status": "uploaded", "filename": filename, "path": path})
    return jsonify({"error": "Upload failed"}), 500


@app.route('/api/knowledge/list')
def list_knowledge():
    status, data = send_to_engine(CMD_LIST_KNOW)
    if status == 0x00:
        return jsonify(json.loads(data.decode('utf-8', errors='replace')))
    return jsonify([])


@app.route('/api/model/info')
def model_info():
    status, data = send_to_engine(CMD_MODEL_INFO)
    if status == 0x00:
        return jsonify(json.loads(data.decode('utf-8', errors='replace')))
    return jsonify({"error": "Unavailable"}), 503


@app.route('/api/raw', methods=['POST'])
def raw_command():
    body = request.get_json()
    if not body or 'data' not in body:
        return jsonify({"error": "Missing data"}), 400

    try:
        raw_data = base64.b64decode(body['data'])
    except Exception:
        return jsonify({"error": "Invalid base64"}), 400

    if len(raw_data) < 1:
        return jsonify({"error": "Empty data"}), 400

    command = raw_data[0]
    payload = raw_data[1:]

    status, data = send_to_engine(command, payload)
    if status is not None:
        resp = bytes([status]) + data
        return jsonify({"data": base64.b64encode(resp).decode()})
    return jsonify({"error": str(data)}), 500



if __name__ == '__main__':
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)
