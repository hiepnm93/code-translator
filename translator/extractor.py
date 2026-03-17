"""Hybrid regex + AST string extraction from source code."""
import json
import re
from dataclasses import dataclass
from typing import List


@dataclass
class StringMatch:
    text: str
    line: int
    start: int
    end: int
    delimiter: str
    context: str


_TEMPLATE_TEXT = re.compile(r">([^<>]+)<")
_ATTR_PATTERN = re.compile(r'(?:placeholder|title|label|alt|aria-label)\s*=\s*"([^"]+)"')
_COMMENT_SINGLE = re.compile(r"//\s*(.+)$", re.MULTILINE)
_COMMENT_BLOCK = re.compile(r"/\*\s*([\s\S]*?)\s*\*/")
_COMMENT_HTML = re.compile(r"<!--\s*([\s\S]*?)\s*-->")
_STRING_DQ = re.compile(r'"((?:[^"\\]|\\.)*)"')
_STRING_SQ = re.compile(r"'((?:[^'\\]|\\.)*)'")
_STRING_BT = re.compile(r"`((?:[^`\\]|\\.)*)`")
_IMPORT_LINE = re.compile(r"^\s*import\s+.*from\s+", re.MULTILINE)
_HAS_CJK = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")


def _offset_to_line(content: str, offset: int) -> int:
    return content[:offset].count("\n") + 1


def _extract_vue_template(content: str) -> str:
    match = re.search(r"<template[^>]*>([\s\S]*?)</template>", content)
    return match.group(1) if match else ""


def _extract_vue_script(content: str) -> str:
    match = re.search(r"<script[^>]*>([\s\S]*?)</script>", content)
    return match.group(1) if match else ""


def _is_import_context(content: str, offset: int) -> bool:
    line_start = content.rfind("\n", 0, offset) + 1
    line = content[line_start:content.find("\n", offset)]
    return bool(_IMPORT_LINE.match(line))


def _extract_regex_strings(content: str, ext: str) -> List[StringMatch]:
    matches: List[StringMatch] = []
    if ext == ".vue":
        template = _extract_vue_template(content)
        if template:
            tmpl_start = content.find(template)
            for m in _TEMPLATE_TEXT.finditer(template):
                text = m.group(1).strip()
                if text:
                    offset = tmpl_start + m.start(1)
                    matches.append(StringMatch(text=text, line=_offset_to_line(content, offset), start=offset, end=offset + len(text), delimiter="", context="template"))
        for m in _ATTR_PATTERN.finditer(content):
            text = m.group(1).strip()
            if text:
                matches.append(StringMatch(text=text, line=_offset_to_line(content, m.start(1)), start=m.start(1), end=m.end(1), delimiter='"', context="template"))

    if ext != ".json":
        for m in _COMMENT_SINGLE.finditer(content):
            text = m.group(1).strip()
            if text:
                matches.append(StringMatch(text=text, line=_offset_to_line(content, m.start(1)), start=m.start(1), end=m.end(1), delimiter="", context="comment"))
        for m in _COMMENT_BLOCK.finditer(content):
            text = m.group(1).strip()
            if text:
                matches.append(StringMatch(text=text, line=_offset_to_line(content, m.start(1)), start=m.start(1), end=m.end(1), delimiter="", context="comment"))
        if ext == ".vue":
            for m in _COMMENT_HTML.finditer(content):
                text = m.group(1).strip()
                if text:
                    matches.append(StringMatch(text=text, line=_offset_to_line(content, m.start(1)), start=m.start(1), end=m.end(1), delimiter="", context="comment"))
    return matches


def _extract_script_strings(content: str, ext: str) -> List[StringMatch]:
    if ext == ".vue":
        script = _extract_vue_script(content)
        if not script:
            return []
        script_offset = content.find(script)
    else:
        script = content
        script_offset = 0

    matches: List[StringMatch] = []
    for pattern, delimiter in [(_STRING_DQ, '"'), (_STRING_SQ, "'"), (_STRING_BT, "`")]:
        for m in pattern.finditer(script):
            text = m.group(1)
            if not text.strip():
                continue
            abs_offset = script_offset + m.start(1)
            if _is_import_context(content, abs_offset):
                continue
            matches.append(StringMatch(text=text, line=_offset_to_line(content, abs_offset), start=abs_offset, end=abs_offset + len(text), delimiter=delimiter, context="script"))
    return matches


def _extract_json_strings(content: str, json_keys: List[str] | None = None) -> List[StringMatch]:
    matches: List[StringMatch] = []
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return matches

    search_offset = 0

    def _walk(obj, path=""):
        nonlocal search_offset
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.strip():
                    if json_keys and key not in json_keys:
                        continue
                    if not json_keys and not _HAS_CJK.search(value):
                        continue
                    search = f'"{value}"'
                    key_search = f'"{key}"'
                    key_idx = content.find(key_search, search_offset)
                    if key_idx >= 0:
                        idx = content.find(search, key_idx + len(key_search))
                        if idx >= 0:
                            val_start = idx + 1
                            search_offset = idx + len(search)
                            matches.append(StringMatch(text=value, line=_offset_to_line(content, val_start), start=val_start, end=val_start + len(value), delimiter='"', context="json"))
                elif isinstance(value, (dict, list)):
                    _walk(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for item in obj:
                _walk(item, path)

    _walk(data)
    return matches


def extract_strings(content: str, ext: str, json_keys: List[str] | None = None) -> List[StringMatch]:
    if ext == ".json":
        return _extract_json_strings(content, json_keys=json_keys)

    matches: List[StringMatch] = []
    matches.extend(_extract_regex_strings(content, ext))
    matches.extend(_extract_script_strings(content, ext))

    seen = set()
    unique = []
    for m in matches:
        key = (m.start, m.end)
        if key not in seen:
            seen.add(key)
            unique.append(m)
    return sorted(unique, key=lambda m: m.start)
