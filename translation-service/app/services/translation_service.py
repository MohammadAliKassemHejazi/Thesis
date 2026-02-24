from sqlalchemy.orm import Session
from app.translator import translation_engine
from app.models import Translation
import logging

logger = logging.getLogger(__name__)

class TranslationService:
    def translate_content(self, db: Session, request):
        translations = []

        for target_lang in request.target_languages:
            try:
                # Check if language is supported
                if target_lang not in translation_engine.supported_languages:
                    logger.warning(f"Unsupported language: {target_lang}")
                    continue

                # Check if translation already exists and delete it
                existing_translation = db.query(Translation).filter(
                    Translation.original_request_id == request.original_request_id,
                    Translation.language == target_lang
                ).first()

                if existing_translation:
                    db.delete(existing_translation)

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

                translations.append(translation)

            except Exception as e:
                logger.error(f"Translation failed for {target_lang}: {str(e)}")
                db.rollback()
                continue

        return translations

translation_service = TranslationService()
