import os

with open('app.py', 'r') as f:
    code = f.read()

# إضافة مسار الـ Webhook الخاص بالتليجرام داخل السيرفر الرئيسي لو مش موجود
if 'telegram-webhook' not in code:
    webhook_code = """
import sqlite3
from flask import request

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.json
    if 'message' in data:
        text = data['message'].get('text', '')
        lines = [l.strip() for l in text.split('\\n') if l.strip()]
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
"""
    code += webhook_code
    with open('app.py', 'w') as f:
        f.write(code)
    print('تم دمج كود التليجرام داخل المنصة بنجاح!')

