"""Apply profanity replacement and rewrite rules to transcripts."""

from __future__ import annotations

import argparse
import json
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
        "--preview-only",
        action="store_true",
        help="Load rules and report what would be applied without writing outputs.",
    )


def _load_json(path: Path) -> dict:
    """Load a JSON configuration file."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def run_step(config: AppConfig, args: argparse.Namespace) -> int:
    """Execute the clean_text stage."""
    settings = config.pipeline_for("clean_text")
    profanity_map_path = config.resolve_repo_path(
        settings.get("profanity_map_path", "config/profanity_map.json")
    )
    rewrite_rules_path = config.resolve_repo_path(
        settings.get("rewrite_rules_path", "config/rewrite_rules.json")
    )
    cleaned_dir = config.paths.work_dir / "clean_text"
    cleaned_dir.mkdir(parents=True, exist_ok=True)

    profanity_map = _load_json(profanity_map_path)
    rewrite_rules = _load_json(rewrite_rules_path)

    LOGGER.info("Loaded %s profanity replacements", len(profanity_map.get("replacements", [])))
    LOGGER.info("Loaded %s rewrite rules", len(rewrite_rules.get("rules", [])))
    LOGGER.info("Prepared cleaned text workspace at %s", cleaned_dir)
    if args.preview_only:
        LOGGER.info("Preview mode enabled; no transcript output will be written.")
    LOGGER.warning(
        "Transcript cleaning is not implemented yet. This step currently validates the JSON config files."
    )
    log_todos(
        LOGGER,
        "Clean text stage next steps:",
        [
            "Load transcript records and apply profanity replacements in a deterministic order.",
            "Track original text, cleaned text, and which rewrite rules fired for auditability.",
            "Preserve protected names and mission-specific terms so cleanup does not damage meaning.",
        ],
    )
    return 0


def main() -> int:
    """Run the clean_text step directly."""
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
