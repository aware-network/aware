import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:aware_comms/service/duplex/ipc/client.dart';
import 'package:aware_comms/service/duplex/ipc/codec.dart';
import 'package:aware_comms/service/duplex/ipc/models.dart';
import 'package:aware_comms/service/duplex/protocol/models.dart';

class UnixSocketDuplexIpcClient implements DuplexIpcClient {
  UnixSocketDuplexIpcClient({
    required DuplexIpcEndpoint endpoint,
    DuplexIpcFrameCodec codec = const DuplexIpcFrameCodec(),
  })  : _endpoint = endpoint,
        _codec = codec {
    if (_endpoint.transport != DuplexIpcTransportKind.unixSocket) {
      throw ArgumentError.value(
        endpoint.transport,
        'endpoint.transport',
        'UnixSocketDuplexIpcClient requires a unixSocket endpoint',
      );
    }
  }

  final DuplexIpcEndpoint _endpoint;
  final DuplexIpcFrameCodec _codec;

  Socket? _socket;
  StreamIterator<String>? _socketLines;

  Future<void> connect() async {
    if (_socket != null) {
      return;
    }
    final socketPath = _endpoint.socketPath;
    if (socketPath == null || socketPath.isEmpty) {
      throw StateError('unix socket endpoint is missing socketPath');
    }
    final address = InternetAddress(
      socketPath,
      type: InternetAddressType.unix,
    );
    final socket = await Socket.connect(address, 0);
    _socket = socket;
    _socketLines = StreamIterator<String>(
      socket
          .cast<List<int>>()
          .transform(utf8.decoder)
          .transform(const LineSplitter()),
    );
  }

  @override
  Future<void> sendFrame(DuplexMessageFrame frame) async {
    await connect();
    final socket = _requireSocket();
    socket.write(_codec.encodeFrame(frame));
    await socket.flush();
  }

  @override
  Future<DuplexMessageFrame> readFrame({
    Duration timeout = const Duration(seconds: 5),
  }) async {
    await connect();
    final socketLines = _requireSocketLines();
    final hasLine = await socketLines.moveNext().timeout(timeout);
    if (!hasLine) {
      throw StateError('unix socket IPC peer closed');
    }
    return _codec.decodeFrame(socketLines.current);
  }

  @override
  Future<DuplexMessageFrame> sendAndReceive(
    DuplexMessageFrame frame, {
    Duration timeout = const Duration(seconds: 5),
  }) async {
    await sendFrame(frame);
    return readFrame(timeout: timeout);
  }

  @override
  Future<void> close() async {
    final socket = _socket;
    if (socket == null) {
      return;
    }
    await socket.close();
    _socket = null;
    _socketLines = null;
  }

  Socket _requireSocket() {
    final socket = _socket;
    if (socket == null) {
      throw StateError('unix socket IPC client is not connected');
    }
    return socket;
  }

  StreamIterator<String> _requireSocketLines() {
    final socketLines = _socketLines;
    if (socketLines == null) {
      throw StateError('unix socket IPC client is not connected');
    }
    return socketLines;
  }
}
