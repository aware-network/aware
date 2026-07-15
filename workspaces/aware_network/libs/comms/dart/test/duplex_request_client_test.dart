import 'dart:convert';
import 'dart:io';

import 'package:aware_comms/aware_comms.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('duplex json request client handles unary ack then response', () async {
    if (Platform.isWindows) {
      return;
    }

    final socketPath = await _createSocketPath('aware-duplex-unary');
    final server = await _bindUnixServer(socketPath);

    server.listen((Socket socket) {
      socket
          .cast<List<int>>()
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((String line) async {
        final frame = DuplexMessageFrame.fromJson(
          jsonDecode(line) as Map<String, dynamic>,
        );
        final codec = const DuplexIpcFrameCodec();
        socket.write(
          codec.encodeFrame(
            DuplexMessageFrame(
              type: DuplexMessageFrameType.ack,
              requestId: frame.id,
              data: jsonEncode(<String, Object?>{'status': 'accepted'}),
            ),
          ),
        );
        socket.write(
          codec.encodeFrame(
            DuplexMessageFrame(
              type: DuplexMessageFrameType.response,
              requestId: frame.id,
              data: jsonEncode(<String, Object?>{'ready': true}),
            ),
          ),
        );
        await socket.flush();
        await socket.close();
      });
    });

    final client =
        DuplexJsonRequestClient<_TestRequest, _TestResponse, _TestEvent>(
      newClient: () => UnixSocketDuplexIpcClient(
        endpoint: DuplexIpcEndpoint.unixSocket(socketPath: socketPath),
      ),
      encodeRequest: (request) => request.toJson(),
      decodeResponse: _TestResponse.fromJson,
      decodeEvent: _TestEvent.fromJson,
    );

    try {
      final response = await client.sendRequest(
        request: const _TestRequest(operation: 'describe'),
      );
      expect(response.ready, isTrue);
    } finally {
      await server.close();
      _cleanupSocketPath(socketPath);
    }
  });

  test('duplex json request client handles streamed notifications', () async {
    if (Platform.isWindows) {
      return;
    }

    final socketPath = await _createSocketPath('aware-duplex-stream');
    final server = await _bindUnixServer(socketPath);

    server.listen((Socket socket) {
      socket
          .cast<List<int>>()
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((String line) async {
        final frame = DuplexMessageFrame.fromJson(
          jsonDecode(line) as Map<String, dynamic>,
        );
        final codec = const DuplexIpcFrameCodec();
        socket.write(
          codec.encodeFrame(
            DuplexMessageFrame(
              type: DuplexMessageFrameType.ack,
              requestId: frame.id,
              data: jsonEncode(<String, Object?>{'status': 'accepted'}),
            ),
          ),
        );
        socket.write(
          codec.encodeFrame(
            DuplexMessageFrame(
              type: DuplexMessageFrameType.notification,
              requestId: frame.id,
              data: jsonEncode(
                <String, Object?>{'kind': 'phase', 'message': 'starting'},
              ),
            ),
          ),
        );
        socket.write(
          codec.encodeFrame(
            DuplexMessageFrame(
              type: DuplexMessageFrameType.response,
              requestId: frame.id,
              data: jsonEncode(<String, Object?>{'ready': true}),
            ),
          ),
        );
        await socket.flush();
        await socket.close();
      });
    });

    final client =
        DuplexJsonRequestClient<_TestRequest, _TestResponse, _TestEvent>(
      newClient: () => UnixSocketDuplexIpcClient(
        endpoint: DuplexIpcEndpoint.unixSocket(socketPath: socketPath),
      ),
      encodeRequest: (request) => request.toJson(),
      decodeResponse: _TestResponse.fromJson,
      decodeEvent: _TestEvent.fromJson,
    );

    try {
      final handle = client.openRequestStream(
        request: const _TestRequest(operation: 'start'),
      );
      final eventsFuture = handle.events.toList();
      final response = await handle.response;
      final events = await eventsFuture;

      expect(response.ready, isTrue);
      expect(events, hasLength(1));
      expect(events.single.kind, 'phase');
      expect(events.single.message, 'starting');
    } finally {
      await server.close();
      _cleanupSocketPath(socketPath);
    }
  });
}

class _TestRequest {
  const _TestRequest({required this.operation});

  final String operation;

  Map<String, dynamic> toJson() {
    return <String, dynamic>{'operation': operation};
  }
}

class _TestResponse {
  const _TestResponse({required this.ready});

  final bool ready;

  factory _TestResponse.fromJson(Map<String, dynamic> json) {
    return _TestResponse(ready: json['ready'] == true);
  }
}

class _TestEvent {
  const _TestEvent({
    required this.kind,
    required this.message,
  });

  final String kind;
  final String message;

  factory _TestEvent.fromJson(Map<String, dynamic> json) {
    return _TestEvent(
      kind: (json['kind'] ?? '').toString(),
      message: (json['message'] ?? '').toString(),
    );
  }
}

Future<String> _createSocketPath(String prefix) async {
  final tempDir = await Directory.systemTemp.createTemp('$prefix-');
  return '${tempDir.path}/service.sock';
}

Future<ServerSocket> _bindUnixServer(String socketPath) async {
  return ServerSocket.bind(
    InternetAddress(socketPath, type: InternetAddressType.unix),
    0,
  );
}

void _cleanupSocketPath(String socketPath) {
  final socketFile = File(socketPath);
  final parent = socketFile.parent;
  if (socketFile.existsSync()) {
    socketFile.deleteSync();
  }
  if (parent.existsSync()) {
    parent.deleteSync(recursive: true);
  }
}
