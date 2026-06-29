import 'dart:async';

import 'package:uuid/uuid.dart';

class ApiEndpointInvocation {
  const ApiEndpointInvocation({
    required this.endpointRef,
    required this.discriminant,
    required this.requestPayload,
    this.actorId,
  });

  final String endpointRef;
  final String discriminant;
  final Map<String, dynamic> requestPayload;
  final UuidValue? actorId;
}

class ApiEndpointResponse {
  const ApiEndpointResponse({
    this.status = 'succeeded',
    this.responsePayload,
    this.error,
    this.streamLifecycle = 'auto_close',
  });

  final String status;
  final Object? responsePayload;
  final String? error;
  final String streamLifecycle;
}

class ApiEndpointStream {
  const ApiEndpointStream({
    required this.events,
    required this.close,
    this.response,
  });

  final Stream<ApiEndpointResponse> events;
  final Future<ApiEndpointResponse>? response;
  final Future<void> Function() close;
}

abstract class ApiEndpointTransport {
  Future<ApiEndpointResponse> invoke(
    ApiEndpointInvocation invocation, {
    Duration timeout = const Duration(seconds: 30),
  });
}

abstract class ApiEndpointStreamTransport implements ApiEndpointTransport {
  ApiEndpointStream openStream(
    ApiEndpointInvocation invocation, {
    Duration timeout = const Duration(seconds: 30),
  });
}

abstract class AwareApiTransport implements ApiEndpointStreamTransport {}
