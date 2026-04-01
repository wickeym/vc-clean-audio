"""Generate replacement speech audio from cleaned dialogue text."""

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
        "--voice",
        default=None,
        help="Override the configured TTS voice identifier.",
    )


def run_step(config: AppConfig, args: argparse.Namespace) -> int:
    """Execute the tts stage."""
    settings = config.pipeline_for("tts")
    voice = args.voice or settings.get("voice") or "unset"
    tts_dir = config.paths.work_dir / "tts"
    tts_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Prepared TTS workspace at %s", tts_dir)
    LOGGER.info("Configured TTS voice: %s", voice)
    LOGGER.info(
        "TODO: integrate the chosen TTS backend once cleaned dialogue text and timing targets exist."
    )
    return 0


def main() -> int:
    """Run the tts step directly."""
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    add_arguments(parser)
    args = parser.parse_args()

    configure_logging(verbose=args.verbose)
    config = build_config_from_args(args, repo_root=REPO_ROOT)
    return run_step(config, args)


if __name__ == "__main__":
    raise SystemExit(main())
