"""Decode discovered source audio into a standardized working WAV format."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from vc_clean_audio.bootstrap import add_common_arguments, load_config_with_logging
from vc_clean_audio.catalog_data import read_catalog_rows, write_catalog_rows
from vc_clean_audio.config import AppConfig
from vc_clean_audio.logging_utils import configure_logging, log_config_summary
from vc_clean_audio.subprocess_utils import CommandResult, find_executable, run_command

LOGGER = logging.getLogger(__name__)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Register command-line arguments for this step."""
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite decoded files that already exist.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of catalog rows to process.",
    )
    parser.add_argument(
        "--catalog-csv",
        default=None,
        help="Optional path to the catalog CSV to update.",
    )
    parser.add_argument(
        "--ffmpeg-path",
        default=None,
        help="Optional path to ffmpeg.exe. Overrides config and PATH lookup.",
    )
    parser.add_argument(
        "--ffprobe-path",
        default=None,
        help="Optional path to ffprobe.exe. Overrides config and PATH lookup.",
    )


def _resolve_path_like_candidate(config: AppConfig, value: str) -> str | Path:
    """Resolve relative executable paths while preserving PATH-style names."""
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate

    if candidate.parent != Path(".") or "\\" in value or "/" in value:
        return config.resolve_repo_path(candidate)

    return value


def _tool_candidates(
    config: AppConfig,
    *,
    explicit_value: str | None,
    config_key: str,
    executable_name: str,
    include_decoder_tool: bool = False,
) -> list[str | Path]:
    """Build the list of candidate executable locations for a tool."""
    settings = config.pipeline_for("decode")
    candidates: list[str | Path] = []

    configured_values = [explicit_value, settings.get(config_key)]
    if include_decoder_tool:
        configured_values.append(settings.get("decoder_tool"))

    for value in configured_values:
        if value:
            candidates.append(_resolve_path_like_candidate(config, str(value)))

    candidates.extend(
        [
            config.paths.tools_dir / "ffmpeg" / "bin" / executable_name,
            config.paths.tools_dir / executable_name,
            executable_name.removesuffix(".exe"),
            executable_name,
        ]
    )
    return candidates


def resolve_ffmpeg_tools(
    config: AppConfig,
    args: argparse.Namespace,
) -> tuple[Path | None, Path | None]:
    """Resolve ffmpeg and ffprobe executables from config, tools_dir, or PATH."""
    ffmpeg_path = find_executable(
        _tool_candidates(
            config,
            explicit_value=args.ffmpeg_path,
            config_key="ffmpeg_path",
            executable_name="ffmpeg.exe",
            include_decoder_tool=True,
        )
    )
    ffprobe_path = find_executable(
        _tool_candidates(
            config,
            explicit_value=args.ffprobe_path,
            config_key="ffprobe_path",
            executable_name="ffprobe.exe",
        )
    )
    return ffmpeg_path, ffprobe_path


def resolve_catalog_path(config: AppConfig, args: argparse.Namespace) -> Path:
    """Resolve the catalog CSV path used by the decode stage."""
    configured_path = config.pipeline_for("decode").get("catalog_csv", "metadata/catalog.csv")
    return config.resolve_repo_path(args.catalog_csv or configured_path)


def resolve_decoded_root(config: AppConfig) -> Path:
    """Resolve the decode output directory."""
    output_subdir = config.pipeline_for("decode").get("output_subdir", "decoded_wav")
    decoded_root = config.paths.work_dir / output_subdir
    decoded_root.mkdir(parents=True, exist_ok=True)
    return decoded_root


def _optional_int(value: Any) -> int | None:
    """Parse an optional integer setting."""
    if value in (None, "", 0, "0"):
        return None
    return int(value)


def _optional_timeout(value: Any, default: int = 120) -> int | None:
    """Parse an optional timeout setting."""
    if value in (None, ""):
        return default
    if value in (0, "0"):
        return None
    return int(value)


def summarize_command_error(result: CommandResult) -> str:
    """Build a concise error message from a subprocess result."""
    if result.timed_out:
        return result.stderr.strip() or "Command timed out."

    for source in (result.stderr, result.stdout):
        for line in source.splitlines():
            cleaned = line.strip()
            if cleaned:
                return cleaned[:240]

    return f"Command failed with exit code {result.returncode}."


def build_decoded_output_path(decoded_root: Path, relative_path: str) -> Path:
    """Map a source-relative path to a stable decoded WAV path."""
    source_relative = Path(relative_path)
    source_ext = source_relative.suffix.lower().lstrip(".") or "unknown"
    target_name = f"{source_relative.stem}__{source_ext}.wav"
    return decoded_root / source_relative.parent / target_name


def decode_to_wav(
    ffmpeg_path: Path,
    *,
    source_path: Path,
    output_path: Path,
    overwrite: bool,
    timeout_seconds: int | None,
    sample_rate_hz: int | None,
    channels: int | None,
) -> CommandResult:
    """Decode one source file to a PCM WAV output using ffmpeg."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command: list[str | Path] = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if overwrite else "-n",
        "-i",
        source_path,
        "-vn",
        "-acodec",
        "pcm_s16le",
    ]
    if sample_rate_hz is not None:
        command.extend(["-ar", str(sample_rate_hz)])
    if channels is not None:
        command.extend(["-ac", str(channels)])
    command.append(output_path)

    return run_command(command, cwd=REPO_ROOT, timeout_seconds=timeout_seconds)


def probe_audio_metadata(
    ffprobe_path: Path,
    *,
    audio_path: Path,
    timeout_seconds: int | None,
) -> tuple[dict[str, str], str | None]:
    """Probe basic audio metadata from a decoded WAV file."""
    command = [
        ffprobe_path,
        "-v",
        "error",
        "-show_entries",
        "stream=sample_rate,channels:format=duration",
        "-of",
        "json",
        audio_path,
    ]
    result = run_command(command, cwd=REPO_ROOT, timeout_seconds=timeout_seconds)
    if not result.ok:
        return {}, summarize_command_error(result)

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        return {}, f"Could not parse ffprobe output: {exc}"

    streams = payload.get("streams", [])
    stream = streams[0] if streams else {}
    format_data = payload.get("format", {})

    metadata = {
        "duration_seconds": "",
        "sample_rate": "",
        "channels": "",
    }

    duration_raw = format_data.get("duration")
    if duration_raw not in (None, ""):
        metadata["duration_seconds"] = f"{float(duration_raw):.3f}"

    sample_rate_raw = stream.get("sample_rate")
    if sample_rate_raw not in (None, ""):
        metadata["sample_rate"] = str(sample_rate_raw)

    channels_raw = stream.get("channels")
    if channels_raw not in (None, ""):
        metadata["channels"] = str(channels_raw)

    return metadata, None


def update_row_for_failure(
    row: dict[str, Any],
    *,
    status: str,
    error: str,
    clear_decoded_path: bool = False,
) -> None:
    """Apply a failure status to a catalog row."""
    if clear_decoded_path:
        row["decoded_wav_path"] = ""
    row["duration_seconds"] = ""
    row["sample_rate"] = ""
    row["channels"] = ""
    row["decode_status"] = status
    row["decode_error"] = error


def process_catalog_row(
    row: dict[str, Any],
    *,
    decoded_root: Path,
    ffmpeg_path: Path,
    ffprobe_path: Path | None,
    overwrite: bool,
    timeout_seconds: int | None,
    sample_rate_hz: int | None,
    channels: int | None,
) -> None:
    """Decode one catalog row and update it in place."""
    source_path_value = str(row.get("source_path", "")).strip()
    if not source_path_value:
        update_row_for_failure(
            row,
            status="missing_source",
            error="Catalog row is missing source_path.",
            clear_decoded_path=True,
        )
        return

    source_path = Path(source_path_value)
    if not source_path.exists():
        update_row_for_failure(
            row,
            status="missing_source",
            error=f"Source file does not exist: {source_path}",
            clear_decoded_path=True,
        )
        LOGGER.warning("Missing source file: %s", source_path)
        return

    decoded_path = build_decoded_output_path(decoded_root, str(row.get("relative_path", source_path.name)))
    row["decoded_wav_path"] = str(decoded_path)

    if decoded_path.exists() and not overwrite:
        LOGGER.info("Reusing existing decoded WAV for %s", source_path)
        if ffprobe_path is None:
            row["duration_seconds"] = ""
            row["sample_rate"] = ""
            row["channels"] = ""
            row["decode_status"] = "decoded_existing_no_probe"
            row["decode_error"] = "ffprobe not available; metadata not collected."
            return

        metadata, probe_error = probe_audio_metadata(
            ffprobe_path,
            audio_path=decoded_path,
            timeout_seconds=timeout_seconds,
        )
        if probe_error:
            update_row_for_failure(row, status="probe_failed", error=probe_error)
            return

        row.update(metadata)
        row["decode_status"] = "decoded_existing"
        row["decode_error"] = ""
        return

    result = decode_to_wav(
        ffmpeg_path,
        source_path=source_path,
        output_path=decoded_path,
        overwrite=overwrite,
        timeout_seconds=timeout_seconds,
        sample_rate_hz=sample_rate_hz,
        channels=channels,
    )
    if not result.ok:
        error_message = summarize_command_error(result)
        LOGGER.warning("Decode failed for %s: %s", source_path, error_message)
        update_row_for_failure(
            row,
            status="decode_failed",
            error=error_message,
            clear_decoded_path=True,
        )
        return

    if ffprobe_path is None:
        row["duration_seconds"] = ""
        row["sample_rate"] = ""
        row["channels"] = ""
        row["decode_status"] = "decoded_no_probe"
        row["decode_error"] = "ffprobe not available; metadata not collected."
        return

    metadata, probe_error = probe_audio_metadata(
        ffprobe_path,
        audio_path=decoded_path,
        timeout_seconds=timeout_seconds,
    )
    if probe_error:
        LOGGER.warning("Metadata probe failed for %s: %s", decoded_path, probe_error)
        update_row_for_failure(row, status="probe_failed", error=probe_error)
        return

    row.update(metadata)
    row["decode_status"] = "decoded"
    row["decode_error"] = ""


def log_decode_summary(rows: list[dict[str, Any]], catalog_path: Path, decoded_root: Path) -> None:
    """Log a summary of decode results."""
    status_counts = Counter(str(row.get("decode_status", "") or "unprocessed") for row in rows)
    LOGGER.info("Updated catalog CSV: %s", catalog_path)
    LOGGER.info("Decoded WAV root: %s", decoded_root)
    for status, count in sorted(status_counts.items()):
        LOGGER.info("Decode status %s: %s", status, count)


def run_step(config: AppConfig, args: argparse.Namespace) -> int:
    """Execute the decode stage."""
    decode_settings = config.pipeline_for("decode")
    catalog_path = resolve_catalog_path(config, args)
    if not catalog_path.exists():
        LOGGER.error("Catalog CSV not found: %s", catalog_path)
        LOGGER.error("Run `python run_pipeline.py --step catalog` first.")
        return 2
    decoded_root = resolve_decoded_root(config)
    rows = read_catalog_rows(catalog_path)
    if not rows:
        LOGGER.warning("Catalog CSV is empty: %s", catalog_path)
        return 0

    ffmpeg_path, ffprobe_path = resolve_ffmpeg_tools(config, args)
    timeout_seconds = _optional_timeout(decode_settings.get("timeout_seconds"), default=120)
    sample_rate_hz = _optional_int(decode_settings.get("target_sample_rate_hz"))
    channels = _optional_int(decode_settings.get("target_channels"))
    overwrite = bool(args.overwrite or decode_settings.get("overwrite", False))

    LOGGER.info("Catalog CSV: %s", catalog_path)
    LOGGER.info("Decode output directory: %s", decoded_root)
    LOGGER.info("Loaded %s catalog rows", len(rows))

    targeted_rows = rows[: args.limit] if args.limit is not None else rows

    if ffmpeg_path is None:
        error_message = (
            "ffmpeg.exe was not found. Install FFmpeg, add it to PATH, or configure decode.ffmpeg_path."
        )
        LOGGER.error(error_message)
        for row in targeted_rows:
            update_row_for_failure(
                row,
                status="decoder_missing",
                error=error_message,
                clear_decoded_path=True,
            )
        write_catalog_rows(rows, catalog_path)
        return 2

    LOGGER.info("Using ffmpeg: %s", ffmpeg_path)
    if ffprobe_path is None:
        LOGGER.warning(
            "ffprobe.exe was not found. Decoded WAVs can still be written, but metadata columns will stay blank."
        )
    else:
        LOGGER.info("Using ffprobe: %s", ffprobe_path)

    for row in targeted_rows:
        process_catalog_row(
            row,
            decoded_root=decoded_root,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            overwrite=overwrite,
            timeout_seconds=timeout_seconds,
            sample_rate_hz=sample_rate_hz,
            channels=channels,
        )

    write_catalog_rows(rows, catalog_path)
    log_decode_summary(rows, catalog_path, decoded_root)
    return 0


def main() -> int:
    """Run the decode step directly."""
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
