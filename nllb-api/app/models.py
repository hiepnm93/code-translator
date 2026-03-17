"""Pydantic request/response schemas."""
from typing import List, Optional
from pydantic import BaseModel

class TranslateRequest(BaseModel):
    q: str
    source: str
    target: str

class TranslateResponse(BaseModel):
    translatedText: str

class BatchTranslateRequest(BaseModel):
    q: List[str]
    source: str
    target: str

class BatchTranslateResponse(BaseModel):
    translatedTexts: List[str]

class DetectRequest(BaseModel):
    q: str

class DetectResponse(BaseModel):
    language: str
    confidence: float

class LanguageInfo(BaseModel):
    code: str
    name: str
