from transformers import MarianMTModel, MarianTokenizer
import logging

logger = logging.getLogger(__name__)

class TranslationEngine:
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.supported_languages = {
            "es": "Helsinki-NLP/opus-mt-en-es",  # Spanish
            "fr": "Helsinki-NLP/opus-mt-en-fr",  # French
            "de": "Helsinki-NLP/opus-mt-en-de",  # German
            "it": "Helsinki-NLP/opus-mt-en-it",  # Italian
            "pt": "Helsinki-NLP/opus-mt-en-pt",  # Portuguese
        }
        
    def load_model(self, target_lang: str):
        """Load a translation model for a specific language"""
        if target_lang in self.models:
            logger.info(f"Model for {target_lang} already loaded")
            return
        
        if target_lang not in self.supported_languages:
            raise ValueError(f"Language {target_lang} not supported")
        
        model_name = self.supported_languages[target_lang]
        logger.info(f"Loading model: {model_name}")
        
        try:
            self.tokenizers[target_lang] = MarianTokenizer.from_pretrained(model_name)
            self.models[target_lang] = MarianMTModel.from_pretrained(model_name)
            logger.info(f"Successfully loaded model for {target_lang}")
        except Exception as e:
            logger.error(f"Failed to load model for {target_lang}: {str(e)}")
            raise
    
    def translate(self, text: str, target_lang: str) -> str:
        """Translate text to target language"""
        if target_lang not in self.models:
            self.load_model(target_lang)
        
        try:
            tokenizer = self.tokenizers[target_lang]
            model = self.models[target_lang]
            
            # Tokenize and translate
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            translated = model.generate(**inputs)
            translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
            
            logger.info(f"Translated '{text}' to {target_lang}: '{translated_text}'")
            return translated_text
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            raise
    
    def preload_all_models(self):
        """Preload all supported language models"""
        logger.info("Preloading all translation models...")
        for lang in self.supported_languages.keys():
            try:
                self.load_model(lang)
            except Exception as e:
                logger.warning(f"Failed to preload model for {lang}: {str(e)}")
        logger.info("Model preloading complete")

# Global instance
translation_engine = TranslationEngine()
