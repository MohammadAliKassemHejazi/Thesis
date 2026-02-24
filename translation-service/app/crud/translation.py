from sqlalchemy.orm import Session
from app.models import Translation
from app.schemas.translation import EditRequest
from typing import List, Optional

def get_translation(db: Session, translation_id: int):
    return db.query(Translation).filter(Translation.id == translation_id).first()

def get_translations_by_request_id(db: Session, original_request_id: int, lang: Optional[str] = None):
    query = db.query(Translation).filter(
        Translation.original_request_id == original_request_id
    )
    if lang:
        query = query.filter(Translation.language == lang)
    return query.all()

def get_existing_translation(db: Session, original_request_id: int, language: str):
    return db.query(Translation).filter(
        Translation.original_request_id == original_request_id,
        Translation.language == language
    ).first()

def create_translation(db: Session, translation_data: dict):
    translation = Translation(**translation_data)
    db.add(translation)
    db.commit()
    db.refresh(translation)
    return translation

def delete_translation(db: Session, translation: Translation):
    db.delete(translation)
    db.commit()

def update_translation(db: Session, translation: Translation, edit_request: EditRequest):
    if edit_request.edited_name is not None:
        translation.edited_name = edit_request.edited_name

    if edit_request.edited_description is not None:
        translation.edited_description = edit_request.edited_description

    translation.feedback = edit_request.feedback
    translation.is_edited = True

    db.commit()
    db.refresh(translation)
    return translation

def delete_translations_by_request_id(db: Session, original_request_id: int):
    translations = db.query(Translation).filter(
        Translation.original_request_id == original_request_id
    ).all()

    count = 0
    for translation in translations:
        db.delete(translation)
        count += 1

    db.commit()
    return count

def get_all_translations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Translation).offset(skip).limit(limit).all()

def get_statistics(db: Session):
    total = db.query(Translation).count()
    edited = db.query(Translation).filter(Translation.is_edited == True).count()
    pending = total - edited

    edit_rate = 0.0
    if total > 0:
        edit_rate = round((edited / total) * 100, 1)

    return {
        "total_translations": total,
        "pending_review": pending,
        "edited_translations": edited,
        "edit_rate": edit_rate
    }
