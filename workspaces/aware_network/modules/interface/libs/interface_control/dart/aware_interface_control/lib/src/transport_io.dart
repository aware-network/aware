import 'dart:convert';
import 'dart:io';

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
    final address = InternetAddress(socketPath, type: InternetAddressType.unix);
    final socket = await Socket.connect(address, 0);
    return _SocketInterfaceControlPlaneConnection(socket);
  }
}

class InterfaceControlPlaneWebSocketTransport
    implements InterfaceControlPlaneTransport {
  InterfaceControlPlaneWebSocketTransport({required this.uri});

  final Uri uri;

  @override
  Future<InterfaceControlPlaneConnection> connect() async {
    final socket = await WebSocket.connect(uri.toString());
    return _WebSocketInterfaceControlPlaneConnection(socket);
  }
}

class _SocketInterfaceControlPlaneConnection
    implements InterfaceControlPlaneConnection {
  _SocketInterfaceControlPlaneConnection(this._socket);

  final Socket _socket;

  @override
  Stream<String> get lines => _socket
      .cast<List<int>>()
      .transform(utf8.decoder)
      .transform(const LineSplitter());

  @override
  Future<void> writeLine(String line) async {
    _socket.write(line);
    _socket.write('\n');
    await _socket.flush();
  }

  @override
  Future<void> close() async {
    await _socket.close();
  }
}

class _WebSocketInterfaceControlPlaneConnection
    implements InterfaceControlPlaneConnection {
  _WebSocketInterfaceControlPlaneConnection(this._socket);

  final WebSocket _socket;

  @override
  Stream<String> get lines => _socket.map<String>((dynamic message) {
    if (message is String) {
      return message;
    }
    if (message is List<int>) {
      return utf8.decode(message);
    }
    throw StateError(
      'Interface control plane yielded an unsupported WebSocket message type `${message.runtimeType}`.',
    );
  });

  @override
  Future<void> writeLine(String line) async {
    _socket.add(line);
  }

  @override
  Future<void> close() async {
    await _socket.close();
  }
}
