"""Reopening the same data directory raises its existing window, even from tray."""
import hashlib

from PySide6.QtCore import QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket


def server_name(data_directory):
    digest = hashlib.sha256(str(data_directory).casefold().encode('utf-8')).hexdigest()[:24]
    return f'TidyCore-{digest}'


def show_existing(name):
    socket = QLocalSocket()
    socket.connectToServer(name)
    if not socket.waitForConnected(1500):
        return False
    socket.write(b'show')
    socket.flush()
    if socket.bytesToWrite():
        socket.waitForBytesWritten(1000)
    received = socket.waitForReadyRead(1500) and bytes(socket.readAll()) == b'ok'
    socket.disconnectFromServer()
    return received


class InstanceServer(QLocalServer):
    def __init__(self, name, window):
        super().__init__(window)
        self.window = window
        self.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self.newConnection.connect(self.accept_connections)
        if not self.listen(name):
            raise RuntimeError(f'Could not open the local window activation channel: {self.errorString()}')

    def accept_connections(self):
        while self.hasPendingConnections():
            socket = self.nextPendingConnection()
            socket.setProperty('request', b'')
            socket.readyRead.connect(lambda current=socket: self.read_request(current))
            socket.disconnected.connect(socket.deleteLater)
            timer = QTimer(socket)
            timer.setSingleShot(True)
            timer.timeout.connect(socket.abort)
            timer.start(3000)
            if socket.bytesAvailable():
                self.read_request(socket)

    def read_request(self, socket):
        request = socket.property('request') + bytes(socket.readAll())
        socket.setProperty('request', request)
        if request == b'show':
            self.window.show_window()
            socket.write(b'ok')
            socket.flush()
            socket.disconnectFromServer()
        elif not b'show'.startswith(request):
            socket.abort()
