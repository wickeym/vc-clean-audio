"""Step registry for the vc-clean-audio pipeline."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

STEP_MODULES: dict[str, str] = {
    "align_mix": "scripts.align_mix",
    "catalog": "scripts.catalog",
    "classify": "scripts.classify",
    "clean_text": "scripts.clean_text",
    "decode": "scripts.decode",
    "package": "scripts.package",
    "separate": "scripts.separate",
    "transcribe": "scripts.transcribe",
    "tts": "scripts.tts",
}


def get_step_module(step_name: str) -> ModuleType:
    """Import and return the module that implements a step."""
    module_name = STEP_MODULES[step_name]
    return import_module(module_name)
