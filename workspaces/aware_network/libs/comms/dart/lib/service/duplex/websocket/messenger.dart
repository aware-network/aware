import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:logging/logging.dart';
import 'package:uuid/uuid.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import 'package:aware_comms/service/duplex/websocket/message/models.dart';
import 'package:aware_comms/provider/null_websocket_channel.dart';

import 'package:aware_network_api/comms/models/network.dart' as kernel_dto;
import 'package:aware_network_api/network/network_enums.dart' as kernel_net;
import 'package:aware_network_api/comms/models/network_node.dart'
    as kernel_node;

class InterfaceSessionAck {
  const InterfaceSessionAck({
    required this.protocolVersion,
    required this.serverTime,
    required this.interfaceSessionId,
    this.nodeId,
    this.interfaceIdentityNetworkNodeId,
    this.interfaceSessionNetworkBindingId,
  });

  final int protocolVersion;
  final DateTime serverTime;
  final UuidValue interfaceSessionId;
  final UuidValue? nodeId;
  final UuidValue? interfaceIdentityNetworkNodeId;
  final UuidValue? interfaceSessionNetworkBindingId;
}

/// Status of a WebSocket request future
enum WsFutureStatus {
  @JsonValue('created')
  created,
  @JsonValue('received_ack')
  receivedAck,
  @JsonValue('finished_failed')
  finishedFailed,
  @JsonValue('finished_succeeded')
  finishedSucceeded,
}

/// A future for tracking WebSocket request/response pairs
class WsFuture<T> {
  final UuidValue requestId;
  final Completer<T> _completer = Completer<T>();
  final T Function(Object decoded) _decode;
  WsFutureStatus status = WsFutureStatus.created;

  WsFuture(this.requestId, {required T Function(Object decoded) decode})
      : _decode = decode;

  Future<T> get future => _completer.future;

  bool get isCompleted => _completer.isCompleted;

  void complete(T result) {
    if (!_completer.isCompleted) {
      status = WsFutureStatus.finishedSucceeded;
      _completer.complete(result);
    }
  }

  void completeError(Object error, [StackTrace? stackTrace]) {
    if (!_completer.isCompleted) {
      status = WsFutureStatus.finishedFailed;
      _completer.completeError(error, stackTrace);
    }
  }

  void markAsAcknowledged() {
    status = WsFutureStatus.receivedAck;
  }

  T decode(Object decoded) => _decode(decoded);
}

/// WebSocket messenger for handling NetworkOperation communication
class NetworkMessenger {
  final Logger _logger = Logger('NetworkMessenger');
  final WebSocketChannel _channel;
  final VoidCallback? onError;
  final VoidCallback? onDone;
  final Ref ref;

  final Map<UuidValue, WsFuture<dynamic>> _pendingRequests = {};

  String _encodeJson(Object? value) {
    return json.encode(
      value,
      toEncodable: (nonEncodable) {
        if (nonEncodable is UuidValue) {
          return nonEncodable.toString();
        }
        if (nonEncodable is DateTime) {
          return nonEncodable.toIso8601String();
        }
        if (nonEncodable is Uri) {
          return nonEncodable.toString();
        }
        throw StateError(
          'Converting object to an encodable object failed: ${nonEncodable.runtimeType}',
        );
      },
    );
  }

  // Canonical DTO NetworkOperation handlers by message type
  final Map<kernel_net.NetworkOperationMessageType,
      List<DtoNetworkOperationHandler>> _dtoNetworkHandlers = {
    kernel_net.NetworkOperationMessageType.request: [],
    kernel_net.NetworkOperationMessageType.response: [],
    kernel_net.NetworkOperationMessageType.stream: [],
    kernel_net.NetworkOperationMessageType.notification: [],
  };

  bool _isConnected = false;

  Completer<InterfaceSessionAck>? _pendingHandshake;
  Timer? _handshakeTimer;
  Timer? _heartbeatTimer;
  UuidValue? _activeSessionId;
  UuidValue? _activeIdentityId;
  UuidValue? _activeConnectionId;
  bool _handshakeReady = false;

  // Best-effort diagnostic state for the last request failure.
  Object? _lastSendError;
  StackTrace? _lastSendStackTrace;
  DateTime? _lastSendErrorAt;
  UuidValue? _lastSendRequestId;

  /// Constructor
  NetworkMessenger(this._channel, this.onError, this.onDone, this.ref) {
    _setupChannel();
  }

  /// Register a handler for canonical DTO NetworkOperations.
  void registerNetworkOperationHandler(
    kernel_net.NetworkOperationMessageType messageType,
    DtoNetworkOperationHandler handler,
  ) {
    _dtoNetworkHandlers[messageType]?.add(handler);
    _logger.info('Registered NetworkOperationHandler for ${messageType.name}');
  }

  /// Unregister a handler for canonical DTO NetworkOperations.
  void unregisterNetworkOperationHandler(
    kernel_net.NetworkOperationMessageType messageType,
    DtoNetworkOperationHandler handler,
  ) {
    _dtoNetworkHandlers[messageType]?.remove(handler);
    _logger
        .info('Unregistered NetworkOperationHandler for ${messageType.name}');
  }

  bool get isConnected => _isConnected;
  bool get handshakeReady => _handshakeReady;
  Object? get lastSendError => _lastSendError;
  StackTrace? get lastSendStackTrace => _lastSendStackTrace;
  DateTime? get lastSendErrorAt => _lastSendErrorAt;
  UuidValue? get lastSendRequestId => _lastSendRequestId;

  void _recordSendFailure({
    UuidValue? requestId,
    required Object error,
    StackTrace? stackTrace,
  }) {
    _lastSendError = error;
    _lastSendStackTrace = stackTrace;
    _lastSendErrorAt = DateTime.now().toUtc();
    _lastSendRequestId = requestId;
  }

  void _setupChannel() {
    if (_channel is NullWebSocketChannel) {
      _isConnected = false;
      return;
    }
    _isConnected = true;

    // Listen for incoming messages
    _channel.stream.listen(
      (dynamic message) {
        try {
          if (message is String) {
            final data = json.decode(message) as Map<String, dynamic>;
            handleData(data);
          }
        } catch (e, stackTrace) {
          _logger.severe('Error handling WebSocket message', e, stackTrace);
        }
      },
      onError: (error, stackTrace) {
        _logger.severe('WebSocket error', error, stackTrace);
        _isConnected = false;
        onError?.call();
      },
      onDone: () {
        _logger.info('WebSocket connection closed');
        _isConnected = false;
        onDone?.call();
      },
      cancelOnError: false,
    );
  }

  /// Send a canonical DTO NetworkOperation request and get a response.
  Future<kernel_dto.NetworkOperation?> sendDtoNetworkOperation({
    required kernel_dto.NetworkOperation networkOperation,
    Duration timeout = const Duration(seconds: 30),
    bool allowWithoutHandshake = false,
  }) async {
    if (!_isConnected) {
      _logger.warning('WebSocket is not connected');
      _recordSendFailure(
        requestId: networkOperation.id,
        error: StateError('WebSocket is not connected'),
      );
      return null;
    }

    if (!_handshakeReady && !allowWithoutHandshake) {
      if (_pendingHandshake != null) {
        try {
          await _pendingHandshake!.future;
        } catch (error) {
          _logger.severe('Handshake failed: $error');
          _recordSendFailure(requestId: networkOperation.id, error: error);
          return null;
        }
      } else {
        _logger.warning('Handshake not completed; refusing to send operation.');
        _recordSendFailure(
          requestId: networkOperation.id,
          error: StateError('Handshake not completed'),
        );
        return null;
      }
    }

    final hopList = networkOperation.networkOperationHopList;
    if (hopList == null || hopList.isEmpty) {
      _logger.severe('Kernel DTO NetworkOperation hop list is empty');
      _recordSendFailure(
        requestId: networkOperation.id,
        error: StateError('Kernel DTO NetworkOperation hop list is empty'),
      );
      return null;
    }

    final messageId = networkOperation.id;
    final wsFuture = WsFuture<kernel_dto.NetworkOperation>(
      messageId,
      decode: (decoded) =>
          kernel_dto.NetworkOperation.fromJson(decoded as Map<String, dynamic>),
    );
    _pendingRequests[messageId] = wsFuture;

    final frame = WsMessageFrame(
      id: messageId,
      type: WsMessageFrameType.request,
      data: _encodeJson(networkOperation.toJson()),
      requestId: messageId,
    );

    Timer(timeout, () {
      if (!wsFuture.isCompleted) {
        _pendingRequests.remove(messageId);
        wsFuture.completeError(
          TimeoutException(
              'Request timed out after ${timeout.inSeconds} seconds'),
        );
      }
    });

    try {
      _logger
          .info('Sending Kernel DTO NetworkOperation frame: ${frame.toJson()}');
      sendFrame(frame);
      final result = await wsFuture.future.timeout(timeout);
      _logger.info('Kernel DTO NetworkOperation completed for $messageId');
      return result;
    } catch (e, stackTrace) {
      _pendingRequests.remove(messageId);
      _logger.severe(
          'Failed to send Kernel DTO NetworkOperation', e, stackTrace);
      _recordSendFailure(
        requestId: messageId,
        error: e,
        stackTrace: stackTrace,
      );
      return null;
    }
  }

  /// Send a canonical DTO NetworkOperation notification (fire-and-forget).
  ///
  /// Prefer this for high-frequency operations where a response isn't needed
  /// (e.g. LSP message forwarding).
  Future<bool> sendDtoNetworkOperationNotification({
    required kernel_dto.NetworkOperation networkOperation,
  }) async {
    if (!_isConnected) {
      _logger.warning('WebSocket is not connected');
      return false;
    }

    if (!_handshakeReady) {
      if (_pendingHandshake != null) {
        try {
          await _pendingHandshake!.future;
        } catch (error) {
          _logger.severe('Handshake failed: $error');
          return false;
        }
      } else {
        _logger
            .warning('Handshake not completed; refusing to send notification.');
        return false;
      }
    }

    final hopList = networkOperation.networkOperationHopList;
    if (hopList == null || hopList.isEmpty) {
      _logger.severe('Kernel DTO NetworkOperation hop list is empty');
      return false;
    }

    final frame = WsMessageFrame(
      id: networkOperation.id,
      type: WsMessageFrameType.notification,
      data: _encodeJson(networkOperation.toJson()),
    );

    try {
      _logger.fine(
        'Sending Kernel DTO NetworkOperation notification frame: ${frame.toJson()}',
      );
      sendFrame(frame);
      return true;
    } catch (e, stackTrace) {
      _logger.severe('Failed to send Kernel DTO NetworkOperation notification',
          e, stackTrace);
      return false;
    }
  }

  /// Send a WebSocket frame
  void sendFrame(WsMessageFrame frame) {
    if (!_isConnected) {
      throw StateError('WebSocket is not connected');
    }

    try {
      final data = frame.toJson();
      _channel.sink.add(_encodeJson(data));
    } catch (e, stackTrace) {
      _logger.severe('Error sending WebSocket frame', e, stackTrace);
      rethrow;
    }
  }

  /// Handle an incoming WebSocket frame
  Future<void> handleData(Map<String, dynamic> data) async {
    try {
      // Parse the base message frame
      final frame = WsMessageFrame.fromJson(data);

      // Handle based on frame type
      switch (frame.type) {
        case WsMessageFrameType.request:
          await _handleRequestFrame(frame);
          break;
        case WsMessageFrameType.response:
          _handleResponseFrame(frame);
          break;
        case WsMessageFrameType.ack:
          _handleAckFrame(frame);
          break;
        case WsMessageFrameType.error:
          _handleErrorFrame(frame);
          break;
        case WsMessageFrameType.notification:
          await _handleNotificationFrame(frame);
          break;
        default:
          _logger.warning('Unhandled frame type: ${frame.type}');
      }
    } catch (e, stackTrace) {
      _logger.severe('Error handling frame: $e\n$stackTrace');
    }
  }

  /// Handle a request frame containing NetworkOperation
  Future<void> _handleRequestFrame(WsMessageFrame frame) async {
    try {
      // Parse NetworkOperation from frame data
      if (frame.data.isNotEmpty) {
        final decoded = json.decode(frame.data);
        kernel_dto.NetworkOperation? dtoOp;
        try {
          dtoOp = kernel_dto.NetworkOperation.fromJson(
              decoded as Map<String, dynamic>);
        } catch (_) {
          dtoOp = null;
        }

        if (dtoOp != null) {
          final handlers = List<DtoNetworkOperationHandler>.of(
            _dtoNetworkHandlers[
                    kernel_net.NetworkOperationMessageType.request] ??
                const <DtoNetworkOperationHandler>[],
          );
          for (final handler in handlers) {
            try {
              final response = await handler(frame, dtoOp);
              if (response != null) {
                await _sendDtoNetworkOperationResponse(frame, response);
              }
            } catch (e, stackTrace) {
              _logger.severe(
                  'Error in Kernel DTO NetworkOperation handler: $e\n$stackTrace');
            }
          }
        }
      }
    } catch (e, stackTrace) {
      _logger.severe('Error handling request frame: $e\n$stackTrace');

      // Send error response
      final errorFrame = WsMessageFrame(
        id: frame.id,
        type: WsMessageFrameType.error,
        data: _encodeJson({'message': 'Error processing request: $e'}),
      );

      sendFrame(errorFrame);
    }
  }

  /// Handle a notification frame containing NetworkOperation or handshake events
  Future<void> _handleNotificationFrame(WsMessageFrame frame) async {
    try {
      if (frame.data.isEmpty) {
        return;
      }

      final decoded = json.decode(frame.data);
      kernel_dto.NetworkOperation? dtoOp;
      try {
        dtoOp = kernel_dto.NetworkOperation.fromJson(
            decoded as Map<String, dynamic>);
      } catch (_) {
        dtoOp = null;
      }

      if (dtoOp != null) {
        final handlers = List<DtoNetworkOperationHandler>.of(
          _dtoNetworkHandlers[dtoOp.messageType] ??
              const <DtoNetworkOperationHandler>[],
        );
        for (final handler in handlers) {
          try {
            await handler(frame, dtoOp);
          } catch (e, stackTrace) {
            _logger.severe(
                'Error in Kernel DTO handler (${dtoOp.messageType.name}): $e\n$stackTrace');
          }
        }
      }
    } catch (e, stackTrace) {
      _logger.severe('Error handling notification: $e\n$stackTrace');
    }
  }

  /// Send a canonical DTO NetworkOperation response.
  Future<void> _sendDtoNetworkOperationResponse(
    WsMessageFrame requestFrame,
    kernel_dto.NetworkOperation response,
  ) async {
    final responseFrame = WsMessageFrame(
      id: requestFrame.id,
      type: WsMessageFrameType.response,
      data: _encodeJson(response.toJson()),
    );

    sendFrame(responseFrame);
  }

  /// Handle a response frame
  void _handleResponseFrame(WsMessageFrame frame) {
    final key = frame.requestId ?? frame.id;
    final wsFuture = _pendingRequests[key];

    if (wsFuture == null) {
      _logger.warning('Received response for unknown request: ${key}');
      return;
    }

    if (frame.data.isEmpty) {
      _pendingRequests.remove(key);
      wsFuture.completeError(StateError('Empty response data'));
      return;
    }

    try {
      final decoded = json.decode(frame.data);
      final parsed = wsFuture.decode(decoded);

      // Notify any registered canonical DTO handlers for this message type.
      // This enables side-effect consumers (e.g., lane sync / receipts) to observe
      // responses without coupling to individual request call sites.
      if (parsed is kernel_dto.NetworkOperation) {
        final handlers = List<DtoNetworkOperationHandler>.of(
          _dtoNetworkHandlers[parsed.messageType] ??
              const <DtoNetworkOperationHandler>[],
        );
        for (final handler in handlers) {
          unawaited(() async {
            try {
              await handler(frame, parsed);
            } catch (e, stackTrace) {
              _logger.severe(
                'Error in Kernel DTO handler (${parsed.messageType.name}): $e\n$stackTrace',
              );
            }
          }());
        }
      }

      _pendingRequests.remove(key);
      wsFuture.complete(parsed);
      _logger.fine('Request ${key} completed successfully');
    } catch (e, stackTrace) {
      _pendingRequests.remove(key);
      wsFuture.completeError(e);
      String? operation;
      Object? statusValue;
      Object? providerValue;
      List<String>? keysPreview;
      try {
        final decoded = json.decode(frame.data);
        if (decoded is Map) {
          operation = decoded['operation']?.toString();
          statusValue = decoded['status'];
          providerValue = decoded['provider'];
          keysPreview = decoded.keys.map((k) => k.toString()).take(20).toList();
        }
      } catch (_) {
        // Ignore diagnostics failures.
      }

      final diag = <String>[
        if (operation != null) 'operation=$operation',
        if (statusValue != null || (keysPreview?.contains('status') ?? false))
          'statusType=${statusValue?.runtimeType}',
        if (providerValue != null ||
            (keysPreview?.contains('provider') ?? false))
          'providerType=${providerValue?.runtimeType}',
        if (keysPreview != null && keysPreview.isNotEmpty)
          'keys=${keysPreview.join(',')}',
        'len=${frame.data.length}',
      ].join(' ');

      _logger
          .severe('Error decoding response for $key ($diag): $e\n$stackTrace');
    }
  }

  /// Handle an acknowledgment frame
  void _handleAckFrame(WsMessageFrame frame) {
    try {
      final key = frame.requestId ?? frame.id;
      final wsFuture = _pendingRequests[key];

      if (wsFuture != null) {
        wsFuture.markAsAcknowledged();
        _logger.fine('Request ${key} acknowledged');
      } else {
        _logger.warning('Received ack for unknown request: ${key}');
      }
    } catch (e, stackTrace) {
      _logger.severe('Error processing ack: $e\n$stackTrace');
    }
  }

  /// Handle an error frame
  void _handleErrorFrame(WsMessageFrame frame) {
    try {
      final key = frame.requestId ?? frame.id;
      final wsFuture = _pendingRequests[key];

      if (wsFuture != null) {
        _pendingRequests.remove(key);

        // Extract error data
        final errorData = frame.data.isNotEmpty ? json.decode(frame.data) : {};
        final errorMessage = errorData is Map
            ? (errorData['message'] as String? ?? 'Unknown error')
            : 'Error: $errorData';

        wsFuture.completeError(errorMessage);
        _logger.warning('Request ${key} failed: $errorMessage');
      } else {
        _logger.warning('Received error for unknown request: ${key}');
      }
    } catch (e, stackTrace) {
      _logger.severe('Error processing error frame: $e\n$stackTrace');
    }
  }

  Future<InterfaceSessionAck> sendHandshake({
    required UuidValue interfaceId,
    required UuidValue sessionId,
    required UuidValue identityId,
    required List<String> capabilities,
    required int protocolVersion,
    String? sessionLabel,
    Duration timeout = const Duration(seconds: 15),
  }) async {
    if (!_isConnected) {
      throw StateError('WebSocket is not connected');
    }
    if (_pendingHandshake != null && !_pendingHandshake!.isCompleted) {
      throw StateError('Handshake already in progress');
    }

    final completer = Completer<InterfaceSessionAck>();
    _pendingHandshake = completer;
    _activeSessionId = sessionId;
    _activeIdentityId = identityId;
    _activeConnectionId = interfaceId;
    _handshakeReady = false;

    _handshakeTimer?.cancel();
    _handshakeTimer = Timer(timeout, () {
      if (!completer.isCompleted) {
        completer.completeError(
          TimeoutException('Handshake timed out after ${timeout.inSeconds}s'),
        );
        _pendingHandshake = null;
        _activeSessionId = null;
        _activeIdentityId = null;
        _activeConnectionId = null;
      }
    });

    try {
      final hop = kernel_dto.NetworkOperationHop(
        sourceAppType: kernel_net.NetworkAppType.interface_,
        sourceInterfaceId: interfaceId,
        targetAppType: kernel_net.NetworkAppType.networkNode,
        targetNodeId: null,
      );

      final networkRequest = kernel_dto.NetworkRequest(
        id: UuidValue.fromString(const Uuid().v4()),
        requesterId: identityId,
        status: kernel_net.NetworkRequestStatus.pending,
      );

      final register =
          kernel_node.NetworkNodeOperationRequest.interfaceSessionRegister(
        actorId: identityId,
        nodeId: null,
        interfaceId: interfaceId,
        interfaceSessionId: sessionId,
        sessionLabel: sessionLabel ?? 'Studio Desktop',
        capabilities: capabilities,
        protocolVersion: protocolVersion,
      );

      final op = kernel_dto.NetworkOperation(
        id: UuidValue.fromString(const Uuid().v4()),
        messageType: kernel_net.NetworkOperationMessageType.request,
        type: kernel_net.NetworkOperationType.networkNode,
        networkRequest: networkRequest,
        networkOperationHopList: [hop],
        networkNodeOperation:
            kernel_node.NetworkNodeOperation(request: register),
      );

      final responseOp = await sendDtoNetworkOperation(
        networkOperation: op,
        timeout: timeout,
        allowWithoutHandshake: true,
      );

      if (responseOp == null) {
        throw TimeoutException('Handshake returned no response');
      }

      final networkStatus = responseOp.networkResponse?.status;
      if (networkStatus == kernel_net.NetworkRequestStatus.failed) {
        throw StateError(
            responseOp.networkResponse?.error ?? 'Handshake failed');
      }

      final response = responseOp.networkNodeOperation?.response;
      if (response is! kernel_node.InterfaceSessionRegisterResponse) {
        throw StateError(
          'Handshake expected InterfaceSessionRegisterResponse but got ${response.runtimeType}',
        );
      }

      if (response.status != 'succeeded') {
        throw StateError(response.error ?? 'Handshake failed');
      }

      final serverTimeRaw = response.lastSeenAt;
      final ackTime = serverTimeRaw != null
          ? DateTime.tryParse(serverTimeRaw)?.toUtc()
          : DateTime.now().toUtc();

      _handshakeTimer?.cancel();
      _handshakeTimer = null;
      _handshakeReady = true;

      final ack = InterfaceSessionAck(
        protocolVersion: response.protocolVersion,
        serverTime: ackTime ?? DateTime.now().toUtc(),
        interfaceSessionId: sessionId,
        nodeId: response.nodeId,
        interfaceIdentityNetworkNodeId: response.interfaceIdentityNetworkNodeId,
        interfaceSessionNetworkBindingId:
            response.interfaceSessionNetworkBindingId,
      );

      if (!completer.isCompleted) {
        completer.complete(ack);
      }
      _pendingHandshake = null;
      return ack;
    } catch (error, stackTrace) {
      _logger.severe('Handshake failed: $error', error, stackTrace);

      _handshakeTimer?.cancel();
      _handshakeTimer = null;
      _pendingHandshake = null;
      _handshakeReady = false;
      _activeSessionId = null;
      _activeIdentityId = null;
      _activeConnectionId = null;

      if (!completer.isCompleted) {
        completer.completeError(error, stackTrace);
      }
      rethrow;
    }
  }

  void startHeartbeat(Duration interval) {
    final sessionId = _activeSessionId;
    final identityId = _activeIdentityId;
    final connectionId = _activeConnectionId;
    if (sessionId == null || identityId == null || connectionId == null) {
      return;
    }
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(interval, (_) {
      _sendHeartbeat(sessionId, identityId, connectionId);
    });
  }

  void stopHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
  }

  void _sendHeartbeat(
      UuidValue sessionId, UuidValue identityId, UuidValue connectionId) {
    if (!_isConnected) return;

    final hop = kernel_dto.NetworkOperationHop(
      sourceAppType: kernel_net.NetworkAppType.interface_,
      sourceInterfaceId: connectionId,
      targetAppType: kernel_net.NetworkAppType.networkNode,
      targetNodeId: null,
    );

    final networkRequest = kernel_dto.NetworkRequest(
      id: UuidValue.fromString(const Uuid().v4()),
      requesterId: identityId,
      status: kernel_net.NetworkRequestStatus.pending,
    );

    final heartbeat =
        kernel_node.NetworkNodeOperationRequest.interfaceSessionHeartbeat(
      actorId: identityId,
      nodeId: null,
      interfaceSessionId: sessionId,
      timestamp: DateTime.now().toUtc().toIso8601String(),
    );

    final op = kernel_dto.NetworkOperation(
      id: UuidValue.fromString(const Uuid().v4()),
      messageType: kernel_net.NetworkOperationMessageType.notification,
      type: kernel_net.NetworkOperationType.networkNode,
      networkRequest: networkRequest,
      networkOperationHopList: [hop],
      networkNodeOperation:
          kernel_node.NetworkNodeOperation(request: heartbeat),
    );

    // Fire-and-forget keepalive; failures are logged by the messenger.
    unawaited(sendDtoNetworkOperationNotification(networkOperation: op));
  }

  /// Close the WebSocket connection
  Future<void> close() async {
    stopHeartbeat();
    await _channel.sink.close();
    _isConnected = false;
  }

  void dispose() {
    // Complete any pending requests with an error
    for (final future in _pendingRequests.values.toList()) {
      if (!future.isCompleted) {
        future.completeError('WebSocket connection closed');
      }
    }
    _pendingRequests.clear();
    _dtoNetworkHandlers.clear();
  }
}

/// Type definition for canonical DTO NetworkOperation handler functions.
typedef DtoNetworkOperationHandler = Future<kernel_dto.NetworkOperation?>
    Function(WsMessageFrame frame, kernel_dto.NetworkOperation networkOp);
