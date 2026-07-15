import 'package:uuid/uuid.dart';

enum DuplexMessageFrameType { request, response, ack, error, notification }

String _frameTypeToWire(DuplexMessageFrameType type) {
  return switch (type) {
    DuplexMessageFrameType.request => 'request',
    DuplexMessageFrameType.response => 'response',
    DuplexMessageFrameType.ack => 'ack',
    DuplexMessageFrameType.error => 'error',
    DuplexMessageFrameType.notification => 'notification',
  };
}

DuplexMessageFrameType _frameTypeFromWire(String value) {
  return switch (value) {
    'request' => DuplexMessageFrameType.request,
    'response' => DuplexMessageFrameType.response,
    'ack' => DuplexMessageFrameType.ack,
    'error' => DuplexMessageFrameType.error,
    'notification' => DuplexMessageFrameType.notification,
    _ => throw ArgumentError.value(
      value,
      'value',
      'Unsupported duplex message frame type',
    ),
  };
}

class DuplexMessageFrame {
  DuplexMessageFrame({
    UuidValue? id,
    required this.type,
    required this.data,
    this.requestId,
  }) : id = id ?? UuidValue.fromString(const Uuid().v4());

  factory DuplexMessageFrame.fromJson(Map<String, dynamic> json) {
    return DuplexMessageFrame(
      id: UuidValue.fromString(json['id'] as String),
      type: _frameTypeFromWire(json['type'] as String),
      data: json['data'] as String,
      requestId: json['request_id'] == null
          ? null
          : UuidValue.fromString(json['request_id'] as String),
    );
  }

  final UuidValue id;
  final DuplexMessageFrameType type;
  final String data;
  final UuidValue? requestId;

  DuplexMessageFrame copyWith({
    UuidValue? id,
    DuplexMessageFrameType? type,
    String? data,
    UuidValue? requestId,
    bool clearRequestId = false,
  }) {
    return DuplexMessageFrame(
      id: id ?? this.id,
      type: type ?? this.type,
      data: data ?? this.data,
      requestId: clearRequestId ? null : (requestId ?? this.requestId),
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id.toString(),
      'type': _frameTypeToWire(type),
      'data': data,
      'request_id': requestId?.toString(),
    };
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        other is DuplexMessageFrame &&
            runtimeType == other.runtimeType &&
            other.id == id &&
            other.type == type &&
            other.data == data &&
            other.requestId == requestId;
  }

  @override
  int get hashCode => Object.hash(id, type, data, requestId);
}
