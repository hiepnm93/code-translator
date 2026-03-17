# Code Translator

Python CLI tool + self-hosted NLLB Translation API to translate source code strings between languages. Designed for translating hardcoded text in projects like Vue.js games, web apps, etc.

## Features

- Scan project files (`.vue`, `.ts`, `.js`, `.jsx`, `.tsx`, `.py`, `.json`)
- Hybrid string extraction: regex for templates/comments, AST-aware for script blocks
- Unicode-based language detection (CJK, Vietnamese, Latin)
- Mixed string segmentation (translate only Chinese portions in mixed text)
- Self-hosted NLLB API via Docker (no external API keys needed)
- Batch translation with retry and concurrent file processing
- Atomic file writes with delimiter preservation
- Dry-run mode and JSON reports

## Architecture

```
┌─────────────────────────────────────────────┐
│              translate-tool (CLI)            │
│                                             │
│  Scanner ──→ Extractor ──→ Filter           │
│                                             │
│       Translator ──→ Replacer               │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
          ┌─────────────────┐
          │  NLLB API       │
          │  (Docker)       │
          │  POST /translate│
          └─────────────────┘
```

## Quick Start

### 1. Start the Translation API

```bash
docker compose up -d
# First run downloads the model (~1.2GB), wait for "Model loaded successfully"
docker compose logs -f nllb-api
```

### 2. Install the CLI

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Translate a project

```bash
# Dry run (preview only)
python translate.py \
  --path ./your-project/src \
  --source zh \
  --target vi \
  --dry-run

# Apply translations
python translate.py \
  --path ./your-project/src \
  --source zh \
  --target vi

# With report
python translate.py \
  --path ./your-project/src \
  --source zh \
  --target vi \
  --report output.json
```

## CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `--path` | Project directory to scan | (required) |
| `--source` | Source language (`zh`, `en`, etc.) | (required) |
| `--target` | Target language (`vi`, `en`, etc.) | (required) |
| `--source-code` | Direct NLLB code override (e.g., `zho_Hant`) | - |
| `--api` | NLLB API URL | `http://localhost:5000` |
| `--ext` | File extensions (comma-separated) | `.vue,.ts,.js,.jsx,.tsx,.py,.json` |
| `--exclude` | Directories to exclude | `node_modules,dist,.git,__pycache__,.venv` |
| `--json-keys` | Allowlist of JSON keys to translate | all string values |
| `--batch-size` | Strings per API request | `32` |
| `--concurrency` | Parallel file processing threads | `4` |
| `--dry-run` | Preview changes without writing | `false` |
| `--report` | Output JSON report file path | - |
| `--verbose` | Enable debug logging | `false` |

## Supported Languages

| Code | Language |
|------|----------|
| `zh` | Chinese (Simplified) |
| `zh-tw` | Chinese (Traditional) |
| `en` | English |
| `vi` | Vietnamese |
| `ja` | Japanese |
| `ko` | Korean |
| `fr` | French |
| `es` | Spanish |
| `de` | German |
| `ru` | Russian |

NLLB supports 200+ languages. Use `--source-code` with FLORES-200 codes for unlisted languages.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/translate` | Single translation |
| `POST` | `/translate/batch` | Batch translation (max 64) |
| `POST` | `/detect` | Language detection |
| `GET` | `/languages` | List supported languages |
| `GET` | `/health` | Health check |

## Translation Model

Uses [Meta's NLLB-200-distilled-600M](https://huggingface.co/facebook/nllb-200-distilled-600M) — a 600M parameter neural machine translation model supporting 200+ languages. Runs on CPU (~1.2GB RAM).

## Running Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

## License

MIT
