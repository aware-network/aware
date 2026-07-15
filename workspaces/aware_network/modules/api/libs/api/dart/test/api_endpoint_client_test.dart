import 'dart:async';

import 'package:aware_api/aware_api.dart';
import 'package:test/test.dart';
import 'package:uuid/uuid.dart';

void main() {
  group('AwareApiClient endpoint helpers', () {
    test(
      'invokeApiEndpoint encodes request payload and decodes response',
      () async {
        final transport = _FakeAwareApiTransport(
          apiResponse: ApiEndpointResponse(
            responsePayload: <String, dynamic>{'accepted': true},
          ),
        );
        final actorId = UuidValue.fromString(const Uuid().v4());
        final client = AwareApiClient(
          transport: transport,
          config: AwareApiConfig(
            context: AwareApiContext(
              environmentId: UuidValue.fromString(const Uuid().v4()),
              actorId: actorId,
            ),
          ),
        );

        final payload = await client.invokeApiEndpoint<Map<String, dynamic>>(
          endpointRef: 'agent.session.start_session',
          discriminant: 'agent.session.start_session',
          requestPayload: <String, Object?>{
            'session_id': UuidValue.fromString(
              '00000000-0000-0000-0000-000000000010',
            ),
            'created_at': DateTime.utc(2026, 4, 16, 12, 0, 0),
          },
          decodeResponse: (payload) => payload! as Map<String, dynamic>,
        );

        expect(payload, <String, dynamic>{'accepted': true});
        expect(transport.lastApiRequest, isNotNull);
        expect(transport.lastApiRequest!.actorId, actorId);
        expect(transport.lastApiRequest!.requestPayload, <String, dynamic>{
          'session_id': '00000000-0000-0000-0000-000000000010',
          'created_at': '2026-04-16T12:00:00.000Z',
        });
      },
    );

    test('ensureReady uses the generated environment API endpoint rail',
        () async {
      final actorId = UuidValue.fromString(const Uuid().v4());
      final environmentId = UuidValue.fromString(const Uuid().v4());
      final transport = _FakeAwareApiTransport(
        apiResponse: ApiEndpointResponse(
          responsePayload: <String, dynamic>{
            'operation': 'ensure_ready',
            'actor_id': actorId.toString(),
            'environment_id': environmentId.toString(),
            'status': 'succeeded',
          },
        ),
      );
      final client = AwareApiClient(
        transport: transport,
        config: AwareApiConfig(
          context: AwareApiContext(
            environmentId: environmentId,
            actorId: actorId,
          ),
        ),
      );

      final response = await client.ensureReady();

      expect(response?['status'], 'succeeded');
      expect(transport.lastApiRequest, isNotNull);
      expect(
        transport.lastApiRequest!.endpointRef,
        'environment.ready.ensure_ready',
      );
      expect(
        transport.lastApiRequest!.discriminant,
        'environment.ready.ensure_ready',
      );
      expect(transport.lastApiRequest!.actorId, actorId);
      expect(
        transport.lastApiRequest!.requestPayload,
        containsPair(
          'operation',
          'ensure_ready',
        ),
      );
      expect(
        transport.lastApiRequest!.requestPayload,
        containsPair(
          'environment_id',
          environmentId.toString(),
        ),
      );
    });

    test(
      'streamApiEndpoint yields typed event payloads and closes handle',
      () async {
        final events = StreamController<ApiEndpointResponse>();
        var closed = false;
        final transport = _FakeAwareApiTransport(
          apiStreamHandle: ApiEndpointStream(
            response: Future.value(
              const ApiEndpointResponse(
                responsePayload: <String, dynamic>{'accepted': true},
                streamLifecycle: 'started',
              ),
            ),
            events: events.stream,
            close: () async {
              closed = true;
              await events.close();
            },
          ),
        );
        final client = AwareApiClient(
          transport: transport,
          config: AwareApiConfig(
            context: AwareApiContext(
              environmentId: UuidValue.fromString(const Uuid().v4()),
            ),
          ),
        );

        unawaited(
          Future<void>(() async {
            events.add(
              const ApiEndpointResponse(
                status: 'pending',
                responsePayload: <String, dynamic>{'text': 'hello'},
                streamLifecycle: 'started',
              ),
            );
            events.add(
              const ApiEndpointResponse(
                status: 'pending',
                responsePayload: <String, dynamic>{'text': 'world'},
                streamLifecycle: 'started',
              ),
            );
            events.add(
              const ApiEndpointResponse(
                responsePayload: null,
                streamLifecycle: 'closed',
              ),
            );
          }),
        );

        final seen = await client
            .streamApiEndpoint<String>(
              endpointRef: 'agent.session.subscribe_session',
              discriminant: 'agent.session.subscribe_session',
              requestPayload: const <String, dynamic>{
                'agent_session_id': 'abc',
              },
              decodeEvent: (payload) =>
                  (payload! as Map<String, dynamic>)['text']! as String,
            )
            .toList();

        expect(seen, <String>['hello', 'world']);
        expect(closed, isTrue);
      },
    );
  });
}

class _FakeAwareApiTransport implements AwareApiTransport {
  _FakeAwareApiTransport({this.apiResponse, this.apiStreamHandle});

  final ApiEndpointResponse? apiResponse;
  final ApiEndpointStream? apiStreamHandle;

  ApiEndpointInvocation? lastApiRequest;

  @override
  Future<ApiEndpointResponse> invoke(
    ApiEndpointInvocation invocation, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    lastApiRequest = invocation;
    return apiResponse!;
  }

  @override
  ApiEndpointStream openStream(
    ApiEndpointInvocation invocation, {
    Duration timeout = const Duration(seconds: 30),
  }) {
    lastApiRequest = invocation;
    return apiStreamHandle!;
  }
}
