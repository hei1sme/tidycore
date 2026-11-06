"""Validated atomic settings. Bundled config is a safe default template."""
import copy
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

from .utils import data_path, data_root, get_absolute_path, resource_root, isolated_mode

CONFIG_PATH = None  # Explicit override for integration tests/import tools.
PARTIAL_EXTENSIONS = {'.crdownload', '.part', '.tmp', '.download', '.partial', '.!ut'}


def config_path() -> Path:
    return Path(CONFIG_PATH or data_path('config.json'))


def validate_component(value: str) -> None:
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
    if (not isinstance(value, str) or not value or value.startswith('.')
            or value.endswith((' ', '.')) or any(c in value for c in '<>:"/\\|?*')
            or any(ord(c) < 32 for c in value) or len(value) > 100
            or value.split('.')[0].upper() in reserved):
        raise ValueError(f'Invalid Windows category name: {value!r}')


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise ValueError('Settings must be a JSON object.')
    result = copy.deepcopy(config)
    target = result.get('target_folder', '')
    if not isinstance(target, str):
        raise ValueError('Target folder must be text.')
    if target == '{USER_DOWNLOADS}':
        target = ''  # A legacy placeholder does not authorize organization.
    if target:
        p = Path(target)
        if not p.is_absolute() or not p.is_dir() or p.is_symlink() or p.is_junction():
            raise ValueError('Choose an existing absolute folder without a junction or symbolic link.')
        protected_roots = [data_root(), resource_root()]
        if getattr(sys, 'frozen', False):
            protected_roots.append(Path(sys.executable).parent)
        for protected in protected_roots:
            if p.resolve() == protected or protected.is_relative_to(p.resolve()):
                raise ValueError('The watched folder cannot contain TidyCore application files or its state directory.')
        if isolated_mode():
            try:
                p.resolve().relative_to(data_root())
            except ValueError:
                raise ValueError('In test mode, the watched folder must be inside the isolated data directory.') from None
        result['target_folder'] = str(p.resolve())
    else:
        result['target_folder'] = ''
    cooldown = result.get('cooldown_period_seconds', 5)
    if isinstance(cooldown, bool) or not isinstance(cooldown, (int, float)) or not 1 <= cooldown <= 3600:
        raise ValueError('Cooldown must be between 1 and 3600 seconds.')
    result['cooldown_period_seconds'] = cooldown
    strategy = result.get('folder_handling_strategy', 'ignore')
    if strategy not in {'ignore', 'smart_scan', 'move_to_others'}:
        raise ValueError('Unknown folder handling strategy.')
    result['folder_handling_strategy'] = strategy
    ignores = result.get('ignore_list', [])
    if not isinstance(ignores, list) or not all(isinstance(x, str) and x.strip() for x in ignores):
        raise ValueError('Ignore entries must be nonempty text.')
    result['ignore_list'] = list(dict.fromkeys(ignores))
    rules = result.get('rules', {})
    if not isinstance(rules, dict):
        raise ValueError('Rules must be an object.')
    seen_categories, seen_extensions = set(), set()

    def extensions(values):
        if not isinstance(values, list):
            raise ValueError('Extensions must be a list.')
        normalized = []
        for ext in values:
            if not isinstance(ext, str) or not re.fullmatch(r'\.[\w!+-]+', ext):
                raise ValueError(f'Invalid extension: {ext!r}; use a suffix such as .pdf.')
            ext = ext.lower()
            if ext in seen_extensions:
                raise ValueError(f'Extension {ext} is assigned more than once.')
            seen_extensions.add(ext)
            normalized.append(ext)
        return normalized

    for category, values in rules.items():
        validate_component(category)
        if category.casefold() in seen_categories:
            raise ValueError('Category names must be unique without regard to case.')
        seen_categories.add(category.casefold())
        if isinstance(values, dict):
            sub_seen = set()
            for sub, exts in values.items():
                if sub != '__extensions__':
                    validate_component(sub)
                if sub.casefold() in sub_seen:
                    raise ValueError('Duplicate subcategory.')
                sub_seen.add(sub.casefold())
                result['rules'][category][sub] = extensions(exts)
        else:
            result['rules'][category] = extensions(values)
    return result


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        defaults = json.loads(Path(get_absolute_path('config/config.json')).read_text(encoding='utf-8'))
        defaults['target_folder'] = ''
        defaults['start_paused'] = True
        save_config(defaults)
    return validate_config(json.loads(path.read_text(encoding='utf-8')))


def save_config(config_data: dict[str, Any]) -> None:
    config = validate_config(config_data)
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        from shutil import copy2
        copy2(path, path.with_suffix('.json.bak'))
    fd, temporary = tempfile.mkstemp(prefix='config-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(config, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class ConfigManager:
    load_config = staticmethod(load_config)
    save_config = staticmethod(save_config)
