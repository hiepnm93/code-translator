"""FastAPI server for NLLB Translation API."""
import logging
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException
from app.models import (TranslateRequest, TranslateResponse, BatchTranslateRequest, BatchTranslateResponse, DetectRequest, DetectResponse, LanguageInfo)
from app.translator import translator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
MAX_BATCH_SIZE = 64
MAX_REQUEST_BODY_KB = 10

@asynccontextmanager
async def lifespan(app: FastAPI):
    translator.load()
    yield

app = FastAPI(title="NLLB Translation API", version="1.0.0", lifespan=lifespan)

@app.post("/translate", response_model=TranslateResponse)
async def translate(req: TranslateRequest):
    try:
        result = translator.translate(req.q, req.source, req.target)
        return TranslateResponse(translatedText=result)
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate/batch", response_model=BatchTranslateResponse)
async def translate_batch(req: BatchTranslateRequest):
    if len(req.q) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=400, detail=f"Batch size {len(req.q)} exceeds maximum {MAX_BATCH_SIZE}")
    body_size_kb = sum(len(s.encode()) for s in req.q) / 1024
    if body_size_kb > MAX_REQUEST_BODY_KB:
        raise HTTPException(status_code=400, detail=f"Request body {body_size_kb:.1f}KB exceeds maximum {MAX_REQUEST_BODY_KB}KB")
    try:
        results = translator.translate_batch(req.q, req.source, req.target)
        return BatchTranslateResponse(translatedTexts=results)
    except Exception as e:
        logger.error(f"Batch translation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect", response_model=DetectResponse)
async def detect(req: DetectRequest):
    lang, confidence = translator.detect_language(req.q)
    return DetectResponse(language=lang, confidence=confidence)

@app.get("/languages", response_model=List[LanguageInfo])
async def languages():
    return [
        LanguageInfo(code="zho_Hans", name="Chinese (Simplified)"),
        LanguageInfo(code="zho_Hant", name="Chinese (Traditional)"),
        LanguageInfo(code="eng_Latn", name="English"),
        LanguageInfo(code="vie_Latn", name="Vietnamese"),
        LanguageInfo(code="jpn_Jpan", name="Japanese"),
        LanguageInfo(code="kor_Hang", name="Korean"),
        LanguageInfo(code="fra_Latn", name="French"),
        LanguageInfo(code="spa_Latn", name="Spanish"),
        LanguageInfo(code="deu_Latn", name="German"),
        LanguageInfo(code="rus_Cyrl", name="Russian"),
    ]

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": translator.model is not None}
