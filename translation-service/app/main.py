from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db, engine
from app.models import Base, Translation
from app.translator import translation_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Translation Microservice",
    description="AI-powered translation service using OPUS-MT models",
    version="1.0.0"
)

# Pydantic models for request/response
class TranslateRequest(BaseModel):
    original_request_id: int
    text: str
    target_languages: List[str]

class TranslationResponse(BaseModel):
    id: int
    original_request_id: int
    language: str
    original_text: str
    translated_text: str

@app.on_event("startup")
async def startup_event():
    """Load AI models on startup"""
    logger.info("Starting Translation Microservice...")
    try:
        # Preload models (optional - can be lazy loaded instead)
        # translation_engine.preload_all_models()
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

@app.post("/translate", response_model=List[TranslationResponse])
async def translate_text(request: TranslateRequest, db: Session = Depends(get_db)):
    """
    Translate text into multiple languages and store results
    """
    translations = []
    
    for target_lang in request.target_languages:
        try:
            # Check if language is supported
            if target_lang not in translation_engine.supported_languages:
                logger.warning(f"Unsupported language: {target_lang}")
                continue
            
            # Translate text
            translated_text = translation_engine.translate(request.text, target_lang)
            
            # Store in database
            translation = Translation(
                original_request_id=request.original_request_id,
                language=target_lang,
                original_text=request.text,
                translated_text=translated_text
            )
            db.add(translation)
            db.commit()
            db.refresh(translation)
            
            translations.append(TranslationResponse(
                id=translation.id,
                original_request_id=translation.original_request_id,
                language=translation.language,
                original_text=translation.original_text,
                translated_text=translation.translated_text
            ))
            
        except Exception as e:
            logger.error(f"Translation failed for {target_lang}: {str(e)}")
            db.rollback()
            continue
    
    if not translations:
        raise HTTPException(status_code=500, detail="All translations failed")
    
    return translations

@app.get("/translations/{original_request_id}")
async def get_translations(
    original_request_id: int,
    lang: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get translations for a specific product/request ID
    Optionally filter by language
    """
    query = db.query(Translation).filter(
        Translation.original_request_id == original_request_id
    )
    
    if lang:
        query = query.filter(Translation.language == lang)
    
    translations = query.all()
    
    if not translations:
        raise HTTPException(status_code=404, detail="Translations not found")
    
    return [t.to_dict() for t in translations]

@app.get("/translations")
async def list_all_translations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all translations with pagination
    """
    translations = db.query(Translation).offset(skip).limit(limit).all()
    return [t.to_dict() for t in translations]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
