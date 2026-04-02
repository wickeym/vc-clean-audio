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

from vc_clean_audio.bootstrap import add_common_arguments, load_config_with_logging
from vc_clean_audio.config import AppConfig
from vc_clean_audio.logging_utils import configure_logging, log_config_summary, log_todos

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
    LOGGER.warning(
        "TTS generation is not implemented yet. This step currently reserves workspace and settings only."
    )
    log_todos(
        LOGGER,
        "TTS stage next steps:",
        [
            "Select a TTS backend and voice strategy that balances quality, cost, and local batch automation.",
            "Write generated lines with stable identifiers so alignment and packaging can trace each output.",
            "Capture synthesis settings per line to make regenerated audio reproducible.",
        ],
    )
    return 0


def main() -> int:
    """Run the tts step directly."""
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
