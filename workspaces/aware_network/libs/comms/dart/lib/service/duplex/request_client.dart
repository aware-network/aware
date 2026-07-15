import 'dart:async';
import 'dart:convert';

import 'package:aware_comms/service/duplex/client.dart';
import 'package:aware_comms/service/duplex/protocol/models.dart';
import 'package:uuid/uuid.dart';

typedef DuplexJsonRequestEncoder<TRequest> = Map<String, dynamic> Function(
    TRequest request);
typedef DuplexJsonResponseDecoder<TResponse> = TResponse Function(
    Map<String, dynamic> json);
typedef DuplexJsonEventDecoder<TEvent> = TEvent Function(
    Map<String, dynamic> json);

class DuplexRequestHandle<TEvent, TResponse> {
  const DuplexRequestHandle({
    required this.events,
    required this.response,
    required this.close,
  });

  final Stream<TEvent> events;
  final Future<TResponse> response;
  final Future<void> Function() close;
}

class DuplexJsonRequestClient<TRequest, TResponse, TEvent> {
  DuplexJsonRequestClient({
    required DuplexFrameClient Function() newClient,
    required DuplexJsonRequestEncoder<TRequest> encodeRequest,
    required DuplexJsonResponseDecoder<TResponse> decodeResponse,
    required DuplexJsonEventDecoder<TEvent> decodeEvent,
  })  : _newClient = newClient,
        _encodeRequest = encodeRequest,
        _decodeResponse = decodeResponse,
        _decodeEvent = decodeEvent;

  final DuplexFrameClient Function() _newClient;
  final DuplexJsonRequestEncoder<TRequest> _encodeRequest;
  final DuplexJsonResponseDecoder<TResponse> _decodeResponse;
  final DuplexJsonEventDecoder<TEvent> _decodeEvent;

  Future<TResponse> sendRequest({
    required TRequest request,
    Duration timeout = const Duration(seconds: 5),
  }) async {
    final client = _newClient();
    final frame = DuplexMessageFrame(
      type: DuplexMessageFrameType.request,
      data: jsonEncode(_encodeRequest(request)),
    );

    try {
      await client.sendFrame(frame);
      while (true) {
        final nextFrame = await client.readFrame(timeout: timeout);
        _requireMatchingRequestId(frame: nextFrame, requestId: frame.id);
        switch (nextFrame.type) {
          case DuplexMessageFrameType.response:
            return _decodeResponse(_decodeJsonObject(nextFrame.data));
          case DuplexMessageFrameType.error:
            throw StateError(nextFrame.data);
          case DuplexMessageFrameType.ack:
            continue;
          case DuplexMessageFrameType.request:
          case DuplexMessageFrameType.notification:
            throw StateError(
              'unexpected frame type during duplex unary request: '
              '${nextFrame.type}',
            );
        }
      }
    } finally {
      await client.close();
    }
  }

  DuplexRequestHandle<TEvent, TResponse> openRequestStream({
    required TRequest request,
    Duration timeout = const Duration(seconds: 5),
  }) {
    final client = _newClient();
    final frame = DuplexMessageFrame(
      type: DuplexMessageFrameType.request,
      data: jsonEncode(_encodeRequest(request)),
    );
    final events = StreamController<TEvent>();
    final response = Completer<TResponse>();
    var closed = false;

    Future<void> close() async {
      if (closed) {
        return;
      }
      closed = true;
      await client.close();
      if (!events.isClosed) {
        await events.close();
      }
      if (!response.isCompleted) {
        response.completeError(
          StateError('duplex stream closed before terminal response'),
        );
      }
    }

    unawaited(
      Future<void>(() async {
        try {
          await client.sendFrame(frame);
          while (true) {
            final nextFrame = await client.readFrame(timeout: timeout);
            _requireMatchingRequestId(frame: nextFrame, requestId: frame.id);
            switch (nextFrame.type) {
              case DuplexMessageFrameType.notification:
                events.add(_decodeEvent(_decodeJsonObject(nextFrame.data)));
              case DuplexMessageFrameType.response:
                response.complete(
                  _decodeResponse(_decodeJsonObject(nextFrame.data)),
                );
                break;
              case DuplexMessageFrameType.error:
                throw StateError(nextFrame.data);
              case DuplexMessageFrameType.ack:
                continue;
              case DuplexMessageFrameType.request:
                throw StateError(
                  'unexpected frame type during duplex request stream: '
                  '${nextFrame.type}',
                );
            }
            if (nextFrame.type == DuplexMessageFrameType.response) {
              break;
            }
          }
        } catch (error, stackTrace) {
          if (!events.isClosed) {
            events.addError(error, stackTrace);
          }
          if (!response.isCompleted) {
            response.completeError(error, stackTrace);
          }
        } finally {
          await client.close();
          if (!events.isClosed) {
            await events.close();
          }
        }
      }),
    );

    return DuplexRequestHandle<TEvent, TResponse>(
      events: events.stream,
      response: response.future,
      close: close,
    );
  }
}

void _requireMatchingRequestId({
  required DuplexMessageFrame frame,
  required UuidValue requestId,
}) {
  if (frame.requestId != requestId) {
    throw StateError(
      'duplex frame request_id mismatch '
      '(expected=$requestId actual=${frame.requestId})',
    );
  }
}

Map<String, dynamic> _decodeJsonObject(String payload) {
  final decoded = jsonDecode(payload);
  if (decoded is! Map<String, dynamic>) {
    throw StateError('duplex payload must decode to an object');
  }
  return decoded;
}
