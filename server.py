# server.py – גרסה תקינה עבור sentibot-doc

from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>Sentibot: תיעוד פעולות</h1><a href='/download-log'>📄 הורד את קובץ הלמידה</a>"

@app.route("/download-log")
def download_log():
    log_path = "/tmp/learning_log.csv"
    if os.path.exists(log_path):
        return send_file(log_path, as_attachment=True)
    else:
        return "⚠️ הקובץ לא נמצא. ודא שהרצת את Sentibot לפחות פעם אחת.", 404

# מריץ את Sentibot במצב תיעוד (לא חובה, אבל שומר על עדכניות)
os.system("python main.py")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
