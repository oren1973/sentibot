import subprocess
import time
from flask import Flask, send_file
import os

app = Flask(__name__)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, "learning_log.csv")

@app.route("/")
def home():
    # נוסיף הדפסת מצב
    file_exists = os.path.exists(LOG_FILE_PATH)
    return f"""
    <h3>Sentibot is alive ✅</h3>
    <p>File exists: {'✅' if file_exists else '❌'} at <code>{LOG_FILE_PATH}</code></p>
    <p><a href='/download-log'>Download learning_log.csv</a></p>
    """

@app.route("/download-log")
def download_log():
    if not os.path.exists(LOG_FILE_PATH):
        print(f"❌ קובץ לא נמצא: {LOG_FILE_PATH}")
        return f"Error: File not found at {LOG_FILE_PATH}", 404

    print(f"✅ שולח את הקובץ: {LOG_FILE_PATH}")
    return send_file(LOG_FILE_PATH, as_attachment=True)

if __name__ == "__main__":
    print("🚀 מריץ את Sentibot (main.py)...")
    try:
        subprocess.run(["python", "main.py"], check=True)
        print("✅ Sentibot הסתיים. הקובץ אמור להיווצר.")
    except subprocess.CalledProcessError as e:
        print(f"❌ שגיאה בהרצת main.py: {e}")

    time.sleep(1)
    print("📂 קבצים בסביבת הריצה:", os.listdir(PROJECT_ROOT))
    print(f"🔍 בודק אם הקובץ קיים: {LOG_FILE_PATH}")
    app.run(debug=True, host="0.0.0.0", port=8000)
