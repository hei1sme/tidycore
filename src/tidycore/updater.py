"""Compatibility entry point for manual updates.

The former self-replacer could overwrite Python when run from source, used
unverified executables, and killed processes by name. It is intentionally retired
until a separately verified and signed update design is available.
"""
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


class UpdateManager:
    def check_for_updates(self, silent=False):
        if not silent:
            return QDesktopServices.openUrl(QUrl('https://github.com/hei1sme/TidyCore/releases'))
        return False

    def download_and_install_update(self, *args, **kwargs):
        raise RuntimeError('Self-installation is disabled. Download updates manually from the official releases page.')


update_manager = UpdateManager()


def get_update_manager():
    return update_manager
