import 'package:flutter/foundation.dart';

import 'pane_key.dart';

/// Metadata describing a pane selection invocation.
@immutable
class PaneSelectionPayload<TPayload> {
  const PaneSelectionPayload({
    required this.paneKey,
    required this.payload,
    this.parameters = const <String, dynamic>{},
    this.metadata = const <String, Object?>{},
    this.sourceEvent,
  });

  final PaneKey paneKey;
  final TPayload payload;
  final Map<String, dynamic> parameters;
  final Map<String, Object?> metadata;
  final Map<String, Object?>? sourceEvent;

  PaneSelectionPayload<TPayload> copyWith({
    PaneKey? paneKey,
    TPayload? payload,
    Map<String, dynamic>? parameters,
    Map<String, Object?>? metadata,
    Map<String, Object?>? sourceEvent,
  }) {
    return PaneSelectionPayload<TPayload>(
      paneKey: paneKey ?? this.paneKey,
      payload: payload ?? this.payload,
      parameters: parameters ?? this.parameters,
      metadata: metadata ?? this.metadata,
      sourceEvent: sourceEvent ?? this.sourceEvent,
    );
  }
}
