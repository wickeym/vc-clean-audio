"""Separate speech from backing audio when the workflow requires it."""

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
        help="Override the configured separation engine.",
    )


def run_step(config: AppConfig, args: argparse.Namespace) -> int:
    """Execute the separate stage."""
    settings = config.pipeline_for("separate")
    engine = args.engine or settings.get("engine") or "unset"
    vocals_dir = config.paths.work_dir / settings.get("vocals_subdir", "separated/vocals")
    backing_dir = config.paths.work_dir / settings.get("backing_subdir", "separated/backing")
    vocals_dir.mkdir(parents=True, exist_ok=True)
    backing_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Prepared vocals output directory at %s", vocals_dir)
    LOGGER.info("Prepared backing output directory at %s", backing_dir)
    LOGGER.info("Configured separation engine: %s", engine)
    LOGGER.info(
        "TODO: integrate a source-separation backend after decode and classification are reliable."
    )
    return 0


def main() -> int:
    """Run the separate step directly."""
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    add_arguments(parser)
    args = parser.parse_args()

    configure_logging(verbose=args.verbose)
    config = build_config_from_args(args, repo_root=REPO_ROOT)
    return run_step(config, args)


if __name__ == "__main__":
    raise SystemExit(main())
