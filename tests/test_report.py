"""Tests for report module."""
from translator.report import TranslationReport


def test_report_add_translation():
    report = TranslationReport()
    report.add_translation("src/data/items.ts", 15, "铜矿石", "Quặng đồng")
    data = report.to_dict()
    assert data["summary"]["strings_translated"] == 1
    assert data["summary"]["files_modified"] == 1
    assert len(data["files"]) == 1
    assert data["files"][0]["path"] == "src/data/items.ts"

def test_report_add_error():
    report = TranslationReport()
    report.add_error("src/broken.ts", "API timeout")
    data = report.to_dict()
    assert data["summary"]["errors"] == 1
    assert len(data["errors"]) == 1

def test_report_add_skip():
    report = TranslationReport()
    report.add_skip("src/app.ts", 10, "myVariable")
    data = report.to_dict()
    assert data["summary"]["strings_skipped"] == 1

def test_report_multiple_files():
    report = TranslationReport()
    report.add_translation("a.ts", 1, "你好", "Xin chào")
    report.add_translation("b.ts", 2, "世界", "Thế giới")
    data = report.to_dict()
    assert data["summary"]["files_modified"] == 2
    assert data["summary"]["strings_translated"] == 2

def test_report_to_json():
    report = TranslationReport()
    report.add_translation("a.ts", 1, "你好", "Xin chào")
    json_str = report.to_json()
    assert '"Xin chào"' in json_str
