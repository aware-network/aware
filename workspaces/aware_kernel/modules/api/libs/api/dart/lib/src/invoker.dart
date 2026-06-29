import 'dart:async';

import 'package:uuid/uuid.dart';

import 'transport.dart';

class AwareApiEndpointInvoker {
  const AwareApiEndpointInvoker({required ApiEndpointTransport transport})
      : _transport = transport;

  final ApiEndpointTransport _transport;

  ApiEndpointTransport get transport => _transport;

  Future<Object?> invokeApiEndpointRaw({
    required String endpointRef,
    required String discriminant,
    Object? requestPayload = const <String, dynamic>{},
    Duration timeout = const Duration(seconds: 30),
    UuidValue? actorId,
  }) async {
    final response = await _transport.invoke(
      ApiEndpointInvocation(
        actorId: actorId,
        endpointRef: _requiredText('endpointRef', endpointRef),
        discriminant: _requiredText('discriminant', discriminant),
        requestPayload: normalizeApiEndpointRequestPayload(requestPayload),
      ),
      timeout: timeout,
    );

    _ensureSucceeded(endpointRef: endpointRef, response: response);
    return response.responsePayload;
  }

  Future<T> invokeApiEndpoint<T>({
    required String endpointRef,
    required String discriminant,
    Object? requestPayload = const <String, dynamic>{},
    required T Function(Object? payload) decodeResponse,
    Duration timeout = const Duration(seconds: 30),
    UuidValue? actorId,
  }) async {
    final payload = await invokeApiEndpointRaw(
      endpointRef: endpointRef,
      discriminant: discriminant,
      requestPayload: requestPayload,
      timeout: timeout,
      actorId: actorId,
    );
    return decodeResponse(payload);
  }

  Stream<Object?> streamApiEndpointRaw({
    required String endpointRef,
    required String discriminant,
    Object? requestPayload = const <String, dynamic>{},
    Duration timeout = const Duration(seconds: 30),
    UuidValue? actorId,
  }) async* {
    final transport = _streamTransport();
    final handle = transport.openStream(
      ApiEndpointInvocation(
        actorId: actorId,
        endpointRef: _requiredText('endpointRef', endpointRef),
        discriminant: _requiredText('discriminant', discriminant),
        requestPayload: normalizeApiEndpointRequestPayload(requestPayload),
      ),
      timeout: timeout,
    );

    try {
      final responseFuture = handle.response;
      if (responseFuture != null) {
        final initial = await responseFuture;
        _ensureStreamStarted(endpointRef: endpointRef, response: initial);
        if (initial.streamLifecycle != 'started') {
          if (initial.responsePayload != null) {
            yield initial.responsePayload;
          }
          return;
        }
      }

      await for (final event in handle.events) {
        _ensureNotFailed(endpointRef: endpointRef, response: event);
        if (event.streamLifecycle == 'closed') {
          break;
        }
        if (event.responsePayload != null) {
          yield event.responsePayload;
        }
      }
    } finally {
      await handle.close();
    }
  }

  Stream<T> streamApiEndpoint<T>({
    required String endpointRef,
    required String discriminant,
    Object? requestPayload = const <String, dynamic>{},
    required T Function(Object? payload) decodeEvent,
    Duration timeout = const Duration(seconds: 30),
    UuidValue? actorId,
  }) async* {
    await for (final payload in streamApiEndpointRaw(
      endpointRef: endpointRef,
      discriminant: discriminant,
      requestPayload: requestPayload,
      timeout: timeout,
      actorId: actorId,
    )) {
      yield decodeEvent(payload);
    }
  }

  ApiEndpointStreamTransport _streamTransport() {
    final transport = _transport;
    if (transport is ApiEndpointStreamTransport) {
      return transport;
    }
    throw StateError('API endpoint transport does not support streaming.');
  }

  void _ensureSucceeded({
    required String endpointRef,
    required ApiEndpointResponse response,
  }) {
    _ensureNotFailed(endpointRef: endpointRef, response: response);
    if (response.status != 'succeeded') {
      throw StateError(
        'API endpoint $endpointRef returned non-terminal status '
        '${response.status}.',
      );
    }
  }

  void _ensureStreamStarted({
    required String endpointRef,
    required ApiEndpointResponse response,
  }) {
    _ensureNotFailed(endpointRef: endpointRef, response: response);
    if (response.streamLifecycle == 'closed' ||
        response.streamLifecycle == 'autoClose' ||
        response.streamLifecycle == 'auto_close') {
      return;
    }
    if (response.streamLifecycle != 'started') {
      throw StateError(
        'API stream $endpointRef returned unsupported stream lifecycle '
        '${response.streamLifecycle}.',
      );
    }
  }

  void _ensureNotFailed({
    required String endpointRef,
    required ApiEndpointResponse response,
  }) {
    if (response.status == 'failed') {
      throw StateError(response.error ?? 'API endpoint $endpointRef failed.');
    }
  }
}

Map<String, dynamic> normalizeApiEndpointRequestPayload(Object? value) {
  final normalized = coerceApiEndpointJson(value);
  if (normalized == null) {
    return const <String, dynamic>{};
  }
  if (normalized is! Map) {
    throw ArgumentError(
      'API request payload must encode to a JSON object, '
      'but got ${normalized.runtimeType}.',
    );
  }
  return normalized.map((key, entry) => MapEntry(key.toString(), entry));
}

dynamic coerceApiEndpointJson(Object? value) {
  if (value == null) return null;
  if (value is UuidValue) return value.toString();
  if (value is DateTime) return value.toIso8601String();
  if (value is num || value is bool || value is String) return value;
  if (value is Enum) return _encodeEnumWireValue(value);
  if (value is Iterable) return value.map(coerceApiEndpointJson).toList();
  if (value is Map) {
    final normalized = <String, dynamic>{};
    value.forEach((key, entry) {
      normalized[key.toString()] = coerceApiEndpointJson(entry);
    });
    return normalized;
  }
  try {
    final dynamic dyn = value;
    final toJson = dyn.toJson;
    if (toJson is Function) {
      return coerceApiEndpointJson(toJson());
    }
  } catch (_) {
    // Fall through to string conversion for legacy DTO-like values.
  }
  return value.toString();
}

String _requiredText(String label, String value) {
  final normalized = value.trim();
  if (normalized.isEmpty) {
    throw ArgumentError.value(value, label, 'must be non-empty');
  }
  return normalized;
}

String _encodeEnumWireValue(Enum value) {
  final name = value.name;
  if (name.isEmpty) return name;

  if (name.toUpperCase() == name) {
    return name.toLowerCase();
  }

  final snake = name.replaceAllMapped(
    RegExp(r'(?<!^)[A-Z]'),
    (m) => '_${m.group(0)!.toLowerCase()}',
  );
  return snake.toLowerCase();
}
