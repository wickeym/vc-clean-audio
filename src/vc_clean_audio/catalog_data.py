"""Shared helpers for reading and writing the pipeline catalog CSV."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Mapping, Sequence

CATALOG_FIELDNAMES: list[str] = [
    "source_path",
    "relative_path",
    "filename",
    "extension",
    "size_bytes",
    "discovered_at",
    "decoded_wav_path",
    "duration_seconds",
    "sample_rate",
    "channels",
    "decode_status",
    "decode_error",
]


def normalize_catalog_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return a catalog row with all expected keys present."""
    normalized = {field: row.get(field, "") for field in CATALOG_FIELDNAMES}
    for key, value in row.items():
        if key not in normalized:
            normalized[key] = value
    return normalized


def write_catalog_rows(rows: Sequence[Mapping[str, Any]], output_path: Path) -> None:
    """Write catalog rows to CSV, preserving any extra columns."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(CATALOG_FIELDNAMES)
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(normalize_catalog_row(row))


def read_catalog_rows(catalog_path: Path) -> list[dict[str, Any]]:
    """Load catalog rows from CSV."""
    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalog CSV not found: {catalog_path}")

    with catalog_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Catalog CSV is missing a header row: {catalog_path}")
        return [normalize_catalog_row(row) for row in reader]
