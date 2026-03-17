"""Tests for language filter module."""
from translator.filter import contains_cjk, classify_string, segment_mixed


def test_contains_cjk_chinese():
    assert contains_cjk("你好世界") is True

def test_contains_cjk_english():
    assert contains_cjk("Hello World") is False

def test_contains_cjk_mixed():
    assert contains_cjk("Hello 你好") is True

def test_contains_cjk_vietnamese():
    assert contains_cjk("Xin chào thế giới") is False

def test_classify_chinese():
    assert classify_string("铜矿石") == "translate"

def test_classify_english():
    assert classify_string("copper ore", source_lang="en") == "translate"

def test_classify_vietnamese():
    assert classify_string("Quặng đồng") == "skip"

def test_classify_pure_ascii_identifier():
    assert classify_string("myVariable") == "skip"

def test_classify_url():
    assert classify_string("https://example.com") == "skip"

def test_classify_file_path():
    assert classify_string("./src/main.ts") == "skip"

def test_classify_empty():
    assert classify_string("") == "skip"

def test_segment_mixed_chinese_english():
    segments = segment_mixed("已经 Level 5 了")
    assert len(segments) >= 2
    assert any(s["type"] == "cjk" for s in segments)
    assert any(s["type"] == "other" for s in segments)

def test_segment_pure_chinese():
    segments = segment_mixed("你好世界")
    assert len(segments) == 1
    assert segments[0]["type"] == "cjk"
