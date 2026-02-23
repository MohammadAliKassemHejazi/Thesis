from fastapi import FastAPI
import logging

from app.database import engine
from app.models import Base
from app.translator import translation_engine
from app.routers import system, translations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Translation Microservice",
    description="AI-powered translation service using OPUS-MT models",
    version="1.0.0"
)

# Include routers
app.include_router(system.router)
app.include_router(translations.router)

@app.on_event("startup")
async def startup_event():
    """Load AI models on startup and migrate DB"""
    logger.info("Starting Translation Microservice...")
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)

        # Preload models (optional - can be lazy loaded instead)
        translation_engine.preload_all_models()
        logger.info("Translation service ready")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
