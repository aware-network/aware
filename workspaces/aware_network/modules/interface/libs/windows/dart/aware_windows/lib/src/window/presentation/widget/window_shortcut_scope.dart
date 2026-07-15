import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/model/window_shortcut_binding.dart';
import '../../domain/provider/window_focus_provider.dart';
import '../../domain/provider/window_shortcut_provider.dart';
import '../../domain/service/window_command_router.dart';
import '../../domain/service/window_shortcut_registry.dart';

class WindowShortcutScope extends ConsumerStatefulWidget {
  const WindowShortcutScope({
    super.key,
    required this.windowId,
    required this.child,
    this.globalBindings = const <ShortcutBinding>[],
    this.windowBindings = const <ShortcutBinding>[],
  });

  final String windowId;
  final Widget child;
  final List<ShortcutBinding> globalBindings;
  final List<ShortcutBinding> windowBindings;

  @override
  ConsumerState<WindowShortcutScope> createState() =>
      _WindowShortcutScopeState();
}

class _WindowShortcutScopeState extends ConsumerState<WindowShortcutScope> {
  ProviderSubscription<WindowFocusState>? _focusSubscription;
  late final WindowShortcutRegistry _shortcutRegistry;

  @override
  void initState() {
    super.initState();
    _shortcutRegistry = ref.read(
      windowShortcutRegistryProvider(widget.windowId).notifier,
    );
    Future.microtask(() {
      if (!mounted) return;
      _shortcutRegistry.registerGlobalBindings(widget.globalBindings);
      _shortcutRegistry.registerWindowBindings(widget.windowBindings);
    });
    _focusSubscription = ref.listenManual<WindowFocusState>(
      windowFocusControllerProvider(widget.windowId),
      (previous, next) => _shortcutRegistry.updateFocus(next),
    );
    _focusSubscription?.read();
  }

  @override
  void didUpdateWidget(WindowShortcutScope oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!listEquals(oldWidget.globalBindings, widget.globalBindings)) {
      Future.microtask(() {
        if (!mounted) return;
        _shortcutRegistry.registerGlobalBindings(widget.globalBindings);
      });
    }
    if (!listEquals(oldWidget.windowBindings, widget.windowBindings)) {
      Future.microtask(() {
        if (!mounted) return;
        _shortcutRegistry.registerWindowBindings(widget.windowBindings);
      });
    }
  }

  @override
  void dispose() {
    _focusSubscription?.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(windowShortcutRegistryProvider(widget.windowId));

    if (state.activeBindings.isEmpty) {
      return widget.child;
    }

    final shortcuts = <ShortcutActivator, Intent>{};
    for (final entry in state.activeBindings.entries) {
      shortcuts[entry.key] = _ShortcutCallbackIntent(
        onInvoke: () {
          final binding = entry.value;
          final shouldRun = binding.when?.call(ref) ?? true;
          if (!shouldRun) {
            return;
          }
          final action = binding.action;
          if (action != null) {
            final result = action(ref);
            if (result is Future) {
              unawaited(
                result.catchError((Object error, StackTrace stack) {
                  debugPrint(
                    'aware_windows shortcut "${binding.id}" error: $error',
                  );
                }),
              );
            }
          } else if (binding.descriptor?.commandId != null) {
            _emitCommand(binding);
          }
        },
      );
    }

    return Shortcuts(
      shortcuts: shortcuts,
      child: Actions(
        actions: <Type, Action<Intent>>{
          _ShortcutCallbackIntent: CallbackAction<_ShortcutCallbackIntent>(
            onInvoke: (_ShortcutCallbackIntent intent) {
              intent.onInvoke();
              return null;
            },
          ),
        },
        child: widget.child,
      ),
    );
  }

  void _emitCommand(ShortcutBinding binding) {
    final targetWindowId =
        binding.commandPayload?[_kShortcutTargetWindowKey] as String? ??
        widget.windowId;
    final payload = _sanitizePayload(binding.commandPayload);
    ref
        .read(windowCommandRouterProvider(targetWindowId))
        .emit(
          WindowCommandIntent(
            commandId: binding.descriptor!.commandId,
            payload: payload,
          ),
        );
  }

  Map<String, dynamic>? _sanitizePayload(Map<String, dynamic>? payload) {
    if (payload == null) {
      return null;
    }
    final sanitized = Map<String, dynamic>.from(payload);
    sanitized.remove(_kShortcutTargetWindowKey);
    if (sanitized.isEmpty) {
      return null;
    }
    return sanitized;
  }
}

class _ShortcutCallbackIntent extends Intent {
  const _ShortcutCallbackIntent({required this.onInvoke});

  final VoidCallback onInvoke;
}

const String _kShortcutTargetWindowKey = 'targetWindowId';
