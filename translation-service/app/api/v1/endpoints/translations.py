from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.translation import TranslateRequest, TranslationResponse, EditRequest
from app.services.translation_service import translation_service
from app.crud.translation import (
    get_translation,
    get_translations_by_request_id,
    get_all_translations,
    update_translation,
    delete_translation,
    delete_translations_by_request_id,
    get_statistics
)

router = APIRouter()

@router.get("/translations/statistics")
async def get_stats(db: Session = Depends(get_db)):
    """Get translation statistics"""
    return get_statistics(db)

@router.post("/translate", response_model=List[TranslationResponse])
async def translate_text(request: TranslateRequest, db: Session = Depends(get_db)):
    """
    Translate text into multiple languages and store results
    """
    translations = translation_service.translate_content(db, request)

    if not translations:
        raise HTTPException(status_code=500, detail="All translations failed")

    return translations

@router.get("/translations/{original_request_id}")
async def get_translations(
    original_request_id: int,
    lang: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get translations for a specific product/request ID
    Optionally filter by language
    """
    translations = get_translations_by_request_id(db, original_request_id, lang)

    if not translations:
        raise HTTPException(status_code=404, detail="Translations not found")

    return [t.to_dict() for t in translations]

@router.get("/translations")
async def list_all_translations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all translations with pagination
    """
    translations = get_all_translations(db, skip, limit)
    return [t.to_dict() for t in translations]

@router.put("/translations/{translation_id}/edit")
async def edit_translation_endpoint(
    translation_id: int,
    edit_request: EditRequest,
    db: Session = Depends(get_db)
):
    """Update a translation with manual edits"""
    translation = get_translation(db, translation_id)
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    translation = update_translation(db, translation, edit_request)

    return {"message": "Translation updated", "translation": translation.to_dict()}

@router.delete("/translations/{translation_id}")
async def delete_translation_endpoint(
    translation_id: int,
    db: Session = Depends(get_db)
):
    """Delete a translation"""
    translation = get_translation(db, translation_id)
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    delete_translation(db, translation)

    return {"message": "Translation deleted"}

@router.delete("/translations/product/{original_request_id}")
async def delete_translations_by_product(
    original_request_id: int,
    db: Session = Depends(get_db)
):
    """Delete all translations for a specific product/request ID"""
    deleted_count = delete_translations_by_request_id(db, original_request_id)

    # We return success even if count is 0 (idempotent)
    return {"message": "All translations for product deleted", "deleted_count": deleted_count}
