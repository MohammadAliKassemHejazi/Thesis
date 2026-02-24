from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
import logging

from app.core.config import settings
from app.api.v1.endpoints import translations
from app.database import engine
from app.models import Base
from app.translator import translation_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered translation service using OPUS-MT models",
    version="1.0.0"
)

# Include routers
# We include it without a prefix because the router defines specific paths (e.g. /translate, /translations/statistics)
# that don't share a common root prefix for all endpoints (some start with /translations, some with /translate).
app.include_router(translations.router)

@app.on_event("startup")
async def startup_event():
    """Load AI models on startup and migrate DB"""
    logger.info("Starting Translation Microservice...")
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)

        # Preload models
        translation_engine.preload_all_models()
        logger.info("Translation service ready")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")

@app.get("/")
async def root():
    return {
        "service": "Translation Microservice",
        "status": "running",
        "supported_languages": list(translation_engine.supported_languages.keys())
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_loaded": len(translation_engine.models),
        "supported_languages": list(translation_engine.supported_languages.keys())
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML"""
    dashboard_path = Path("app/templates/dashboard.html")
    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard template not found")
    return dashboard_path.read_text(encoding="utf-8")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
