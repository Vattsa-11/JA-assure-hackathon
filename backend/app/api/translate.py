import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.translation_service import (
    get_translations,
    warm_language_caches,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Translation"])


class TranslateRequest(BaseModel):
    texts: list[str]
    target_language: str


class TranslateResponse(BaseModel):
    translations: dict[str, str]
    target_language: str


@router.post("/translate", response_model=TranslateResponse)
def translate_texts(request: TranslateRequest, db: Session = Depends(get_db)):
    """Translate a batch of dynamic texts (drafts, emails, reasons, topics).

    Cache-first: repeated strings never hit the LLM again.
    """
    if not request.texts:
        return TranslateResponse(translations={}, target_language=request.target_language)

    try:
        translations = get_translations(db, request.texts, request.target_language)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return TranslateResponse(translations=translations, target_language=request.target_language)


@router.post("/translate/warm")
def warm_caches(background_tasks: BackgroundTasks, languages: list[str] | None = None):
    """Pre-translate all DB content into the given languages (default: all).

    Returns immediately; the warm-up runs as a background task. Once warm,
    switching UI language renders dynamic content instantly from cache.
    """
    background_tasks.add_task(warm_language_caches, languages)
    return {"message": "Translation warm-up started in background."}
