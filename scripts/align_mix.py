"""Align regenerated speech with source timing and prepare replacement mixes."""

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
        "--dry-run",
        action="store_true",
        help="Validate settings without producing aligned mixes.",
    )


def run_step(config: AppConfig, args: argparse.Namespace) -> int:
    """Execute the align_mix stage."""
    mixes_dir = config.paths.work_dir / "aligned"
    mixes_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Prepared alignment workspace at %s", mixes_dir)
    if args.dry_run:
        LOGGER.info("Dry-run mode enabled for future alignment validation.")
    LOGGER.warning(
        "Alignment and mix assembly are not implemented yet. This step currently prepares the workspace only."
    )
    log_todos(
        LOGGER,
        "Align/mix stage next steps:",
        [
            "Match regenerated speech timing to the source clip or transcript timing markers.",
            "Apply consistent loudness and trim handling so replacements do not stand out in-game.",
            "Keep mix decisions reversible by writing manifests instead of mutating assets in place.",
        ],
    )
    return 0


def main() -> int:
    """Run the align_mix step directly."""
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
