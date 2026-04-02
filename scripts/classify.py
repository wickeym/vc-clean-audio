"""Classify cataloged assets into likely dialogue and non-dialogue groups."""

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
        "--strategy",
        default=None,
        help="Override the configured classification strategy.",
    )


def run_step(config: AppConfig, args: argparse.Namespace) -> int:
    """Execute the classify stage."""
    strategy = args.strategy or config.pipeline_for("classify").get(
        "strategy",
        "extension_then_manual_review",
    )
    review_manifest = config.resolve_repo_path(
        config.pipeline_for("classify").get(
            "review_manifest",
            "metadata/classification_review.csv",
        )
    )
    review_manifest.parent.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Classification strategy: %s", strategy)
    LOGGER.info("Review manifest path reserved at %s", review_manifest)
    LOGGER.warning(
        "Classification is not implemented yet. This step only records how the workflow should evolve."
    )
    log_todos(
        LOGGER,
        "Classify stage next steps:",
        [
            "Use catalog output to group assets by extension, naming patterns, and source folder.",
            "Mark likely speech candidates separately from music, ambience, and unknown content.",
            "Export a review queue so uncertain files can be checked manually before transcription.",
        ],
    )
    return 0


def main() -> int:
    """Run the classify step directly."""
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
