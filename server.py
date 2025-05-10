from flask import Flask, send_file
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    return "Sentibot עובד. עבור ל- /download-log כדי להוריד את הקובץ."

@app.route("/download-log")
def download_log():
    path = "/tmp/learning_log.csv"
    try:
        return send_file(path, as_attachment=True)
    except FileNotFoundError:
        return "קובץ הלוג לא נמצא", 404

if __name__ == "__main__":
    print("🚀 מריץ את Sentibot (main.py)...")
    subprocess.run(["python", "main.py"], check=False)
    app.run(host="0.0.0.0", port=8000, debug=True)
