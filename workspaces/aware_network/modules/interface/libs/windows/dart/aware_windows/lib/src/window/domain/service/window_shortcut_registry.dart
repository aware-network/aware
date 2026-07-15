import 'dart:collection';

import 'package:flutter/services.dart' show LogicalKeyboardKey;
import 'package:flutter/widgets.dart' show ShortcutActivator, SingleActivator;
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../model/window_shortcut_binding.dart';
import '../provider/window_focus_provider.dart';

class WindowShortcutState {
  const WindowShortcutState({
    this.activeBindings = const <ShortcutActivator, ShortcutBinding>{},
    this.diagnostics = const <String>[],
  });

  final Map<ShortcutActivator, ShortcutBinding> activeBindings;
  final List<String> diagnostics;
}

class WindowShortcutRegistry extends StateNotifier<WindowShortcutState> {
  WindowShortcutRegistry(this.windowId) : super(const WindowShortcutState());

  final String windowId;

  final List<ShortcutBinding> _globalBindings = <ShortcutBinding>[];
  final List<ShortcutBinding> _windowBindings = <ShortcutBinding>[];
  final Map<String, List<ShortcutBinding>> _paneBindings =
      <String, List<ShortcutBinding>>{};
  final Map<String, List<ShortcutBinding>> _overlayBindings =
      <String, List<ShortcutBinding>>{};

  final List<String> _diagnostics = <String>[];

  String? _activePaneId;
  String? _activeOverlayId;
  bool _isSuspended = false;

  void registerGlobalBindings(Iterable<ShortcutBinding> bindings) {
    _globalBindings
      ..clear()
      ..addAll(
        bindings.map((binding) => binding.copyWithScope(ShortcutScope.global)),
      );
    _rebuildActiveBindings();
  }

  void registerWindowBindings(Iterable<ShortcutBinding> bindings) {
    _windowBindings
      ..clear()
      ..addAll(
        bindings.map(
          (binding) => binding.copyWithScope(ShortcutScope.window(windowId)),
        ),
      );
    _rebuildActiveBindings();
  }

  void registerPaneBindings(String paneId, Iterable<ShortcutBinding> bindings) {
    _paneBindings[paneId] = bindings
        .map((binding) => binding.copyWithScope(ShortcutScope.pane(paneId)))
        .toList(growable: false);
    _rebuildActiveBindings();
  }

  void registerOverlayBindings(
    String overlayId,
    Iterable<ShortcutBinding> bindings,
  ) {
    _overlayBindings[overlayId] = bindings
        .map(
          (binding) => binding.copyWithScope(ShortcutScope.overlay(overlayId)),
        )
        .toList(growable: false);
    _rebuildActiveBindings();
  }

  void unregisterOverlayBindings(String overlayId) {
    final removed = _overlayBindings.remove(overlayId);
    if (removed == null) {
      return;
    }
    _rebuildActiveBindings();
  }

  void updateFocus(WindowFocusState focus) {
    _activePaneId = focus.activePaneId;
    _activeOverlayId = focus.overlayCapture;
    _isSuspended = focus.isSuspended;
    _rebuildActiveBindings();
  }

  List<String> takeDiagnostics() {
    final snapshot = List<String>.from(_diagnostics);
    _diagnostics.clear();
    state = WindowShortcutState(
      activeBindings: state.activeBindings,
      diagnostics: const <String>[],
    );
    return snapshot;
  }

  void clearAll() {
    _globalBindings.clear();
    _windowBindings.clear();
    _paneBindings.clear();
    _overlayBindings.clear();
    _diagnostics.clear();
    _activePaneId = null;
    _activeOverlayId = null;
    _isSuspended = false;
    state = const WindowShortcutState();
  }

  void _rebuildActiveBindings() {
    final Map<_BindingKey, ShortcutBinding> resolved =
        <_BindingKey, ShortcutBinding>{};

    void addBindings(Iterable<ShortcutBinding> bindings) {
      for (final binding in bindings) {
        final key = _BindingKey.fromActivator(binding.activator);
        final existing = resolved[key];
        final shouldOverride =
            existing == null || _shouldOverride(binding, existing);
        if (shouldOverride) {
          if (existing != null && !_isSameBinding(binding, existing)) {
            _diagnostics.add(
              'Shortcut conflict on ${binding.activator}: '
              'replacing "${existing.id}" (${existing.scope.type.name}) '
              'with "${binding.id}" (${binding.scope.type.name}).',
            );
          }
          resolved[key] = binding;
        } else if (!_isSameBinding(binding, existing)) {
          _diagnostics.add(
            'Shortcut collision for ${binding.activator}: '
            '"${existing.id}" (${existing.scope.type.name}) '
            'vs "${binding.id}" (${binding.scope.type.name}).',
          );
        }
      }
    }

    addBindings(_globalBindings);
    addBindings(_windowBindings);

    if (_isSuspended && _activeOverlayId != null) {
      addBindings(_overlayBindings[_activeOverlayId!] ?? const []);
    } else if (_activePaneId != null) {
      addBindings(_paneBindings[_activePaneId!] ?? const []);
    }

    final active = <ShortcutActivator, ShortcutBinding>{};
    for (final binding in resolved.values) {
      active[binding.activator] = binding;
    }

    state = WindowShortcutState(
      activeBindings: UnmodifiableMapView<ShortcutActivator, ShortcutBinding>(
        active,
      ),
      diagnostics: List.unmodifiable(_diagnostics),
    );
  }

  bool _shouldOverride(ShortcutBinding candidate, ShortcutBinding existing) {
    final scopeCompare = _scopePriority(
      candidate.scope,
    ).compareTo(_scopePriority(existing.scope));
    if (scopeCompare > 0) {
      return true;
    }
    if (scopeCompare < 0) {
      return false;
    }
    return candidate.priority.weight >= existing.priority.weight;
  }

  bool _isSameBinding(ShortcutBinding a, ShortcutBinding b) =>
      a.id == b.id &&
      a.scope.type == b.scope.type &&
      a.activator == b.activator;

  int _scopePriority(ShortcutScope scope) {
    switch (scope.type) {
      case ShortcutScopeType.global:
        return 0;
      case ShortcutScopeType.window:
        return 1;
      case ShortcutScopeType.pane:
        return 2;
      case ShortcutScopeType.overlay:
        return 3;
    }
    return 0;
  }
}

class _BindingKey {
  const _BindingKey._single({
    required this.keyId,
    required this.control,
    required this.shift,
    required this.alt,
    required this.meta,
  }) : activatorRef = null;

  const _BindingKey._other(this.activatorRef)
    : keyId = null,
      control = false,
      shift = false,
      alt = false,
      meta = false;

  final int? keyId;
  final bool control;
  final bool shift;
  final bool alt;
  final bool meta;
  final ShortcutActivator? activatorRef;

  factory _BindingKey.fromActivator(ShortcutActivator activator) {
    if (activator is SingleActivator) {
      final LogicalKeyboardKey key = activator.trigger;
      return _BindingKey._single(
        keyId: key.keyId,
        control: activator.control,
        shift: activator.shift,
        alt: activator.alt,
        meta: activator.meta,
      );
    }
    return _BindingKey._other(activator);
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    if (other is! _BindingKey) return false;
    if (activatorRef != null || other.activatorRef != null) {
      return activatorRef == other.activatorRef;
    }
    return keyId == other.keyId &&
        control == other.control &&
        shift == other.shift &&
        alt == other.alt &&
        meta == other.meta;
  }

  @override
  int get hashCode {
    if (activatorRef != null) {
      return identityHashCode(activatorRef);
    }
    return Object.hash(keyId, control, shift, alt, meta);
  }
}
