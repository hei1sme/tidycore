"""Opt-in Windows login startup; never enabled implicitly or in test mode."""
import subprocess
import sys
from pathlib import Path

from .utils import isolated_mode, resource_root

if sys.platform == 'win32':
    import winreg


def get_application_path():
    args = [sys.executable]
    if not getattr(sys, 'frozen', False):
        args.append(str(resource_root() / 'main.py'))
    return subprocess.list2cmdline(args)


class StartupManager:
    def __init__(self, app_name='TidyCore', app_path=None):
        self.app_name = app_name
        self.app_path = app_path or get_application_path()
        self.run_key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'

    def is_enabled(self):
        if sys.platform != 'win32' or isolated_mode():
            return False
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.run_key_path, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                return value == self.app_path
        except FileNotFoundError:
            return False

    def _require_allowed(self):
        if isolated_mode() or sys.platform != 'win32':
            raise RuntimeError('Windows startup changes are disabled in this session.')

    def enable(self):
        self._require_allowed()
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.run_key_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, self.app_path)

    def disable(self):
        self._require_allowed()
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.run_key_path, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, self.app_name)
        except FileNotFoundError:
            pass


startup_manager = StartupManager()
