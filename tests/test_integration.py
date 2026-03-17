"""Integration test — full pipeline with mocked API."""
import os
import tempfile
from unittest.mock import patch, MagicMock

from translator.cli import main


def _mock_translate_batch(texts, source, target):
    mapping = {
        "铜矿石": "Quặng đồng",
        "你好": "Xin chào",
        "一种矿石": "Một loại quặng",
        "块注释": "Chú thích khối",
    }
    return [mapping.get(t, f"[translated:{t}]") for t in texts]


@patch("translator.cli.NLLBClient")
def test_full_pipeline_dry_run(MockClient):
    client_instance = MockClient.return_value
    client_instance.translate_batch.side_effect = _mock_translate_batch

    with tempfile.TemporaryDirectory() as tmpdir:
        ts_file = os.path.join(tmpdir, "items.ts")
        with open(ts_file, "w", encoding="utf-8") as f:
            f.write('export const items = [\n')
            f.write('  { name: "铜矿石", description: "一种矿石" },\n')
            f.write('];\n')

        main([
            "--path", tmpdir,
            "--source", "zh",
            "--target", "vi",
            "--api", "http://localhost:5000",
            "--ext", ".ts",
            "--dry-run",
            "--concurrency", "1",
        ])

        with open(ts_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "铜矿石" in content  # not modified in dry-run


@patch("translator.cli.NLLBClient")
def test_full_pipeline_write(MockClient):
    client_instance = MockClient.return_value
    client_instance.translate_batch.side_effect = _mock_translate_batch

    with tempfile.TemporaryDirectory() as tmpdir:
        ts_file = os.path.join(tmpdir, "items.ts")
        with open(ts_file, "w", encoding="utf-8") as f:
            f.write('export const items = [\n')
            f.write('  { name: "铜矿石", description: "一种矿石" },\n')
            f.write('];\n')

        main([
            "--path", tmpdir,
            "--source", "zh",
            "--target", "vi",
            "--api", "http://localhost:5000",
            "--ext", ".ts",
            "--concurrency", "1",
        ])

        with open(ts_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Quặng đồng" in content
        assert "Một loại quặng" in content
        assert "铜矿石" not in content


@patch("translator.cli.NLLBClient")
def test_pipeline_with_report(MockClient):
    client_instance = MockClient.return_value
    client_instance.translate_batch.side_effect = _mock_translate_batch

    with tempfile.TemporaryDirectory() as tmpdir:
        ts_file = os.path.join(tmpdir, "test.ts")
        with open(ts_file, "w", encoding="utf-8") as f:
            f.write('const msg = "你好";\n')

        report_file = os.path.join(tmpdir, "report.json")

        main([
            "--path", tmpdir,
            "--source", "zh",
            "--target", "vi",
            "--api", "http://localhost:5000",
            "--ext", ".ts",
            "--report", report_file,
            "--concurrency", "1",
        ])

        assert os.path.exists(report_file)
        import json
        with open(report_file) as f:
            report = json.load(f)
        assert report["summary"]["strings_translated"] >= 1
