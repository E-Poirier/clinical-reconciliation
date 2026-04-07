"""CLI entrypoint: loads environment variables then runs Uvicorn with hot reload."""

from pathlib import Path

import uvicorn
from dotenv import load_dotenv

# Load backend/.env before the app module is imported (API_KEY, ANTHROPIC_API_KEY, etc.).
load_dotenv(Path(__file__).resolve().parent / ".env")

if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=[".venv", ".git"],
    )
