from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from pathlib import Path

from app.database import get_db, engine, check_and_migrate_db
from app.models import Base, Translation
from app.translator import translation_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables if they don't exist
# We defer this slightly so check_and_migrate_db can handle schema changes
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Translation Microservice",
    description="AI-powered translation service using OPUS-MT models",
    version="1.0.0"
)

# Pydantic models for request/response
class TranslateRequest(BaseModel):
    original_request_id: int
    name: str
    description: str
    target_languages: List[str]

class TranslationResponse(BaseModel):
    id: int
    original_request_id: int
    language: str
    original_name: str
    translated_name: str
    original_description: str
    translated_description: str
    is_edited: bool = False
    edited_name: Optional[str] = None
    edited_description: Optional[str] = None
    feedback: Optional[str] = None

class EditRequest(BaseModel):
    edited_name: Optional[str] = None
    edited_description: Optional[str] = None
    feedback: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Load AI models on startup and migrate DB"""
    logger.info("Starting Translation Microservice...")
    try:
        # ✅ Uncomment this line:
        Base.metadata.create_all(bind=engine)
        # Check and migrate database (pass Base to allow table creation)
        #check_and_migrate_db(engine, Base)

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

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML"""
    dashboard_path = Path("app/templates/dashboard.html")
    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard template not found")
    return dashboard_path.read_text(encoding="utf-8")

@app.get("/translations/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get translation statistics"""
    total = db.query(Translation).count()
    edited = db.query(Translation).filter(Translation.is_edited == True).count()
    pending = total - edited

    edit_rate = 0
    if total > 0:
        edit_rate = round((edited / total) * 100, 1)

    return {
        "total_translations": total,
        "pending_review": pending,
        "edited_translations": edited,
        "edit_rate": edit_rate
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
            
            # Translate name
            translated_name = translation_engine.translate(request.name, target_lang)

            # Translate description (handle empty description gracefully)
            translated_desc = ""
            if request.description and request.description.strip():
                translated_desc = translation_engine.translate(request.description, target_lang)
            
            # Store in database
            translation = Translation(
                original_request_id=request.original_request_id,
                language=target_lang,
                original_name=request.name,
                translated_name=translated_name,
                original_description=request.description,
                translated_description=translated_desc
            )
            db.add(translation)
            db.commit()
            db.refresh(translation)
            
            translations.append(TranslationResponse(
                id=translation.id,
                original_request_id=translation.original_request_id,
                language=translation.language,
                original_name=translation.original_name,
                translated_name=translation.translated_name,
                original_description=translation.original_description,
                translated_description=translation.translated_description
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

@app.put("/translations/{translation_id}/edit")
async def edit_translation(
    translation_id: int,
    edit_request: EditRequest,
    db: Session = Depends(get_db)
):
    """Update a translation with manual edits"""
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    if edit_request.edited_name is not None:
        translation.edited_name = edit_request.edited_name

    if edit_request.edited_description is not None:
        translation.edited_description = edit_request.edited_description

    translation.feedback = edit_request.feedback
    translation.is_edited = True

    db.commit()
    db.refresh(translation)

    return {"message": "Translation updated", "translation": translation.to_dict()}

@app.delete("/translations/{translation_id}")
async def delete_translation(
    translation_id: int,
    db: Session = Depends(get_db)
):
    """Delete a translation"""
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    db.delete(translation)
    db.commit()

    return {"message": "Translation deleted"}

@app.delete("/translations/product/{original_request_id}")
async def delete_translations_by_product(
    original_request_id: int,
    db: Session = Depends(get_db)
):
    """Delete all translations for a specific product/request ID"""
    translations = db.query(Translation).filter(
        Translation.original_request_id == original_request_id
    ).all()

    if not translations:
        # If no translations found, we can still consider this a success (idempotent)
        # or return 404. Given the requirement is to "ensure deleted", success is better.
        return {"message": "No translations found for this product", "deleted_count": 0}

    deleted_count = 0
    for translation in translations:
        db.delete(translation)
        deleted_count += 1

    db.commit()

    return {"message": "All translations for product deleted", "deleted_count": deleted_count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
