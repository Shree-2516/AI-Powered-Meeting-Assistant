# Meeting Notes AI

Meeting Notes AI is a backend and web UI for turning meeting audio into useful notes. Upload an audio file and the system generates a transcript, summary, key points, action items, sentiment, and main topics.

The project supports two processing modes:

- **Local mode**: Uses local Whisper, Hugging Face Transformers, NLTK, TextBlob, and scikit-learn.
- **OpenAI mode**: Uses OpenAI Whisper API for transcription and OpenAI chat completion for summarization when enabled.

## Features

- Upload meeting audio from a web interface.
- Transcribe audio into text.
- Generate a concise meeting summary.
- Extract important key points.
- Detect action items and follow-ups.
- Analyze meeting sentiment and tone.
- Extract main discussion topics.
- Supports large audio uploads up to 200 MB.
- Provides REST API endpoints for backend integration.

## Tech Stack

### Backend

- **Python**
- **FastAPI** for the API server
- **Uvicorn** for running the FastAPI app
- **Pydantic** for response models
- **python-dotenv** for environment configuration
- **python-multipart** for file uploads

### AI and NLP

- **OpenAI Whisper / openai-whisper** for speech-to-text
- **OpenAI API** for optional cloud transcription and summary generation
- **Hugging Face Transformers** for local summarization
- **PyTorch** for running local ML models
- **NLTK** for tokenization, stop words, and text processing
- **TextBlob** for sentiment analysis
- **scikit-learn** for TF-IDF topic extraction
- **NumPy** for numeric processing
- **sumy** as an available summarization dependency

### Frontend

- **Flask** for the web UI server
- **HTML templates** with Jinja
- **CSS**
- **JavaScript**

## Project Structure

```text
meeting-backend/
+-- app/
|   +-- api/
|   |   +-- routes.py
|   +-- core/
|   |   +-- settings.py
|   +-- models/
|   |   +-- response_models.py
|   +-- services/
|       +-- keypoints/
|       +-- sentiment/
|       +-- stt/
|       +-- summary/
|       +-- topics/
+-- frontend/
|   +-- static/
|   |   +-- css/
|   |   +-- js/
|   +-- templates/
|   +-- app.py
+-- main.py
+-- requirements.txt
+-- README.md
```

## Requirements

- Python 3.10 or newer is recommended.
- FFmpeg should be installed and available in your system PATH for local Whisper audio processing.
- Internet connection is needed the first time local AI models are downloaded.
- OpenAI API key is optional and only needed for OpenAI mode.

## Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=
USE_OPENAI=false
WHISPER_MODEL=base
SUMMARY_MODEL=facebook/bart-large-cnn
```

### Configuration Details

- `OPENAI_API_KEY`: Your OpenAI API key. Leave empty for local mode.
- `USE_OPENAI`: Set to `true` to use OpenAI services. Set to `false` for local mode.
- `WHISPER_MODEL`: Local Whisper model name, such as `tiny`, `base`, `small`, `medium`, or `large`.
- `SUMMARY_MODEL`: Summary model setting used by the app configuration.

OpenAI mode is used only when both conditions are true:

- `OPENAI_API_KEY` is set.
- `USE_OPENAI=true`.

## Installation

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks virtual environment activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## How To Run

You need to run the backend and frontend in two separate terminals.

### 1. Run FastAPI Backend

In terminal 1:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

The backend will run at:

```text
http://localhost:8000
```

Backend health check:

```text
http://localhost:8000/
```

API status endpoint:

```text
http://localhost:8000/api/status
```

### 2. Run Flask Frontend

In terminal 2:

```powershell
.\.venv\Scripts\Activate.ps1
python frontend/app.py
```

The frontend will run at:

```text
http://localhost:5000
```

Open this URL in your browser, upload a meeting audio file, and wait for the meeting analysis result.

## API Endpoints

### Health Check

```http
GET /
```

Returns backend running status.

### API Status

```http
GET /api/status
```

Returns current processing mode, model settings, OpenAI flag status, and upload limit.

### Process Meeting

```http
POST /api/process-meeting
```

Form-data field:

```text
audio=<meeting audio file>
```

Supported file types:

```text
.wav, .mp3, .m4a, .ogg, .flac, .webm, .mp4
```

Maximum file size:

```text
200 MB
```

Example response:

```json
{
  "meetingId": "AB12CD34",
  "mode": "local",
  "transcription": "Full meeting transcript...",
  "summary": "Meeting summary...",
  "keyPoints": ["Important point 1", "Important point 2"],
  "actionItems": ["Follow up task 1"],
  "sentiment": {
    "label": "POSITIVE",
    "score": 0.78,
    "tone": "Constructive and productive meeting"
  },
  "topics": ["Planning", "Budget", "Timeline"],
  "error": null
}
```

## Local Mode

Local mode runs without an OpenAI API key.

Use this in `.env`:

```env
USE_OPENAI=false
OPENAI_API_KEY=
```

In local mode:

- Local Whisper transcribes audio.
- Hugging Face Transformers summarizes the transcript.
- TextBlob analyzes sentiment.
- NLTK extracts key points and action items.
- scikit-learn extracts topics using TF-IDF.

The first run can be slow because models and NLTK data may need to download.

## OpenAI Mode

Use this in `.env`:

```env
USE_OPENAI=true
OPENAI_API_KEY=your_api_key_here
```

In OpenAI mode:

- OpenAI Whisper API transcribes audio.
- OpenAI chat completion generates the summary.
- Local services still handle sentiment, key points, action items, and topics.

## Troubleshooting

### Cannot connect to backend

Make sure the FastAPI backend is running:

```powershell
python main.py
```

The frontend expects the backend at:

```text
http://localhost:8000
```

### Local Whisper fails

Install FFmpeg and make sure it is available in PATH:

```powershell
ffmpeg -version
```

### Processing is slow

Large meetings can take several minutes, especially in local mode. Smaller Whisper models such as `tiny` or `base` are faster, while larger models are more accurate but slower.

### Unsupported file type

Use one of the supported formats:

```text
wav, mp3, m4a, ogg, flac, webm, mp4
```

## Notes

- Backend upload limit is 200 MB.
- The frontend upload request timeout is set for long-running meeting processing.
- NLTK data is downloaded automatically when the backend starts.
- Local AI models may require significant CPU, memory, and disk space.
