import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

enum InterfaceSessionStatus {
  unregistered,
  pending,
  registered,
  failed,
}

class InterfaceSessionBinding {
  InterfaceSessionBinding({
    required this.interfaceId,
    required this.identityId,
    required this.sessionId,
    required this.status,
    this.protocolVersion,
    this.lastAckAt,
    this.errorMessage,
    this.nodeId,
    this.interfaceIdentityNetworkNodeId,
    this.interfaceSessionNetworkBindingId,
  });

  final UuidValue interfaceId;
  final UuidValue identityId;
  final UuidValue sessionId;
  final InterfaceSessionStatus status;
  final int? protocolVersion;
  final DateTime? lastAckAt;
  final String? errorMessage;
  final UuidValue? nodeId;
  final UuidValue? interfaceIdentityNetworkNodeId;
  final UuidValue? interfaceSessionNetworkBindingId;

  InterfaceSessionBinding copyWith({
    InterfaceSessionStatus? status,
    int? protocolVersion,
    DateTime? lastAckAt,
    String? errorMessage,
    UuidValue? nodeId,
    UuidValue? interfaceIdentityNetworkNodeId,
    UuidValue? interfaceSessionNetworkBindingId,
  }) {
    return InterfaceSessionBinding(
      interfaceId: interfaceId,
      identityId: identityId,
      sessionId: sessionId,
      status: status ?? this.status,
      protocolVersion: protocolVersion ?? this.protocolVersion,
      lastAckAt: lastAckAt ?? this.lastAckAt,
      errorMessage: errorMessage ?? this.errorMessage,
      nodeId: nodeId ?? this.nodeId,
      interfaceIdentityNetworkNodeId:
          interfaceIdentityNetworkNodeId ?? this.interfaceIdentityNetworkNodeId,
      interfaceSessionNetworkBindingId: interfaceSessionNetworkBindingId ??
          this.interfaceSessionNetworkBindingId,
    );
  }
}

class InterfaceSessionBindingNotifier
    extends StateNotifier<InterfaceSessionBinding?> {
  InterfaceSessionBindingNotifier() : super(null);

  void clear() {
    state = null;
  }

  void reset({
    required UuidValue interfaceId,
    required UuidValue identityId,
  }) {
    state = InterfaceSessionBinding(
      interfaceId: interfaceId,
      identityId: identityId,
      sessionId: UuidValue.fromString(const Uuid().v4()),
      status: InterfaceSessionStatus.pending,
      nodeId: null,
    );
  }

  void markRegistered({
    required int protocolVersion,
    required DateTime ackTime,
    UuidValue? nodeId,
    UuidValue? interfaceIdentityNetworkNodeId,
    UuidValue? interfaceSessionNetworkBindingId,
  }) {
    final current = state;
    if (current == null) return;
    state = current.copyWith(
      status: InterfaceSessionStatus.registered,
      protocolVersion: protocolVersion,
      lastAckAt: ackTime,
      errorMessage: null,
      nodeId: nodeId,
      interfaceIdentityNetworkNodeId: interfaceIdentityNetworkNodeId,
      interfaceSessionNetworkBindingId: interfaceSessionNetworkBindingId,
    );
  }

  void markFailed(String message) {
    final current = state;
    if (current == null) return;
    state = current.copyWith(
      status: InterfaceSessionStatus.failed,
      errorMessage: message,
    );
  }
}

final interfaceSessionBindingNotifierProvider = StateNotifierProvider<
    InterfaceSessionBindingNotifier, InterfaceSessionBinding?>(
  (ref) => InterfaceSessionBindingNotifier(),
);
