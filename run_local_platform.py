import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

from app import app

if __name__ == '__main__':
    print("جاري تشغيل منصة lingux_new2 الكاملة...")
    print("افتح المتصفح على: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
