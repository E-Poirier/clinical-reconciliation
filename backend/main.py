"""Entry point for running the FastAPI application."""

from pathlib import Path

from dotenv import load_dotenv

# Load .env before uvicorn starts (so API_KEY, ANTHROPIC_API_KEY are available)
load_dotenv(Path(__file__).parent / ".env")

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=[".venv", ".git"],
       
    )
