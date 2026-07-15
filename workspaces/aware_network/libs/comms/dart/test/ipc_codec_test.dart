import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid.dart';

import 'package:aware_comms/aware_comms.dart';

void main() {
  test('ipc endpoint stdio roundtrip preserves command metadata', () {
    final endpoint = DuplexIpcEndpoint.stdio(
      command: <String>['python3', '-m', 'aware.runtime'],
      workingDirectory: '/tmp/aware',
      environment: const <String, String>{'AWARE_ROOT': '/tmp/aware-root'},
    );

    final restored = DuplexIpcEndpoint.fromJson(endpoint.toJson());

    expect(restored.transport, DuplexIpcTransportKind.stdio);
    expect(restored.command, <String>['python3', '-m', 'aware.runtime']);
    expect(restored.workingDirectory, '/tmp/aware');
    expect(
      restored.environment,
      const <String, String>{'AWARE_ROOT': '/tmp/aware-root'},
    );
  });

  test('ipc frame codec roundtrip preserves duplex message frame', () {
    final frame = DuplexMessageFrame(
      id: UuidValue.fromString(const Uuid().v4()),
      type: DuplexMessageFrameType.request,
      data: '{"hello":"world"}',
    );
    const codec = DuplexIpcFrameCodec();

    final restored = codec.decodeFrame(codec.encodeFrame(frame));

    expect(restored, frame);
  });
}
