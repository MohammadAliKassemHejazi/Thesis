from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
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
    is_edited = Column(Boolean, default=False)
    edited_text = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "original_request_id": self.original_request_id,
            "language": self.language,
            "original_text": self.original_text,
            "translated_text": self.translated_text,
            "is_edited": self.is_edited,
            "edited_text": self.edited_text,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
