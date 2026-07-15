import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'window_chrome_context.dart';
import 'window_chrome_controller.dart';

/// Helper widget that keeps a contributor's [WindowChromeContext] up to date for
/// a given window id.
///
/// Canonical:
/// - Performs provider writes outside of build (microtask).
/// - Removes the contribution on dispose.
class WindowChromeContributor extends ConsumerStatefulWidget {
  const WindowChromeContributor({
    super.key,
    required this.windowId,
    required this.contributorId,
    required this.context,
    required this.child,
  });

  final String windowId;
  final String contributorId;
  final WindowChromeContext? context;
  final Widget child;

  @override
  ConsumerState<WindowChromeContributor> createState() =>
      _WindowChromeContributorState();
}

class _WindowChromeContributorState
    extends ConsumerState<WindowChromeContributor> {
  int? _lastSignature;

  @override
  void initState() {
    super.initState();
    _sync();
  }

  @override
  void didUpdateWidget(WindowChromeContributor oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.windowId != widget.windowId ||
        oldWidget.contributorId != widget.contributorId) {
      _scheduleRemove(oldWidget.windowId, oldWidget.contributorId);
      _lastSignature = null;
    }
    _sync();
  }

  void _sync() {
    final signature = _signature(widget.context);
    if (signature == _lastSignature) {
      return;
    }
    _lastSignature = signature;

    final windowId = widget.windowId;
    final contributorId = widget.contributorId;
    final context = widget.context;

    Future.microtask(() {
      if (!mounted) return;
      final controller = ref.read(
        windowChromeControllerProvider(windowId).notifier,
      );
      if (context == null) {
        controller.remove(contributorId);
      } else {
        controller.upsert(contributorId, context);
      }
    });
  }

  void _scheduleRemove(String windowId, String contributorId) {
    // Remove synchronously while we're still mounted: this avoids leaving stale
    // contributions behind if the widget is disposed before a microtask runs.
    try {
      ref
          .read(windowChromeControllerProvider(windowId).notifier)
          .remove(contributorId);
    } catch (_) {
      // Best-effort cleanup; never crash on teardown/update.
    }
  }

  int _signature(WindowChromeContext? ctx) {
    if (ctx == null) return 0;
    return Object.hash(
      ctx.sectionId,
      ctx.priority,
      ctx.title,
      ctx.subtitle,
      Object.hashAll(
        ctx.breadcrumbs.map(
          (b) => Object.hash(b.label, b.path, b.icon?.codePoint),
        ),
      ),
      Object.hashAll(
        ctx.badges.map(
          (b) => Object.hash(
            b.label,
            b.tooltip,
            b.color?.toARGB32(),
            b.style?.icon?.codePoint,
          ),
        ),
      ),
      Object.hashAll(
        ctx.actions.map(
          (a) => Object.hash(a.icon.codePoint, a.tooltip, a.onPressed != null),
        ),
      ),
      ctx.theme?.backgroundColor?.toARGB32(),
      ctx.theme?.textColor?.toARGB32(),
      ctx.theme?.emphasize,
      ctx.theme?.centerTitle,
      Object.hashAll(
        (ctx.secondary?.badges ?? const []).map(
          (b) => Object.hash(b.label, b.tooltip, b.color?.toARGB32()),
        ),
      ),
      Object.hashAll(
        (ctx.secondary?.breadcrumbs ?? const []).map(
          (b) => Object.hash(b.label, b.path),
        ),
      ),
      ctx.notification?.message,
      ctx.notification?.severity,
      ctx.notification?.icon?.codePoint,
      ctx.notification?.ctaLabel,
    );
  }

  @override
  void dispose() {
    // Remove synchronously: scheduling a microtask here can run after the
    // widget is disposed, and Riverpod forbids using `ref` post-disposal.
    try {
      ref
          .read(windowChromeControllerProvider(widget.windowId).notifier)
          .remove(widget.contributorId);
    } catch (_) {
      // Best-effort cleanup; never crash on teardown.
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
