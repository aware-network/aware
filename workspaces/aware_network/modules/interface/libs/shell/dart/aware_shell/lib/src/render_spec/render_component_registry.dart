import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:flutter/widgets.dart';

import 'pane_render_spec.dart';

typedef RenderComponentWidgetBuilder =
    Widget Function(BuildContext context, RenderComponentBuildData component);

typedef RenderComponentActionPortInvoker =
    Future<void> Function(String componentActionPortKey);

@immutable
class RenderComponentRegistration {
  const RenderComponentRegistration({
    required this.componentRef,
    required this.builder,
    this.displayName,
  });

  final String componentRef;
  final String? displayName;
  final RenderComponentWidgetBuilder builder;

  String get normalizedComponentRef => _normalizeComponentRef(componentRef)!;
}

@immutable
class RenderComponentBuildData {
  const RenderComponentBuildData({
    required this.spec,
    required this.node,
    required this.paneContext,
    required this.inputsByPort,
    required this.actionsByPort,
    required this.invokeActionPort,
    this.materializedState,
  });

  final PaneRenderSpec spec;
  final PaneRenderNode node;
  final PaneContext paneContext;
  final InterfaceMaterializedPaneState? materializedState;
  final Map<String, Object?> inputsByPort;
  final Map<String, PaneActionBinding> actionsByPort;
  final RenderComponentActionPortInvoker invokeActionPort;

  Iterable<String> get inputPortKeys => inputsByPort.keys;
  Iterable<String> get actionPortKeys => actionsByPort.keys;

  Object? input(String componentInputPortKey) {
    return inputsByPort[_normalizeComponentRef(componentInputPortKey)];
  }

  PaneActionBinding? action(String componentActionPortKey) {
    return actionsByPort[_normalizeComponentRef(componentActionPortKey)];
  }

  bool hasAction(String componentActionPortKey) {
    return action(componentActionPortKey) != null;
  }
}

@immutable
class RenderComponentRegistry {
  const RenderComponentRegistry.empty()
    : _registrationsByRef = const <String, RenderComponentRegistration>{};

  factory RenderComponentRegistry.fromRegistrations(
    Iterable<RenderComponentRegistration> registrations,
  ) {
    final byRef = <String, RenderComponentRegistration>{};
    for (final registration in registrations) {
      final componentRef = registration.normalizedComponentRef;
      if (byRef.containsKey(componentRef)) {
        throw ArgumentError.value(
          registration.componentRef,
          'registration.componentRef',
          'duplicate render component registration',
        );
      }
      byRef[componentRef] = registration;
    }
    return RenderComponentRegistry._(
      Map<String, RenderComponentRegistration>.unmodifiable(byRef),
    );
  }

  const RenderComponentRegistry._(this._registrationsByRef);

  final Map<String, RenderComponentRegistration> _registrationsByRef;

  bool get isEmpty => _registrationsByRef.isEmpty;
  bool get isNotEmpty => _registrationsByRef.isNotEmpty;

  Iterable<String> get componentRefs => _registrationsByRef.keys;
  Iterable<RenderComponentRegistration> get registrations =>
      _registrationsByRef.values;

  RenderComponentRegistration? resolve(String? componentRef) {
    final normalized = _normalizeComponentRef(componentRef);
    if (normalized == null) {
      return null;
    }
    return _registrationsByRef[normalized];
  }

  bool supports(String? componentRef) {
    return resolve(componentRef) != null;
  }

  Widget? build(BuildContext context, RenderComponentBuildData component) {
    final registration = resolve(component.node.componentRef);
    if (registration == null) {
      return null;
    }
    return registration.builder(context, component);
  }

  RenderComponentRegistry mergedWith(RenderComponentRegistry other) {
    if (isEmpty) {
      return other;
    }
    if (other.isEmpty) {
      return this;
    }
    return RenderComponentRegistry._(
      Map<String, RenderComponentRegistration>.unmodifiable(
        <String, RenderComponentRegistration>{
          ..._registrationsByRef,
          ...other._registrationsByRef,
        },
      ),
    );
  }
}

class RenderComponentRegistryBuilder {
  final Map<String, RenderComponentRegistration> _registrationsByRef =
      <String, RenderComponentRegistration>{};

  bool get isEmpty => _registrationsByRef.isEmpty;
  bool get isNotEmpty => _registrationsByRef.isNotEmpty;

  Iterable<String> get componentRefs => _registrationsByRef.keys;

  void register(RenderComponentRegistration registration) {
    final componentRef = registration.normalizedComponentRef;
    if (_registrationsByRef.containsKey(componentRef)) {
      throw ArgumentError.value(
        registration.componentRef,
        'registration.componentRef',
        'duplicate render component registration',
      );
    }
    _registrationsByRef[componentRef] = registration;
  }

  void registerAll(Iterable<RenderComponentRegistration> registrations) {
    for (final registration in registrations) {
      register(registration);
    }
  }

  RenderComponentRegistration? resolve(String? componentRef) {
    final normalized = _normalizeComponentRef(componentRef);
    if (normalized == null) {
      return null;
    }
    return _registrationsByRef[normalized];
  }

  bool supports(String? componentRef) {
    return resolve(componentRef) != null;
  }

  RenderComponentRegistry build() {
    if (_registrationsByRef.isEmpty) {
      return const RenderComponentRegistry.empty();
    }
    return RenderComponentRegistry._(
      Map<String, RenderComponentRegistration>.unmodifiable(
        _registrationsByRef,
      ),
    );
  }
}

String? _normalizeComponentRef(String? value) {
  final text = value?.trim();
  if (text == null || text.isEmpty) {
    return null;
  }
  return text;
}
