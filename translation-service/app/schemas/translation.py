from pydantic import BaseModel
from typing import List, Optional

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
