"""NLLB model wrapper — load and translate."""
import logging
from typing import List
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

logger = logging.getLogger(__name__)
MODEL_NAME = "facebook/nllb-200-distilled-600M"

class NLLBTranslator:
    def __init__(self):
        self.model = None
        self.tokenizer = None

    def load(self):
        logger.info(f"Loading model: {MODEL_NAME}")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
        self.model.eval()
        logger.info("Model loaded successfully")

    def translate(self, text: str, source: str, target: str) -> str:
        self.tokenizer.src_lang = source
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        target_lang_id = self.tokenizer.convert_tokens_to_ids(target)
        generated = self.model.generate(**inputs, forced_bos_token_id=target_lang_id, max_new_tokens=256)
        result = self.tokenizer.batch_decode(generated, skip_special_tokens=True)
        return result[0] if result else ""

    def translate_batch(self, texts: List[str], source: str, target: str) -> List[str]:
        if not texts:
            return []
        self.tokenizer.src_lang = source
        inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
        target_lang_id = self.tokenizer.convert_tokens_to_ids(target)
        generated = self.model.generate(**inputs, forced_bos_token_id=target_lang_id, max_new_tokens=256)
        return self.tokenizer.batch_decode(generated, skip_special_tokens=True)

    def detect_language(self, text: str) -> tuple[str, float]:
        cjk_count = sum(1 for c in text if 0x4E00 <= ord(c) <= 0x9FFF)
        total = len(text.strip())
        if total == 0:
            return "und", 0.0
        if cjk_count / total > 0.3:
            return "zho_Hans", min(cjk_count / total + 0.2, 1.0)
        return "eng_Latn", 0.7

translator = NLLBTranslator()
