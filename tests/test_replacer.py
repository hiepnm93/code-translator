"""Tests for replacer module."""
import os
import tempfile
from translator.replacer import replace_strings
from translator.extractor import StringMatch


def test_replace_double_quoted_string():
    content = 'const name = "铜矿石";'
    matches = [StringMatch(text="铜矿石", line=1, start=14, end=17, delimiter='"', context="script")]
    translations = {"铜矿石": "Quặng đồng"}
    result = replace_strings(content, matches, translations)
    assert result == 'const name = "Quặng đồng";'


def test_replace_single_quoted_string():
    content = "const msg = '你好';"
    matches = [StringMatch(text="你好", line=1, start=13, end=15, delimiter="'", context="script")]
    translations = {"你好": "Xin chào"}
    result = replace_strings(content, matches, translations)
    assert result == "const msg = 'Xin chào';"


def test_replace_preserves_untranslated():
    content = 'const a = "hello";\nconst b = "铜矿石";'
    matches = [StringMatch(text="铜矿石", line=2, start=30, end=33, delimiter='"', context="script")]
    translations = {"铜矿石": "Quặng đồng"}
    result = replace_strings(content, matches, translations)
    assert '"hello"' in result
    assert '"Quặng đồng"' in result


def test_replace_escapes_quotes_in_translation():
    content = 'const msg = "你好";'
    matches = [StringMatch(text="你好", line=1, start=13, end=15, delimiter='"', context="script")]
    translations = {"你好": 'Xin "chào"'}
    result = replace_strings(content, matches, translations)
    assert r'Xin \"chào\"' in result


def test_replace_template_text():
    content = "<div>你好世界</div>"
    matches = [StringMatch(text="你好世界", line=1, start=5, end=9, delimiter="", context="template")]
    translations = {"你好世界": "Xin chào thế giới"}
    result = replace_strings(content, matches, translations)
    assert "<div>Xin chào thế giới</div>" == result


def test_replace_skips_missing_translation():
    content = 'const a = "你好";'
    matches = [StringMatch(text="你好", line=1, start=11, end=13, delimiter='"', context="script")]
    translations = {}
    result = replace_strings(content, matches, translations)
    assert result == content


def test_write_file_atomic(tmp_path):
    from translator.replacer import write_file_atomic
    filepath = str(tmp_path / "test.txt")
    write_file_atomic(filepath, "hello world")
    with open(filepath) as f:
        assert f.read() == "hello world"
