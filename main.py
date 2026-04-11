import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
import nltk

def download_nltk_data():
    packages = ["punkt", "punkt_tab", "stopwords", "averaged_perceptron_tagger"]
    for pkg in packages:
        try:
            nltk.download(pkg, quiet=True)
        except Exception:
            pass

download_nltk_data()

app = FastAPI(
    title="Meeting Notes AI Backend",
    description="Hybrid AI backend — local models + optional OpenAI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "running", "message": "Meeting Notes AI Backend is live"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        timeout_keep_alive=1800,    # 30 min
        h11_max_incomplete_event_size=200 * 1024 * 1024  # 200 MB
    )