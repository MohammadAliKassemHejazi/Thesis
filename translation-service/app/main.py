from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import os
from pathlib import Path

from app.database import get_db, engine, SessionLocal
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

# Add CORS middleware for the review UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class TranslateRequest(BaseModel):
    original_request_id: int
    text: str = Field(..., min_length=2, description="Text to translate (minimum 2 characters)")
    target_languages: List[str]

    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Text cannot be empty or just whitespace')
        return v

class TranslationResponse(BaseModel):
    id: int
    original_request_id: int
    language: str
    original_text: str
    translated_text: str

class TranslationAcceptedResponse(BaseModel):
    message: str
    original_request_id: int
    status: str = "accepted"

def process_translation_task(request_id: int, text: str, target_languages: List[str]):
    """
    Background task to process translations
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting background translation for request {request_id}")
        for target_lang in target_languages:
            try:
                # Check if language is supported
                if target_lang not in translation_engine.supported_languages:
                    logger.warning(f"Unsupported language: {target_lang}")
                    continue

                # Translate text
                translated_text = translation_engine.translate(text, target_lang)

                # Store in database
                translation = Translation(
                    original_request_id=request_id,
                    language=target_lang,
                    original_text=text,
                    translated_text=translated_text
                )
                db.add(translation)
                db.commit()
                logger.info(f"Saved translation for {target_lang}")

            except Exception as e:
                logger.error(f"Translation failed for {target_lang}: {str(e)}")
                db.rollback()
                continue
    finally:
        db.close()
        logger.info(f"Finished background translation for request {request_id}")

@app.on_event("startup")
async def startup_event():
    """Load AI models on startup"""
    logger.info("Starting Translation Microservice...")
    try:
        # Preload models (optional - can be lazy loaded instead)
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

@app.post("/translate", response_model=TranslationAcceptedResponse, status_code=202)
async def translate_text(
    request: TranslateRequest,
    background_tasks: BackgroundTasks
):
    """
    Queue text for translation into multiple languages
    """
    # Queue the background task
    background_tasks.add_task(
        process_translation_task,
        request.original_request_id,
        request.text,
        request.target_languages
    )
    
    return TranslationAcceptedResponse(
        message="Translation request accepted",
        original_request_id=request.original_request_id
    )

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

# Human-in-the-loop endpoints for quality control

class EditTranslationRequest(BaseModel):
    edited_text: str
    feedback: Optional[str] = None
    edited_by: Optional[str] = "reviewer"

@app.get("/translations/pending")
async def get_pending_translations(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get translations that haven't been reviewed/edited yet
    """
    translations = db.query(Translation).filter(
        Translation.is_edited == False
    ).offset(skip).limit(limit).all()
    
    return [t.to_dict() for t in translations]

@app.put("/translations/{translation_id}/edit")
async def edit_translation(
    translation_id: int,
    edit_request: EditTranslationRequest,
    db: Session = Depends(get_db)
):
    """
    Submit human edits for a translation
    """
    from datetime import datetime
    
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")
    
    # Update with human edits
    translation.is_edited = True
    translation.edited_text = edit_request.edited_text
    translation.feedback = edit_request.feedback
    translation.edited_at = datetime.utcnow()
    translation.edited_by = edit_request.edited_by
    
    db.commit()
    db.refresh(translation)
    
    return {
        "message": "Translation edited successfully",
        "translation": translation.to_dict()
    }

@app.get("/translations/statistics")
async def get_translation_statistics(db: Session = Depends(get_db)):
    """
    Get statistics about translation quality and human edits
    """
    total = db.query(Translation).count()
    edited = db.query(Translation).filter(Translation.is_edited == True).count()
    pending = total - edited
    
    return {
        "total_translations": total,
        "edited_translations": edited,
        "pending_review": pending,
        "edit_rate": round((edited / total * 100), 2) if total > 0 else 0
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """
    Serve the translation dashboard
    """
    html_path = Path(__file__).parent / "templates" / "dashboard.html"
    return html_path.read_text()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
