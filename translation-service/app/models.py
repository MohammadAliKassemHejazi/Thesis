from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Translation(Base):
    __tablename__ = "translations"
    
    id = Column(Integer, primary_key=True, index=True)
    original_request_id = Column(Integer, index=True, nullable=False)
    language = Column(String(10), nullable=False)
    original_name = Column(Text, nullable=False)
    translated_name = Column(Text, nullable=False)
    original_description = Column(Text, nullable=False)
    translated_description = Column(Text, nullable=False)
    is_edited = Column(Boolean, default=False)
    edited_name = Column(Text, nullable=True)
    edited_description = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "original_request_id": self.original_request_id,
            "language": self.language,
            "original_name": self.original_name,
            "translated_name": self.translated_name,
            "original_description": self.original_description,
            "translated_description": self.translated_description,
            "is_edited": self.is_edited,
            "edited_name": self.edited_name,
            "edited_description": self.edited_description,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
