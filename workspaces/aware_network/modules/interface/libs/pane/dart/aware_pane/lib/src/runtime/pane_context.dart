import 'package:flutter/foundation.dart';

import 'pane_key.dart';

/// Execution context supplied to pane factories.
@immutable
class PaneContext {
  const PaneContext({
    required this.paneKey,
    this.instanceId,
    this.parameters = const <String, dynamic>{},
    this.metadata = const <String, Object?>{},
    this.onClose,
  });

  final PaneKey paneKey;
  final String? instanceId;
  final Map<String, dynamic> parameters;
  final Map<String, Object?> metadata;
  final VoidCallback? onClose;

  PaneContext copyWith({
    PaneKey? paneKey,
    String? instanceId,
    Map<String, dynamic>? parameters,
    Map<String, Object?>? metadata,
    VoidCallback? onClose,
  }) {
    return PaneContext(
      paneKey: paneKey ?? this.paneKey,
      instanceId: instanceId ?? this.instanceId,
      parameters: parameters ?? this.parameters,
      metadata: metadata ?? this.metadata,
      onClose: onClose ?? this.onClose,
    );
  }
}
