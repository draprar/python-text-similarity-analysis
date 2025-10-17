from pathlib import Path
import argparse
import logging
import sys
from enum import IntEnum

from diff_engine import compare_blocks
from report_builder import generate_html_report, generate_json_report

# extractors
from extractors.extract_docx import DocxExtractor
from extractors.extract_txt import TxtExtractor
from extractors.extract_xlsx import XlsxExtractor

_LOGGER = logging.getLogger(__name__)


class ExitCode(IntEnum):
    OK = 0
    OLD_NOT_FOUND = 2
    NEW_NOT_FOUND = 3
    PARSE_ERROR = 4
    HTML_ERROR = 5
    JSON_ERROR = 6

EXTRACTOR_MAP = {
    ".docx": DocxExtractor,
    ".doc": DocxExtractor,
    ".txt": TxtExtractor,
    ".xlsx": XlsxExtractor,
    ".xls": XlsxExtractor,
}


def parse_args():
    parser = argparse.ArgumentParser(description="Compare two files and generate a report.")
    parser.add_argument("old", type=Path, help="Old file")
    parser.add_argument("new", type=Path, help="New file")
    parser.add_argument("-o", "--output", type=Path, default=Path("report.html"), help="Output HTML file")
    parser.add_argument("--json", type=Path, default=None, help="(optional) save result as JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable DEBUG logging")
    return parser.parse_args()


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s: %(message)s")


def choose_extractor(path: Path):
    ext = path.suffix.lower()
    cls = EXTRACTOR_MAP.get(ext)
    if cls is None:
        raise ValueError(
            f"No extractor available for extension: {ext}. "
            "Supported formats: .docx, .doc, .xlsx, .txt"
        )
    return cls()


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)

    if not args.old.exists():
        _LOGGER.error("Old file does not exist: %s", args.old)
        return ExitCode.OLD_NOT_FOUND
    if not args.new.exists():
        _LOGGER.error("New file does not exist: %s", args.new)
        return ExitCode.NEW_NOT_FOUND

    try:
        old_ex = choose_extractor(args.old)
        new_ex = choose_extractor(args.new)

        old_blocks = old_ex.extract_blocks(args.old)
        new_blocks = new_ex.extract_blocks(args.new)
    except Exception as exc:
        _LOGGER.exception("Error while parsing documents: %s", exc)
        return ExitCode.PARSE_ERROR

    diffs = compare_blocks(old_blocks, new_blocks)

    try:
        generate_html_report(diffs, output_path=str(args.output))
        _LOGGER.info("HTML report generated: %s", args.output)
    except Exception:
        _LOGGER.exception("Error while saving HTML report")
        return ExitCode.HTML_ERROR

    if args.json:
        try:
            generate_json_report(diffs, output_path=str(args.json))
            _LOGGER.info("JSON report generated: %s", args.json)
        except Exception:
            _LOGGER.exception("Error while saving JSON report")
            return ExitCode.JSON_ERROR

    return ExitCode.OK


if __name__ == "__main__":
    sys.exit(int(main()))
