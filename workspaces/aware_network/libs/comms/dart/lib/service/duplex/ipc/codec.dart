import 'dart:convert';

import 'package:aware_comms/service/duplex/protocol/models.dart';

class DuplexIpcFrameCodec {
  const DuplexIpcFrameCodec();

  String encodeFrame(DuplexMessageFrame frame) {
    return '${jsonEncode(frame.toJson())}\n';
  }

  DuplexMessageFrame decodeFrame(String payload) {
    final line = payload.trim();
    if (line.isEmpty) {
      throw ArgumentError.value(
          payload, 'payload', 'IPC frame payload is empty');
    }
    final decoded = jsonDecode(line);
    if (decoded is! Map<String, dynamic>) {
      throw ArgumentError.value(
        payload,
        'payload',
        'IPC frame payload must decode to an object',
      );
    }
    return DuplexMessageFrame.fromJson(decoded);
  }
}
