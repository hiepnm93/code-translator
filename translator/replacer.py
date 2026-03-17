"""Atomic file replacement with delimiter preservation."""
import os
import tempfile
from typing import Dict, List
from translator.extractor import StringMatch


def _escape_for_delimiter(text: str, delimiter: str) -> str:
    if delimiter == '"':
        return text.replace("\\", "\\\\").replace('"', '\\"')
    elif delimiter == "'":
        return text.replace("\\", "\\\\").replace("'", "\\'")
    elif delimiter == "`":
        return text.replace("\\", "\\\\").replace("`", "\\`")
    return text


def replace_strings(content: str, matches: List[StringMatch], translations: Dict[str, str]) -> str:
    sorted_matches = sorted(matches, key=lambda m: m.start, reverse=True)
    for match in sorted_matches:
        translated = translations.get(match.text)
        if not translated or translated == match.text:
            continue
        escaped = _escape_for_delimiter(translated, match.delimiter)
        content = content[:match.start] + escaped + content[match.end:]
    return content


def write_file_atomic(filepath: str, content: str, encoding: str = "utf-8") -> None:
    dirpath = os.path.dirname(filepath) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dirpath, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
        os.replace(tmp_path, filepath)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
