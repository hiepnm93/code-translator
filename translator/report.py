"""JSON report generation for translation results."""
import json
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class FileReport:
    path: str
    translations: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class TranslationReport:
    def __init__(self):
        self.files_scanned: int = 0
        self._files: Dict[str, FileReport] = {}
        self._errors: List[Dict] = []
        self._strings_skipped: int = 0

    def _get_file(self, path: str) -> FileReport:
        if path not in self._files:
            self._files[path] = FileReport(path=path)
        return self._files[path]

    def add_translation(self, path: str, line: int, original: str, translated: str):
        f = self._get_file(path)
        f.translations.append({"line": line, "original": original, "translated": translated})

    def add_error(self, path: str, error: str):
        self._errors.append({"file": path, "error": error})

    def add_skip(self, path: str, line: int, text: str):
        self._strings_skipped += 1

    def to_dict(self) -> dict:
        total_translated = sum(len(f.translations) for f in self._files.values())
        return {
            "summary": {
                "files_scanned": self.files_scanned,
                "files_modified": len([f for f in self._files.values() if f.translations]),
                "strings_translated": total_translated,
                "strings_skipped": self._strings_skipped,
                "errors": len(self._errors),
            },
            "files": [{"path": f.path, "translations": f.translations, "errors": f.errors} for f in self._files.values() if f.translations],
            "errors": self._errors,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
