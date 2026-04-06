"""Catalog source audio files for later batch processing."""

from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from vc_clean_audio.bootstrap import add_common_arguments, load_config_with_logging
from vc_clean_audio.catalog_data import normalize_catalog_row, write_catalog_rows
from vc_clean_audio.config import AppConfig
from vc_clean_audio.logging_utils import configure_logging, log_config_summary

LOGGER = logging.getLogger(__name__)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Register command-line arguments for this step."""
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of files to catalog.",
    )
    parser.add_argument(
        "--output-csv",
        default=None,
        help="Optional CSV output path. Defaults to the configured catalog output path.",
    )


def scan_audio_files(config: AppConfig, limit: int | None = None) -> list[dict[str, object]]:
    """Scan the configured audio directory and build catalog rows."""
    input_dir = config.paths.input_audio_dir
    if not input_dir.exists():
        raise FileNotFoundError(f"Input audio directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input audio path is not a directory: {input_dir}")

    catalog_settings = config.pipeline_for("catalog")
    include_extensions = {
        extension.lower()
        for extension in catalog_settings.get("include_extensions", [])
        if extension
    }
    recursive = bool(catalog_settings.get("recursive", True))

    iterator = sorted(input_dir.rglob("*") if recursive else input_dir.glob("*"))
    discovered_at = datetime.now(timezone.utc).isoformat()

    rows: list[dict[str, object]] = []
    for path in iterator:
        if not path.is_file():
            continue

        if include_extensions and path.suffix.lower() not in include_extensions:
            continue

        try:
            stat = path.stat()
        except OSError as exc:
            LOGGER.warning("Skipping unreadable file %s: %s", path, exc)
            continue

        rows.append(
            normalize_catalog_row(
                {
                    "source_path": str(path),
                    "relative_path": str(path.relative_to(input_dir)),
                    "filename": path.name,
                    "extension": path.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "discovered_at": discovered_at,
                }
            )
        )

        if limit is not None and len(rows) >= limit:
            break

    return rows


def write_catalog(rows: list[dict[str, object]], output_path: Path) -> None:
    """Write the catalog rows to CSV."""
    write_catalog_rows(rows, output_path)


def log_catalog_summary(rows: list[dict[str, object]], output_path: Path) -> None:
    """Log a compact summary of the generated catalog."""
    extension_counts = Counter(str(row.get("extension") or "<no_ext>") for row in rows)
    LOGGER.info("Catalog output path: %s", output_path)
    LOGGER.info("Cataloged %s files across %s extension groups", len(rows), len(extension_counts))

    if not rows:
        LOGGER.warning(
            "No matching files were found. Review config/pipeline.yaml include_extensions or input_audio_dir."
        )
        return

    for extension, count in extension_counts.most_common(5):
        LOGGER.info("Top extension: %s (%s files)", extension, count)


def run_step(config: AppConfig, args: argparse.Namespace) -> int:
    """Execute the catalog stage."""
    input_dir = config.paths.input_audio_dir
    configured_output = config.pipeline_for("catalog").get("output_csv", "metadata/catalog.csv")
    output_csv = config.resolve_repo_path(args.output_csv or configured_output)

    LOGGER.info("Cataloging audio files from %s", input_dir)
    rows = scan_audio_files(config, limit=args.limit)
    write_catalog(rows, output_csv)
    log_catalog_summary(rows, output_csv)
    return 0


def main() -> int:
    """Run the catalog step directly."""
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    add_arguments(parser)
    args = parser.parse_args()

    configure_logging(verbose=args.verbose)
    config = load_config_with_logging(args, repo_root=REPO_ROOT, logger=LOGGER)
    log_config_summary(LOGGER, config)
    return run_step(config, args)


if __name__ == "__main__":
    raise SystemExit(main())
