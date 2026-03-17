"""Tests for scanner module."""
import os
import tempfile
from translator.scanner import scan_files


def test_scan_finds_matching_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "src"))
        open(os.path.join(tmpdir, "src", "app.ts"), "w").close()
        open(os.path.join(tmpdir, "src", "style.css"), "w").close()
        open(os.path.join(tmpdir, "index.vue"), "w").close()
        files = scan_files(tmpdir, extensions=[".ts", ".vue"])
        names = [os.path.basename(f) for f in files]
        assert "app.ts" in names
        assert "index.vue" in names
        assert "style.css" not in names


def test_scan_excludes_directories():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "node_modules"))
        open(os.path.join(tmpdir, "node_modules", "lib.js"), "w").close()
        open(os.path.join(tmpdir, "app.js"), "w").close()
        files = scan_files(tmpdir, extensions=[".js"], excludes=["node_modules"])
        names = [os.path.basename(f) for f in files]
        assert "app.js" in names
        assert "lib.js" not in names


def test_scan_empty_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        files = scan_files(tmpdir, extensions=[".ts"])
        assert files == []
