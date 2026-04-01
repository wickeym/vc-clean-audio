"""Catalog source audio files for later batch processing."""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from vc_clean_audio.bootstrap import add_common_arguments, build_config_from_args
from vc_clean_audio.config import AppConfig
from vc_clean_audio.logging_utils import configure_logging

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class CatalogRow:
    """Serializable metadata for a discovered source file."""

    source_path: str
    relative_path: str
    filename: str
    extension: str
    size_bytes: int
    discovered_at: str


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Register command-line arguments for this step."""
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of files to catalog.",
    )


def scan_audio_files(config: AppConfig, limit: int | None = None) -> list[CatalogRow]:
    """Scan the configured audio directory and build catalog rows."""
    input_dir = config.paths.input_audio_dir
    if not input_dir.exists():
        raise FileNotFoundError(f"Input audio directory does not exist: {input_dir}")

    catalog_settings = config.pipeline_for("catalog")
    include_extensions = {
        extension.lower()
        for extension in catalog_settings.get("include_extensions", [])
        if extension
    }
    recursive = bool(catalog_settings.get("recursive", True))

    iterator = sorted(input_dir.rglob("*") if recursive else input_dir.glob("*"))
    discovered_at = datetime.now(timezone.utc).isoformat()

    rows: list[CatalogRow] = []
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
            CatalogRow(
                source_path=str(path),
                relative_path=str(path.relative_to(input_dir)),
                filename=path.name,
                extension=path.suffix.lower(),
                size_bytes=stat.st_size,
                discovered_at=discovered_at,
            )
        )

        if limit is not None and len(rows) >= limit:
            break

    return rows


def write_catalog(rows: list[CatalogRow], output_path: Path) -> None:
    """Write the catalog rows to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else list(CatalogRow.__annotations__.keys())

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def run_step(config: AppConfig, args: argparse.Namespace) -> int:
    """Execute the catalog stage."""
    input_dir = config.paths.input_audio_dir
    output_csv = config.resolve_repo_path(
        config.pipeline_for("catalog").get("output_csv", "metadata/catalog.csv")
    )

    LOGGER.info("Cataloging audio files from %s", input_dir)
    rows = scan_audio_files(config, limit=args.limit)
    write_catalog(rows, output_csv)
    LOGGER.info("Wrote %s catalog rows to %s", len(rows), output_csv)
    return 0


def main() -> int:
    """Run the catalog step directly."""
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    add_arguments(parser)
    args = parser.parse_args()

    configure_logging(verbose=args.verbose)
    config = build_config_from_args(args, repo_root=REPO_ROOT)
    return run_step(config, args)


if __name__ == "__main__":
    raise SystemExit(main())
