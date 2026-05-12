from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import nltk

from app.api.v1.api import api_router
from app.db.session import init_db
from app.core.config import settings

def download_nltk_data():
    packages = ["punkt", "punkt_tab", "stopwords", "averaged_perceptron_tagger"]
    for pkg in packages:
        try:
            nltk.download(pkg, quiet=True)
        except Exception:
            pass

download_nltk_data()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("[Main] Initializing database...")
    try:
        await init_db()
    except Exception as e:
        print(f"[Main] Database initialization failed: {e}")
        print("[Main] App will continue but DB-dependent features might fail.")
    yield
    # Shutdown logic (if any)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Hybrid AI backend — Groq LPU + local models",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["health"])
def health_check():
    return {"status": "running", "message": f"{settings.PROJECT_NAME} Backend is live"}
