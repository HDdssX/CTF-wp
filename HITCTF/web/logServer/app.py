from flask import Flask, request, jsonify, render_template_string
import sqlite3
import random


def gen_secret():
    secret_int = random.getrandbits(96)
    secret_bits = secret_int.to_bytes((secret_int.bit_length() + 7) // 8, byteorder='big')
    return secret_bits.hex()


app = Flask(__name__)
conn = sqlite3.connect("database.db", isolation_level=None, check_same_thread=False)
conn.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL
    )
""")
conn.execute("""
    CREATE TABLE IF NOT EXISTS secret (
        secret TEXT NOT NULL
    )
""")
conn.execute(f"INSERT INTO secret VALUES ('{gen_secret()}')")


@app.route("/")
def health_check():
    return jsonify({"status": "ok"}), 200


@app.route("/log", methods=["POST"])
def log_message():
    data = request.get_json()
    message = data.get("message")
    if not message:
        return jsonify({"success": False, "error": "Message is required"}), 400

    try:
        conn.execute(f"INSERT INTO logs (message) VALUES ('{message}')")
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/backdoor", methods=["POST"])
def backdoor():
    data = request.get_json()
    secret = data.get("secret")
    code = data.get("code")

    if not secret or not code:
        return jsonify(
            {"success": False, "error": "Secret and code are required"}
        ), 400

    stored_secret = conn.execute("SELECT secret FROM secret").fetchone()[0]
    if secret != stored_secret:
        return jsonify({"success": False, "error": "Invalid secret"}), 403

    res = render_template_string(code)
    return jsonify({"success": True, "result": res}), 200


@app.after_request
def update_secret(response):
    new_secret = gen_secret()
    conn.execute(f"UPDATE secret SET secret = '{new_secret}'")
    print(f"New secret generated: {new_secret}")
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
