// ignore_for_file: deprecated_member_use

import 'dart:async';
import 'dart:convert';
import 'dart:html' as html;

abstract class InterfaceControlPlaneConnection {
  Stream<String> get lines;

  Future<void> writeLine(String line);

  Future<void> close();
}

abstract class InterfaceControlPlaneTransport {
  Future<InterfaceControlPlaneConnection> connect();
}

class InterfaceControlPlaneSocketTransport
    implements InterfaceControlPlaneTransport {
  InterfaceControlPlaneSocketTransport({required this.socketPath});

  final String socketPath;

  @override
  Future<InterfaceControlPlaneConnection> connect() async {
    throw UnsupportedError(
      'Local Interface control-plane sockets are not available in browsers. '
      'Use AWARE_INTERFACE_CONTROL_PLANE_URL or a remote WebSocket profile.',
    );
  }
}

class InterfaceControlPlaneWebSocketTransport
    implements InterfaceControlPlaneTransport {
  InterfaceControlPlaneWebSocketTransport({required this.uri});

  final Uri uri;

  @override
  Future<InterfaceControlPlaneConnection> connect() async {
    final socket = html.WebSocket(uri.toString());
    await socket.onOpen.first;
    return _WebInterfaceControlPlaneConnection(socket);
  }
}

class _WebInterfaceControlPlaneConnection
    implements InterfaceControlPlaneConnection {
  _WebInterfaceControlPlaneConnection(this._socket);

  final html.WebSocket _socket;

  @override
  Stream<String> get lines => _socket.onMessage.expand<String>((event) {
    final data = event.data;
    if (data is String) {
      return const LineSplitter().convert(data);
    }
    if (data is List<int>) {
      return const LineSplitter().convert(utf8.decode(data));
    }
    throw StateError(
      'Interface control plane yielded an unsupported WebSocket message '
      'type `${data.runtimeType}`.',
    );
  });

  @override
  Future<void> writeLine(String line) async {
    _socket.send('$line\n');
  }

  @override
  Future<void> close() async {
    if (_socket.readyState == html.WebSocket.CLOSED ||
        _socket.readyState == html.WebSocket.CLOSING) {
      return;
    }
    _socket.close();
    await _socket.onClose.first;
  }
}
