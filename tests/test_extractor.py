"""Tests for hybrid string extractor."""
from translator.extractor import extract_strings, StringMatch


def test_extract_vue_template_text():
    content = '<template><div>你好世界</div></template>'
    matches = extract_strings(content, ".vue")
    texts = [m.text for m in matches]
    assert "你好世界" in texts

def test_extract_vue_attribute():
    content = '<template><input placeholder="请输入名称" /></template>'
    matches = extract_strings(content, ".vue")
    texts = [m.text for m in matches]
    assert "请输入名称" in texts

def test_extract_js_string_literal():
    content = 'const name = "铜矿石";'
    matches = extract_strings(content, ".ts")
    texts = [m.text for m in matches]
    assert "铜矿石" in texts

def test_extract_single_quote_string():
    content = "const msg = '你好';"
    matches = extract_strings(content, ".ts")
    texts = [m.text for m in matches]
    assert "你好" in texts

def test_extract_template_literal():
    content = 'const msg = `欢迎来到游戏`;'
    matches = extract_strings(content, ".ts")
    texts = [m.text for m in matches]
    assert "欢迎来到游戏" in texts

def test_extract_comment_single_line():
    content = "// 这是一个注释"
    matches = extract_strings(content, ".ts")
    texts = [m.text for m in matches]
    assert "这是一个注释" in texts

def test_extract_comment_block():
    content = "/* 块注释 */"
    matches = extract_strings(content, ".ts")
    texts = [m.text for m in matches]
    assert "块注释" in texts

def test_extract_html_comment():
    content = "<!-- HTML注释 -->"
    matches = extract_strings(content, ".vue")
    texts = [m.text for m in matches]
    assert "HTML注释" in texts

def test_skip_import_path():
    content = 'import foo from "./path/to/module";'
    matches = extract_strings(content, ".ts")
    texts = [m.text for m in matches]
    assert "./path/to/module" not in texts

def test_extract_json_values():
    content = '{"name": "铜矿石", "id": "copper_ore", "count": 5}'
    matches = extract_strings(content, ".json")
    texts = [m.text for m in matches]
    assert "铜矿石" in texts
    assert "copper_ore" not in texts

def test_string_match_has_position():
    content = 'const x = "你好";'
    matches = extract_strings(content, ".ts")
    assert len(matches) > 0
    m = matches[0]
    assert m.line >= 1
    assert m.start >= 0
    assert m.end > m.start
    assert m.delimiter in ('"', "'", "`", "")
