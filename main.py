import uvicorn
import os

# This is the entry point for the application.
# It runs the FastAPI app defined in app/main.py

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        timeout_keep_alive=1800,    # 30 min
        h11_max_incomplete_event_size=200 * 1024 * 1024  # 200 MB
    )