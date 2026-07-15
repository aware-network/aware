import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

typedef PaneControllerDisposer<T> = void Function(T controller);

/// Controller registry for window/pane sessions.
///
/// Controllers are kept alive across widget mount/unmount as long as their
/// pane instance remains open inside the window session.
class PaneControllerRegistry {
  final Map<String, Map<String, Map<String, Object>>> _controllers = {};
  final Map<String, Map<String, Map<String, PaneControllerDisposer<Object>>>>
  _disposers = {};

  T obtain<T>(
    String windowSessionId,
    String paneInstanceId,
    String controllerKey,
    PaneControllerEntry<T> entry,
  ) {
    final sessionControllers = _controllers.putIfAbsent(
      windowSessionId,
      () => <String, Map<String, Object>>{},
    );
    final instanceControllers = sessionControllers.putIfAbsent(
      paneInstanceId,
      () => <String, Object>{},
    );

    final existing = instanceControllers[controllerKey];
    if (existing is T) {
      return existing;
    }

    final controller = entry.create();
    instanceControllers[controllerKey] = controller as Object;

    final sessionDisposers = _disposers.putIfAbsent(
      windowSessionId,
      () => <String, Map<String, PaneControllerDisposer<Object>>>{},
    );
    final instanceDisposers = sessionDisposers.putIfAbsent(
      paneInstanceId,
      () => <String, PaneControllerDisposer<Object>>{},
    );
    instanceDisposers[controllerKey] = (controller) =>
        entry.dispose(controller as T);

    return controller;
  }

  void releasePaneInstance(String windowSessionId, String paneInstanceId) {
    final instanceControllers = _controllers[windowSessionId]?[paneInstanceId];
    final instanceDisposers = _disposers[windowSessionId]?[paneInstanceId];
    if (instanceControllers == null) return;

    for (final entry in instanceControllers.entries) {
      final controllerKey = entry.key;
      final controller = entry.value;

      final disposer = instanceDisposers?[controllerKey];
      if (disposer != null) {
        disposer(controller);
        continue;
      }
      if (controller is ChangeNotifier) {
        controller.dispose();
      } else if (controller is Disposable) {
        controller.dispose();
      }
    }

    _controllers[windowSessionId]?.remove(paneInstanceId);
    _disposers[windowSessionId]?.remove(paneInstanceId);

    if (_controllers[windowSessionId]?.isEmpty ?? false) {
      _controllers.remove(windowSessionId);
    }
    if (_disposers[windowSessionId]?.isEmpty ?? false) {
      _disposers.remove(windowSessionId);
    }
  }

  void releaseWindowSession(String windowSessionId) {
    final sessionControllers = _controllers.remove(windowSessionId);
    if (sessionControllers != null) {
      for (final paneInstanceId in sessionControllers.keys.toList()) {
        releasePaneInstance(windowSessionId, paneInstanceId);
      }
    }
    _disposers.remove(windowSessionId);
  }
}

final paneControllerRegistryProvider = Provider<PaneControllerRegistry>(
  (_) => PaneControllerRegistry(),
);

class PaneControllerScope extends InheritedWidget {
  const PaneControllerScope({
    super.key,
    required this.registry,
    required super.child,
  });

  final PaneControllerRegistry registry;

  static PaneControllerRegistry? maybeOf(BuildContext context) => context
      .dependOnInheritedWidgetOfExactType<PaneControllerScope>()
      ?.registry;

  static PaneControllerRegistry of(BuildContext context) {
    final registry = maybeOf(context);
    assert(registry != null, 'PaneControllerScope not found in context');
    return registry!;
  }

  @override
  bool updateShouldNotify(covariant PaneControllerScope oldWidget) =>
      oldWidget.registry != registry;
}

abstract class Disposable {
  void dispose();
}

abstract class PaneControllerEntry<T> {
  const PaneControllerEntry();

  T create();

  void dispose(T controller);
}
