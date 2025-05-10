from flask import Flask, send_file

app = Flask(__name__)

@app.route("/")
def home():
    return "<h3>Sentibot is alive ✅</h3><p><a href='/download-log'>Download learning_log.csv</a></p>"

@app.route("/download-log")
def download_log():
    try:
        return send_file("learning_log.csv", as_attachment=True)
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
