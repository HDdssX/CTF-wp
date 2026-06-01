import sqlite3
import os

db_path = '/var/lib/sqlite/tax.db'
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    password TEXT,
    role TEXT
)
''')
cur.execute('''
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    year INTEGER,
    income INTEGER,
    deductions INTEGER,
    state TEXT,
    custom_footer TEXT
)
''')
cur.execute('''
CREATE TABLE config_flags (
    flag TEXT
)
''')

cur.execute('INSERT INTO users (username, password, role) VALUES ("admin", "123456", "admin")')
cur.execute('INSERT INTO config_flags (flag) VALUES ("flag{xxxxxxxxxxxxxxxx}")')

cur.execute('INSERT INTO profiles (user_id, year, income, deductions, state, custom_footer) VALUES (1, 2025, 65000, 12000, "SUBMITTED", "Standard Confidential Footer")')

conn.commit()
conn.close()
