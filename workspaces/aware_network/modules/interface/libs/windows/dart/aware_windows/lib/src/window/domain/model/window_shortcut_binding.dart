import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart' show ShortcutActivator;
import 'package:flutter_riverpod/flutter_riverpod.dart';

typedef ShortcutAction = FutureOr<void> Function(WidgetRef ref);
typedef ShortcutPredicate = bool Function(WidgetRef ref);

enum ShortcutPriority {
  low(0),
  normal(1),
  high(2);

  const ShortcutPriority(this.weight);
  final int weight;
}

enum ShortcutScopeType { global, window, pane, overlay }

@immutable
class ShortcutScope {
  const ShortcutScope._(this.type, this.identifier);

  final ShortcutScopeType type;
  final String? identifier;

  static const ShortcutScope global = ShortcutScope._(
    ShortcutScopeType.global,
    null,
  );

  static ShortcutScope window(String windowId) =>
      ShortcutScope._(ShortcutScopeType.window, windowId);

  static ShortcutScope pane([String? paneId]) =>
      ShortcutScope._(ShortcutScopeType.pane, paneId);

  static ShortcutScope overlay([String? overlayId]) =>
      ShortcutScope._(ShortcutScopeType.overlay, overlayId);

  ShortcutScope withIdentifier(String id) => ShortcutScope._(type, id);
}

@immutable
class PaneShortcutDescriptor {
  const PaneShortcutDescriptor({
    required this.commandId,
    required this.title,
    this.category,
  });

  final String commandId;
  final String title;
  final String? category;
}

@immutable
class ShortcutBinding {
  ShortcutBinding({
    required this.id,
    required this.activator,
    required this.scope,
    this.priority = ShortcutPriority.normal,
    this.when,
    this.descriptor,
    this.action,
    this.commandPayload,
  });

  final String id;
  final ShortcutActivator activator;
  final ShortcutScope scope;
  final ShortcutPriority priority;
  final ShortcutAction? action;
  final ShortcutPredicate? when;
  final PaneShortcutDescriptor? descriptor;
  final Map<String, dynamic>? commandPayload;

  ShortcutBinding copyWithScope(ShortcutScope newScope) {
    return ShortcutBinding(
      id: id,
      activator: activator,
      scope: newScope,
      priority: priority,
      action: action,
      when: when,
      descriptor: descriptor,
      commandPayload: commandPayload,
    );
  }
}

ShortcutBinding globalShortcut({
  required String id,
  required ShortcutActivator activator,
  ShortcutAction? onInvoke,
  ShortcutPriority priority = ShortcutPriority.normal,
  ShortcutPredicate? when,
  PaneShortcutDescriptor? descriptor,
  Map<String, dynamic>? commandPayload,
}) {
  return ShortcutBinding(
    id: id,
    activator: activator,
    scope: ShortcutScope.global,
    action: onInvoke,
    priority: priority,
    when: when,
    descriptor: descriptor,
    commandPayload: commandPayload,
  );
}

ShortcutBinding windowShortcut({
  required String id,
  required ShortcutActivator activator,
  ShortcutAction? onInvoke,
  ShortcutPriority priority = ShortcutPriority.normal,
  ShortcutPredicate? when,
  PaneShortcutDescriptor? descriptor,
  Map<String, dynamic>? commandPayload,
}) {
  return ShortcutBinding(
    id: id,
    activator: activator,
    scope: ShortcutScope.window(''),
    action: onInvoke,
    priority: priority,
    when: when,
    descriptor: descriptor,
    commandPayload: commandPayload,
  );
}

ShortcutBinding paneShortcut({
  required String id,
  required ShortcutActivator activator,
  ShortcutAction? onInvoke,
  ShortcutPriority priority = ShortcutPriority.normal,
  ShortcutPredicate? when,
  PaneShortcutDescriptor? descriptor,
  Map<String, dynamic>? commandPayload,
}) {
  return ShortcutBinding(
    id: id,
    activator: activator,
    scope: ShortcutScope.pane(),
    action: onInvoke,
    priority: priority,
    when: when,
    descriptor: descriptor,
    commandPayload: commandPayload,
  );
}

ShortcutBinding overlayShortcut({
  required String id,
  required ShortcutActivator activator,
  ShortcutAction? onInvoke,
  ShortcutPriority priority = ShortcutPriority.normal,
  ShortcutPredicate? when,
  PaneShortcutDescriptor? descriptor,
  Map<String, dynamic>? commandPayload,
}) {
  return ShortcutBinding(
    id: id,
    activator: activator,
    scope: ShortcutScope.overlay(),
    action: onInvoke,
    priority: priority,
    when: when,
    descriptor: descriptor,
    commandPayload: commandPayload,
  );
}
