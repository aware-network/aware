import 'dart:async';

import 'event.dart';

typedef EventListener<E extends Event> = Future<void> Function(E event);

typedef _EventCallback = Future<void> Function(Event event);

class EventSubscription {
  final Type eventType;
  final _EventCallback callback;

  EventSubscription(this.eventType, this.callback);
}

abstract class EventMiddleware {
  Future<bool> before(Event event) async => true;

  Future<void> after(Event event) async {}
}

class EventBus {
  final Map<Type, List<_EventCallback>> _listeners = {};
  final List<EventMiddleware> _middleware = [];
  final StreamController<Event> _streamController =
      StreamController<Event>.broadcast();

  Stream<Event> get allEvents => _streamController.stream;

  EventSubscription subscribe<E extends Event>(EventListener<E> listener) {
    final Future<void> Function(Event) callback = (Event event) =>
        listener(event as E);
    final registrations = _listeners.putIfAbsent(E, () => <_EventCallback>[]);
    registrations.add(callback);
    return EventSubscription(E, callback);
  }

  void unsubscribe(EventSubscription subscription) {
    final registrations = _listeners[subscription.eventType];
    registrations?.remove(subscription.callback);
  }

  Future<void> publish(Event event) async {
    for (final middleware in _middleware) {
      final shouldContinue = await middleware.before(event);
      if (!shouldContinue) {
        return;
      }
    }

    _streamController.add(event);

    final callbacks = List<_EventCallback>.from(
      _listeners[event.runtimeType] ?? const <_EventCallback>[],
    );
    await Future.wait(
      callbacks.map((callback) async {
        try {
          await callback(event);
        } catch (_) {
          // Errors are intentionally swallowed; handlers should surface via middleware.
        }
      }),
    );

    for (final middleware in _middleware.reversed) {
      await middleware.after(event);
    }
  }

  Stream<E> events<E extends Event>() {
    return _streamController.stream.where((event) => event is E).cast<E>();
  }

  void addMiddleware(EventMiddleware middleware) {
    _middleware.add(middleware);
  }

  void removeMiddleware(EventMiddleware middleware) {
    _middleware.remove(middleware);
  }

  bool hasListeners<E extends Event>() => _listeners[E]?.isNotEmpty ?? false;

  int listenerCount<E extends Event>() => _listeners[E]?.length ?? 0;

  int get totalListenerCount => _listeners.values.fold<int>(
    0,
    (count, callbacks) => count + callbacks.length,
  );

  void clear() {
    _listeners.clear();
    _middleware.clear();
  }

  void dispose() {
    clear();
    _streamController.close();
  }
}
