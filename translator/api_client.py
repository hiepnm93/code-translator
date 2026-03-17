"""HTTP client for NLLB Translation API with batching and retry."""
import time
import logging
from typing import List
import requests
from translator.config import resolve_lang_code, DEFAULT_BATCH_SIZE, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


class TranslationError(Exception):
    pass


class NLLBClient:
    def __init__(self, base_url: str, batch_size: int = DEFAULT_BATCH_SIZE, timeout: int = DEFAULT_TIMEOUT, retries: int = 3):
        self.base_url = base_url.rstrip("/")
        self.batch_size = batch_size
        self.timeout = timeout
        self.retries = retries

    def _post(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        last_error = None
        for attempt in range(self.retries):
            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last_error = e
                if attempt < self.retries - 1:
                    wait = 2 ** attempt
                    logger.warning(f"API call failed (attempt {attempt + 1}), retrying in {wait}s: {e}")
                    time.sleep(wait)
        raise TranslationError(f"Failed after {self.retries} retries: {last_error}")

    def translate(self, text: str, source: str, target: str) -> str:
        payload = {"q": text, "source": resolve_lang_code(source), "target": resolve_lang_code(target)}
        result = self._post("/translate", payload)
        return result["translatedText"]

    def translate_batch(self, texts: List[str], source: str, target: str) -> List[str]:
        source_code = resolve_lang_code(source)
        target_code = resolve_lang_code(target)
        all_results: List[str] = []
        for i in range(0, len(texts), self.batch_size):
            chunk = texts[i:i + self.batch_size]
            payload = {"q": chunk, "source": source_code, "target": target_code}
            try:
                result = self._post("/translate/batch", payload)
                all_results.extend(result["translatedTexts"])
            except TranslationError as e:
                logger.error(f"Batch {i // self.batch_size} failed: {e}")
                all_results.extend([""] * len(chunk))
        return all_results

    def detect(self, text: str) -> tuple[str, float]:
        result = self._post("/detect", {"q": text})
        return result["language"], result["confidence"]
