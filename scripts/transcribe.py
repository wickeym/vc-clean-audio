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

from vc_clean_audio.bootstrap import add_common_arguments, build_config_from_args
from vc_clean_audio.config import AppConfig
from vc_clean_audio.logging_utils import configure_logging

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
    LOGGER.info(
        "TODO: connect a transcription backend once decoding and candidate selection are in place."
    )
    return 0


def main() -> int:
    """Run the transcribe step directly."""
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    add_arguments(parser)
    args = parser.parse_args()

    configure_logging(verbose=args.verbose)
    config = build_config_from_args(args, repo_root=REPO_ROOT)
    return run_step(config, args)


if __name__ == "__main__":
    raise SystemExit(main())
