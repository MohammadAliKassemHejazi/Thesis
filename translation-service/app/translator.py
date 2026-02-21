from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import logging
from difflib import SequenceMatcher
import torch

logger = logging.getLogger(__name__)

class TranslationEngine:
    def __init__(self):
        self.model_name = "facebook/nllb-200-distilled-600M"
        self.model = None
        self.tokenizer = None

        # Map ISO codes to NLLB codes
        self.lang_map = {
            "es": "spa_Latn",
            "fr": "fra_Latn",
            "de": "deu_Latn",
            "it": "ita_Latn",
            "pt": "por_Latn",
            "en": "eng_Latn"
        }

        # Supported target languages (excluding English which is source/back-target)
        self.supported_languages = {
            code: self.model_name
            for code in ["es", "fr", "de", "it", "pt"]
        }
        
    def load_model(self):
        """Load the NLLB model"""
        if self.model is not None:
            return
        
        logger.info(f"Loading model: {self.model_name}")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            logger.info("Successfully loaded NLLB model")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
    
    def translate(self, text: str, target_lang: str, source_lang: str = "en") -> str:
        """
        Translate text to target language.
        Defaults to translating from English.
        """
        if self.model is None:
            self.load_model()

        # Resolve NLLB language codes
        nllb_target = self.lang_map.get(target_lang)
        nllb_source = self.lang_map.get(source_lang)

        if not nllb_target:
            raise ValueError(f"Target language {target_lang} not supported")
        if not nllb_source:
             raise ValueError(f"Source language {source_lang} not supported")
        
        try:
            # Set source language
            self.tokenizer.src_lang = nllb_source

            # Tokenize
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)

            # Generate with forced BOS token for target language
            forced_bos_token_id = self.tokenizer.convert_tokens_to_ids(nllb_target)
            
            translated = self.model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=512
            )
            
            translated_text = self.tokenizer.decode(translated[0], skip_special_tokens=True)
            return translated_text
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            raise

    def translate_with_validation(self, text: str, target_lang: str) -> dict:
        """Translate and validate via back-translation"""
        # Forward translation: English -> Target
        translated = self.translate(text, target_lang, source_lang="en")

        # Back translation: Target -> English
        back_translated = self.translate(translated, target_lang="en", source_lang=target_lang)

        # Calculate similarity
        similarity = SequenceMatcher(None, text.lower().strip(), back_translated.lower().strip()).ratio()

        return {
            "translated_text": translated,
            "back_translation": back_translated,
            "confidence_score": round(similarity, 3),
            "needs_review": similarity < 0.6  # Flag low-confidence translations
        }
    
    def preload_all_models(self):
        """Preload the single NLLB model"""
        try:
            self.load_model()
        except Exception as e:
            logger.warning(f"Failed to preload model: {str(e)}")

# Global instance
translation_engine = TranslationEngine()
