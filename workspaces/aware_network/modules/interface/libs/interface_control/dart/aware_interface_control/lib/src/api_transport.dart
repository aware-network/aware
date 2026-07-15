import 'dart:async';

import 'package:aware_api/aware_api.dart';

import 'client.dart';

class InterfaceControlPlaneApiTransport implements AwareApiTransport {
  InterfaceControlPlaneApiTransport({
    required InterfaceControlPlaneClient client,
    required this.namespace,
  }) : _client = client;

  final InterfaceControlPlaneClient _client;
  final String namespace;

  @override
  Future<ApiEndpointResponse> invoke(
    ApiEndpointInvocation invocation, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    final response = await _client.invokeApi(
      namespace: namespace,
      endpointRef: invocation.endpointRef,
      discriminant: invocation.discriminant,
      requestPayload: invocation.requestPayload,
    );
    return ApiEndpointResponse(
      status: _normalizeStatus(
        response.serviceStatus,
        fallback: response.error == null ? 'succeeded' : 'failed',
      ),
      error: response.error,
      responsePayload: response.responsePayload,
      streamLifecycle: 'auto_close',
    );
  }

  @override
  ApiEndpointStream openStream(
    ApiEndpointInvocation invocation, {
    Duration timeout = const Duration(seconds: 30),
  }) {
    final events = StreamController<ApiEndpointResponse>();
    final responseCompleter = Completer<ApiEndpointResponse>();
    InterfaceControlPlaneApiStreamHandle? delegateHandle;
    var closed = false;
    var cleanedUp = false;

    Future<void> cleanup({bool closeDelegate = false}) async {
      if (cleanedUp) {
        return;
      }
      cleanedUp = true;
      if (closeDelegate && delegateHandle != null) {
        await delegateHandle!.close();
      }
      if (!events.isClosed) {
        await events.close();
      }
    }

    Future<void> close() async {
      if (closed) {
        return;
      }
      closed = true;
      if (!responseCompleter.isCompleted) {
        responseCompleter.completeError(
          StateError('API stream closed before initial response'),
        );
      }
      await cleanup(closeDelegate: true);
    }

    unawaited(
      Future<void>(() async {
        try {
          delegateHandle = await _client.openApiStream(
            namespace: namespace,
            endpointRef: invocation.endpointRef,
            discriminant: invocation.discriminant,
            requestPayload: invocation.requestPayload,
          );
          if (closed) {
            await cleanup(closeDelegate: true);
            return;
          }

          responseCompleter.complete(
            const ApiEndpointResponse(
              status: 'succeeded',
              responsePayload: null,
              streamLifecycle: 'started',
            ),
          );

          await for (final event in delegateHandle!.events) {
            if (closed) {
              break;
            }
            if (!events.isClosed) {
              events.add(
                ApiEndpointResponse(
                  status: 'pending',
                  responsePayload: event.payload,
                  streamLifecycle: 'started',
                ),
              );
            }
          }

          if (closed) {
            return;
          }
          final terminal = await delegateHandle!.response;
          if (!events.isClosed) {
            events.add(
              ApiEndpointResponse(
                status: _normalizeStatus(
                  terminal.serviceStatus,
                  fallback: terminal.error == null ? 'succeeded' : 'failed',
                ),
                error: terminal.error,
                responsePayload: terminal.responsePayload,
                streamLifecycle: 'closed',
              ),
            );
          }
        } catch (error, stackTrace) {
          if (!responseCompleter.isCompleted) {
            responseCompleter.completeError(error, stackTrace);
          }
          if (!events.isClosed) {
            events.addError(error, stackTrace);
          }
        } finally {
          await cleanup(closeDelegate: true);
        }
      }),
    );

    return ApiEndpointStream(
      events: events.stream,
      response: responseCompleter.future,
      close: close,
    );
  }
}

String _normalizeStatus(String? rawStatus, {required String fallback}) {
  final normalized = rawStatus?.trim();
  if (normalized == null || normalized.isEmpty) {
    return fallback;
  }
  if (normalized == 'succeeded' ||
      normalized == 'failed' ||
      normalized == 'pending') {
    return normalized;
  }
  throw StateError('Unsupported Interface Product A status: $rawStatus');
}
