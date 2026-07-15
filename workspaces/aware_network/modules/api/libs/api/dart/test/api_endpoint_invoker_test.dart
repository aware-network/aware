import 'dart:async';

import 'package:aware_api/aware_api.dart';
import 'package:test/test.dart';
import 'package:uuid/uuid.dart';

void main() {
  group('AwareApiEndpointInvoker', () {
    test('normalizes request payload and decodes typed response', () async {
      final transport = _FakeEndpointTransport(
        response: const ApiEndpointResponse(
          status: 'succeeded',
          responsePayload: <String, dynamic>{'accepted': true},
        ),
      );
      final actorId = UuidValue.fromString(const Uuid().v4());
      final invoker = AwareApiEndpointInvoker(transport: transport);

      final response = await invoker.invokeApiEndpoint<Map<String, dynamic>>(
        actorId: actorId,
        endpointRef: 'identity.signup.via_profile',
        discriminant: 'identity.signup.via_profile',
        requestPayload: <String, Object?>{
          'profile_id': UuidValue.fromString(
            '00000000-0000-0000-0000-000000000011',
          ),
          'created_at': DateTime.utc(2026, 4, 30, 10, 0, 0),
        },
        decodeResponse: (payload) => payload! as Map<String, dynamic>,
      );

      expect(response, <String, dynamic>{'accepted': true});
      expect(transport.lastInvocation, isNotNull);
      expect(transport.lastInvocation!.actorId, actorId);
      expect(transport.lastInvocation!.requestPayload, <String, dynamic>{
        'profile_id': '00000000-0000-0000-0000-000000000011',
        'created_at': '2026-04-30T10:00:00.000Z',
      });
    });

    test('streams endpoint event payloads and closes handle', () async {
      final controller = StreamController<ApiEndpointResponse>();
      var closed = false;
      final transport = _FakeEndpointTransport(
        stream: ApiEndpointStream(
          response: Future.value(
            const ApiEndpointResponse(
              status: 'succeeded',
              streamLifecycle: 'started',
            ),
          ),
          events: controller.stream,
          close: () async {
            closed = true;
            await controller.close();
          },
        ),
      );
      final invoker = AwareApiEndpointInvoker(transport: transport);

      unawaited(
        Future<void>(() async {
          controller.add(
            const ApiEndpointResponse(
              status: 'pending',
              responsePayload: <String, dynamic>{'text': 'one'},
              streamLifecycle: 'started',
            ),
          );
          controller.add(
            const ApiEndpointResponse(
              status: 'pending',
              responsePayload: <String, dynamic>{'text': 'two'},
              streamLifecycle: 'started',
            ),
          );
          controller.add(
            const ApiEndpointResponse(
              status: 'succeeded',
              streamLifecycle: 'closed',
            ),
          );
        }),
      );

      final events = await invoker
          .streamApiEndpoint<String>(
            endpointRef: 'agent.session.subscribe',
            discriminant: 'agent.session.subscribe',
            requestPayload: const <String, Object?>{'session_id': 'abc'},
            decodeEvent: (payload) =>
                (payload! as Map<String, dynamic>)['text']! as String,
          )
          .toList();

      expect(events, <String>['one', 'two']);
      expect(closed, isTrue);
    });
  });
}

class _FakeEndpointTransport implements ApiEndpointStreamTransport {
  _FakeEndpointTransport({this.response, this.stream});

  final ApiEndpointResponse? response;
  final ApiEndpointStream? stream;

  ApiEndpointInvocation? lastInvocation;

  @override
  Future<ApiEndpointResponse> invoke(
    ApiEndpointInvocation invocation, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    lastInvocation = invocation;
    return response!;
  }

  @override
  ApiEndpointStream openStream(
    ApiEndpointInvocation invocation, {
    Duration timeout = const Duration(seconds: 30),
  }) {
    lastInvocation = invocation;
    return stream!;
  }
}
