"""Prepare pipeline outputs for later reinsertion into the Vice City workflow."""

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
        "--manifest-only",
        action="store_true",
        help="Prepare packaging metadata without building a final package.",
    )


def run_step(config: AppConfig, args: argparse.Namespace) -> int:
    """Execute the package stage."""
    settings = config.pipeline_for("package")
    packages_dir = config.paths.output_dir / settings.get("package_subdir", "packages")
    packages_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Prepared package output directory at %s", packages_dir)
    if args.manifest_only:
        LOGGER.info("Manifest-only mode enabled for future packaging work.")
    LOGGER.info(
        "TODO: define the final Vice City reinsertion and packaging workflow before implementing this step."
    )
    return 0


def main() -> int:
    """Run the package step directly."""
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser)
    add_arguments(parser)
    args = parser.parse_args()

    configure_logging(verbose=args.verbose)
    config = build_config_from_args(args, repo_root=REPO_ROOT)
    return run_step(config, args)


if __name__ == "__main__":
    raise SystemExit(main())
