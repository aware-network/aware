import 'package:aware_pane/aware_pane.dart' as runtime;

/// Pane events in the app now extend the shared aware_pane runtime implementation
/// so they interoperate with the reusable PaneBus/EventBus surface.
abstract class PaneEvent extends runtime.PaneEvent {
  PaneEvent({DateTime? timestamp, Map<String, dynamic>? metadata})
    : super(
        timestamp: timestamp,
        metadata: metadata ?? const <String, dynamic>{},
      );
}

/// Mixin for events that have a source pane
mixin SourcePaneMixin on PaneEvent {
  String get sourcePaneId;
  String get sourcePaneType;
}

/// Mixin for events that target a specific pane
mixin TargetPaneMixin on PaneEvent {
  String get targetPaneId;
  String get targetPaneType;
}

/// Mixin for events that carry data
mixin DataEventMixin<T> on PaneEvent {
  T get data;
}
