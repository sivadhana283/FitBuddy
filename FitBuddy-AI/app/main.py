from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .config import Settings, get_settings
from .database import init_db
from .routes import router

BASE_DIR = Path(__file__).resolve().parent.parent

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="AI-assisted 7-day fitness and wellness plan generator.",
    version="1.0.0"
)

# Mount static folder
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Include routes
app.include_router(router)

@app.on_event("startup")
def on_startup():
    init_db()