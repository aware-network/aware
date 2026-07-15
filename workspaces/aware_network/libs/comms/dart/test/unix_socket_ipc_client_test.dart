import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid.dart';

import 'package:aware_comms/aware_comms.dart';

void main() {
  test('unix socket IPC client roundtrip echoes a duplex frame', () async {
    if (Platform.isWindows) {
      return;
    }

    final tempDir = await Directory.systemTemp.createTemp('aware-comms-unix-');
    final socketPath = '${tempDir.path}/aware-comms.sock';
    final codec = DuplexIpcFrameCodec();
    final server = await ServerSocket.bind(
      InternetAddress(socketPath, type: InternetAddressType.unix),
      0,
    );

    server.listen((Socket socket) {
      socket
          .cast<List<int>>()
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((String line) async {
        final frame = codec.decodeFrame(line);
        socket.write(codec.encodeFrame(frame));
        await socket.flush();
        await socket.close();
      });
    });

    final client = UnixSocketDuplexIpcClient(
      endpoint: DuplexIpcEndpoint.unixSocket(socketPath: socketPath),
    );

    try {
      final frame = DuplexMessageFrame(
        id: UuidValue.fromString(const Uuid().v4()),
        type: DuplexMessageFrameType.notification,
        data: '{"ready":true}',
      );

      final response = await client.sendAndReceive(frame);

      expect(response, frame);
    } finally {
      await client.close();
      await server.close();
      if (File(socketPath).existsSync()) {
        File(socketPath).deleteSync();
      }
      tempDir.deleteSync(recursive: true);
    }
  });
}
