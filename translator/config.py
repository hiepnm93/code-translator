"""Configuration defaults and language code mapping."""

# NLLB FLORES-200 language code mapping
LANG_MAP = {
    "zh": "zho_Hans",
    "zh-tw": "zho_Hant",
    "en": "eng_Latn",
    "vi": "vie_Latn",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "fr": "fra_Latn",
    "es": "spa_Latn",
    "de": "deu_Latn",
    "ru": "rus_Cyrl",
}

DEFAULT_EXTENSIONS = [".vue", ".ts", ".js", ".jsx", ".tsx", ".py", ".json"]
DEFAULT_EXCLUDES = ["node_modules", "dist", ".git", "__pycache__", ".venv"]
DEFAULT_BATCH_SIZE = 32
DEFAULT_CONCURRENCY = 4
DEFAULT_TIMEOUT = 60
DEFAULT_API_URL = "http://localhost:5000"
MAX_BATCH_SIZE = 64
MAX_REQUEST_BODY_KB = 10


def resolve_lang_code(short_code: str) -> str:
    if "_" in short_code:
        return short_code
    code = LANG_MAP.get(short_code.lower())
    if code is None:
        raise ValueError(
            f"Unknown language code: '{short_code}'. "
            f"Available: {', '.join(LANG_MAP.keys())}. "
            f"Or use NLLB code directly (e.g., 'vie_Latn')."
        )
    return code
