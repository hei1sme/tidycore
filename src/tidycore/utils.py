"""Separate immutable bundled resources from durable per-user state."""
import os
from pathlib import Path
import sys


def resource_root() -> Path:
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[2]))


def get_absolute_path(relative_path: str) -> str:
    return str(resource_root() / relative_path)


def data_root() -> Path:
    override = os.environ.get('TIDYCORE_DATA_DIR')
    path = Path(override) if override else Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'TidyCore'
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_path(name: str) -> str:
    return str(data_root() / name)


def isolated_mode() -> bool:
    return os.environ.get('TIDYCORE_TEST_MODE') == '1'
