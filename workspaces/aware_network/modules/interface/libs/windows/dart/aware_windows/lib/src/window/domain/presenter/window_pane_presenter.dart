import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../model/window_config.dart';
import '../provider/window_header_provider.dart';
import '../model/window_pane_header.dart';
import '../model/window_overlay_descriptor.dart';
import '../model/window_shortcut_binding.dart';

typedef WindowPaneBuilder =
    Widget Function(
      BuildContext context,
      WidgetRef ref,
      WindowSectionConfig config,
      HeaderControllerArgs headerArgs,
    );

typedef WindowPaneHeaderResolver =
    WindowPaneHeaderData? Function(WindowSectionConfig config);

typedef WindowPaneOverlayResolver =
    List<WindowOverlayDescriptor> Function(
      WidgetRef ref,
      WindowSectionConfig config,
      HeaderControllerArgs headerArgs,
    );

typedef WindowPaneShortcutContributor =
    Iterable<ShortcutBinding> Function(
      WidgetRef ref,
      WindowSectionConfig config,
      HeaderControllerArgs headerArgs,
    );

class PaneFocusConfig {
  const PaneFocusConfig({this.canRequestFocus = true, this.autofocus = false});

  /// Whether the pane's section can request focus.
  final bool canRequestFocus;

  /// Whether the section should request focus automatically after build.
  final bool autofocus;
}

class WindowPanePresenter {
  WindowPanePresenter({
    required this.paneId,
    required WindowPaneBuilder builder,
    WindowPaneHeaderResolver? header,
    WindowPaneOverlayResolver? overlays,
    PaneFocusConfig? focusConfig,
    WindowPaneShortcutContributor? shortcuts,
  }) : _builder = builder,
       _header = header,
       _overlays = overlays,
       _focusConfig = focusConfig ?? const PaneFocusConfig(),
       _shortcutContributor = shortcuts;

  final String paneId;
  final WindowPaneBuilder _builder;
  final WindowPaneHeaderResolver? _header;
  final WindowPaneOverlayResolver? _overlays;
  final PaneFocusConfig _focusConfig;
  final WindowPaneShortcutContributor? _shortcutContributor;

  Widget build(
    BuildContext context,
    WidgetRef ref,
    WindowSectionConfig config,
    HeaderControllerArgs headerArgs,
  ) {
    return _builder(context, ref, config, headerArgs);
  }

  WindowPaneHeaderData? buildHeader(WindowSectionConfig config) {
    return _header?.call(config);
  }

  List<WindowOverlayDescriptor> buildOverlays(
    WidgetRef ref,
    WindowSectionConfig config,
    HeaderControllerArgs headerArgs,
  ) {
    if (_overlays == null) {
      return const [];
    }
    return _overlays!(ref, config, headerArgs);
  }

  PaneFocusConfig get focusConfig => _focusConfig;

  Iterable<ShortcutBinding> buildShortcuts(
    WidgetRef ref,
    WindowSectionConfig config,
    HeaderControllerArgs headerArgs,
  ) {
    if (_shortcutContributor == null) {
      return const Iterable<ShortcutBinding>.empty();
    }
    return _shortcutContributor!(ref, config, headerArgs);
  }
}

class WindowPaneRegistry {
  WindowPaneRegistry();

  final Map<String, WindowPanePresenter> _presenters = {};
  final List<String> _diagnostics = [];

  bool register(WindowPanePresenter presenter) {
    final existing = _presenters[presenter.paneId];
    if (existing != null && !identical(existing, presenter)) {
      _recordDiagnostic(
        'Duplicate presenter registration for "${presenter.paneId}". '
        'Previous presenter will be replaced.',
      );
    }
    _presenters[presenter.paneId] = presenter;
    return existing == null;
  }

  void registerAll(Iterable<WindowPanePresenter> presenters) {
    for (final presenter in presenters) {
      register(presenter);
    }
  }

  WindowPanePresenter? presenterFor(String paneId) => _presenters[paneId];

  List<String> takeDiagnostics() {
    final snapshot = List<String>.from(_diagnostics);
    _diagnostics.clear();
    return snapshot;
  }

  void clear() {
    _presenters.clear();
    _diagnostics.clear();
  }

  void _recordDiagnostic(String message) {
    _diagnostics.add(message);
    assert(() {
      debugPrint('aware_windows: $message');
      return true;
    }());
  }
}

final windowPaneRegistryProvider = Provider<WindowPaneRegistry>(
  (ref) => WindowPaneRegistry(),
);

class WindowPanePresenterScope extends ConsumerWidget {
  const WindowPanePresenterScope({
    super.key,
    required this.presenters,
    required this.child,
  });

  final List<WindowPanePresenter> presenters;
  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final registry = ref.read(windowPaneRegistryProvider);
    registry.registerAll(presenters);
    registry.takeDiagnostics();
    return child;
  }
}
