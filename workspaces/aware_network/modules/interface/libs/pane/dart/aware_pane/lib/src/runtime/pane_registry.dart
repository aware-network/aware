import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

import '../contracts/pane_agreement_data.dart';
import '../runtime/pane_capabilities.dart';
import '../runtime/pane_context.dart';
import '../runtime/pane_display_info.dart';
import '../runtime/pane_key.dart';
import '../runtime/pane_manifest_contract.dart';
import '../runtime/pane_selection_handler.dart';
import '../runtime/pane_delta_watcher.dart';

/// Signature for factories that build pane widgets.
typedef PaneFactory = Widget Function(PaneContext context);

/// Callback used to observe agreement registration.
typedef PaneAgreementCallback = void Function(PaneAgreementData agreement);

/// Core registry that tracks pane factories, capabilities, agreements, and
/// optional adapters supplied by host applications.
class PaneRegistry {
  PaneRegistry();

  final Map<PaneKey, PaneFactory> _factories = {};
  final Map<PaneKey, PaneCapabilities> _capabilities = {};
  final Map<PaneKey, PaneDisplayInfo> _displayInfo = {};
  final Map<PaneKey, PaneAgreementData> _agreements = {};
  final Map<PaneKey, PaneManifestAdapterContract<dynamic>> _manifestAdapters =
      {};
  final Map<PaneKey, PaneSelectionHandler<dynamic>> _selectionHandlers = {};
  final Map<PaneKey, PaneDeltaWatcherContract<dynamic>> _deltaWatchers = {};

  PaneAgreementCallback? _agreementCallback;
  final List<String> _diagnostics = [];

  /// Registers a pane with the given metadata and optional agreement.
  void registerPane({
    required PaneKey key,
    required PaneFactory factory,
    required PaneCapabilities capabilities,
    PaneDisplayInfo? displayInfo,
    PaneAgreementData? agreement,
  }) {
    if (_factories.containsKey(key)) {
      _recordDiagnostic(
        'Duplicate pane registration for "$key". Previous factory will be replaced.',
      );
    }
    _factories[key] = factory;
    _capabilities[key] = capabilities;
    _displayInfo[key] =
        displayInfo ?? PaneDisplayInfo(paneKey: key, title: key);

    if (agreement != null) {
      _agreements[key] = agreement;
      _agreementCallback?.call(agreement);
    }
  }

  /// Removes the pane and all associated metadata.
  void unregisterPane(PaneKey key) {
    _factories.remove(key);
    _capabilities.remove(key);
    _displayInfo.remove(key);
    _agreements.remove(key);
    _manifestAdapters.remove(key);
    _selectionHandlers.remove(key);
    _deltaWatchers.remove(key);
  }

  /// Builds a pane widget if a factory has been registered.
  Widget? build(PaneKey key, PaneContext context) {
    final factory = _factories[key];
    if (factory == null) {
      return null;
    }
    return factory(context);
  }

  PaneCapabilities? capabilitiesFor(PaneKey key) => _capabilities[key];

  PaneDisplayInfo? displayInfoFor(PaneKey key) => _displayInfo[key];

  PaneAgreementData? agreementFor(PaneKey key) => _agreements[key];

  bool isRegistered(PaneKey key) => _factories.containsKey(key);

  List<PaneKey> registeredPanes() => _factories.keys.toList(growable: false);

  /// Registers a manifest adapter contract for a specific pane.
  void registerManifestAdapter<TPayload>(
    PaneManifestAdapterContract<TPayload> adapter,
  ) {
    if (_manifestAdapters.containsKey(adapter.paneKey)) {
      _recordDiagnostic(
        'Duplicate manifest adapter registration for "${adapter.paneKey}". '
        'Previous adapter will be replaced.',
      );
    }
    _manifestAdapters[adapter.paneKey] = adapter;
  }

  void unregisterManifestAdapter(PaneKey key) {
    _manifestAdapters.remove(key);
  }

  PaneManifestAdapterContract<TPayload>? manifestAdapterFor<TPayload>(
    PaneKey key,
  ) {
    final adapter =
        _manifestAdapters[key] as PaneManifestAdapterContract<TPayload>?;
    return adapter;
  }

  void registerSelectionHandler<TContext>(
    PaneSelectionHandler<TContext> handler,
  ) {
    if (_selectionHandlers.containsKey(handler.paneKey)) {
      _recordDiagnostic(
        'Duplicate selection handler registration for "${handler.paneKey}". '
        'Previous handler will be replaced.',
      );
    }
    _selectionHandlers[handler.paneKey] = handler;
  }

  void unregisterSelectionHandler(PaneKey key) {
    _selectionHandlers.remove(key);
  }

  PaneSelectionHandler<TContext>? selectionHandlerFor<TContext>(PaneKey key) {
    return _selectionHandlers[key] as PaneSelectionHandler<TContext>?;
  }

  void registerDeltaWatcher<TPayload>(
    PaneDeltaWatcherContract<TPayload> watcher,
  ) {
    if (_deltaWatchers.containsKey(watcher.paneKey)) {
      _recordDiagnostic(
        'Duplicate delta watcher registration for "${watcher.paneKey}". '
        'Previous watcher will be replaced.',
      );
    }
    _deltaWatchers[watcher.paneKey] = watcher;
  }

  void unregisterDeltaWatcher(PaneKey key) {
    _deltaWatchers.remove(key);
  }

  PaneDeltaWatcherContract<TPayload>? deltaWatcherFor<TPayload>(PaneKey key) {
    return _deltaWatchers[key] as PaneDeltaWatcherContract<TPayload>?;
  }

  void setAgreementCallback(PaneAgreementCallback? callback) {
    _agreementCallback = callback;
    if (callback != null) {
      for (final agreement in _agreements.values) {
        callback(agreement);
      }
    }
  }

  void clear() {
    _factories.clear();
    _capabilities.clear();
    _displayInfo.clear();
    _agreements.clear();
    _manifestAdapters.clear();
    _selectionHandlers.clear();
    _deltaWatchers.clear();
    _diagnostics.clear();
  }

  List<String> takeDiagnostics() {
    final snapshot = List<String>.from(_diagnostics);
    _diagnostics.clear();
    return snapshot;
  }

  void _recordDiagnostic(String message) {
    _diagnostics.add(message);
    assert(() {
      debugPrint('aware_pane: $message');
      return true;
    }());
  }
}
