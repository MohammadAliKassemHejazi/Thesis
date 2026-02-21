from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Translation(Base):
    __tablename__ = "translations"
    
    id = Column(Integer, primary_key=True, index=True)
    original_request_id = Column(Integer, index=True, nullable=False)
    language = Column(String(10), nullable=False)
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Validation fields
    confidence_score = Column(Float, nullable=True)
    back_translation = Column(Text, nullable=True)
    needs_review = Column(Boolean, default=False)

    # Human-in-the-loop fields for quality control
    is_edited = Column(Boolean, default=False)
    edited_text = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    edited_at = Column(DateTime, nullable=True)
    edited_by = Column(String(100), nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "original_request_id": self.original_request_id,
            "language": self.language,
            "original_text": self.original_text,
            "translated_text": self.translated_text,
            "confidence_score": self.confidence_score,
            "back_translation": self.back_translation,
            "needs_review": self.needs_review,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_edited": self.is_edited,
            "edited_text": self.edited_text,
            "feedback": self.feedback,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "edited_by": self.edited_by
        }
