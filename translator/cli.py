"""CLI entry point — argument parsing and main translation pipeline."""
import argparse
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from translator.config import (
    DEFAULT_API_URL,
    DEFAULT_BATCH_SIZE,
    DEFAULT_CONCURRENCY,
    DEFAULT_EXTENSIONS,
    DEFAULT_EXCLUDES,
)
from translator.scanner import scan_files
from translator.extractor import extract_strings
from translator.filter import classify_string, segment_mixed, contains_cjk
from translator.api_client import NLLBClient, TranslationError
from translator.replacer import replace_strings, write_file_atomic
from translator.report import TranslationReport

logger = logging.getLogger(__name__)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Translate source code strings between languages."
    )
    parser.add_argument("--path", required=True, help="Project directory to scan")
    parser.add_argument("--source", required=True, help="Source language (e.g., zh, en)")
    parser.add_argument("--target", required=True, help="Target language (e.g., vi)")
    parser.add_argument("--source-code", help="Direct NLLB code override (e.g., zho_Hant)")
    parser.add_argument("--api", default=DEFAULT_API_URL, help="NLLB API URL")
    parser.add_argument(
        "--ext",
        default=",".join(DEFAULT_EXTENSIONS),
        help="File extensions to scan (comma-separated)",
    )
    parser.add_argument(
        "--exclude",
        default=",".join(DEFAULT_EXCLUDES),
        help="Directories to exclude (comma-separated)",
    )
    parser.add_argument(
        "--json-keys",
        help="Allowlist of JSON keys to translate (comma-separated)",
    )
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    parser.add_argument("--report", help="Output JSON report to file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args(argv)


def _translate_mixed_string(text, client, source, target):
    """Handle mixed CJK+non-CJK strings by segmenting and translating CJK parts."""
    segments = segment_mixed(text)
    if len(segments) <= 1:
        return client.translate(text, source, target)

    cjk_texts = [s["text"] for s in segments if s["type"] == "cjk"]
    if not cjk_texts:
        return text

    translated_cjk = client.translate_batch(cjk_texts, source, target)
    cjk_iter = iter(translated_cjk)

    result_parts = []
    for seg in segments:
        if seg["type"] == "cjk":
            result_parts.append(next(cjk_iter))
        else:
            result_parts.append(seg["text"])
    return "".join(result_parts)


def _process_file(filepath, args, client, report, json_keys):
    """Process a single file: extract, filter, translate, replace."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        logger.warning(f"Skipping non-UTF-8 file: {filepath}")
        report.add_error(filepath, "Non-UTF-8 encoding")
        return 0

    _, ext = os.path.splitext(filepath)
    source_lang = args.source_code if args.source_code else args.source

    matches = extract_strings(content, ext, json_keys=json_keys)
    if not matches:
        return 0

    to_translate = []
    for match in matches:
        cls = classify_string(match.text, args.source)
        if cls == "translate":
            to_translate.append(match)
        else:
            report.add_skip(filepath, match.line, match.text)

    if not to_translate:
        return 0

    pure_strings = []
    mixed_strings = []
    for match in to_translate:
        segs = segment_mixed(match.text)
        if len(segs) > 1 and any(s["type"] == "other" for s in segs):
            mixed_strings.append(match)
        else:
            pure_strings.append(match)

    translations = {}

    if pure_strings:
        texts = [m.text for m in pure_strings]
        try:
            translated = client.translate_batch(texts, source_lang, args.target)
            for match, trans in zip(pure_strings, translated):
                if trans and trans != match.text:
                    translations[match.text] = trans
        except TranslationError as e:
            logger.error(f"Batch translation failed for {filepath}: {e}")
            report.add_error(filepath, str(e))

    for match in mixed_strings:
        try:
            trans = _translate_mixed_string(match.text, client, source_lang, args.target)
            if trans and trans != match.text:
                translations[match.text] = trans
        except TranslationError as e:
            logger.error(f"Mixed string translation failed: {match.text}: {e}")

    if not translations:
        return 0

    for match in to_translate:
        if match.text in translations:
            report.add_translation(filepath, match.line, match.text, translations[match.text])

    new_content = replace_strings(content, to_translate, translations)

    if args.dry_run:
        rel_path = os.path.relpath(filepath, args.path)
        print(f"\n--- {rel_path} ---")
        for orig, trans in translations.items():
            print(f"  {orig} → {trans}")
    else:
        write_file_atomic(filepath, new_content)
        logger.info(f"Updated {filepath} ({len(translations)} strings)")

    return len(translations)


def main(argv=None):
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    extensions = [e.strip() for e in args.ext.split(",")]
    excludes = [e.strip() for e in args.exclude.split(",")]
    json_keys = [k.strip() for k in args.json_keys.split(",")] if args.json_keys else None

    logger.info(f"Scanning {args.path} for {extensions}...")
    files = scan_files(args.path, extensions, excludes)
    logger.info(f"Found {len(files)} files")

    if not files:
        logger.info("No files found. Exiting.")
        return

    client = NLLBClient(args.api, batch_size=args.batch_size)
    report = TranslationReport()
    report.files_scanned = len(files)

    total_translated = 0

    if args.concurrency > 1:
        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            futures = {
                executor.submit(_process_file, fp, args, client, report, json_keys): fp
                for fp in files
            }
            for future in as_completed(futures):
                try:
                    total_translated += future.result()
                except Exception as e:
                    logger.error(f"Error processing {futures[future]}: {e}")
                    report.add_error(futures[future], str(e))
    else:
        for filepath in files:
            total_translated += _process_file(filepath, args, client, report, json_keys)

    logger.info(f"\nDone! {total_translated} strings translated across {len(files)} files")

    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report.to_json())
        logger.info(f"Report saved to {args.report}")
