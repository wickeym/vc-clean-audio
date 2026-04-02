"""Logging helpers for the vc-clean-audio pipeline."""

from __future__ import annotations

import logging

from vc_clean_audio.config import AppConfig


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )


def log_config_summary(logger: logging.Logger, config: AppConfig) -> None:
    """Log the config files and resolved root paths used for a run."""
    logger.info("Using paths config: %s", config.sources.paths_config_path)
    logger.info("Using pipeline config: %s", config.sources.pipeline_config_path)

    if config.sources.paths_from_example:
        logger.warning(
            "Using example paths config because config/paths.yaml was not found yet."
        )
    if config.sources.pipeline_from_example:
        logger.warning(
            "Using example pipeline config because config/pipeline.yaml was not found yet."
        )

    logger.info("Resolved input audio dir: %s", config.paths.input_audio_dir)
    logger.info("Resolved work dir: %s", config.paths.work_dir)
    logger.info("Resolved output dir: %s", config.paths.output_dir)


def log_todos(logger: logging.Logger, title: str, items: list[str]) -> None:
    """Log a compact TODO list for unfinished pipeline steps."""
    logger.info("%s", title)
    for item in items:
        logger.info("TODO: %s", item)
