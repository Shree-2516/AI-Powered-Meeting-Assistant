from flask import Flask, render_template, request, redirect, url_for, send_file
import requests
import os
import io

app = Flask(__name__)

BACKEND_URL = "http://127.0.0.1:8000"

def _preferred_backend():
    if os.getenv("USE_GROQ", "false").lower() == "true" and os.getenv("GROQ_API_KEY", "").strip():
        return "groq", f"Groq Whisper ({os.getenv('GROQ_SPEECH_MODEL', 'whisper-large-v3-turbo')})"
    return "local", f"Local Whisper ({os.getenv('WHISPER_MODEL', 'base')})"

@app.route("/")
def index():
    preferred_stt, preferred_backend = _preferred_backend()
    return render_template("index.html", preferred_stt=preferred_stt, preferred_backend=preferred_backend)

@app.route("/upload", methods=["POST"])
def upload():
    if "audio" not in request.files:
        return render_template("index.html", error="No file selected.")

    audio_file = request.files["audio"]

    if audio_file.filename == "":
        return render_template("index.html", error="No file selected.")

    try:
        files = {"audio": (audio_file.filename, audio_file.read(), audio_file.content_type)}
        response = requests.post(f"{BACKEND_URL}/api/v1/process-meeting", files=files, timeout=1800)

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

@app.route("/history")
def history():
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/history/", timeout=10)
        if response.status_code == 200:
            history_data = response.json()
            return render_template("history.html", history=history_data)
        else:
            return render_template("index.html", error="Could not fetch history.")
    except Exception as e:
        return render_template("index.html", error=f"History error: {str(e)}")

@app.route("/meeting/<meeting_id>")
def meeting_detail(meeting_id):
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/history/{meeting_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return render_template("result.html", data=data, is_history=True)
        else:
            return redirect(url_for("history"))
    except Exception as e:
        return redirect(url_for("history"))

@app.route("/delete-meeting/<meeting_id>", methods=["POST"])
def delete_meeting(meeting_id):
    try:
        response = requests.delete(f"{BACKEND_URL}/api/v1/history/{meeting_id}", timeout=10)
        return redirect(url_for("history"))
    except Exception as e:
        return redirect(url_for("history"))

@app.route("/download-pdf/<meeting_id>")
def download_pdf_file(meeting_id):
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/history/{meeting_id}/pdf", timeout=30)
        if response.status_code == 200:
            return send_file(
                io.BytesIO(response.content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"Meeting_Report_{meeting_id}.pdf"
            )
        return "Error from backend", response.status_code
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    app.run(debug=True, port=5000)