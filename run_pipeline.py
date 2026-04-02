"""Entry point for the vc-clean-audio batch pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from vc_clean_audio.bootstrap import add_common_arguments, load_config_with_logging
from vc_clean_audio.logging_utils import configure_logging, log_config_summary
from vc_clean_audio.pipeline import STEP_MODULES, get_step_module

LOGGER = logging.getLogger("vc_clean_audio")


def build_parser(
    step: str | None = None,
    *,
    add_help: bool = True,
) -> argparse.ArgumentParser:
    """Create the top-level argument parser."""
    parser = argparse.ArgumentParser(
        description="Run a configured step in the vc-clean-audio pipeline.",
        add_help=add_help,
    )
    add_common_arguments(parser)
    parser.add_argument(
        "--step",
        choices=sorted(STEP_MODULES),
        help="Pipeline step to run.",
    )
    parser.add_argument(
        "--list-steps",
        action="store_true",
        help="Print the available pipeline steps and exit.",
    )

    if step:
        module = get_step_module(step)
        module.add_arguments(parser)

    return parser


def main() -> int:
    """Parse arguments and dispatch the selected pipeline step."""
    bootstrap_parser = build_parser(add_help=False)
    bootstrap_args, _ = bootstrap_parser.parse_known_args()

    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        if bootstrap_args.step:
            parser = build_parser(bootstrap_args.step)
        else:
            parser = build_parser()
        parser.print_help()
        return 0

    if bootstrap_args.list_steps:
        for step_name in sorted(STEP_MODULES):
            print(step_name)
        return 0

    if not bootstrap_args.step:
        bootstrap_parser.error("--step is required unless --list-steps is used.")

    parser = build_parser(bootstrap_args.step)
    args = parser.parse_args()
    configure_logging(verbose=args.verbose)

    config = load_config_with_logging(args, repo_root=REPO_ROOT, logger=LOGGER)
    log_config_summary(LOGGER, config)
    module = get_step_module(args.step)
    return module.run_step(config, args)


if __name__ == "__main__":
    raise SystemExit(main())
