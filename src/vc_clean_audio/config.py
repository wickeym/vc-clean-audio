"""Configuration loading for the vc-clean-audio pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(slots=True)
class PathsConfig:
    """Resolved filesystem paths used by the pipeline."""

    gta_vc_root: Path
    input_audio_dir: Path
    work_dir: Path
    output_dir: Path
    tools_dir: Path


@dataclass(slots=True)
class AppConfig:
    """Application configuration bundled for pipeline steps."""

    repo_root: Path
    paths: PathsConfig
    pipeline: dict[str, Any]

    def resolve_repo_path(self, value: str | Path) -> Path:
        """Resolve a possibly relative path against the repository root."""
        path = Path(str(value))
        if path.is_absolute():
            return path
        return (self.repo_root / path).resolve()

    def pipeline_for(self, step_name: str) -> dict[str, Any]:
        """Return settings for a named pipeline step."""
        step_config = self.pipeline.get(step_name, {})
        if not isinstance(step_config, dict):
            raise TypeError(f"Expected mapping for pipeline step '{step_name}'.")
        return step_config


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file into a dictionary."""
    import yaml

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    if not isinstance(payload, dict):
        raise TypeError(f"Expected top-level mapping in config file: {path}")

    return payload


def _resolve_value(repo_root: Path, raw_value: str) -> Path:
    """Expand environment variables and resolve a config path value."""
    expanded = os.path.expandvars(raw_value)
    path = Path(expanded).expanduser()
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def load_app_config(
    repo_root: Path,
    paths_config_path: Path,
    pipeline_config_path: Path,
) -> AppConfig:
    """Load and resolve the full application configuration."""
    paths_payload = _load_yaml(paths_config_path)
    pipeline_payload = _load_yaml(pipeline_config_path)

    required_keys = (
        "gta_vc_root",
        "input_audio_dir",
        "work_dir",
        "output_dir",
        "tools_dir",
    )
    missing = [key for key in required_keys if key not in paths_payload]
    if missing:
        raise KeyError(f"Missing required paths config keys: {', '.join(missing)}")

    paths = PathsConfig(
        gta_vc_root=_resolve_value(repo_root, str(paths_payload["gta_vc_root"])),
        input_audio_dir=_resolve_value(repo_root, str(paths_payload["input_audio_dir"])),
        work_dir=_resolve_value(repo_root, str(paths_payload["work_dir"])),
        output_dir=_resolve_value(repo_root, str(paths_payload["output_dir"])),
        tools_dir=_resolve_value(repo_root, str(paths_payload["tools_dir"])),
    )

    return AppConfig(
        repo_root=repo_root.resolve(),
        paths=paths,
        pipeline=pipeline_payload,
    )
