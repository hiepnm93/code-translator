"""Unicode-based language detection and string classification."""
import re
from typing import List, TypedDict


class Segment(TypedDict):
    text: str
    type: str  # "cjk" or "other"


_VIET_CHARS = set("àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"
                  "ÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ")

_URL_PATTERN = re.compile(r"^https?://|^ftp://|^//")
_PATH_PATTERN = re.compile(r"^[./\\].*\.\w+$")
_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{3,8}$")


def contains_cjk(text: str) -> bool:
    for char in text:
        cp = ord(char)
        if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0x20000 <= cp <= 0x2A6DF:
            return True
    return False


def _has_vietnamese(text: str) -> bool:
    return bool(_VIET_CHARS & set(text))


def classify_string(text: str, source_lang: str = "zh") -> str:
    text = text.strip()
    if not text:
        return "skip"
    if _URL_PATTERN.match(text):
        return "skip"
    if _PATH_PATTERN.match(text):
        return "skip"
    if _HEX_COLOR_PATTERN.match(text):
        return "skip"
    if _IDENTIFIER_PATTERN.match(text):
        return "skip"

    if source_lang in ("zh", "zho_Hans", "zho_Hant"):
        if contains_cjk(text):
            return "translate"
        if _has_vietnamese(text):
            return "skip"
        return "skip"

    if source_lang in ("en", "eng_Latn"):
        if _has_vietnamese(text):
            return "skip"
        if re.search(r"[a-zA-Z]", text) and not _IDENTIFIER_PATTERN.match(text):
            return "translate"

    return "skip"


def segment_mixed(text: str) -> List[Segment]:
    segments: List[Segment] = []
    current_text = ""
    current_type = ""
    for char in text:
        cp = ord(char)
        is_cjk = 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0x20000 <= cp <= 0x2A6DF
        char_type = "cjk" if is_cjk else "other"
        if char_type != current_type and current_text:
            segments.append(Segment(text=current_text, type=current_type))
            current_text = ""
        current_type = char_type
        current_text += char
    if current_text:
        segments.append(Segment(text=current_text, type=current_type))
    return segments
