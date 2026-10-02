import os
import sqlite3
from flask import Flask, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.json
    if 'message' in data:
        message = data['message']
        text = message.get('text', '')
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        yt_url = ''
        level = 'A1'
        section = 'Lessons'
        
        levels_list = ['A1', 'A2', 'B1', 'B2', 'C1']
        sections_list = ['Lessons', 'Listening', 'Accent', 'Shadowing', 'Podcast']
        
        for line in lines:
            if 'youtube.com' in line or 'youtu.be' in line:
                yt_url = line
            elif line in levels_list:
                level = line
            elif line in sections_list:
                section = line

        if yt_url:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO lessons (title, url, section, level, sort_order) VALUES (?, ?, ?, ?, ?)',
                (f"درس بوت - {level} - {section}", yt_url, section, level, 1)
            )
            conn.commit()
            conn.close()
            print(f"تمت الإضافة بنجاح: المستوى [{level}] والقسم [{section}]")
            
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
