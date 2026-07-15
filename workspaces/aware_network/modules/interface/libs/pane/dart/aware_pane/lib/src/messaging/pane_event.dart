/// Base event type for panes. The structure is intentionally lightweight so
/// host applications can bridge to their own event systems.
import 'package:aware_messaging/aware_messaging.dart';

/// Base event type for panes. Implements aware_messaging [Event] so pane events
/// flow through the shared event bus without adapters.
abstract class PaneEvent implements Event {
  PaneEvent({
    DateTime? timestamp,
    Map<String, dynamic> metadata = const <String, dynamic>{},
  }) : timestamp = timestamp ?? DateTime.now().toUtc(),
       _metadata = Map.unmodifiable(metadata);

  @override
  final DateTime timestamp;

  final Map<String, dynamic> _metadata;

  @override
  Map<String, dynamic>? get metadata =>
      _metadata.isEmpty ? null : Map<String, dynamic>.from(_metadata);

  @override
  String get eventType => runtimeType.toString();

  /// Convenience alias used by existing pane code.
  String get source => eventType;

  @override
  Map<String, dynamic> toJson() {
    return {
      'eventType': eventType,
      'timestamp': timestamp.toIso8601String(),
      if (_metadata.isNotEmpty) 'metadata': _metadata,
    };
  }
}

/// Events that report the pane instance emitting them.
abstract class IdentifiedPaneEvent extends PaneEvent {
  IdentifiedPaneEvent({required this.paneInstanceId, super.metadata});

  final String paneInstanceId;
}
