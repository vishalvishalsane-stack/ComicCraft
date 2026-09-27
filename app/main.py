import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("comiccraft")

app = FastAPI(
    title="ComicCraft",
    description="AI Comic Story Creator — Generate 5-panel comic strips with Gemini & Stable Diffusion",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Ensure static directories exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
PANELS_DIR = os.path.join(STATIC_DIR, "panels")
EXPORTS_DIR = os.path.join(STATIC_DIR, "exports")

os.makedirs(PANELS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include application routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
