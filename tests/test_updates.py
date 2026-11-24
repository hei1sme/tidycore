import json

import pytest

from src.tidycore.updater import latest_version


@pytest.mark.parametrize(('tag', 'expected'), [
    ('v2.10.0', '2.10.0'),
    ('v2.3.0', None),
    ('v2.2.9', None),
])
def test_compare_release_versions_numerically(tag, expected):
    feed = {'tag_name': tag, 'draft': False, 'prerelease': False}
    assert latest_version(json.dumps(feed).encode(), '2.3.0') == expected


@pytest.mark.parametrize('feed', [
    b'not JSON',
    b'[]',
    b'{"tag_name": "v3.0.0"}',
    b'{"tag_name": "v3.0.0", "draft": true, "prerelease": false}',
    b'{"tag_name": "v3.0.0-rc.1", "draft": false, "prerelease": false}',
    b'{"tag_name": "v3.0.0/../../bad", "draft": false, "prerelease": false}',
    b'{"tag_name": "v3.0.0", "draft": false, "prerelease": true}',
])
def test_reject_invalid_or_unstable_feed(feed):
    with pytest.raises(ValueError):
        latest_version(feed, '2.3.0')


@pytest.fixture
def app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


@pytest.fixture
def mock_feed(monkeypatch):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Event, Thread

    from src.tidycore import updater

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append((self.path, self.headers.get('User-Agent')))
            if response.get('stall'):
                done.wait(5)
                return
            self.send_response(response['status'])
            self.send_header('Content-Length', str(len(response['body'])))
            self.send_header('Location', '/must-not-follow')
            self.end_headers()
            try:
                self.wfile.write(response['body'])
            except ConnectionError:
                pass

        def log_message(self, *args):
            pass

    monkeypatch.setattr(updater, '__version__', '2.3.0')
    requests = []
    response = {'status': 200, 'body': b'{"tag_name":"v2.10.0","draft":false,"prerelease":false}'}
    done = Event()
    with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        monkeypatch.setattr(updater, 'LATEST_RELEASE_API',
                            f'http://127.0.0.1:{server.server_port}/releases/latest')
        thread = Thread(target=server.serve_forever)
        thread.start()
        try:
            yield response, requests
        finally:
            done.set()
            server.shutdown()
            thread.join()


@pytest.mark.parametrize(('change', 'version', 'error'), [
    ({}, '2.10.0', ''),
    ({'body': b'{"tag_name":"v2.3.0","draft":false,"prerelease":false}'}, '', ''),
    ({'body': b'{"tag_name":"v3.0.0","draft":false,"prerelease":false,'
              b'"html_url":"https://untrusted.example/","assets":[{"url":"https://untrusted.example/"}]}'},
     '3.0.0', ''),
    ({'body': b'{"tag_name":"v9.0.0/../../payload","draft":false,"prerelease":false}'}, '', 'invalid'),
    ({'body': b'x' * (256 * 1024 + 1)}, '', 'too much'),
    ({'status': 302}, '', 'Could not check'),
    ({'status': 403}, '', 'Could not check'),
    ({'stall': True}, '', 'timed out'),
])
def test_release_check_against_mock_feed(app, mock_feed, monkeypatch, change, version, error):
    from PySide6.QtCore import QEventLoop, QTimer

    from src.tidycore import updater

    response, requests = mock_feed
    response.update(change)
    monkeypatch.delenv('TIDYCORE_TEST_MODE')
    if change.get('stall'):
        monkeypatch.setattr(updater, 'CHECK_TIMEOUT_MS', 1000)
    checker = updater.ReleaseChecker()
    results = []
    loop = QEventLoop()
    checker.completed.connect(lambda *result: results.append(result))
    checker.completed.connect(loop.quit)
    assert checker.check()
    assert not checker.check()
    QTimer.singleShot(5000, loop, loop.quit)
    loop.exec()
    [(actual_version, actual_error)] = results
    assert actual_version == version
    if error:
        assert error in actual_error
    else:
        assert actual_error == ''
    assert requests == [('/releases/latest', f'TidyCore/{updater.__version__}')]


def test_isolation_blocks_requests_and_installation(app, mock_feed, tmp_path, monkeypatch):
    from src.tidycore import updater

    executable = tmp_path / 'python.exe'
    executable.write_bytes(b'fake interpreter')
    monkeypatch.setattr('sys.executable', str(executable))
    assert not updater.ReleaseChecker().check()
    for frozen in (False, True):
        monkeypatch.setattr('sys.frozen', frozen, raising=False)
        with pytest.raises(RuntimeError, match='disabled'):
            updater.update_manager.download_and_install_update()
    assert executable.read_bytes() == b'fake interpreter'
    assert mock_feed[1] == []
