import 'dart:async';

import 'package:aware_api/aware_api.dart';
import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:aware_interface_sdk/aware_interface_sdk.dart';
import 'package:aware_pane_runtime/aware_pane_runtime.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'host_state_provider.dart';
import 'package_runtime_provider.dart';
import '../runtime/interface_host_view_state_cache.dart';
import '../runtime/interface_host_view_state_cache_store_factory.dart';
import '../runtime/interface_package_runtime.dart';
import '../runtime/interface_renderer_capabilities.dart';
import '../runtime/interface_view_state_decoder_registry.dart';
import '../render_spec/pane_render_spec.dart';

final interfacePaneApiNamespaceProvider = Provider<String>((ref) {
  throw UnimplementedError(
    'Interface pane API namespace is only available inside InterfacePaneApiScope.',
  );
});

final interfacePaneApiTransportProvider = Provider<AwareApiTransport>(
  dependencies: <ProviderOrFamily>[
    interfaceSdkClientProvider,
    interfacePaneApiNamespaceProvider,
  ],
  (ref) {
    final client = ref.watch(interfaceSdkClientProvider);
    final namespace = ref.watch(interfacePaneApiNamespaceProvider);
    return InterfaceSdkAwareApiTransport(client: client, namespace: namespace);
  },
);

final interfacePaneApiClientProvider = Provider<AwareApiClient>(
  dependencies: <ProviderOrFamily>[interfacePaneApiTransportProvider],
  (ref) {
    final transport = ref.watch(interfacePaneApiTransportProvider);
    return AwareApiClient(transport: transport);
  },
);

final interfacePaneActionDispatcherProvider =
    Provider<InterfacePaneActionDispatcher>(
      dependencies: <ProviderOrFamily>[interfaceHostStateProvider],
      (ref) {
        return InterfacePaneActionDispatcher(ref);
      },
    );

class InterfacePaneActionDispatcher {
  InterfacePaneActionDispatcher(this._ref);

  final Ref _ref;

  Future<InterfaceHostState> invokeAction({
    required PaneContext paneContext,
    required String actionKey,
    InterfaceActionTarget? actionTarget,
    Map<String, dynamic>? payload,
  }) async {
    final hostState = await _ref
        .read(interfaceHostStateProvider.notifier)
        .invokeAction(
          paneRef: interfacePaneRefForContext(paneContext),
          actionKey: actionKey,
          actionTarget: actionTarget,
          payload: payload,
        );
    _throwIfReturnedPaneActionFailed(
      hostState,
      actionKey: actionKey,
      actionTarget: actionTarget,
    );
    return hostState;
  }

  Future<InterfaceHostState> invokeActionTarget({
    required PaneContext paneContext,
    required PaneRenderActionTarget actionTarget,
    Map<String, dynamic>? payload,
  }) {
    return invokeAction(
      paneContext: paneContext,
      actionKey: actionTarget.actionKey,
      actionTarget: _transportActionTarget(actionTarget),
      payload: payload,
    );
  }

  Future<InterfaceHostState> invokeRenderSpecAction(
    PaneRenderActionInvocation invocation,
  ) {
    return invokeActionTarget(
      paneContext: invocation.paneContext,
      actionTarget: invocation.actionTarget,
      payload: invocation.payload,
    );
  }

  Future<InterfaceHostState> invokeSdkOperation({
    required PaneContext paneContext,
    required String operationRef,
    Map<String, dynamic>? payload,
  }) {
    return invokeAction(
      paneContext: paneContext,
      actionKey: 'sdk:$operationRef',
      actionTarget: InterfaceActionTarget(
        actionKey: 'sdk:$operationRef',
        actionKind: kPaneRenderActionKindSdkOperation,
        operationRef: operationRef,
      ),
      payload: payload,
    );
  }
}

@immutable
class InterfacePaneActionFailure implements Exception {
  const InterfacePaneActionFailure({
    required this.actionKey,
    required this.operationKey,
    required this.message,
  });

  final String actionKey;
  final String operationKey;
  final String message;

  @override
  String toString() {
    final trimmedActionKey = actionKey.trim();
    final actionLabel = trimmedActionKey.isEmpty
        ? 'Interface pane action'
        : trimmedActionKey;
    return 'Interface pane action `$actionLabel` failed: $message';
  }
}

void _throwIfReturnedPaneActionFailed(
  InterfaceHostState hostState, {
  required String actionKey,
  InterfaceActionTarget? actionTarget,
}) {
  final operation = hostState.currentOperation;
  if (operation == null || !_operationFailed(operation)) {
    return;
  }
  if (!_operationMatchesPaneAction(
    operation,
    actionKey: actionKey,
    actionTarget: actionTarget,
  )) {
    return;
  }
  throw InterfacePaneActionFailure(
    actionKey: actionKey,
    operationKey: operation.operationKey,
    message: _operationFailureMessage(operation),
  );
}

bool _operationFailed(InterfaceOperationState operation) {
  final status = operation.status.trim().toLowerCase();
  final phase = operation.phase?.trim().toLowerCase();
  return status == 'failed' ||
      phase == 'failed' ||
      (operation.error?.trim().isNotEmpty ?? false);
}

bool _operationMatchesPaneAction(
  InterfaceOperationState operation, {
  required String actionKey,
  InterfaceActionTarget? actionTarget,
}) {
  final operationKey = operation.operationKey.trim();
  final isMountedPaneOperation =
      operationKey == 'mounted_pane_sdk_operation' ||
      operationKey == 'mounted_pane_view_action' ||
      operationKey == 'mounted_pane_api_action';
  if (!isMountedPaneOperation) {
    return false;
  }

  final expected = _normalizedTokenSet(<String?>[
    actionKey,
    actionTarget?.actionKey,
    actionTarget?.operationRef,
    actionTarget?.endpointRef,
    actionTarget?.sdkOperationId,
    actionTarget?.paneConfigSdkOperationId,
    actionTarget?.apiCapabilityEndpointId,
    actionTarget?.paneConfigApiCapabilityEndpointId,
  ]);
  if (expected.isEmpty) {
    return true;
  }

  final actual = _normalizedTokenSet(<String?>[
    operation.currentTargetId,
    operation.currentTargetTitle,
    for (final target in operation.targetStatuses) ...<String?>[
      target.targetId,
      target.displayName,
      target.endpoint,
    ],
  ]);
  if (actual.any(expected.contains)) {
    return true;
  }

  final activityText = operation.recentActivity.join('\n').toLowerCase();
  return expected.any(activityText.contains);
}

Set<String> _normalizedTokenSet(Iterable<String?> values) {
  return values
      .map(_trimmedOrNull)
      .whereType<String>()
      .map((value) => value.toLowerCase())
      .toSet();
}

String _operationFailureMessage(InterfaceOperationState operation) {
  final targetError = _firstTrimmed(
    operation.targetStatuses.map((target) => target.error),
  );
  return _trimmedOrNull(operation.error) ??
      targetError ??
      _trimmedOrNull(operation.summary) ??
      'Interface Host reported `${operation.status}` for `${operation.operationKey}`.';
}

String? _firstTrimmed(Iterable<String?> values) {
  for (final value in values) {
    final trimmed = _trimmedOrNull(value);
    if (trimmed != null) {
      return trimmed;
    }
  }
  return null;
}

InterfaceActionTarget _transportActionTarget(PaneRenderActionTarget target) {
  return InterfaceActionTarget(
    actionKey: target.actionKey,
    actionKind: target.actionKind,
    operationRef: target.operationRef,
    sdkOperationId: target.sdkOperationId,
    paneConfigSdkOperationId: target.paneConfigSdkOperationId,
    endpointRef: target.endpointRef,
    apiCapabilityEndpointId: target.apiCapabilityEndpointId,
    paneConfigApiCapabilityEndpointId: target.paneConfigApiCapabilityEndpointId,
  );
}

String interfacePaneRefForContext(PaneContext context) {
  final windowKey = _stringParameter(context, kPaneParamWindowKey);
  final layoutKey = _stringParameter(context, kPaneParamLayoutKey);
  final sectionKey = _stringParameter(context, kPaneParamSectionKey);
  if (windowKey != null && layoutKey != null && sectionKey != null) {
    return '$windowKey/$layoutKey/$sectionKey';
  }
  if (context.kind.trim().isNotEmpty) {
    return context.kind;
  }
  return context.paneId;
}

String? _stringParameter(PaneContext context, String key) {
  final value = context.parameters[key];
  if (value is! String) {
    return null;
  }
  return _trimmedOrNull(value);
}

String? _trimmedOrNull(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}

final interfacePaneMaterializedStatesProvider =
    Provider<List<InterfaceMaterializedPaneState>>((ref) {
      return const <InterfaceMaterializedPaneState>[];
    });

final interfaceHostViewStateCacheStoreConfigProvider =
    Provider<InterfaceHostViewStateCacheStoreConfig>((ref) {
      return const InterfaceHostViewStateCacheStoreConfig.memory();
    });

final interfaceHostViewStateCacheStoreProvider =
    Provider<InterfaceHostViewStateCacheStore>(
      dependencies: <ProviderOrFamily>[
        interfaceHostViewStateCacheStoreConfigProvider,
      ],
      (ref) {
        final store = buildInterfaceHostViewStateCacheStore(
          ref.watch(interfaceHostViewStateCacheStoreConfigProvider),
        );
        if (store is InterfaceHostViewStateCacheStoreLifecycle) {
          final closeableStore =
              store as InterfaceHostViewStateCacheStoreLifecycle;
          ref.onDispose(() {
            unawaited(closeableStore.close());
          });
        }
        return store;
      },
    );

final interfaceHostViewStateCacheProvider =
    Provider<InterfaceHostViewStateCache>(
      dependencies: <ProviderOrFamily>[
        interfaceHostViewStateCacheStoreProvider,
      ],
      (ref) {
        return InterfaceHostViewStateCache(
          ref.watch(interfaceHostViewStateCacheStoreProvider),
        );
      },
    );

enum InterfaceHostViewStateCacheSyncPhase { idle, syncing, ready, failed }

@immutable
class InterfaceHostViewStateCacheSyncStatus {
  const InterfaceHostViewStateCacheSyncStatus({
    required this.phase,
    this.namespace,
    this.result,
    this.errorMessage,
  });

  const InterfaceHostViewStateCacheSyncStatus.idle({String? namespace})
    : this(
        phase: InterfaceHostViewStateCacheSyncPhase.idle,
        namespace: namespace,
      );

  const InterfaceHostViewStateCacheSyncStatus.syncing({
    required String namespace,
  }) : this(
         phase: InterfaceHostViewStateCacheSyncPhase.syncing,
         namespace: namespace,
       );

  const InterfaceHostViewStateCacheSyncStatus.ready({
    required String namespace,
    required InterfaceHostViewStateCacheSyncResult result,
  }) : this(
         phase: InterfaceHostViewStateCacheSyncPhase.ready,
         namespace: namespace,
         result: result,
       );

  const InterfaceHostViewStateCacheSyncStatus.failed({
    required String namespace,
    required String errorMessage,
  }) : this(
         phase: InterfaceHostViewStateCacheSyncPhase.failed,
         namespace: namespace,
         errorMessage: errorMessage,
       );

  final InterfaceHostViewStateCacheSyncPhase phase;
  final String? namespace;
  final InterfaceHostViewStateCacheSyncResult? result;
  final String? errorMessage;

  bool get ready => phase == InterfaceHostViewStateCacheSyncPhase.ready;
  bool get failed => phase == InterfaceHostViewStateCacheSyncPhase.failed;
}

final interfaceHostViewStateCacheSyncStatusProvider =
    StateProvider<InterfaceHostViewStateCacheSyncStatus>((ref) {
      return const InterfaceHostViewStateCacheSyncStatus.idle();
    });

enum InterfaceRendererCapabilityHandshakePhase {
  idle,
  reporting,
  ready,
  failed,
}

@immutable
class InterfaceRendererCapabilityHandshakeStatus {
  const InterfaceRendererCapabilityHandshakeStatus({
    required this.phase,
    this.namespace,
    this.rendererId,
    this.capabilities,
    this.response,
    this.errorMessage,
  });

  const InterfaceRendererCapabilityHandshakeStatus.idle({
    String? namespace,
    String? rendererId,
  }) : this(
         phase: InterfaceRendererCapabilityHandshakePhase.idle,
         namespace: namespace,
         rendererId: rendererId,
       );

  const InterfaceRendererCapabilityHandshakeStatus.reporting({
    required String namespace,
    required String rendererId,
    required InterfaceRendererCapabilitiesState capabilities,
  }) : this(
         phase: InterfaceRendererCapabilityHandshakePhase.reporting,
         namespace: namespace,
         rendererId: rendererId,
         capabilities: capabilities,
       );

  const InterfaceRendererCapabilityHandshakeStatus.ready({
    required String namespace,
    required String rendererId,
    required InterfaceRendererCapabilitiesState capabilities,
    required InterfaceReportRendererCapabilitiesResponse response,
  }) : this(
         phase: InterfaceRendererCapabilityHandshakePhase.ready,
         namespace: namespace,
         rendererId: rendererId,
         capabilities: capabilities,
         response: response,
       );

  const InterfaceRendererCapabilityHandshakeStatus.failed({
    required String namespace,
    required String rendererId,
    required InterfaceRendererCapabilitiesState capabilities,
    required String errorMessage,
  }) : this(
         phase: InterfaceRendererCapabilityHandshakePhase.failed,
         namespace: namespace,
         rendererId: rendererId,
         capabilities: capabilities,
         errorMessage: errorMessage,
       );

  final InterfaceRendererCapabilityHandshakePhase phase;
  final String? namespace;
  final String? rendererId;
  final InterfaceRendererCapabilitiesState? capabilities;
  final InterfaceReportRendererCapabilitiesResponse? response;
  final String? errorMessage;

  bool get ready => phase == InterfaceRendererCapabilityHandshakePhase.ready;
  bool get failed => phase == InterfaceRendererCapabilityHandshakePhase.failed;
}

final interfaceRendererCapabilityHandshakeStatusProvider =
    StateProvider<InterfaceRendererCapabilityHandshakeStatus>((ref) {
      return const InterfaceRendererCapabilityHandshakeStatus.idle();
    });

final interfacePaneViewStateDecoderRegistryProvider =
    Provider<InterfaceViewStateDecoderRegistry>(
      dependencies: <ProviderOrFamily>[currentInterfacePackageRuntimeProvider],
      (ref) {
        final runtime = ref.watch(currentInterfacePackageRuntimeProvider);
        return runtime?.viewStateDecoderRegistry ??
            const InterfaceViewStateDecoderRegistry.empty();
      },
    );

InterfaceMaterializedPaneState? interfacePaneMaterializedStateForContext(
  WidgetRef ref,
  PaneContext context,
) {
  final explicit =
      context.parameters[kPaneParamMaterializedState]
          as InterfaceMaterializedPaneState?;
  if (explicit != null) {
    return explicit;
  }
  final stateKey = context.parameters[kPaneParamPaneStateKey] as String?;
  if (stateKey == null || stateKey.isEmpty) {
    return null;
  }
  for (final state in ref.watch(interfacePaneMaterializedStatesProvider)) {
    if (state.paneStateKey == stateKey) {
      return state;
    }
  }
  return null;
}

Future<InterfaceHostViewStateCacheSyncResult> interfaceSyncHostViewStateCache(
  WidgetRef ref,
  InterfaceHostState hostState, {
  String? interfacePackageId,
  String? interfacePackageName,
}) {
  final cache = ref.read(interfaceHostViewStateCacheProvider);
  return cache.replaceFromHostState(
    hostState,
    interfacePackageId: interfacePackageId,
    interfacePackageName: interfacePackageName,
  );
}

Future<InterfaceHostViewStateCacheSyncResult> interfaceCacheHostViewState(
  WidgetRef ref,
  InterfaceHostState hostState,
) {
  final packageRuntime = ref.read(currentInterfacePackageRuntimeProvider);
  return interfaceSyncHostViewStateCache(
    ref,
    hostState,
    interfacePackageId: packageRuntime?.interfacePackageId,
    interfacePackageName: packageRuntime?.interfacePackageName,
  );
}

Future<InterfaceHostViewStateCacheEntry?>
interfaceCachedPaneViewStateForContext(WidgetRef ref, PaneContext context) {
  final namespace = ref.watch(interfacePaneApiNamespaceProvider);
  final stateKey = _stringParameter(context, kPaneParamPaneStateKey);
  if (stateKey == null) {
    return Future<InterfaceHostViewStateCacheEntry?>.value();
  }
  return ref
      .watch(interfaceHostViewStateCacheStoreProvider)
      .readPaneState(
        namespace: namespace,
        paneStateKey: stateKey,
        viewRef: _stringParameter(context, kPaneParamViewRef),
        projectionViewKey: _stringParameter(context, kPaneParamViewKey),
      );
}

Future<InterfaceReportRendererCapabilitiesResponse>
interfaceReportRendererCapabilities(
  WidgetRef ref, {
  required InterfaceRendererCapabilitiesState rendererCapabilities,
  String? namespace,
}) {
  final resolvedNamespace =
      _trimmedOrNull(namespace) ??
      _trimmedOrNull(ref.read(interfacePaneApiNamespaceProvider));
  if (resolvedNamespace == null) {
    throw StateError(
      'Interface renderer capability report requires namespace.',
    );
  }
  return ref
      .read(interfaceSdkClientProvider)
      .reportRendererCapabilities(
        namespace: resolvedNamespace,
        rendererCapabilities: rendererCapabilities,
      );
}

Future<InterfaceSyncViewStateCursorResponse> interfaceSyncViewStateCursor(
  WidgetRef ref, {
  String? namespace,
  String? rendererId,
  String? knownCursor,
  String? knownDigest,
}) {
  final resolvedNamespace =
      _trimmedOrNull(namespace) ??
      _trimmedOrNull(ref.read(interfacePaneApiNamespaceProvider));
  if (resolvedNamespace == null) {
    throw StateError('Interface view-state cursor sync requires namespace.');
  }
  return ref
      .read(interfaceSdkClientProvider)
      .syncViewStateCursor(
        namespace: resolvedNamespace,
        rendererId: rendererId,
        knownCursor: knownCursor,
        knownDigest: knownDigest,
      );
}

InterfaceViewStateDecodeResult<T> interfacePaneViewStateForContext<
  T extends Object
>(WidgetRef ref, PaneContext context) {
  final materializedState = interfacePaneMaterializedStateForContext(
    ref,
    context,
  );
  final decoderRegistry = ref.watch(
    interfacePaneViewStateDecoderRegistryProvider,
  );
  return decoderRegistry.decodeMaterialized<T>(
    materializedState: materializedState,
    viewRef: _stringParameter(context, kPaneParamViewRef),
    viewKey: _stringParameter(context, kPaneParamViewKey),
  );
}

class InterfaceRendererCapabilityHandshakeSync extends ConsumerStatefulWidget {
  const InterfaceRendererCapabilityHandshakeSync({
    required this.rendererId,
    required this.child,
    super.key,
    this.interfacePackageRuntime,
    this.rendererVersion,
    this.enabled = true,
  });

  final String rendererId;
  final InterfacePackageRuntime? interfacePackageRuntime;
  final String? rendererVersion;
  final bool enabled;
  final Widget child;

  @override
  ConsumerState<InterfaceRendererCapabilityHandshakeSync> createState() =>
      _InterfaceRendererCapabilityHandshakeSyncState();
}

class _InterfaceRendererCapabilityHandshakeSyncState
    extends ConsumerState<InterfaceRendererCapabilityHandshakeSync> {
  int _syncGeneration = 0;

  @override
  void initState() {
    super.initState();
    _scheduleCapabilityReport();
  }

  @override
  void didUpdateWidget(
    covariant InterfaceRendererCapabilityHandshakeSync oldWidget,
  ) {
    super.didUpdateWidget(oldWidget);
    if (!identical(
          oldWidget.interfacePackageRuntime,
          widget.interfacePackageRuntime,
        ) ||
        oldWidget.rendererId != widget.rendererId ||
        oldWidget.rendererVersion != widget.rendererVersion ||
        oldWidget.enabled != widget.enabled) {
      _scheduleCapabilityReport();
    }
  }

  @override
  Widget build(BuildContext context) => widget.child;

  void _scheduleCapabilityReport() {
    final generation = ++_syncGeneration;
    unawaited(Future<void>(() => _reportCapabilities(generation)));
  }

  Future<void> _reportCapabilities(int generation) async {
    if (!mounted || generation != _syncGeneration) {
      return;
    }
    final namespace = _trimmedOrNull(
      ref.read(interfacePaneApiNamespaceProvider),
    );
    final rendererId = _trimmedOrNull(widget.rendererId);
    final runtime = widget.interfacePackageRuntime;
    if (!widget.enabled ||
        namespace == null ||
        rendererId == null ||
        runtime == null) {
      ref
          .read(interfaceRendererCapabilityHandshakeStatusProvider.notifier)
          .state = InterfaceRendererCapabilityHandshakeStatus.idle(
        namespace: namespace,
        rendererId: rendererId,
      );
      return;
    }

    final capabilities = buildInterfaceRendererCapabilities(
      runtime: runtime,
      rendererId: rendererId,
      rendererVersion: widget.rendererVersion,
    );
    ref
        .read(interfaceRendererCapabilityHandshakeStatusProvider.notifier)
        .state = InterfaceRendererCapabilityHandshakeStatus.reporting(
      namespace: namespace,
      rendererId: rendererId,
      capabilities: capabilities,
    );
    try {
      final response = await interfaceReportRendererCapabilities(
        ref,
        namespace: namespace,
        rendererCapabilities: capabilities,
      );
      if (!mounted || generation != _syncGeneration) {
        return;
      }
      ref
          .read(interfaceRendererCapabilityHandshakeStatusProvider.notifier)
          .state = InterfaceRendererCapabilityHandshakeStatus.ready(
        namespace: namespace,
        rendererId: rendererId,
        capabilities: capabilities,
        response: response,
      );
    } catch (error) {
      if (!mounted || generation != _syncGeneration) {
        return;
      }
      ref
          .read(interfaceRendererCapabilityHandshakeStatusProvider.notifier)
          .state = InterfaceRendererCapabilityHandshakeStatus.failed(
        namespace: namespace,
        rendererId: rendererId,
        capabilities: capabilities,
        errorMessage: error.toString(),
      );
    }
  }
}

class InterfaceHostViewStateCacheLifecycleSync extends ConsumerStatefulWidget {
  const InterfaceHostViewStateCacheLifecycleSync({
    required this.hostState,
    required this.child,
    super.key,
  });

  final InterfaceHostState hostState;
  final Widget child;

  @override
  ConsumerState<InterfaceHostViewStateCacheLifecycleSync> createState() =>
      _InterfaceHostViewStateCacheLifecycleSyncState();
}

class _InterfaceHostViewStateCacheLifecycleSyncState
    extends ConsumerState<InterfaceHostViewStateCacheLifecycleSync> {
  int _syncGeneration = 0;

  @override
  void initState() {
    super.initState();
    _scheduleHostStateSync();
  }

  @override
  void didUpdateWidget(
    covariant InterfaceHostViewStateCacheLifecycleSync oldWidget,
  ) {
    super.didUpdateWidget(oldWidget);
    if (!identical(oldWidget.hostState, widget.hostState)) {
      _scheduleHostStateSync();
    }
  }

  @override
  Widget build(BuildContext context) => widget.child;

  void _scheduleHostStateSync() {
    final generation = ++_syncGeneration;
    final hostState = widget.hostState;
    unawaited(Future<void>(() => _syncHostState(generation, hostState)));
  }

  Future<void> _syncHostState(
    int generation,
    InterfaceHostState hostState,
  ) async {
    if (!mounted || generation != _syncGeneration) {
      return;
    }
    final namespace = _trimmedOrNull(hostState.namespace);
    final runtime = hostState.runtime;
    if (namespace == null || runtime == null) {
      ref.read(interfaceHostViewStateCacheSyncStatusProvider.notifier).state =
          InterfaceHostViewStateCacheSyncStatus.idle(namespace: namespace);
      return;
    }

    ref.read(interfaceHostViewStateCacheSyncStatusProvider.notifier).state =
        InterfaceHostViewStateCacheSyncStatus.syncing(namespace: namespace);
    try {
      final result = await interfaceSyncHostViewStateCache(ref, hostState);
      if (!mounted || generation != _syncGeneration) {
        return;
      }
      ref
          .read(interfaceHostViewStateCacheSyncStatusProvider.notifier)
          .state = InterfaceHostViewStateCacheSyncStatus.ready(
        namespace: namespace,
        result: result,
      );
    } catch (error) {
      if (!mounted || generation != _syncGeneration) {
        return;
      }
      ref
          .read(interfaceHostViewStateCacheSyncStatusProvider.notifier)
          .state = InterfaceHostViewStateCacheSyncStatus.failed(
        namespace: namespace,
        errorMessage: error.toString(),
      );
    }
  }
}

class InterfacePaneApiScope extends StatelessWidget {
  const InterfacePaneApiScope({
    required this.namespace,
    required this.child,
    super.key,
    this.materializedPaneStates = const <InterfaceMaterializedPaneState>[],
  });

  final String namespace;
  final List<InterfaceMaterializedPaneState> materializedPaneStates;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return ProviderScope(
      overrides: <Override>[
        interfacePaneApiNamespaceProvider.overrideWithValue(namespace),
        interfacePaneMaterializedStatesProvider.overrideWithValue(
          materializedPaneStates,
        ),
      ],
      child: child,
    );
  }
}
