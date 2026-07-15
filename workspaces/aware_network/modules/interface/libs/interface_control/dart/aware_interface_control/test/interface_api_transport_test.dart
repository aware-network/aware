import 'dart:convert';
import 'dart:io';

import 'package:aware_api/aware_api.dart';
import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:aware_interface_control/aware_interface_control.dart';
import 'package:path/path.dart' as p;
import 'package:test/test.dart';
import 'package:uuid/uuid.dart';

void main() {
  test(
    'transport maps interface_invoke_api to canonical Product A response',
    () async {
      if (Platform.isWindows) {
        return;
      }

      final tempDir = await Directory.systemTemp.createTemp(
        'aware-interface-control-dart-api-transport-invoke-',
      );
      final socketPath = p.join(tempDir.path, 'interface-control.sock');
      final server = await ServerSocket.bind(
        InternetAddress(socketPath, type: InternetAddressType.unix),
        0,
      );

      addTearDown(() async {
        await server.close();
        if (File(socketPath).existsSync()) {
          await File(socketPath).delete();
        }
        await tempDir.delete(recursive: true);
      });

      server.listen((Socket socket) {
        socket
            .cast<List<int>>()
            .transform(utf8.decoder)
            .transform(const LineSplitter())
            .listen((String line) async {
              final operation = InterfaceControlPlaneOperation.fromJson(
                Map<String, dynamic>.from(jsonDecode(line) as Map),
              );
              final request = operation.request;
              expect(request, isA<InterfaceInvokeApiRequest>());
              final invokeRequest = request! as InterfaceInvokeApiRequest;
              expect(invokeRequest.namespace, 'flutter-test');
              expect(invokeRequest.endpointRef, 'agent/session/start_session');
              expect(invokeRequest.discriminant, 'start_session');
              expect(invokeRequest.requestPayload, <String, dynamic>{
                'prompt': 'hello',
              });
              socket.write(
                jsonEncode(
                  InterfaceControlPlaneOperation(
                    response: InterfaceControlPlaneResponse.interfaceInvokeApi(
                      requestId: invokeRequest.requestId,
                      protocolVersion: 1,
                      success: true,
                      namespace: invokeRequest.namespace,
                      endpointRef: invokeRequest.endpointRef,
                      discriminant: invokeRequest.discriminant,
                      serviceStatus: 'succeeded',
                      responsePayload: <String, dynamic>{'accepted': true},
                    ),
                  ).toJson(),
                ),
              );
              socket.write('\n');
              await socket.flush();
              await socket.close();
            });
      });

      final transport = InterfaceControlPlaneApiTransport(
        client: InterfaceControlPlaneClient(socketPath: socketPath),
        namespace: 'flutter-test',
      );

      final response = await transport.invoke(
        ApiEndpointInvocation(
          actorId: UuidValue.fromString(const Uuid().v4()),
          endpointRef: 'agent/session/start_session',
          discriminant: 'start_session',
          requestPayload: <String, dynamic>{'prompt': 'hello'},
        ),
      );

      expect(response.status, 'succeeded');
      expect(response.streamLifecycle, 'auto_close');
      expect(response.responsePayload, <String, dynamic>{'accepted': true});
    },
  );

  test(
    'transport maps interface_stream_api to canonical Product A stream',
    () async {
      if (Platform.isWindows) {
        return;
      }

      final tempDir = await Directory.systemTemp.createTemp(
        'aware-interface-control-dart-api-transport-stream-',
      );
      final socketPath = p.join(tempDir.path, 'interface-control.sock');
      final server = await ServerSocket.bind(
        InternetAddress(socketPath, type: InternetAddressType.unix),
        0,
      );

      addTearDown(() async {
        await server.close();
        if (File(socketPath).existsSync()) {
          await File(socketPath).delete();
        }
        await tempDir.delete(recursive: true);
      });

      server.listen((Socket socket) {
        socket
            .cast<List<int>>()
            .transform(utf8.decoder)
            .transform(const LineSplitter())
            .listen((String line) async {
              final operation = InterfaceControlPlaneOperation.fromJson(
                Map<String, dynamic>.from(jsonDecode(line) as Map),
              );
              final request = operation.request;
              expect(request, isA<InterfaceStreamApiRequest>());
              final streamRequest = request! as InterfaceStreamApiRequest;
              expect(streamRequest.namespace, 'flutter-test');
              expect(
                streamRequest.endpointRef,
                'agent/session/subscribe_session',
              );
              expect(streamRequest.discriminant, 'subscribe_session');
              expect(streamRequest.requestPayload, <String, dynamic>{
                'agent_session_id': 'session-1',
              });

              socket.write(
                jsonEncode(
                  InterfaceControlPlaneOperation(
                    response: InterfaceControlPlaneResponse.interfaceStreamApi(
                      requestId: streamRequest.requestId,
                      protocolVersion: 1,
                      success: true,
                      namespace: streamRequest.namespace,
                      endpointRef: streamRequest.endpointRef,
                      discriminant: streamRequest.discriminant,
                    ),
                  ).toJson(),
                ),
              );
              socket.write('\n');
              socket.write(
                jsonEncode(
                  InterfaceControlPlaneOperation(
                    notification:
                        InterfaceControlPlaneNotification.interfaceApiEvent(
                          notificationId: streamRequest.requestId,
                          protocolVersion: 1,
                          namespace: streamRequest.namespace,
                          endpointRef: streamRequest.endpointRef,
                          discriminant: streamRequest.discriminant,
                          eventKind: 'delta',
                          sequence: 1,
                          itemKey: 'event-1',
                          payload: <String, dynamic>{'text': 'hello'},
                        ),
                  ).toJson(),
                ),
              );
              socket.write('\n');
              socket.write(
                jsonEncode(
                  InterfaceControlPlaneOperation(
                    notification:
                        InterfaceControlPlaneNotification.interfaceApiStreamClosed(
                          notificationId: streamRequest.requestId,
                          protocolVersion: 1,
                          namespace: streamRequest.namespace,
                          endpointRef: streamRequest.endpointRef,
                          discriminant: streamRequest.discriminant,
                          serviceStatus: 'succeeded',
                          responsePayload: <String, dynamic>{'closed': true},
                          error: null,
                        ),
                  ).toJson(),
                ),
              );
              socket.write('\n');
              await socket.flush();
              await socket.close();
            });
      });

      final transport = InterfaceControlPlaneApiTransport(
        client: InterfaceControlPlaneClient(socketPath: socketPath),
        namespace: 'flutter-test',
      );

      final handle = transport.openStream(
        ApiEndpointInvocation(
          actorId: UuidValue.fromString(const Uuid().v4()),
          endpointRef: 'agent/session/subscribe_session',
          discriminant: 'subscribe_session',
          requestPayload: <String, dynamic>{'agent_session_id': 'session-1'},
        ),
      );

      final initialResponse = await handle.response;
      final events = await handle.events.toList();
      await handle.close();

      expect(initialResponse!.status, 'succeeded');
      expect(initialResponse.streamLifecycle, 'started');

      expect(events, hasLength(2));
      expect(events.first.status, 'pending');
      expect(events.first.streamLifecycle, 'started');
      expect(events.first.responsePayload, <String, dynamic>{'text': 'hello'});

      expect(events.last.status, 'succeeded');
      expect(events.last.streamLifecycle, 'closed');
      expect(events.last.responsePayload, <String, dynamic>{'closed': true});
    },
  );
}
