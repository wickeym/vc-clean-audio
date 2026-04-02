"""Transcribe prepared dialogue assets."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from vc_clean_audio.bootstrap import add_common_arguments, load_config_with_logging
from vc_clean_audio.config import AppConfig
from vc_clean_audio.logging_utils import configure_logging, log_config_summary, log_todos

LOGGER = logging.getLogger(__name__)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Register command-line arguments for this step."""
    parser.add_argument(
        "--engine",
        default=None,
        help="Override the configured transcription engine.",
    )


def run_step(config: AppConfig, args: argparse.Namespace) -> int:
    """Execute the transcribe stage."""
    settings = config.pipeline_for("transcribe")
    engine = args.engine or settings.get("engine") or "unset"
    transcripts_dir = config.paths.work_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Prepared transcript workspace at %s", transcripts_dir)
    LOGGER.info("Configured transcription engine: %s", engine)
    LOGGER.warning(
        "Transcription is not implemented yet. This step only prepares workspace and expected settings."
    )
    log_todos(
        LOGGER,
        "Transcribe stage next steps:",
        [
            "Choose a speech-to-text backend that works well on short Vice City dialogue clips.",
            "Store raw transcript text plus timing data so later rewrite and alignment steps have traceability.",
            "Keep transcripts tied to catalog and decode manifests instead of relying on filenames alone.",
        ],
    )
    return 0


def main() -> int:
    """Run the transcribe step directly."""
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
