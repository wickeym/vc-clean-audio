"""Shared CLI bootstrap helpers for pipeline scripts."""

from __future__ import annotations

import argparse
from pathlib import Path

from vc_clean_audio.config import AppConfig, load_app_config


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add shared arguments used by the runner and individual step scripts."""
    parser.add_argument(
        "--paths-config",
        default=None,
        help="Path to the paths YAML file. Defaults to config/paths.yaml if present.",
    )
    parser.add_argument(
        "--pipeline-config",
        default=None,
        help="Path to the pipeline YAML file. Defaults to config/pipeline.yaml if present.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output.",
    )


def _resolve_config_arg(
    repo_root: Path,
    explicit_path: str | None,
    preferred_name: str,
    example_name: str,
) -> Path:
    """Pick an explicit config path or fall back to the local/example file."""
    if explicit_path:
        return Path(explicit_path).expanduser()

    preferred_path = repo_root / "config" / preferred_name
    if preferred_path.exists():
        return preferred_path

    return repo_root / "config" / example_name


def build_config_from_args(args: argparse.Namespace, repo_root: Path) -> AppConfig:
    """Load application config based on parsed CLI arguments."""
    paths_config = _resolve_config_arg(
        repo_root=repo_root,
        explicit_path=args.paths_config,
        preferred_name="paths.yaml",
        example_name="paths.example.yaml",
    )
    pipeline_config = _resolve_config_arg(
        repo_root=repo_root,
        explicit_path=args.pipeline_config,
        preferred_name="pipeline.yaml",
        example_name="pipeline.example.yaml",
    )
    return load_app_config(
        repo_root=repo_root,
        paths_config_path=paths_config,
        pipeline_config_path=pipeline_config,
    )
