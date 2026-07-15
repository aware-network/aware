import 'dart:async';

import 'package:aware_messaging/aware_messaging.dart';

import 'pane_event.dart';

/// Adapter interface used to integrate external event buses.
abstract class PaneEventDispatcher {
  void publish(PaneEvent event);
  Stream<T> events<T extends PaneEvent>();
}

/// Simple dispatcher backed by a broadcast stream. Hosts can use this as a
/// fallback when they do not have a dedicated bus implementation yet.
class InMemoryPaneEventDispatcher implements PaneEventDispatcher {
  final StreamController<PaneEvent> _controller =
      StreamController<PaneEvent>.broadcast();

  @override
  void publish(PaneEvent event) {
    _controller.add(event);
  }

  @override
  Stream<T> events<T extends PaneEvent>() {
    return _controller.stream.where((event) => event is T).cast<T>();
  }

  void dispose() {
    _controller.close();
  }
}

/// Dispatcher that forwards pane events to an [EventBus] from aware_messaging.
class AwareMessagingPaneDispatcher implements PaneEventDispatcher {
  AwareMessagingPaneDispatcher(this._eventBus);

  final EventBus _eventBus;

  @override
  void publish(PaneEvent event) {
    _eventBus.publish(event);
  }

  @override
  Stream<T> events<T extends PaneEvent>() {
    return _eventBus.events<T>();
  }
}

/// Convenience wrapper used by panes to emit/listen without depending on the
/// concrete dispatcher implementation.
class PaneBus {
  factory PaneBus.fromEventBus(EventBus eventBus) {
    return PaneBus(dispatcher: AwareMessagingPaneDispatcher(eventBus));
  }

  PaneBus({PaneEventDispatcher? dispatcher})
    : _dispatcher = dispatcher ?? InMemoryPaneEventDispatcher();

  final PaneEventDispatcher _dispatcher;

  void emit(PaneEvent event) => _dispatcher.publish(event);

  Stream<T> listen<T extends PaneEvent>() => _dispatcher.events<T>();
}
