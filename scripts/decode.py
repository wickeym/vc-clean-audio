"""Decode GTA Vice City audio into a workable intermediate format."""

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
        "--overwrite",
        action="store_true",
        help="Overwrite decoded files when a decoder is added.",
    )


def run_step(config: AppConfig, args: argparse.Namespace) -> int:
    """Execute the decode stage."""
    decode_settings = config.pipeline_for("decode")
    output_dir = config.paths.work_dir / decode_settings.get("output_subdir", "decoded")
    output_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Prepared decode output directory at %s", output_dir)
    LOGGER.warning(
        "Decoding is not implemented yet. This step only prepares the workspace and documents next work."
    )
    if args.overwrite or decode_settings.get("overwrite", False):
        LOGGER.info("Overwrite mode is enabled for future decoder integration.")
    log_todos(
        LOGGER,
        "Decode stage next steps:",
        [
            "Pick a Vice City-compatible decoder and document how it is installed in tools_dir.",
            "Map game-native source formats to an intermediate WAV workflow without overwriting originals.",
            "Write a decode manifest so later steps know which source file produced which decoded asset.",
        ],
    )
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
