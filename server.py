import subprocess
import time
from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "<h3>Sentibot is alive ✅</h3><p><a href='/download-log'>Download learning_log.csv</a></p>"

@app.route("/download-log")
def download_log():
    file_path = os.path.join(os.path.dirname(__file__), "learning_log.csv")
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}", 404
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    print("🚀 מריץ את Sentibot (main.py)...")
    try:
        subprocess.run(["python", "main.py"], check=True)
        print("✅ Sentibot הסתיים. מעלים את השרת...")
    except subprocess.CalledProcessError as e:
        print(f"❌ שגיאה בהרצת main.py: {e}")
    
    time.sleep(1)  # שיהיה זמן ל־CSV להיווצר

    app.run(debug=True, host="0.0.0.0", port=8000)
