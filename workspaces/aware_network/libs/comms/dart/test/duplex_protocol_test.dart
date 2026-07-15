import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid.dart';

import 'package:aware_comms/aware_comms.dart';

void main() {
  test('duplex message frame roundtrip preserves payload', () {
    final frame = DuplexMessageFrame(
      id: UuidValue.fromString(const Uuid().v4()),
      type: DuplexMessageFrameType.request,
      data: '{"ping":"pong"}',
    );

    final restored = DuplexMessageFrame.fromJson(frame.toJson());

    expect(restored.id, frame.id);
    expect(restored.type, DuplexMessageFrameType.request);
    expect(restored.data, '{"ping":"pong"}');
    expect(restored.requestId, isNull);
  });

  test('websocket frame compatibility maps onto duplex protocol', () {
    final wsFrame = WsMessageFrame(
      id: UuidValue.fromString(const Uuid().v4()),
      type: WsMessageFrameType.notification,
      data: '{"ready":true}',
    );

    final duplex = wsFrame.toDuplex();
    final restored = WsMessageFrame.fromJson(wsFrame.toJson());

    expect(duplex.type, DuplexMessageFrameType.notification);
    expect(restored.type, WsMessageFrameType.notification);
    expect(restored.data, '{"ready":true}');
  });
}
