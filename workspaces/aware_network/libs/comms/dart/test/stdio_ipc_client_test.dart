import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid.dart';

import 'package:aware_comms/aware_comms.dart';

void main() {
  test('stdio IPC client roundtrip echoes a duplex frame', () async {
    if (Platform.isWindows) {
      return;
    }

    final client = StdioDuplexIpcClient(
      endpoint: DuplexIpcEndpoint.stdio(command: <String>['/bin/cat']),
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
    }
  });
}
