import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import sqlite3
import yt_dlp
import uuid
import datetime
import qrcode
import io
import base64

app = Flask(__name__)
app.secret_key = 'lingomax_secret_key_123'

ADMIN_EMAIL = "farsalnwby16@gmail.com"
ADMIN_PASSWORD = "farsalnwby16@gmail.com"

CATEGORIES = ["Lessons", "Listening", "Accent", "Shadowing", "Podcast"]
LEVELS = ["A1", "A2", "B1", "B2", "C1"]

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# إنشاء وتنظيم قاعدة البيانات الدائمة (SQLite)
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # جدول الدروس
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            level TEXT NOT NULL,
            youtube_url TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0
        )
    ''')
    
    # جدول الطلاب للوحة الأدمن
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # جدول الحسابات الدائمة (للتسجيل والدخول للطلاب والأدمن)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # جدول الشهادات الموثقة
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cert_id TEXT UNIQUE NOT NULL,
            student_name TEXT NOT NULL,
            course_name TEXT DEFAULT 'LINGOMAX Diploma in English Language & Communication',
            issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # التأكد من وجود حساب الأدمن دائماً في قاعدة البيانات
    cursor.execute('SELECT * FROM users WHERE email = ?', (ADMIN_EMAIL,))
    admin_exists = cursor.fetchone()
    if not admin_exists:
        cursor.execute('''
            INSERT INTO users (fullname, email, password, role)
            VALUES (?, ?, ?, ?)
        ''', ('أدمن المنصة', ADMIN_EMAIL, ADMIN_PASSWORD, 'admin'))

    conn.commit()
    conn.close()

init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session.get('role') != 'admin':
            flash('عذراً، هذه الصفحة مخصصة للأدمن فقط', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action')
        
        # 1. إنشاء حساب طالب جديد بشكل دائم في داتابيز
        if action == 'register':
            fullname = request.form.get('fullname', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            if not fullname or not password:
                flash('يرجى كتابة الاسم كامل وكلمة المرور', 'danger')
                return render_template('login.html', tab='register')

            # لو الإيميل مش مكتوب نعمل إيميل أوتوماتيكي فريد
            user_email = email if email else f"{uuid.uuid4().hex[:8]}@lingomax.local"

            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            # فحص وجود الحساب
            cursor.execute('SELECT * FROM users WHERE email = ? OR fullname = ?', (user_email, fullname))
            existing_user = cursor.fetchone()

            if existing_user:
                conn.close()
                flash('هذا الاسم أو البريد مسجل بالفعل، اختر اسماً آخر أو سجل دخولك', 'warning')
                return render_template('login.html', tab='register')

            # إدخال الحساب في الداتابيز
            cursor.execute('INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)',
                           (fullname, user_email, password, 'student'))
            
            # حفظ الطالب في جدول الطلاب أيضاً
            cursor.execute('INSERT INTO students (name, email) VALUES (?, ?)', (fullname, user_email))
            conn.commit()
            conn.close()

            session['user'] = fullname
            session['role'] = 'student'
            flash(f'أهلاً بك يا {fullname}! تم إنشاء الحساب بنجاح', 'success')
            return redirect(url_for('student'))

        # 2. تسجيل الدخول بالتحقق من الداتابيز
        elif action == 'login':
            login_input = request.form.get('login_input', '').strip()
            password = request.form.get('password', '')

            conn = sqlite3.connect('database.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM users WHERE (email = ? OR fullname = ?) AND password = ?', 
                           (login_input, login_input, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                session['user'] = user['fullname']
                session['role'] = user['role']
                flash(f'مرحباً بعودتك، {user["fullname"]}!', 'success')
                
                if user['role'] == 'admin':
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('student'))
            else:
                flash('البيانات غير صحيحة، تأكد من الاسم/البريد وكلمة المرور', 'danger')
                return render_template('login.html', tab='login')

    return render_template('login.html', tab='login')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('login'))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/student')
@login_required
def student():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM lessons ORDER BY sort_order ASC, id ASC')
    lessons = cursor.fetchall()
    conn.close()
    return render_template('student.html', lessons=lessons, categories=CATEGORIES, levels=LEVELS)

@app.route('/admin')
@admin_required
def admin():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM lessons ORDER BY category, level, sort_order ASC, id ASC')
    lessons = cursor.fetchall()
    
    cursor.execute('SELECT * FROM students ORDER BY id DESC')
    students = cursor.fetchall()

    cursor.execute('SELECT * FROM certificates ORDER BY id DESC')
    certificates = cursor.fetchall()
    
    conn.close()
    return render_template('admin.html', lessons=lessons, students=students, certificates=certificates, categories=CATEGORIES, levels=LEVELS)

@app.route('/issue_cert', methods=['POST'])
@admin_required
def issue_cert():
    student_name = request.form.get('student_name')
    if student_name:
        cert_id = f"LMX-{str(uuid.uuid4())[:8].upper()}"
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO certificates (cert_id, student_name) VALUES (?, ?)', (cert_id, student_name))
        conn.commit()
        conn.close()
        return redirect(url_for('view_certificate', cert_id=cert_id))
    return redirect(url_for('admin'))

@app.route('/certificate/<cert_id>')
def view_certificate(cert_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM certificates WHERE cert_id = ?', (cert_id,))
    cert = cursor.fetchone()
    conn.close()

    if not cert:
        return "الشهادة غير موجودة بالنظام", 404

    verify_url = url_for('verify_certificate', cert_id=cert['cert_id'], _external=True)
    qr_base64 = generate_qr_code(verify_url)

    return render_template('certificate.html', cert=cert, qr_code=qr_base64, is_preview=False)

@app.route('/admin/cert_preview')
@admin_required
def cert_preview():
    dummy_cert = {
        'cert_id': 'PREVIEW-ONLY',
        'student_name': 'اسم الطالب يظهر هنا',
        'course_name': 'LINGOMAX Diploma in English Language & Communication'
    }
    verify_url = url_for('admin', _external=True)
    qr_base64 = generate_qr_code(verify_url)
    return render_template('certificate.html', cert=dummy_cert, qr_code=qr_base64, is_preview=True)

@app.route('/verify/<cert_id>')
def verify_certificate(cert_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM certificates WHERE cert_id = ?', (cert_id,))
    cert = cursor.fetchone()
    conn.close()

    if cert:
        return render_template('verify.html', status="valid", cert=cert)
    else:
        return render_template('verify.html', status="invalid", cert_id=cert_id)

@app.route('/add_single', methods=['POST'])
@admin_required
def add_single():
    title = request.form.get('title')
    category = request.form.get('category')
    level = request.form.get('level')
    youtube_url = request.form.get('youtube_url')

    if title and category and level and youtube_url:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(sort_order) FROM lessons WHERE category=? AND level=?', (category, level))
        max_order = cursor.fetchone()[0]
        new_order = (max_order + 1) if max_order is not None else 1
        
        cursor.execute('INSERT INTO lessons (title, category, level, youtube_url, sort_order) VALUES (?, ?, ?, ?, ?)',
                       (title, category, level, youtube_url, new_order))
        conn.commit()
        conn.close()

    return redirect(url_for('admin'))

@app.route('/add_playlist', methods=['POST'])
@admin_required
def add_playlist():
    category = request.form.get('category')
    level = request.form.get('level')
    playlist_url = request.form.get('playlist_url')

    if category and level and playlist_url:
        ydl_opts = {'extract_flat': True, 'skip_download': True, 'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                if 'entries' in info:
                    conn = sqlite3.connect('database.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT MAX(sort_order) FROM lessons WHERE category=? AND level=?', (category, level))
                    max_order = cursor.fetchone()[0]
                    current_order = (max_order + 1) if max_order is not None else 1

                    for entry in info['entries']:
                        if entry:
                            video_title = entry.get('title', 'درس بدون عنوان')
                            video_id = entry.get('id')
                            if video_id:
                                video_url = f"https://www.youtube.com/watch?v={video_id}"
                                cursor.execute('INSERT INTO lessons (title, category, level, youtube_url, sort_order) VALUES (?, ?, ?, ?, ?)',
                                               (video_title, category, level, video_url, current_order))
                                current_order += 1
                    conn.commit()
                    conn.close()
        except Exception as e:
            print(f"Error: {e}")

    return redirect(url_for('admin'))

@app.route('/edit_lesson/<int:lesson_id>', methods=['POST'])
@admin_required
def edit_lesson(lesson_id):
    title = request.form.get('title')
    youtube_url = request.form.get('youtube_url')
    category = request.form.get('category')
    level = request.form.get('level')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE lessons SET title=?, youtube_url=?, category=?, level=? WHERE id=?',
                   (title, youtube_url, category, level, lesson_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/delete_lesson/<int:lesson_id>', methods=['POST'])
@admin_required
def delete_lesson(lesson_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM lessons WHERE id = ?', (lesson_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/reorder_lesson/<int:lesson_id>/<direction>', methods=['POST'])
@admin_required
def reorder_lesson(lesson_id, direction):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM lessons WHERE id = ?', (lesson_id,))
    current_lesson = cursor.fetchone()
    
    if current_lesson:
        cat = current_lesson['category']
        lvl = current_lesson['level']
        
        if direction == 'up':
            cursor.execute('SELECT * FROM lessons WHERE category=? AND level=? AND sort_order < ? ORDER BY sort_order DESC LIMIT 1',
                           (cat, lvl, current_lesson['sort_order']))
        else:
            cursor.execute('SELECT * FROM lessons WHERE category=? AND level=? AND sort_order > ? ORDER BY sort_order ASC LIMIT 1',
                           (cat, lvl, current_lesson['sort_order']))
            
        target_lesson = cursor.fetchone()
        
        if target_lesson:
            cursor.execute('UPDATE lessons SET sort_order=? WHERE id=?', (target_lesson['sort_order'], current_lesson['id']))
            cursor.execute('UPDATE lessons SET sort_order=? WHERE id=?', (current_lesson['sort_order'], target_lesson['id']))
            conn.commit()
            
    conn.close()
    return redirect(url_for('admin'))

@app.route('/delete_student/<int:student_id>', methods=['POST'])
@admin_required
def delete_student(student_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

import yt_dlp

@app.route("/admin/import_playlist", methods=["POST"])
def import_playlist():
    playlist_url = request.form.get("playlist_url")
    level = request.form.get("level", "A1")
    if not playlist_url:
        return "برجاء إدخال اللينك", 400
    ydl_opts = {"extract_flat": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            if "entries" in info:
                for entry in info["entries"]:
                    if entry:
                        v_title = entry.get("title")
                        v_id = entry.get("id")
                        v_url = f"https://www.youtube.com/watch?v={v_id}"
                        new_lesson = Lesson(title=v_title, youtube_url=v_url, level=level)
                        db.session.add(new_lesson)
                db.session.commit()
            elif "id" in info:
                v_title = info.get("title")
                new_lesson = Lesson(title=v_title, youtube_url=playlist_url, level=level)
                db.session.add(new_lesson)
                db.session.commit()
        return "تم جلب جميع الفيديوهات وترتيبها بنجاح للطلاب!"
    except Exception as e:
        return f"خطأ في السحب: {str(e)}", 500

import sqlite3
from flask import request

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.json
    if 'message' in data:
        text = data['message'].get('text', '')
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        yt_url, level, section = '', 'A1', 'Lessons'
        
        for line in lines:
            if 'youtube.com' in line or 'youtu.be' in line:
                yt_url = line
            elif line in ['A1', 'A2', 'B1', 'B2', 'C1']:
                level = line
            elif line in ['Lessons', 'Listening', 'Accent', 'Shadowing', 'Podcast']:
                section = line

        if yt_url:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO lessons (title, url, section, level, sort_order) VALUES (?, ?, ?, ?, ?)',
                (f"درس بوت - {level} - {section}", yt_url, section, level, 1)
            )
            conn.commit()
            conn.close()
            print(f"تم سحب الدروس بنجاح: المستوى [{level}] وقسم [{section}]")
    return {'status': 'ok'}
