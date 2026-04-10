from flask import Flask, render_template, request, redirect, url_for
import requests
import os

app = Flask(__name__)

BACKEND_URL = "http://localhost:8000"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "audio" not in request.files:
        return render_template("index.html", error="No file selected.")

    audio_file = request.files["audio"]

    if audio_file.filename == "":
        return render_template("index.html", error="No file selected.")

    try:
        files = {"audio": (audio_file.filename, audio_file.read(), audio_file.content_type)}
        response = requests.post(f"{BACKEND_URL}/api/process-meeting", files=files, timeout=300)

        if response.status_code == 200:
            data = response.json()
            return render_template("result.html", data=data)
        else:
            error = response.json().get("detail", "Backend error occurred.")
            return render_template("index.html", error=error)

    except requests.exceptions.ConnectionError:
        return render_template("index.html", error="Cannot connect to backend. Make sure FastAPI is running on port 8000.")
    except Exception as e:
        return render_template("index.html", error=str(e))

if __name__ == "__main__":
    app.run(debug=True, port=5000)