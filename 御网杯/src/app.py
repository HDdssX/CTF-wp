from flask import Flask, request, session, redirect, url_for, render_template, render_template_string, jsonify
import sqlite3
import os
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

def get_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    if user:
        session['user_id'] = user['id']
        session['role'] = user['role']
        return redirect(url_for('dashboard'))
    return render_template('login.html', error='Invalid credentials')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    db = get_db()
    profiles = db.execute('SELECT * FROM profiles WHERE user_id = ?', (session['user_id'],)).fetchall()
    return render_template('dashboard.html', profiles=profiles, role=session.get('role', 'user'))

@app.route('/api/create_profile', methods=['POST'])
def create_profile():
    if 'user_id' not in session: return jsonify({'status': 'error', 'message': 'unauthorized'}), 401
    db = get_db()
    db.execute('INSERT INTO profiles (user_id, year, income, deductions, state, custom_footer) VALUES (?, 2026, 0, 0, "DRAFT", "Internal Tax System Standard Footer")', (session['user_id'],))
    db.commit()
    return redirect(url_for('dashboard'))

@app.route('/api/import', methods=['POST'])
def import_data():
    if 'user_id' not in session: return jsonify({'status': 'error', 'message': 'unauthorized'}), 401
    data = request.json
    profile_id = data.get('profile_id')
    import_data = data.get('data', {})
    
    db = get_db()
    profile = db.execute("SELECT * FROM profiles WHERE id = ? AND user_id = ?", (profile_id, session['user_id'])).fetchone()
    if not profile: return jsonify({'status': 'error', 'message': 'not found'}), 404
    
    allowed_fields = ['income', 'deductions', 'state', 'custom_footer', 'year']
    updates = []
    params = []
    for k, v in import_data.items():
        if k in allowed_fields:
            updates.append(f"{k} = ?")
            params.append(v)
            
    if updates:
        params.extend([profile_id, session['user_id']])
        db.execute(f"UPDATE profiles SET {', '.join(updates)} WHERE id = ? AND user_id = ?", params)
        db.commit()
    
    return jsonify({"status": "success"})

@app.route('/preview/<int:profile_id>')
def preview(profile_id):
    if 'user_id' not in session: return redirect(url_for('index'))
    db = get_db()
    profile = db.execute("SELECT * FROM profiles WHERE id = ? AND user_id = ?", (profile_id, session['user_id'])).fetchone()
    if not profile: return "Not Found", 404
    
    state = profile['state']
    
    if state == 'AUDIT_PENDING':
        custom_footer = profile['custom_footer']
        blacklist = ['__', '[', ']', '|', '\\', '+', "'", '"', 'request', 'session', 'url_for', 'popen', 'system']
        for word in blacklist:
            if word in custom_footer:
                return "Security Policy Violation: Blocked character or word detected in footer.", 403
                
        template_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Audit Report</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <style>
                body {{ background-color: #f3f4f6; }}
            </style>
        </head>
        <body class="p-10">
            <div class="max-w-4xl mx-auto bg-white p-8 border-t-8 border-red-600 shadow-xl rounded">
                <div class="flex justify-between items-center mb-6 border-b pb-4">
                    <h1 class="text-3xl font-bold text-gray-800">OFFICIAL AUDIT REP或T</h1>
                    <span class="px-4 py-1 bg-red-100 text-red-800 rounded-full font-semibold">CONFIDENTIAL</span>
                </div>
                <div class="grid grid-cols-2 gap-6 mb-8 text-lg">
                    <div><span class="font-bold text-gray-600">Tax Year:</span> {profile['year']}</div>
                    <div><span class="font-bold text-gray-600">状态: </span> <span class="text-red-600 font-bold">AUDIT PENDING</span></div>
                    <div><span class="font-bold text-gray-600">Declared Income:</span> ${profile['income']}</div>
                    <div><span class="font-bold text-gray-600">Deductions:</span> ${profile['deductions']}</div>
                </div>
                <div class="mt-12 pt-6 border-t border-gray-200 text-sm text-gray-500 italic text-center">
                    {custom_footer}
                </div>
            </div>
            <div class="mt-8 text-center"><a href="/dashboard" class="px-6 py-2 bg-gray-800 text-white rounded hover:bg-gray-700 transition">返回控制台</a></div>
        </body>
        </html>
        """
        try:
            return render_template_string(template_html)
        except Exception as e:
            return str(e), 500
    else:
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Standard Preview</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <style>
                body {{ background: #f8fafc; font-family: system-ui, -apple-system, sans-serif; }}
                .glass {{ background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); }}
            </style>
        </head>
        <body class="min-h-screen flex items-center justify-center p-4">
            <div class="glass w-full max-w-lg p-8 rounded-2xl shadow-lg border border-gray-100 text-center">
                <h2 class="text-2xl font-bold text-gray-800 mb-4">Standard Draft Preview</h2>
                <div class="bg-gray-50 p-4 rounded-lg mb-6 text-left">
                    <p class="mb-2"><span class="font-semibold text-gray-600">Income:</span> ${profile['income']}</p>
                    <p><span class="font-semibold text-gray-600">Current State:</span> {state}</p>
                </div>
                <p class="text-gray-500 text-sm mb-6">
                    Note: Your profile is currently in <span class="font-bold">{state}</span> state. 
                    Only <span class="font-bold text-red-500">AUDIT_PENDING</span> profiles receive the official formatted PDF report rendering engine.
                </p>
                <a href="/dashboard" class="inline-block px-8 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition shadow-md hover:shadow-lg">Back to Dashboard</a>
            </div>
        </body>
        </html>
        """

@app.route('/admin/vault')
def admin_vault():
    if session.get('role') != 'tax_inspector':
        return render_template_string("""
        <div style="text-align:center; margin-top:100px; font-family:sans-serif;">
            <h1 style="color:red;">Unauthorized Access</h1>
            <p>You must be a <b>tax_inspector</b> to access this vault.</p>
            <a href="/dashboard">Back</a>
        </div>
        """), 403
    db = get_db()
    flag = db.execute("SELECT flag FROM config_flags LIMIT 1").fetchone()
    return render_template('admin.html', flag=flag['flag'] if flag else "No flag found")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
