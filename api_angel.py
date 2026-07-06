from flask import Flask, request, jsonify
import sqlite3
import re
import os

DB_PATH = os.environ.get("DB_PATH")
app = Flask(__name__)

API_KEY = os.environ.get("API_KEY")

def clean_phone(s):
    if not s:
        return None
    digits = re.sub(r'\D', '', str(s))
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    if len(digits) == 11:
        return digits
    if len(digits) == 10:
        return '7' + digits
    return None

def check_key():
    key = request.headers.get('X-API-Key') or request.args.get('api_key')
    return key == API_KEY

def search_by_phone(phone):
    clean = clean_phone(phone)
    if not clean:
        return []
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT full_name, phone, birth_date, address, passport, email, inn, snils, source
        FROM all_data
        WHERE phone LIKE ?
        LIMIT 20
    """, (f'%{clean}%',))
    rows = cur.fetchall()
    conn.close()
    return rows

def search_by_name(name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    parts = name.strip().split()
    if not parts:
        return []
    if len(parts) == 1:
        cur.execute("""
            SELECT full_name, phone, birth_date, address, passport, email, inn, snils, source
            FROM all_data
            WHERE full_name LIKE ?
            LIMIT 20
        """, (f'%{name}%',))
    else:
        conditions = []
        params = []
        for word in parts:
            if len(word) > 1:
                conditions.append("full_name LIKE ?")
                params.append(f'%{word}%')
        if not conditions:
            return []
        cur.execute(f"""
            SELECT full_name, phone, birth_date, address, passport, email, inn, snils, source
            FROM all_data
            WHERE {' OR '.join(conditions)}
            LIMIT 20
        """, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def search_by_passport(passport):
    clean = re.sub(r'\D', '', str(passport))
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT full_name, phone, birth_date, address, passport, email, inn, snils, source
        FROM all_data
        WHERE passport LIKE ? OR inn LIKE ? OR snils LIKE ?
        LIMIT 20
    """, (f'%{clean}%', f'%{clean}%', f'%{clean}%'))
    rows = cur.fetchall()
    conn.close()
    return rows

def search_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT full_name, phone, birth_date, address, passport, email, inn, snils, source
        FROM all_data
        WHERE email LIKE ?
        LIMIT 20
    """, (f'%{email}%',))
    rows = cur.fetchall()
    conn.close()
    return rows

def format_results(rows):
    return [{
        "full_name": r[0],
        "phone": r[1],
        "birth_date": r[2],
        "address": r[3],
        "passport": r[4],
        "email": r[5],
        "inn": r[6],
        "snils": r[7],
        "source": r[8]
    } for r in rows]

@app.route('/')
def home():
    return jsonify({
        "name": "Ангел",
        "version": "1.1",
        "status": "online",
        "endpoints": {
            "/search/phone": "?number=79001234567",
            "/search/name": "?query=Иванов Иван",
            "/search/passport": "?number=1234",
            "/search/email": "?email=test@mail.ru",
            "/stats": "статистика БД"
        }
    })

@app.route('/stats')
def stats():
    if not check_key():
        return jsonify({"error": "Неверный ключ"}), 401
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM all_data")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT full_name) FROM all_data WHERE full_name IS NOT NULL")
    unique = cur.fetchone()[0]
    conn.close()
    return jsonify({
        "total_records": f"{total:,}",
        "unique_names": f"{unique:,}",
        "status": "online"
    })

@app.route('/search/phone')
def api_phone():
    if not check_key():
        return jsonify({"error": "Неверный ключ"}), 401
    phone = request.args.get('number')
    if not phone:
        return jsonify({"error": "Укажите номер"}), 400
    rows = search_by_phone(phone)
    return jsonify({
        "success": True,
        "found": len(rows),
        "results": format_results(rows)
    })

@app.route('/search/name')
def api_name():
    if not check_key():
        return jsonify({"error": "Неверный ключ"}), 401
    name = request.args.get('query')
    if not name:
        return jsonify({"error": "Укажите ФИО"}), 400
    rows = search_by_name(name)
    return jsonify({
        "success": True,
        "found": len(rows),
        "results": format_results(rows)
    })

@app.route('/search/passport')
def api_passport():
    if not check_key():
        return jsonify({"error": "Неверный ключ"}), 401
    passport = request.args.get('number')
    if not passport:
        return jsonify({"error": "Укажите паспорт"}), 400
    rows = search_by_passport(passport)
    return jsonify({
        "success": True,
        "found": len(rows),
        "results": format_results(rows)
    })

@app.route('/search/email')
def api_email():
    if not check_key():
        return jsonify({"error": "Неверный ключ"}), 401
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Укажите email"}), 400
    rows = search_by_email(email)
    return jsonify({
        "success": True,
        "found": len(rows),
        "results": format_results(rows)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
