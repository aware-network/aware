import 'package:uuid/uuid.dart';

import 'package:aware_comms/service/duplex/protocol/models.dart';

enum WsMessageFrameType { request, response, ack, error, notification }

DuplexMessageFrameType _toDuplexType(WsMessageFrameType type) {
  return switch (type) {
    WsMessageFrameType.request => DuplexMessageFrameType.request,
    WsMessageFrameType.response => DuplexMessageFrameType.response,
    WsMessageFrameType.ack => DuplexMessageFrameType.ack,
    WsMessageFrameType.error => DuplexMessageFrameType.error,
    WsMessageFrameType.notification => DuplexMessageFrameType.notification,
  };
}

WsMessageFrameType _fromDuplexType(DuplexMessageFrameType type) {
  return switch (type) {
    DuplexMessageFrameType.request => WsMessageFrameType.request,
    DuplexMessageFrameType.response => WsMessageFrameType.response,
    DuplexMessageFrameType.ack => WsMessageFrameType.ack,
    DuplexMessageFrameType.error => WsMessageFrameType.error,
    DuplexMessageFrameType.notification => WsMessageFrameType.notification,
  };
}

class WsMessageFrame {
  WsMessageFrame({
    UuidValue? id,
    required this.type,
    required this.data,
    this.requestId,
  }) : id = id ?? UuidValue.fromString(const Uuid().v4());

  factory WsMessageFrame.fromDuplex(DuplexMessageFrame frame) {
    return WsMessageFrame(
      id: frame.id,
      type: _fromDuplexType(frame.type),
      data: frame.data,
      requestId: frame.requestId,
    );
  }

  factory WsMessageFrame.fromJson(Map<String, dynamic> json) {
    return WsMessageFrame.fromDuplex(DuplexMessageFrame.fromJson(json));
  }

  final UuidValue id;
  final WsMessageFrameType type;
  final String data;
  final UuidValue? requestId;

  DuplexMessageFrame toDuplex() {
    return DuplexMessageFrame(
      id: id,
      type: _toDuplexType(type),
      data: data,
      requestId: requestId,
    );
  }

  Map<String, dynamic> toJson() => toDuplex().toJson();

  WsMessageFrame copyWith({
    UuidValue? id,
    WsMessageFrameType? type,
    String? data,
    UuidValue? requestId,
    bool clearRequestId = false,
  }) {
    return WsMessageFrame(
      id: id ?? this.id,
      type: type ?? this.type,
      data: data ?? this.data,
      requestId: clearRequestId ? null : (requestId ?? this.requestId),
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        other is WsMessageFrame &&
            runtimeType == other.runtimeType &&
            other.id == id &&
            other.type == type &&
            other.data == data &&
            other.requestId == requestId;
  }

  @override
  int get hashCode => Object.hash(id, type, data, requestId);
}
