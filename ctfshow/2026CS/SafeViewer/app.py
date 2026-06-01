import os
import zipfile
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

DATA_DIR = os.environ.get("B_DATA_DIR", "/tmp/b_data")
os.makedirs(DATA_DIR, exist_ok=True)

def _safe_join(base: str, p: str) -> str:
    return os.path.join(base, p)

#恭喜你，拿到SafeViewer的FLAG ctfshow{21afe5f9839175d79e0adbcb9d7f2198}
@app.get("/internal/file")
def internal_file():
    path = request.args.get("path", "docxTemplates")
    filename = request.args.get("filename", "")

    target_dir = _safe_join(DATA_DIR, path)

    if filename:
        fp = os.path.join(target_dir, filename)
        try:
            with open(fp, "rb") as f:
                return Response(f.read(), content_type="application/octet-stream")
        except Exception:
            return Response("NOT_FOUND", status=404)

    try:
        items = []
        for n in sorted(os.listdir(target_dir)):
            p = os.path.join(target_dir, n)
            items.append({"name": n, "is_dir": os.path.isdir(p)})
        return jsonify({"path": path, "items": items})
    except Exception:
        return jsonify({"path": path, "items": []})



@app.get("/render")
def render_xml():
    content = request.args.get("content", "Hello")
    author = request.args.get("author", "Anonymous")
    hide = request.args.get("hide", "0")
    xml = f'''<?xml version="1.0"?>
            <!-- post by {author} -->
            <doc>
            <content>{content}</content>
            <hide>{hide}</hide>
            </doc>
            '''
    return Response(xml, content_type="text/xml; charset=utf-8")


#处理SafeViewer服务器的http://viewer:5000/ops/sync接口 过来的数据同步请求
@app.post("/internal/upload")
def internal_upload():
    dest_path = "docxTemplates"

    if "file" not in request.files:
        return _err("NO_FILE")

    f = request.files["file"]
    if not f or not f.filename:
        return _err("BAD_FILE")

    base_dir = os.path.join("/app/", dest_path)
    os.makedirs(base_dir, exist_ok=True)
    zip_path = os.path.join(base_dir, "src.zip")

    try:
        f.save(zip_path)
    except Exception:
        return _err("SAVE_FAILED")

    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(base_dir)
    except Exception:
        return _err("UNZIP_FAILED")
    finally:
        try:
            os.remove(zip_path)
        except Exception:
            pass

    return jsonify({"ok": True, "path": dest_path})




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001,debug=False)