import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logging/logging.dart';
import 'package:uuid/uuid_value.dart';

import 'package:aware_pane/aware_pane.dart' as runtime;

import 'package:aware_api/aware_api.dart';

import '../../pane_kind.dart';
import '../../pane_system.dart';
import '../../pane_selection_context.dart';
import '../../pane_manifest_runtime.dart';
import '../../pane_manifest_adapter.dart';
import '../../pane_manifest_decoder.dart';
import '../../pane_selection_handler.dart';
import '../../pane_delta_watcher.dart';
import '../../pane_agreement.dart';
import '../../pane_branch_snapshot.dart';
import '../model/pane_factory.dart';

class PaneOpgBinding {
  const PaneOpgBinding({required this.opgName, this.branchTemplate});

  final String opgName;
  final String? branchTemplate;
}

/// Bind a Pane to a canonical view under an ObjectProjectionGraphIdentity.
///
/// This is the v0 bridge between:
/// - commit-backed shared attention (`FocusScope.view` -> `ObjectProjectionGraphView.view_key`), and
/// - local pane implementations (PaneRegistry).
///
/// v1+ will allow environments to provide the available view registry via bundles
/// (materialized `ObjectProjectionGraphView` objects). The host still decides
/// which panes it can render for a given view.
class PaneOpgViewBinding {
  const PaneOpgViewBinding({
    required this.opgIdentityKey,
    required this.viewKey,
  });

  /// Stable key for an ObjectProjectionGraphIdentity (e.g. "{ocg_key}:{projection_name}").
  final String opgIdentityKey;

  /// Stable view selector within the projection family (e.g. "onboarding.welcome").
  final String viewKey;
}

typedef PaneBranchBootstrapArgumentsBuilder =
    List<FunctionInvocationArgument> Function(
      PaneBranchBootstrapArguments args,
    );

class PaneBranchBootstrapArguments {
  const PaneBranchBootstrapArguments({
    this.title,
    this.metadata = const <String, Object?>{},
  });

  final String? title;
  final Map<String, Object?> metadata;
}

class PaneBranchBootstrap {
  const PaneBranchBootstrap({
    required this.objectType,
    required this.functionName,
    this.callTarget = FunctionInvocationCallTarget.opgConstructor,
    this.argumentsBuilder,
  });

  final String objectType;
  final String functionName;
  final FunctionInvocationCallTarget callTarget;
  final PaneBranchBootstrapArgumentsBuilder? argumentsBuilder;
}

class PaneThreadBranding {
  const PaneThreadBranding({
    required this.paneKey,
    required this.accentColor,
    this.icon,
    this.label,
  });

  final PaneKey paneKey;
  final Color accentColor;
  final IconData? icon;
  final String? label;
}

typedef PaneThreadBranchTitleResolver =
    Future<String?> Function(PaneThreadBranchTitleRequest request);

class PaneThreadBranchTitleRequest {
  const PaneThreadBranchTitleRequest({
    required this.read,
    required this.paneKey,
    required this.threadId,
    required this.branchId,
    required this.projectionHash,
    this.processId,
    this.headCommitId,
  });

  final ProviderReader read;
  final PaneKey paneKey;
  final UuidValue threadId;
  final UuidValue branchId;
  final String projectionHash;
  final UuidValue? processId;
  final UuidValue? headCommitId;
}

typedef PaneLaneConstructorBuilder =
    Widget Function(BuildContext context, PaneLaneConstructorRequest request);

enum PaneLaneConstructorIntent { attachLane, createBranch }

class PaneLaneConstructorRequest {
  const PaneLaneConstructorRequest({
    required this.paneKey,
    required this.threadId,
    required this.domainBranchId,
    this.initialTitle,
    this.defaultActive = true,
    this.intent = PaneLaneConstructorIntent.attachLane,
  });

  final PaneKey paneKey;
  final String threadId;
  final String domainBranchId;
  final String? initialTitle;
  final bool defaultActive;
  final PaneLaneConstructorIntent intent;
}

class PaneLaneConstructorResult {
  const PaneLaneConstructorResult({this.title, required this.isActive});

  final String? title;
  final bool isActive;
}

/// Pane Registry - host-facing wrapper over aware_pane runtime.
class PaneRegistry {
  PaneRegistry({runtime.PaneRegistry? core})
    : _core = core ?? runtime.PaneRegistry(),
      _readyCompleter = Completer<void>();

  final runtime.PaneRegistry _core;

  final Map<PaneKey, PaneFactory> _factories = {};
  final Map<PaneKey, runtime.PaneCapabilities> _capabilities = {};
  final Map<PaneKey, PaneDisplayInfo> _displayInfo = {};
  final Map<PaneKey, PaneAgreement> _agreements = {};
  final Map<PaneKey, PaneManifestAdapter<dynamic>> _manifestAdapters = {};
  final Map<PaneKey, PaneManifestDecoder> _manifestDecoders = {};
  final Map<PaneKey, PaneSelectionHandler> _selectionHandlers = {};
  final Map<PaneKey, PaneDeltaWatcher<dynamic>> _deltaWatchers = {};
  final Map<String, _DeltaWatcherBridge<dynamic>> _deltaWatcherBridges = {};
  final Map<PaneKey, PaneOpgBinding> _opgBindings = {};
  final Map<PaneKey, List<PaneOpgViewBinding>> _opgViewBindings = {};
  final Map<PaneKey, PaneOpgViewBinding> _defaultOpgViewBindings = {};
  final Map<PaneKey, PaneLaneConstructorBuilder> _laneConstructors = {};
  final Map<PaneKey, PaneBranchBootstrap> _branchBootstraps = {};
  final Map<PaneKey, PaneThreadBranding> _threadBranding = {};
  final Map<PaneKey, PaneThreadBranchTitleResolver> _threadBranchTitles = {};
  final Map<String, _ManifestAdapterBridge<dynamic>> _manifestAdapterBridges =
      {};
  final Map<String, _SelectionHandlerBridge> _selectionHandlerBridges = {};
  final Logger _logger = Logger('PaneRegistry');
  ProviderReader? _providerReader;

  bool _syntheticBootstrapEnabled = true;
  void Function(PaneAgreement)? _agreementRegistryCallback;
  bool _isReady = false;
  Completer<void> _readyCompleter;

  // === Core registration ===

  void registerPane({
    required PaneKey kind,
    required PaneFactory factory,
    required runtime.PaneCapabilities capabilities,
    PaneAgreement? agreement,
    PaneDisplayInfo? displayInfo,
  }) {
    final existingFactory = _factories[kind];
    if (existingFactory != null && !identical(existingFactory, factory)) {
      _logger.warning(
        'Re-registering pane $kind with a different factory. Previous factory '
        'will be replaced.',
      );
    } else if (existingFactory != null) {
      _logger.fine('Pane $kind registered multiple times with same factory.');
    }
    _factories[kind] = factory;
    _capabilities[kind] = capabilities;
    if (displayInfo != null) {
      _displayInfo[kind] = displayInfo;
    } else {
      _displayInfo[kind] = PaneDisplayInfo(
        paneKey: kind.name,
        title: kind.displayName,
        description: 'Pane: ${kind.displayName}',
        icon: Icons.tab,
      );
    }

    if (agreement != null) {
      _agreements[kind] = agreement;
      _agreementRegistryCallback?.call(agreement);
    }

    _core.registerPane(
      key: _paneKey(kind),
      factory: (runtimeContext) {
        final resolvedKind = _paneKindFromKey(runtimeContext.paneKey);
        final parameters = Map<String, dynamic>.from(runtimeContext.parameters);
        final metadata = Map<String, Object?>.from(runtimeContext.metadata);
        final selectionContext =
            metadata.remove(kPaneMetadataSelectionContext)
                as PaneSelectionContext?;
        final projectId =
            (metadata['projectId'] ?? parameters['projectId']) as String?;
        final selectedNodeId =
            (metadata['selectedNodeId'] ?? parameters['selectedNodeId'])
                as String?;

        final ctx = PaneContext(
          paneId: runtimeContext.instanceId ?? runtimeContext.paneKey,
          instanceId: runtimeContext.instanceId,
          kind: resolvedKind,
          projectId: projectId,
          selectedNodeId: selectedNodeId,
          parameters: parameters,
          metadata: metadata,
          onClose: runtimeContext.onClose,
          selectionContext: selectionContext,
        );
        final child = factory(ctx);

        return child;
      },
      capabilities: capabilities,
      displayInfo:
          _displayInfo[kind] ??
          PaneDisplayInfo(
            paneKey: kind.name,
            title: kind.displayName,
            description: 'Pane: ${kind.displayName}',
            icon: Icons.tab,
          ),
      agreement: agreement != null ? _toRuntimeAgreement(agreement) : null,
    );
  }

  void unregisterPane(PaneKey kind) {
    _factories.remove(kind);
    _capabilities.remove(kind);
    _displayInfo.remove(kind);
    _agreements.remove(kind);
    _manifestAdapters.remove(kind);
    _manifestDecoders.remove(kind);
    _selectionHandlers.remove(kind);
    _deltaWatchers.remove(kind);
    _opgBindings.remove(kind);
    _laneConstructors.remove(kind);
    _branchBootstraps.remove(kind);
    _threadBranding.remove(kind);
    _threadBranchTitles.remove(kind);
    _core.unregisterPane(_paneKey(kind));
  }

  Widget? createPane(PaneKey kind, PaneContext context) {
    if (!_isReady) {
      _logger.fine(
        'createPane invoked before registry marked ready. kind=$kind '
        'paneId=${context.paneId}',
      );
    }
    final metadata = Map<String, Object?>.from(context.metadata);
    if (context.projectId != null) {
      metadata['projectId'] = context.projectId;
    }
    if (context.selectedNodeId != null) {
      metadata['selectedNodeId'] = context.selectedNodeId;
    }
    if (context.selectionContext != null) {
      metadata[kPaneMetadataSelectionContext] = context.selectionContext;
    }

    final runtimeContext = runtime.PaneContext(
      paneKey: _paneKey(kind),
      instanceId: context.instanceId ?? context.paneId,
      parameters: context.parameters,
      metadata: metadata,
      onClose: context.onClose,
    );
    return _core.build(_paneKey(kind), runtimeContext);
  }

  runtime.PaneCapabilities? getCapabilities(PaneKey kind) =>
      _capabilities[kind];

  PaneDisplayInfo? getDisplayInfo(PaneKey kind) => _displayInfo[kind];

  bool arePanesCompatible(PaneKey a, PaneKey b) {
    final first = _capabilities[a];
    final second = _capabilities[b];
    if (first == null || second == null) return false;
    return first.isCompatibleWith(second);
  }

  bool isRegistered(PaneKey kind) => _factories.containsKey(kind);

  List<PaneKey> get registeredPanes => _factories.keys.toList();

  bool get isReady => _isReady;

  Future<void> waitUntilReady() {
    if (_isReady) {
      return Future<void>.value();
    }
    return _readyCompleter.future;
  }

  void markReady() {
    if (_isReady) {
      _logger.fine('PaneRegistry.markReady() invoked after ready state.');
      return;
    }
    _isReady = true;
    if (!_readyCompleter.isCompleted) {
      _readyCompleter.complete();
    }
    _logger.info(
      'PaneRegistry marked ready. Registered panes: ${_factories.keys.length}',
    );
  }

  List<PaneKey> getPanesProvidingCapability(String capability) {
    final result = <PaneKey>[];
    _capabilities.forEach((kind, caps) {
      if (caps.provides.contains(capability)) {
        result.add(kind);
      }
    });
    return result;
  }

  List<PaneKey> getPanesRequiringCapability(String capability) {
    final result = <PaneKey>[];
    _capabilities.forEach((kind, caps) {
      if (caps.requires.contains(capability)) {
        result.add(kind);
      }
    });
    return result;
  }

  List<PaneKey> getPanesEmittingEvent(String eventType) {
    final result = <PaneKey>[];
    _capabilities.forEach((kind, caps) {
      if (caps.emits.contains(eventType)) {
        result.add(kind);
      }
    });
    return result;
  }

  List<PaneKey> getPanesListeningToEvent(String eventType) {
    final result = <PaneKey>[];
    _capabilities.forEach((kind, caps) {
      if (caps.listens.contains(eventType)) {
        result.add(kind);
      }
    });
    return result;
  }

  void registerDeltaWatcher<TPayload>({
    required PaneKey kind,
    required PaneDeltaWatcher<TPayload> watcher,
  }) {
    final existing = _deltaWatchers[kind];
    if (existing != null && !identical(existing, watcher)) {
      _logger.warning('Replacing delta watcher for pane $kind.');
    }
    _deltaWatchers[kind] = watcher;
    final bridge = _DeltaWatcherBridge<TPayload>(
      delegate: watcher,
      paneKey: _paneKey(kind),
      providerReader: () {
        final reader = _providerReader;
        if (reader == null) {
          return null;
        }
        return <T>(ProviderListenable<T> provider) => reader(provider);
      },
    );
    _deltaWatcherBridges[_paneKey(kind)] = bridge;
    _core.registerDeltaWatcher<TPayload>(bridge);
  }

  void unregisterDeltaWatcher(PaneKey kind) {
    _deltaWatchers.remove(kind);
    final key = _paneKey(kind);
    final bridge = _deltaWatcherBridges.remove(key);
    if (bridge != null) {
      _core.unregisterDeltaWatcher(key);
    }
  }

  PaneDeltaWatcher<TPayload>? deltaWatcherFor<TPayload>(PaneKey kind) {
    return _deltaWatchers[kind] as PaneDeltaWatcher<TPayload>?;
  }

  PaneAgreement? getAgreement(PaneKey kind) => _agreements[kind];

  bool canPanesCollaborate(PaneKey kind1, PaneKey kind2) {
    final agreement1 = _agreements[kind1];
    final agreement2 = _agreements[kind2];
    if (agreement1 == null || agreement2 == null) return true;
    if (agreement1.cannotCoexistWith.contains(kind2.name)) return false;
    if (agreement2.cannotCoexistWith.contains(kind1.name)) return false;
    return true;
  }

  Map<PaneKey, PaneAgreement> get agreements => Map.unmodifiable(_agreements);

  void setAgreementRegistryCallback(void Function(PaneAgreement) callback) {
    _agreementRegistryCallback = callback;
    for (final agreement in _agreements.values) {
      callback(agreement);
    }
  }

  // === Manifest adapters & selection handlers ===

  void registerManifestAdapter<TPayload>(
    PaneManifestAdapter<TPayload> adapter,
  ) {
    final existing = _manifestAdapters[adapter.paneKind];
    if (existing != null && !identical(existing, adapter)) {
      _logger.warning(
        'Replacing manifest adapter for pane ${adapter.paneKind}. '
        'Previous adapter will be overwritten.',
      );
    }
    _manifestAdapters[adapter.paneKind] = adapter;
    final bridge = _ManifestAdapterBridge<TPayload>(adapter);
    _manifestAdapterBridges[_paneKey(adapter.paneKind)] = bridge;
    _core.registerManifestAdapter(bridge);
  }

  PaneManifestAdapter<TPayload>? getManifestAdapter<TPayload>(PaneKey kind) {
    final adapter = _manifestAdapters[kind];
    return adapter as PaneManifestAdapter<TPayload>?;
  }

  Future<PaneManifestBundle<TPayload>> ensureManifestBundle<TPayload>({
    required PaneKey paneKind,
    required PaneThreadSnapshot snapshot,
    required String threadDirectory,
  }) async {
    final bridge =
        _manifestAdapterBridges[_paneKey(paneKind)]
            as _ManifestAdapterBridge<TPayload>?;
    if (bridge == null) {
      throw StateError(
        'No manifest adapter registered for pane ${paneKind.name}',
      );
    }

    final branchKey = _manifestBranchKey(paneKind, snapshot);
    final context = runtime.PaneBranchContext(
      branchId: branchKey,
      threadId: snapshot.id.toString(),
      metadata: {
        runtime.PaneManifestMetadataKeys.threadDirectory: threadDirectory,
        runtime.PaneManifestMetadataKeys.threadSnapshot: snapshot,
      },
    );

    final payload = await bridge.ensure(context);
    final branchSnapshot = bridge.branchFor(branchKey);
    if (branchSnapshot == null) {
      throw StateError(
        'Manifest adapter ${paneKind.name} did not provide a branch '
        'for context $branchKey',
      );
    }

    return PaneManifestBundle(branchSnapshot: branchSnapshot, payload: payload);
  }

  Future<List<PaneManifestBundle<TPayload>>> loadManifestBundles<TPayload>({
    required PaneKey paneKind,
    required String threadDirectory,
  }) async {
    final adapter = getManifestAdapter<TPayload>(paneKind);
    if (adapter == null) {
      throw StateError(
        'No manifest adapter registered for pane ${paneKind.name}',
      );
    }
    return adapter.loadAll(threadDirectory: threadDirectory);
  }

  void unregisterManifestAdapter(PaneKey kind) {
    _manifestAdapters.remove(kind);
    final key = _paneKey(kind);
    _manifestAdapterBridges.remove(key);
    _core.unregisterManifestAdapter(key);
  }

  Iterable<PaneKey> get manifestAdapterKinds =>
      _manifestAdapters.keys.toList(growable: false);

  void registerManifestDecoder(PaneManifestDecoder decoder) {
    final existing = _manifestDecoders[decoder.paneKind];
    if (existing != null && !identical(existing, decoder)) {
      _logger.warning(
        'Replacing manifest decoder for pane ${decoder.paneKind}.',
      );
    }
    _manifestDecoders[decoder.paneKind] = decoder;
  }

  PaneManifestDecoder? getManifestDecoder(PaneKey kind) {
    return _manifestDecoders[kind];
  }

  void unregisterManifestDecoder(PaneKey kind) {
    _manifestDecoders.remove(kind);
  }

  void registerSelectionHandler(PaneSelectionHandler handler) {
    final existing = _selectionHandlers[handler.paneKind];
    if (existing != null && !identical(existing, handler)) {
      _logger.warning(
        'Replacing selection handler for pane ${handler.paneKind}.',
      );
    }
    _selectionHandlers[handler.paneKind] = handler;
    final bridge = _SelectionHandlerBridge(
      delegate: handler,
      providerReader: () => _providerReader,
    );
    _selectionHandlerBridges[_paneKey(handler.paneKind)] = bridge;
    _core.registerSelectionHandler(bridge);
  }

  PaneSelectionHandler? getSelectionHandler(PaneKey kind) =>
      _selectionHandlers[kind];

  void unregisterSelectionHandler(PaneKey kind) {
    _selectionHandlers.remove(kind);
    final key = _paneKey(kind);
    _selectionHandlerBridges.remove(key);
    _core.unregisterSelectionHandler(key);
  }

  @visibleForTesting
  runtime.PaneManifestAdapterContract<TPayload>?
  manifestAdapterBridgeForTest<TPayload>(PaneKey kind) {
    final bridge = _manifestAdapterBridges[_paneKey(kind)];
    return bridge as runtime.PaneManifestAdapterContract<TPayload>?;
  }

  void setProviderReader(ProviderReader reader) {
    _providerReader = reader;
  }

  @visibleForTesting
  Future<void> dispatchSelectionForTest({
    required PaneKey kind,
    required runtime.PaneContext context,
    Object? payload,
    Map<String, Object?> metadata = const {},
  }) async {
    final bridge = _selectionHandlerBridges[_paneKey(kind)];
    if (bridge == null) {
      return;
    }
    await bridge.handle(context, payload, metadata);
  }

  void registerOpgBinding(PaneKey kind, PaneOpgBinding binding) {
    final existing = _opgBindings[kind];
    if (existing != null && existing.opgName != binding.opgName) {
      _logger.warning(
        'Replacing OPG binding for pane $kind (${existing.opgName} -> ${binding.opgName}).',
      );
    }
    _opgBindings[kind] = binding;
  }

  PaneOpgBinding? paneOpgBindingFor(PaneKey kind) => _opgBindings[kind];

  void unregisterOpgBinding(PaneKey kind) {
    _opgBindings.remove(kind);
  }

  void registerOpgViewBinding(PaneKey kind, PaneOpgViewBinding binding) {
    final bindings = _opgViewBindings.putIfAbsent(
      kind,
      () => <PaneOpgViewBinding>[],
    );

    final normalizedOpgIdentityKey = runtime.PaneKeys.normalize(
      binding.opgIdentityKey,
    );
    final normalizedViewKey = runtime.PaneKeys.normalize(binding.viewKey);

    for (final existing in bindings) {
      if (runtime.PaneKeys.normalize(existing.opgIdentityKey) ==
              normalizedOpgIdentityKey &&
          runtime.PaneKeys.normalize(existing.viewKey) == normalizedViewKey) {
        return;
      }
    }

    bindings.add(binding);
  }

  /// Register the default projection view to mount for a pane (v0).
  ///
  /// This is used by OS navigation (Environment) when a branch is opened and
  /// the system needs a deterministic "first" view for a projection family.
  ///
  /// Notes:
  /// - This is host-owned state (v0) and should become environment-provided in v1+.
  /// - The provided binding is also registered via [registerOpgViewBinding] to
  ///   guarantee it is part of the renderable view set.
  void registerDefaultOpgViewBinding(PaneKey kind, PaneOpgViewBinding binding) {
    _defaultOpgViewBindings[kind] = binding;
    registerOpgViewBinding(kind, binding);
  }

  PaneOpgViewBinding? defaultOpgViewBindingFor(PaneKey kind) =>
      _defaultOpgViewBindings[kind];

  /// Return the preferred (default) view binding for a pane.
  ///
  /// Falls back to the first registered view binding if no explicit default was set.
  PaneOpgViewBinding? preferredOpgViewBindingFor(PaneKey kind) {
    final explicit = _defaultOpgViewBindings[kind];
    if (explicit != null) return explicit;
    final bindings = _opgViewBindings[kind];
    if (bindings == null || bindings.isEmpty) return null;
    return bindings.first;
  }

  List<PaneOpgViewBinding> paneOpgViewBindingsFor(PaneKey kind) {
    final bindings = _opgViewBindings[kind];
    if (bindings == null || bindings.isEmpty) {
      return const <PaneOpgViewBinding>[];
    }
    return List<PaneOpgViewBinding>.unmodifiable(bindings);
  }

  /// Return the set of registered `ObjectProjectionGraphView.view_key` values
  /// that the current host can render for a given `ObjectProjectionGraphIdentity.key`.
  ///
  /// This is a host-side registry (v0): it reflects what panes are installed and
  /// which views they claim to render, not necessarily what the environment
  /// currently advertises.
  ///
  /// v1+: environments should provide the available view registry via bundles
  /// (materialized `ObjectProjectionGraphView` objects), while the host still
  /// decides which of those views it can render.
  List<String> viewKeysForOpgIdentityKey(String opgIdentityKey) {
    final needle = runtime.PaneKeys.normalize(opgIdentityKey);
    if (needle.isEmpty) return const <String>[];

    final keys = <String>{};
    for (final bindings in _opgViewBindings.values) {
      for (final binding in bindings) {
        if (runtime.PaneKeys.normalize(binding.opgIdentityKey) != needle) {
          continue;
        }
        final viewKey = binding.viewKey.trim();
        if (viewKey.isNotEmpty) {
          keys.add(viewKey);
        }
      }
    }

    final out = keys.toList()..sort();
    return List<String>.unmodifiable(out);
  }

  void unregisterOpgViewBindings(PaneKey kind) {
    _opgViewBindings.remove(kind);
    _defaultOpgViewBindings.remove(kind);
  }

  void registerBranchBootstrap(PaneKey kind, PaneBranchBootstrap bootstrap) {
    final existing = _branchBootstraps[kind];
    if (existing != null && existing != bootstrap) {
      _logger.warning('Replacing branch bootstrap for pane $kind.');
    }
    _branchBootstraps[kind] = bootstrap;
  }

  PaneBranchBootstrap? branchBootstrapFor(PaneKey kind) =>
      _branchBootstraps[kind];

  void unregisterBranchBootstrap(PaneKey kind) {
    _branchBootstraps.remove(kind);
  }

  void registerThreadBranding(PaneKey kind, PaneThreadBranding branding) {
    final existing = _threadBranding[kind];
    if (existing != null && existing != branding) {
      _logger.warning('Replacing thread branding for pane $kind.');
    }
    _threadBranding[kind] = branding;
  }

  PaneThreadBranding? threadBrandingFor(PaneKey kind) => _threadBranding[kind];

  void unregisterThreadBranding(PaneKey kind) {
    _threadBranding.remove(kind);
  }

  void registerThreadBranchTitleResolver(
    PaneKey kind,
    PaneThreadBranchTitleResolver resolver,
  ) {
    final existing = _threadBranchTitles[kind];
    if (existing != null && !identical(existing, resolver)) {
      _logger.warning('Replacing thread branch title resolver for pane $kind.');
    }
    _threadBranchTitles[kind] = resolver;
  }

  PaneThreadBranchTitleResolver? threadBranchTitleResolverFor(PaneKey kind) =>
      _threadBranchTitles[kind];

  void unregisterThreadBranchTitleResolver(PaneKey kind) {
    _threadBranchTitles.remove(kind);
  }

  void registerLaneConstructor(
    PaneKey kind,
    PaneLaneConstructorBuilder builder,
  ) {
    final existing = _laneConstructors[kind];
    if (existing != null && !identical(existing, builder)) {
      _logger.warning('Replacing lane constructor for pane $kind.');
    }
    _laneConstructors[kind] = builder;
  }

  PaneLaneConstructorBuilder? laneConstructorFor(PaneKey kind) =>
      _laneConstructors[kind];

  void unregisterLaneConstructor(PaneKey kind) {
    _laneConstructors.remove(kind);
  }

  bool get syntheticBootstrapEnabled => _syntheticBootstrapEnabled;

  set syntheticBootstrapEnabled(bool value) {
    if (_syntheticBootstrapEnabled == value) return;
    _syntheticBootstrapEnabled = value;
    _logger.info('Synthetic bootstrap ${value ? "ENABLED" : "DISABLED"}');
  }

  void clear() {
    _core.clear();
    _factories.clear();
    _capabilities.clear();
    _displayInfo.clear();
    _agreements.clear();
    _manifestAdapters.clear();
    _manifestDecoders.clear();
    _selectionHandlers.clear();
    _deltaWatchers.clear();
    _deltaWatcherBridges.clear();
    _opgBindings.clear();
    _opgViewBindings.clear();
    _laneConstructors.clear();
    _branchBootstraps.clear();
    _threadBranding.clear();
    _threadBranchTitles.clear();
    _syntheticBootstrapEnabled = true;
    _isReady = false;
    if (!_readyCompleter.isCompleted) {
      _readyCompleter.complete();
    }
    _readyCompleter = Completer<void>();
  }

  // === Helpers ===

  static String _paneKey(PaneKey kind) => runtime.PaneKeys.normalize(kind);

  static String _manifestBranchKey(
    PaneKey paneKind,
    PaneThreadSnapshot snapshot,
  ) => '${paneKind.name}/${snapshot.id}';

  static PaneKey _paneKindFromKey(String key) {
    final normalized = runtime.PaneKeys.normalize(key);
    return normalized.isEmpty ? kPaneKeyGeneric : normalized;
  }

  runtime.PaneAgreementData _toRuntimeAgreement(PaneAgreement agreement) {
    return runtime.PaneAgreementData(
      paneKey: agreement.paneId,
      title: agreement.title,
      provides: agreement.provides.map((capability) => capability.name).toSet(),
      requires: agreement.requires.map((capability) => capability.name).toSet(),
      emitsEvents: agreement.emitsEvents,
      listensToEvents: agreement.listensToEvents,
      cannotCoexistWith: agreement.cannotCoexistWith.toSet(),
    );
  }
}

class _ManifestAdapterBridge<TPayload>
    extends runtime.PaneManifestAdapterContract<TPayload> {
  _ManifestAdapterBridge(this.delegate);

  final PaneManifestAdapter<TPayload> delegate;
  final Map<String, PaneBranchSnapshot> _branchCache = {};

  @override
  runtime.PaneKey get paneKey => delegate.paneKind.name;
  PaneBranchSnapshot? branchFor(String branchId) => _branchCache[branchId];

  @override
  Future<TPayload?> load(runtime.PaneBranchContext context) async {
    final directory =
        context.metadata[runtime.PaneManifestMetadataKeys.threadDirectory]
            as String?;
    if (directory == null) {
      throw StateError(
        'threadDirectory metadata missing for manifest load (${delegate.paneKind})',
      );
    }

    final bundle = await delegate.load(threadDirectory: directory);
    if (bundle == null) {
      return null;
    }

    _branchCache[context.branchId] = bundle.branchSnapshot;
    context.metadata[runtime.PaneManifestMetadataKeys.branch] =
        bundle.branchSnapshot;
    return bundle.payload;
  }

  @override
  Future<TPayload> build(runtime.PaneBranchContext context) async {
    final directory =
        context.metadata[runtime.PaneManifestMetadataKeys.threadDirectory]
            as String?;
    final snapshot =
        context.metadata[runtime.PaneManifestMetadataKeys.threadSnapshot]
            as PaneThreadSnapshot?;
    if (directory == null || snapshot == null) {
      throw StateError(
        'threadDirectory and threadSnapshot metadata required for manifest build (${delegate.paneKind})',
      );
    }

    final bundle = await delegate.build(
      snapshot: snapshot,
      threadDirectory: directory,
    );

    _branchCache[context.branchId] = bundle.branchSnapshot;
    context.metadata[runtime.PaneManifestMetadataKeys.branch] =
        bundle.branchSnapshot;
    return bundle.payload;
  }

  @override
  Future<void> save(runtime.PaneBranchContext context, TPayload payload) async {
    final directory =
        context.metadata[runtime.PaneManifestMetadataKeys.threadDirectory]
            as String?;
    if (directory == null) {
      throw StateError(
        'threadDirectory metadata missing for manifest save (${delegate.paneKind})',
      );
    }

    final cached = _branchCache[context.branchId];
    final branchSnapshot =
        cached ??
        context.metadata[runtime.PaneManifestMetadataKeys.branch]
            as PaneBranchSnapshot?;
    if (branchSnapshot == null) {
      throw StateError(
        'branch metadata missing for manifest save (${delegate.paneKind})',
      );
    }

    final bundle = PaneManifestBundle<TPayload>(
      branchSnapshot: branchSnapshot,
      payload: payload,
    );
    await delegate.save(threadDirectory: directory, manifest: bundle);
  }
}

class _SelectionHandlerBridge extends runtime.PaneSelectionHandler<Object?> {
  _SelectionHandlerBridge({
    required this.delegate,
    required ProviderReader? Function() providerReader,
  }) : _providerReader = providerReader,
       super(paneKey: delegate.paneKind.name);

  final PaneSelectionHandler delegate;
  final ProviderReader? Function() _providerReader;
  static final Logger _logger = Logger('PaneRegistry.SelectionBridge');

  @override
  Future<void> handle(
    runtime.PaneContext paneContext,
    Object? payload,
    Map<String, Object?> metadata,
  ) async {
    final reader = _providerReader();
    if (reader == null) {
      _logger.warning(
        'Selection handler for ${delegate.paneKind} invoked without a provider reader. '
        'Ensure PaneRegistry.setProviderReader is called during bootstrap.',
      );
      return;
    }

    final mergedMetadata = {...paneContext.metadata, ...metadata};

    final selectionPayload = runtime.PaneSelectionPayload<Object?>(
      paneKey: paneContext.paneKey,
      payload: payload,
      parameters: paneContext.parameters,
      metadata: mergedMetadata,
    );

    await delegate.handle(
      read: reader,
      selection: selectionPayload,
      selectionContext: null,
    );
  }
}

class _DeltaWatcherBridge<TPayload>
    implements runtime.PaneDeltaWatcherContract<TPayload> {
  _DeltaWatcherBridge({
    required this.delegate,
    required this.paneKey,
    required PaneProviderReader? Function() providerReader,
  }) : _providerReader = providerReader;

  final PaneDeltaWatcher<TPayload> delegate;
  @override
  final runtime.PaneKey paneKey;
  final PaneProviderReader? Function() _providerReader;
  static final Logger _logger = Logger('PaneRegistry.DeltaBridge');

  @override
  Stream<runtime.PaneDeltaEvent> watch(runtime.PaneWatcherInput input) {
    final readerFactory = _providerReader();
    if (readerFactory == null) {
      _logger.warning(
        'Delta watcher for ${delegate.paneKind} invoked without a provider reader. Ensure PaneRegistry.setProviderReader is called during bootstrap.',
      );
      return const Stream<runtime.PaneDeltaEvent>.empty();
    }
    return delegate.watch(read: readerFactory, input: input);
  }

  @override
  Future<runtime.PaneHydrationDelta<TPayload>> resolve(
    runtime.PaneDeltaEvent event,
  ) async {
    final readerFactory = _providerReader();
    if (readerFactory == null) {
      _logger.warning(
        'Delta watcher resolve for ${delegate.paneKind} invoked without a provider reader.',
      );
      return runtime.PaneHydrationDelta<TPayload>(
        kind: event.kind,
        branchContext: event.branchContext,
        metadata: event.metadata,
      );
    }
    return delegate.resolve(read: readerFactory, event: event);
  }
}
