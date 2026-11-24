"""Check release metadata without downloading or installing updates."""
import json
import re

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from . import __version__
from .utils import isolated_mode

RELEASES_URL = 'https://github.com/hei1sme/tidycore/releases'
LATEST_RELEASE_API = 'https://api.github.com/repos/hei1sme/tidycore/releases/latest'
MAX_RESPONSE_BYTES = 256 * 1024
CHECK_TIMEOUT_MS = 10_000
VERSION_TAG = re.compile(r'v((?:0|[1-9][0-9]{0,8})\.(?:0|[1-9][0-9]{0,8})\.(?:0|[1-9][0-9]{0,8}))')


def latest_version(body: bytes, current_version: str) -> str | None:
    release = json.loads(body)
    if (not isinstance(release, dict) or release.get('draft') is not False
            or release.get('prerelease') is not False):
        raise ValueError('Expected a stable release.')
    tag = release.get('tag_name')
    match = VERSION_TAG.fullmatch(tag) if isinstance(tag, str) else None
    if not match:
        raise ValueError('Invalid release version.')
    version = match[1]
    if tuple(map(int, version.split('.'))) > tuple(map(int, current_version.split('.'))):
        return version
    return None


class ReleaseChecker(QObject):
    completed = Signal(str, str)  # New version and error message, both empty when current.

    def __init__(self, parent=None):
        super().__init__(parent)
        self._network = QNetworkAccessManager(self)
        self._deadline = QTimer(self)
        self._deadline.setSingleShot(True)
        self._deadline.timeout.connect(self._timeout)
        self._reply = None

    def check(self) -> bool:
        if isolated_mode() or self._reply is not None:
            return False

        request = QNetworkRequest(QUrl(LATEST_RELEASE_API))
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
        request.setRawHeader(b'Accept', b'application/vnd.github+json')
        request.setRawHeader(b'User-Agent', f'TidyCore/{__version__}'.encode('ascii'))
        self._body = bytearray()
        self._failure = ''
        self._reply = self._network.get(request)
        self._reply.setReadBufferSize(MAX_RESPONSE_BYTES + 1)
        self._reply.readyRead.connect(self._read)
        self._reply.finished.connect(self._finish)
        self._deadline.start(CHECK_TIMEOUT_MS)
        return True

    def _timeout(self):
        self._failure = 'The update check timed out. Try again later.'
        self._reply.abort()

    def _read(self):
        self._body.extend(bytes(self._reply.read(MAX_RESPONSE_BYTES + 1 - len(self._body))))
        if len(self._body) > MAX_RESPONSE_BYTES:
            self._failure = 'GitHub returned too much release data.'
            if not self._reply.isFinished():
                self._reply.abort()

    def _finish(self):
        self._deadline.stop()
        reply = self._reply
        version = ''
        error = self._failure
        if not error:
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            if status != 200 or reply.error() != QNetworkReply.NetworkError.NoError:
                error = 'Could not check GitHub for updates. Try again later.'
            else:
                if reply.bytesAvailable():
                    self._read()
                error = self._failure
                if not error:
                    try:
                        version = latest_version(self._body, __version__) or ''
                    except (ValueError, RecursionError):
                        error = 'GitHub returned invalid release data.'
        self._reply = None
        reply.deleteLater()
        self.completed.emit(version, error)


class UpdateManager:
    """Compatibility entry point for legacy callers."""

    def check_for_updates(self, silent=False):
        if not silent:
            return QDesktopServices.openUrl(QUrl(RELEASES_URL))
        return False

    def download_and_install_update(self, *args, **kwargs):
        raise RuntimeError('Self-installation is disabled. Download updates manually from the official releases page.')


update_manager = UpdateManager()


def get_update_manager():
    return update_manager
