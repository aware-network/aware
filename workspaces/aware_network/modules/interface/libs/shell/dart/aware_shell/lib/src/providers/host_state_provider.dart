import 'dart:async';

import 'package:aware_interface_service_api/aware_interface_service_api.dart';
import 'package:aware_interface_sdk/aware_interface_sdk.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logging/logging.dart';
import 'package:uuid/uuid.dart';

const String _expectedInterfaceControlService = 'aware_interface_service';
const int _expectedInterfaceControlProtocolVersion = 1;
const String _interfaceNamespaceEnv = 'AWARE_INTERFACE_NAMESPACE';
const String _interfaceEnvironmentIdEnv = 'AWARE_INTERFACE_ENVIRONMENT_ID';
const String _interfaceEnvironmentProfileIdEnv =
    'AWARE_INTERFACE_ENVIRONMENT_PROFILE_ID';
const String _interfaceActorConfigIdEnv = 'AWARE_INTERFACE_ACTOR_CONFIG_ID';
const String _interfaceClassInstanceIdentityIdEnv =
    'AWARE_INTERFACE_CLASS_INSTANCE_IDENTITY_ID';
const String _interfaceEnvironmentSessionIdEnv =
    'AWARE_INTERFACE_ENVIRONMENT_SESSION_ID';
const String _interfaceEnvironmentSessionConfigIdEnv =
    'AWARE_INTERFACE_ENVIRONMENT_SESSION_CONFIG_ID';
const String _interfaceEnvironmentSessionKeyEnv =
    'AWARE_INTERFACE_ENVIRONMENT_SESSION_KEY';
const String _interfaceEnvironmentSessionTitleEnv =
    'AWARE_INTERFACE_ENVIRONMENT_SESSION_TITLE';
const String _interfaceEnvironmentSessionDescriptionEnv =
    'AWARE_INTERFACE_ENVIRONMENT_SESSION_DESCRIPTION';
const String _interfaceEnvironmentSessionPurposeEnv =
    'AWARE_INTERFACE_ENVIRONMENT_SESSION_PURPOSE';
const String _interfaceEnvironmentSourceKindEnv =
    'AWARE_INTERFACE_ENVIRONMENT_SOURCE_KIND';
const String _interfaceEnvironmentSourceRefEnv =
    'AWARE_INTERFACE_ENVIRONMENT_SOURCE_REF';
const String _uuidNamespaceUrl = '6ba7b811-9dad-11d1-80b4-00c04fd430c8';
final Uuid _uuid = Uuid();

typedef InterfaceControlClient = InterfaceSdkClient;
typedef InterfaceControlClientError = InterfaceSdkClientError;

final interfaceHostTargetProvider = Provider<InterfaceHostTarget>((ref) {
  return resolveInterfaceHostTarget(localServiceHost: true);
});

@Deprecated('Use interfaceHostTargetProvider.')
final interfaceControlTargetProvider = interfaceHostTargetProvider;

final interfaceHostClientProvider = Provider<InterfaceSdkClient>(
  dependencies: <ProviderOrFamily>[interfaceHostTargetProvider],
  (ref) {
    return InterfaceSdkClient.fromHostTarget(
      ref.watch(interfaceHostTargetProvider),
    );
  },
);

@Deprecated('Use interfaceHostClientProvider or interfaceSdkClientProvider.')
final interfaceControlClientProvider = interfaceHostClientProvider;

final interfaceSdkClientProvider = interfaceHostClientProvider;

final interfaceControlRemoteUrlProvider = Provider<String?>(
  dependencies: <ProviderOrFamily>[interfaceHostTargetProvider],
  (ref) {
    return ref.watch(interfaceHostTargetProvider).controlPlaneUrl;
  },
);

final interfaceControlNamespaceProvider = FutureProvider<String>(
  dependencies: <ProviderOrFamily>[interfaceHostTargetProvider],
  (ref) async {
    final target = ref.watch(interfaceHostTargetProvider);
    final explicit = _compileTimeInterfaceNamespace();
    if (explicit != null) {
      return explicit;
    }
    return _fallbackInterfaceNamespace(target);
  },
);

final interfaceEnvironmentEntryTargetProvider =
    Provider<InterfaceEnvironmentEntryTarget?>((ref) {
  return resolveInterfaceEnvironmentEntryTarget();
});

final interfaceHostStateFollowPollIntervalMsProvider = Provider<int>((ref) {
  return 1000;
});

final interfaceHostStateFollowReconnectDelayMsProvider = Provider<int>((ref) {
  return 1000;
});

final interfaceHostRemoteEntryEnabledProvider = Provider<bool>(
  dependencies: <ProviderOrFamily>[interfaceHostTargetProvider],
  (ref) {
    return ref.watch(interfaceHostTargetProvider).isRemote;
  },
);

class InterfaceHostConnectionState {
  const InterfaceHostConnectionState({
    required this.service,
    required this.statusLabel,
    required this.title,
    required this.message,
    required this.connected,
    required this.blocksRuntimeEntry,
    required this.restartRecommended,
    required this.restartReason,
    required this.socketPath,
    required this.daemonStartedAt,
    required this.daemonSourceFingerprint,
    required this.expectedSourceFingerprint,
    required this.repositoryRoot,
    required this.stateHome,
    required this.defaultEndpoint,
    required this.namespaceCount,
    this.protocolVersion = _expectedInterfaceControlProtocolVersion,
    this.namespace = '',
    this.namespaceBound = false,
    this.remoteTarget = false,
    this.targetTransport = 'local_socket',
    this.bootstrapSourceLabel = 'unknown',
    this.compatibilityIssues = const <String>[],
  });

  factory InterfaceHostConnectionState.fromBinding({
    required InterfaceHostTarget target,
    required String namespace,
    required PingResponse ping,
    required List<String> compatibilityIssues,
    required bool namespaceBound,
  }) {
    final incompatible = compatibilityIssues.isNotEmpty;
    final legacyFreshnessRestartRequired =
        !target.isRemote && !_hasText(ping.expectedSourceFingerprint);
    final restartRecommended = incompatible
        ? false
        : ping.restartRecommended || legacyFreshnessRestartRequired;
    final restartReason = _normalizeHostRestartReason(
      ping.restartReason,
      daemonSourceFingerprint: ping.daemonSourceFingerprint,
      expectedSourceFingerprint: ping.expectedSourceFingerprint,
      requireLegacyFreshnessMetadata: !target.isRemote,
      reportedRestartRecommended: ping.restartRecommended,
    );
    final connected = ping.status == 'ok';
    final statusLabel = incompatible
        ? 'Incompatible'
        : restartRecommended
            ? 'Restart Recommended'
            : connected
                ? 'Connected'
                : 'Unavailable';
    final title = incompatible
        ? 'Interface Host Incompatible'
        : restartRecommended
            ? (target.isRemote
                ? 'Remote Interface Host Refresh Recommended'
                : 'Interface Host Restart Recommended')
            : connected
                ? (target.isRemote
                    ? 'Remote Interface Host Connected'
                    : 'Interface Host Connected')
                : 'Interface Host Unavailable';
    final message = incompatible
        ? 'Flutter reached an Interface Host, but the control-plane contract does not match this renderer. Update the app or the host before continuing.'
        : restartRecommended
            ? (target.isRemote
                ? 'Flutter reached the remote Interface Host, but it reported stale bootstrap state. Refresh or redeploy the host before continuing into the Interface runtime.'
                : 'Interface Host is reachable, but it is stale for this checkout. Restart the daemon before continuing into the Interface runtime.')
            : connected
                ? (target.isRemote
                    ? 'Flutter is connected to the remote Interface Host. Interface runtime state now flows through this host first.'
                    : 'Flutter is connected to the Interface Host. Interface runtime state now flows through this host first.')
                : 'Flutter reached the Interface Host, but it did not report an active runtime status yet.';
    return InterfaceHostConnectionState(
      service: ping.service,
      statusLabel: statusLabel,
      title: title,
      message: message,
      connected: connected,
      blocksRuntimeEntry: incompatible || restartRecommended || !connected,
      restartRecommended: restartRecommended,
      restartReason:
          incompatible ? compatibilityIssues.join('; ') : restartReason,
      socketPath: ping.socketPath,
      daemonStartedAt: ping.daemonStartedAt,
      daemonSourceFingerprint: ping.daemonSourceFingerprint,
      expectedSourceFingerprint: ping.expectedSourceFingerprint,
      repositoryRoot: ping.repositoryRoot,
      stateHome: ping.stateHome,
      defaultEndpoint: ping.defaultEndpoint,
      namespaceCount: ping.namespaces.length,
      protocolVersion: ping.protocolVersion,
      namespace: namespace,
      namespaceBound: namespaceBound,
      remoteTarget: target.isRemote,
      targetTransport: target.transportLabel,
      bootstrapSourceLabel: target.sourceLabel,
      compatibilityIssues: List<String>.unmodifiable(compatibilityIssues),
    );
  }

  factory InterfaceHostConnectionState.fromPing(
    PingResponse ping, {
    InterfaceHostTarget? target,
    String? namespace,
  }) {
    final effectiveTarget =
        target ?? resolveInterfaceHostTarget(controlPlaneUrl: null);
    final effectiveNamespace = namespace ?? '';
    final compatibilityIssues = _interfaceHostCompatibilityIssues(ping);
    final namespaceSummary = _findHostedNamespace(
      ping.namespaces,
      effectiveNamespace,
    );
    return InterfaceHostConnectionState.fromBinding(
      target: effectiveTarget,
      namespace: effectiveNamespace,
      ping: ping,
      compatibilityIssues: compatibilityIssues,
      namespaceBound: namespaceSummary != null,
    );
  }

  factory InterfaceHostConnectionState.checking({
    String service = 'aware_interface_service',
  }) {
    return InterfaceHostConnectionState(
      service: service,
      statusLabel: 'Checking',
      title: 'Checking Interface Host',
      message:
          'Flutter is verifying the Interface Host before entering a workspace session.',
      connected: false,
      blocksRuntimeEntry: false,
      restartRecommended: false,
      restartReason: null,
      socketPath: null,
      daemonStartedAt: null,
      daemonSourceFingerprint: null,
      expectedSourceFingerprint: null,
      repositoryRoot: null,
      stateHome: null,
      defaultEndpoint: null,
      namespaceCount: 0,
    );
  }

  final String service;
  final String statusLabel;
  final String title;
  final String message;
  final bool connected;
  final bool blocksRuntimeEntry;
  final bool restartRecommended;
  final String? restartReason;
  final String? socketPath;
  final String? daemonStartedAt;
  final String? daemonSourceFingerprint;
  final String? expectedSourceFingerprint;
  final String? repositoryRoot;
  final String? stateHome;
  final String? defaultEndpoint;
  final int namespaceCount;
  final int protocolVersion;
  final String namespace;
  final bool namespaceBound;
  final bool remoteTarget;
  final String targetTransport;
  final String bootstrapSourceLabel;
  final List<String> compatibilityIssues;
}

class InterfaceHostNamespaceBindingState {
  const InterfaceHostNamespaceBindingState({
    required this.namespace,
    required this.bound,
    this.hostLabel,
    this.actorId,
    this.interfaceId,
    this.interfaceSessionId,
    this.environmentId,
    this.environmentConfigId,
    this.warnings = const <String>[],
  });

  factory InterfaceHostNamespaceBindingState.pending({
    required String namespace,
  }) {
    return InterfaceHostNamespaceBindingState(
      namespace: namespace,
      bound: false,
    );
  }

  factory InterfaceHostNamespaceBindingState.fromHostedNamespace(
    HostedInterfaceNamespace namespaceState,
  ) {
    return InterfaceHostNamespaceBindingState(
      namespace: namespaceState.namespace,
      bound: true,
      hostLabel: namespaceState.hostLabel,
      actorId: namespaceState.actorId,
      interfaceId: namespaceState.interfaceId,
      interfaceSessionId: namespaceState.interfaceSessionId,
      environmentId: namespaceState.environmentId,
      environmentConfigId: namespaceState.environmentConfigId,
      warnings: List<String>.unmodifiable(namespaceState.warnings),
    );
  }

  final String namespace;
  final bool bound;
  final String? hostLabel;
  final UuidValue? actorId;
  final UuidValue? interfaceId;
  final UuidValue? interfaceSessionId;
  final UuidValue? environmentId;
  final UuidValue? environmentConfigId;
  final List<String> warnings;
}

class InterfaceEnvironmentEntryTarget {
  const InterfaceEnvironmentEntryTarget({
    this.environmentId,
    this.environmentProfileId,
    this.actorConfigId,
    this.classInstanceIdentityId,
    this.objectInstanceGraphBranchKey = 'all',
    this.objectInstanceGraphBranchId,
    this.requestedRoleConfigIds = const <UuidValue>[],
    this.requestedRoleConfigNames = const <String>[],
    this.environmentSessionId,
    this.environmentSessionConfigId,
    this.sessionKey,
    this.title,
    this.description,
    this.purpose,
    this.sourceKind,
    this.sourceRef,
    this.reason = 'shell_environment_entry',
    this.evidence = const <String, dynamic>{},
  });

  final UuidValue? environmentId;
  final UuidValue? environmentProfileId;
  final UuidValue? actorConfigId;
  final UuidValue? classInstanceIdentityId;
  final String objectInstanceGraphBranchKey;
  final UuidValue? objectInstanceGraphBranchId;
  final List<UuidValue> requestedRoleConfigIds;
  final List<String> requestedRoleConfigNames;
  final UuidValue? environmentSessionId;
  final UuidValue? environmentSessionConfigId;
  final String? sessionKey;
  final String? title;
  final String? description;
  final String? purpose;
  final String? sourceKind;
  final String? sourceRef;
  final String? reason;
  final Map<String, dynamic> evidence;

  bool get hasEntryCoordinates {
    return environmentId != null ||
        environmentProfileId != null ||
        actorConfigId != null ||
        classInstanceIdentityId != null ||
        environmentSessionId != null ||
        environmentSessionConfigId != null ||
        _hasText(sessionKey);
  }
}

class InterfaceHostBindingState {
  const InterfaceHostBindingState({
    required this.target,
    required this.connection,
    required this.namespace,
    required this.namespaceBinding,
    required this.protocolVersion,
    required this.daemonInstanceId,
    this.compatibilityIssues = const <String>[],
  });

  factory InterfaceHostBindingState.fromPing({
    required InterfaceHostTarget target,
    required String namespace,
    required PingResponse ping,
  }) {
    final compatibilityIssues = _interfaceHostCompatibilityIssues(ping);
    final namespaceSummary = _findHostedNamespace(ping.namespaces, namespace);
    final namespaceBinding = namespaceSummary == null
        ? InterfaceHostNamespaceBindingState.pending(namespace: namespace)
        : InterfaceHostNamespaceBindingState.fromHostedNamespace(
            namespaceSummary,
          );
    return InterfaceHostBindingState(
      target: target,
      connection: InterfaceHostConnectionState.fromBinding(
        target: target,
        namespace: namespace,
        ping: ping,
        compatibilityIssues: compatibilityIssues,
        namespaceBound: namespaceBinding.bound,
      ),
      namespace: namespace,
      namespaceBinding: namespaceBinding,
      protocolVersion: ping.protocolVersion,
      daemonInstanceId: ping.daemonInstanceId,
      compatibilityIssues: List<String>.unmodifiable(compatibilityIssues),
    );
  }

  final InterfaceHostTarget target;
  final InterfaceHostConnectionState connection;
  final String namespace;
  final InterfaceHostNamespaceBindingState namespaceBinding;
  final int protocolVersion;
  final UuidValue? daemonInstanceId;
  final List<String> compatibilityIssues;

  bool get compatible => compatibilityIssues.isEmpty;
}

Map<String, dynamic>? interfaceHostRuntimeWindowLayoutPayload(
  InterfaceHostState? hostState,
) {
  final payload =
      hostState?.runtime?.resolvedView?.hostPayload['window_layout'];
  if (payload is! Map) {
    return null;
  }
  final casted = payload.cast<String, dynamic>();
  return casted.isEmpty ? null : casted;
}

InterfaceWindowLayoutState? interfaceHostRuntimeWindowLayoutState(
  InterfaceHostState? hostState,
) {
  return hostState?.runtime?.windowLayout;
}

bool interfaceHostRuntimeShellAvailable(InterfaceHostState? hostState) {
  final runtime = hostState?.runtime;
  final resolvedView = runtime?.resolvedView;
  final windowLayoutState = interfaceHostRuntimeWindowLayoutState(hostState);
  final windowLayoutPayload = interfaceHostRuntimeWindowLayoutPayload(
    hostState,
  );
  if (runtime == null ||
      resolvedView == null ||
      !_interfaceHostRuntimePackageSelected(resolvedView)) {
    return false;
  }
  if (windowLayoutState != null) {
    return windowLayoutState.sections.isNotEmpty;
  }
  final rawSections = windowLayoutPayload?['sections'];
  return rawSections is List && rawSections.isNotEmpty;
}

bool _interfaceHostRuntimePackageSelected(InterfaceResolvedView resolvedView) {
  final packageName = resolvedView.interfacePackageName?.trim();
  if (packageName != null && packageName.isNotEmpty) {
    return true;
  }
  final packageId = resolvedView.interfacePackageId?.uuid.trim();
  return packageId != null && packageId.isNotEmpty;
}

String? interfaceHostRuntimeLayoutKey(InterfaceHostState? hostState) {
  final state = interfaceHostRuntimeWindowLayoutState(hostState);
  final stateKey = state?.layoutKey.trim();
  if (stateKey != null && stateKey.isNotEmpty) {
    return stateKey;
  }
  final windowLayout = interfaceHostRuntimeWindowLayoutPayload(hostState);
  final raw = windowLayout?['layout_key'];
  if (raw is! String) {
    return null;
  }
  final normalized = raw.trim();
  return normalized.isEmpty ? null : normalized;
}

UuidValue? interfaceHostRuntimeLayoutConfigId(InterfaceHostState? hostState) {
  final runtimeValue = hostState?.runtime?.activeLayoutConfigId;
  if (runtimeValue != null) {
    return runtimeValue;
  }
  final stateValue = interfaceHostRuntimeWindowLayoutState(
    hostState,
  )?.layoutConfigId;
  if (stateValue != null) {
    return stateValue;
  }
  final windowLayout = interfaceHostRuntimeWindowLayoutPayload(hostState);
  final raw = windowLayout?['layout_config_id'];
  if (raw is! String) {
    return null;
  }
  final normalized = raw.trim();
  if (normalized.isEmpty) {
    return null;
  }
  return UuidValue.fromString(normalized);
}

List<InterfaceRuntimeLayoutState> interfaceHostRuntimeLayoutStates(
  InterfaceHostState? hostState,
) {
  final layouts = hostState?.runtime?.layoutStates;
  if (layouts == null || layouts.isEmpty) {
    return const <InterfaceRuntimeLayoutState>[];
  }
  return List<InterfaceRuntimeLayoutState>.unmodifiable(layouts);
}

List<InterfaceRuntimeSectionRepresentationState>
    interfaceHostRuntimeSectionRepresentations(InterfaceHostState? hostState) {
  final representations = hostState?.runtime?.sectionRepresentations;
  if (representations == null || representations.isEmpty) {
    return const <InterfaceRuntimeSectionRepresentationState>[];
  }
  return List<InterfaceRuntimeSectionRepresentationState>.unmodifiable(
    representations,
  );
}

bool canEnterInterfaceHostRuntimeShell({
  required InterfaceHostConnectionState? connection,
  required InterfaceHostState? hostState,
}) {
  if (connection == null ||
      !connection.connected ||
      connection.blocksRuntimeEntry) {
    return false;
  }
  return interfaceHostRuntimeShellAvailable(hostState);
}

String? _normalizeHostRestartReason(
  String? raw, {
  required String? daemonSourceFingerprint,
  required String? expectedSourceFingerprint,
  required bool requireLegacyFreshnessMetadata,
  required bool reportedRestartRecommended,
}) {
  final normalized = raw?.trim();
  if (normalized != null && normalized.isNotEmpty) {
    return normalized;
  }
  if (!requireLegacyFreshnessMetadata) {
    return reportedRestartRecommended
        ? 'interface host reported restart recommended'
        : null;
  }
  if (!_hasText(expectedSourceFingerprint)) {
    return 'daemon is missing freshness-comparison metadata';
  }
  if (!_hasText(daemonSourceFingerprint)) {
    return 'daemon is missing source-fingerprint metadata';
  }
  return null;
}

bool _hasText(String? value) => value != null && value.trim().isNotEmpty;

String? _compileTimeInterfaceNamespace() {
  const raw = String.fromEnvironment(_interfaceNamespaceEnv);
  final normalized = raw.trim();
  return normalized.isEmpty ? null : normalized;
}

InterfaceEnvironmentEntryTarget? resolveInterfaceEnvironmentEntryTarget() {
  final target = InterfaceEnvironmentEntryTarget(
    environmentId: _compileTimeUuidValue(
      _interfaceEnvironmentIdEnv,
      const String.fromEnvironment(_interfaceEnvironmentIdEnv),
    ),
    environmentProfileId: _compileTimeUuidValue(
      _interfaceEnvironmentProfileIdEnv,
      const String.fromEnvironment(_interfaceEnvironmentProfileIdEnv),
    ),
    actorConfigId: _compileTimeUuidValue(
      _interfaceActorConfigIdEnv,
      const String.fromEnvironment(_interfaceActorConfigIdEnv),
    ),
    classInstanceIdentityId: _compileTimeUuidValue(
      _interfaceClassInstanceIdentityIdEnv,
      const String.fromEnvironment(_interfaceClassInstanceIdentityIdEnv),
    ),
    environmentSessionId: _compileTimeUuidValue(
      _interfaceEnvironmentSessionIdEnv,
      const String.fromEnvironment(_interfaceEnvironmentSessionIdEnv),
    ),
    environmentSessionConfigId: _compileTimeUuidValue(
      _interfaceEnvironmentSessionConfigIdEnv,
      const String.fromEnvironment(_interfaceEnvironmentSessionConfigIdEnv),
    ),
    sessionKey: _compileTimeText(
      const String.fromEnvironment(_interfaceEnvironmentSessionKeyEnv),
    ),
    title: _compileTimeText(
      const String.fromEnvironment(_interfaceEnvironmentSessionTitleEnv),
    ),
    description: _compileTimeText(
      const String.fromEnvironment(_interfaceEnvironmentSessionDescriptionEnv),
    ),
    purpose: _compileTimeText(
      const String.fromEnvironment(_interfaceEnvironmentSessionPurposeEnv),
    ),
    sourceKind: _compileTimeText(
      const String.fromEnvironment(_interfaceEnvironmentSourceKindEnv),
    ),
    sourceRef: _compileTimeText(
      const String.fromEnvironment(_interfaceEnvironmentSourceRefEnv),
    ),
    evidence: const <String, dynamic>{'source': 'interface_shell_dart_define'},
  );
  return target.hasEntryCoordinates ? target : null;
}

String? _compileTimeText(String raw) {
  final normalized = raw.trim();
  return normalized.isEmpty ? null : normalized;
}

UuidValue? _compileTimeUuidValue(String environmentName, String raw) {
  final normalized = raw.trim();
  if (normalized.isEmpty) {
    return null;
  }
  try {
    return UuidValue.fromString(normalized);
  } catch (_) {
    throw StateError(
      '$environmentName must be a UUID when provided: $normalized',
    );
  }
}

String _fallbackInterfaceNamespace(InterfaceHostTarget target) {
  final targetKey = target.controlPlaneUrl ?? target.socketPath;
  final stableId = _uuid.v5(
    _uuidNamespaceUrl,
    'aware://interface/flutter/${target.transportLabel}/${targetKey ?? 'default'}',
  );
  return 'flutter-${stableId.substring(0, 8)}';
}

List<String> _interfaceHostCompatibilityIssues(PingResponse ping) {
  final issues = <String>[];
  if (ping.service.trim() != _expectedInterfaceControlService) {
    issues.add(
      'unexpected_service:${ping.service.trim().isEmpty ? '<empty>' : ping.service.trim()}',
    );
  }
  if (ping.protocolVersion != _expectedInterfaceControlProtocolVersion) {
    issues.add('unsupported_protocol_version:${ping.protocolVersion}');
  }
  return issues;
}

HostedInterfaceNamespace? _findHostedNamespace(
  List<HostedInterfaceNamespace> namespaces,
  String namespace,
) {
  final normalizedNamespace = namespace.trim().toLowerCase();
  if (normalizedNamespace.isEmpty) {
    return null;
  }
  for (final namespaceState in namespaces) {
    if (namespaceState.namespace.trim().toLowerCase() == normalizedNamespace) {
      return namespaceState;
    }
  }
  return null;
}

bool _hostStateMatchesEnvironmentEntryTarget(
  InterfaceHostState hostState,
  InterfaceEnvironmentEntryTarget target,
) {
  final session = hostState.environmentSession;
  final navigation = hostState.environmentNavigation;
  if (session?.accepted != true && navigation?.accepted != true) {
    return false;
  }
  if (target.environmentId != null &&
      session?.environmentId != target.environmentId &&
      navigation?.environmentId != target.environmentId) {
    return false;
  }
  if (target.environmentProfileId != null &&
      session?.environmentProfileId != target.environmentProfileId) {
    return false;
  }
  if (target.environmentSessionId != null &&
      session?.environmentSessionId != target.environmentSessionId &&
      navigation?.environmentSessionId != target.environmentSessionId) {
    return false;
  }
  if (_hasText(target.sessionKey) &&
      session?.environmentSessionKey != target.sessionKey) {
    return false;
  }
  return true;
}

final interfaceHostBindingProvider = FutureProvider<InterfaceHostBindingState>(
  dependencies: <ProviderOrFamily>[
    interfaceSdkClientProvider,
    interfaceHostTargetProvider,
    interfaceControlNamespaceProvider,
  ],
  (ref) async {
    final client = ref.watch(interfaceSdkClientProvider);
    final target = ref.watch(interfaceHostTargetProvider);
    final namespace = await ref.watch(interfaceControlNamespaceProvider.future);
    final ping = await client.ping();
    return InterfaceHostBindingState.fromPing(
      target: target,
      namespace: namespace,
      ping: ping,
    );
  },
);

final interfaceHostConnectionProvider =
    FutureProvider<InterfaceHostConnectionState>(
  dependencies: <ProviderOrFamily>[interfaceHostBindingProvider],
  (ref) async {
    final binding = await ref.watch(interfaceHostBindingProvider.future);
    return binding.connection;
  },
);

class InterfaceHostDaemonController {
  Future<void> restart({String? endpoint, String? socketPath}) async {
    await restartInterfaceHostDaemon(
      endpoint: endpoint,
      socketPath: socketPath,
    );
  }
}

final interfaceHostDaemonControllerProvider =
    Provider<InterfaceHostDaemonController>((ref) {
  return InterfaceHostDaemonController();
});

final interfaceHostStateProvider =
    AsyncNotifierProvider<InterfaceHostStateNotifier, InterfaceHostState>(
  dependencies: <ProviderOrFamily>[
    interfaceSdkClientProvider,
    interfaceControlNamespaceProvider,
    interfaceEnvironmentEntryTargetProvider,
    interfaceHostBindingProvider,
    interfaceHostConnectionProvider,
    interfaceHostDaemonControllerProvider,
    interfaceHostStateFollowPollIntervalMsProvider,
    interfaceHostStateFollowReconnectDelayMsProvider,
  ],
  InterfaceHostStateNotifier.new,
);

class InterfaceHostStateNotifier extends AsyncNotifier<InterfaceHostState> {
  static const String _hostLabel = 'interface-flutter';
  static final Logger _logger = Logger('InterfaceHostStateNotifier');

  StreamSubscription<InterfaceHostState>? _followSubscription;
  Timer? _followReconnectTimer;
  bool _disposed = false;
  bool _namespaceRecoveryInFlight = false;

  InterfaceSdkClient get _client => ref.read(interfaceSdkClientProvider);

  Future<String> _namespace() async {
    return ref.read(interfaceControlNamespaceProvider.future);
  }

  @override
  Future<InterfaceHostState> build() async {
    ref.onDispose(() {
      _disposed = true;
      _followReconnectTimer?.cancel();
      _followReconnectTimer = null;
      unawaited(_followSubscription?.cancel());
      _followSubscription = null;
    });

    final namespace = await _namespace();
    final entryTarget = ref.watch(interfaceEnvironmentEntryTargetProvider);
    var hostState = await _ensureNamespace(namespace: namespace);
    if (entryTarget != null &&
        !_hostStateMatchesEnvironmentEntryTarget(hostState, entryTarget)) {
      hostState = await _enterEnvironmentTarget(
        namespace: namespace,
        target: entryTarget,
        fallback: hostState,
      );
    }
    await _startFollow(namespace: namespace);
    return hostState;
  }

  Future<InterfaceHostState> refresh() async {
    return _setStateFrom(() async {
      _invalidateHostBinding();
      final hostConnection = await ref.read(
        interfaceHostConnectionProvider.future,
      );
      if (hostConnection.blocksRuntimeEntry && state.valueOrNull != null) {
        return state.valueOrNull;
      }
      return _loadStatusWithNamespaceRecovery();
    });
  }

  Future<InterfaceHostState> restartInterfaceHost() async {
    return _setStateFrom(() async {
      final namespace = await _namespace();
      final endpoint = await _currentHostEndpoint();
      final socketPath = await _currentHostSocketPath();
      await _stopFollowing();
      await ref
          .read(interfaceHostDaemonControllerProvider)
          .restart(endpoint: endpoint, socketPath: socketPath);
      _invalidateHostBinding();
      await ref.read(interfaceHostConnectionProvider.future);
      final hostState = await _recoverNamespaceSnapshot(namespace: namespace);
      if (!_disposed) {
        await _startFollow(namespace: namespace);
      }
      return hostState;
    });
  }

  Future<InterfaceHostState> ensureLocalServiceHost() async {
    return _setStateFrom(
      () async => _withNamespaceRecovery(
        (namespace) async => (await _client.action(
          namespace: namespace,
          actionKey: 'ensure_local_service_host',
        ))
            .hostState,
      ),
    );
  }

  Future<InterfaceHostState> ensureLocalNodeRuntimeStarted() async {
    return _setStateFrom(
      () async => _withNamespaceRecovery(
        (namespace) async => (await _client.action(
          namespace: namespace,
          actionKey: 'ensure_local_node_runtime_started',
        ))
            .hostState,
      ),
    );
  }

  Future<InterfaceHostState> invokeAction({
    required String actionKey,
    String? paneRef,
    InterfaceActionTarget? actionTarget,
    Map<String, dynamic>? payload,
  }) async {
    return _setStateFrom(
      () async => _withNamespaceRecovery(
        (namespace) async => (await _client.action(
          namespace: namespace,
          paneRef: paneRef,
          actionKey: actionKey,
          actionTarget: actionTarget,
          payload: payload ?? const <String, dynamic>{},
        ))
            .hostState,
      ),
    );
  }

  Future<InterfaceHostState> activateRuntimeLayout({
    required String layoutConfigId,
  }) async {
    final normalizedLayoutConfigId = layoutConfigId.trim();
    if (normalizedLayoutConfigId.isEmpty) {
      throw ArgumentError.value(
        layoutConfigId,
        'layoutConfigId',
        'must be non-empty',
      );
    }
    return _setStateFrom(
      () async => _withNamespaceRecovery(
        (namespace) async => (await _client.selectRuntimeLayout(
          namespace: namespace,
          layoutConfigId: UuidValue.fromString(normalizedLayoutConfigId),
        ))
            .hostState,
      ),
    );
  }

  Future<InterfaceHostState> activateRuntimeFocus({
    UuidValue? representationId,
  }) async {
    return _setStateFrom(
      () async => _withNamespaceRecovery(
        (namespace) async => (await _client.activateRuntimeFocus(
          namespace: namespace,
          representationId: representationId,
        ))
            .hostState,
      ),
    );
  }

  Future<InterfaceHostState> applyAttentionLayoutTransition({
    required String clientIntentId,
    UuidValue? expectedPreviousLayoutTransitionId,
    UuidValue? topologyTransitionId,
    required List<InterfaceAttentionLayoutTransitionSectionIntent>
        sectionStates,
  }) async {
    return _setStateFrom(
      () async => _withNamespaceRecovery(
        (namespace) async => (await _client.applyAttentionLayoutTransition(
          namespace: namespace,
          clientIntentId: clientIntentId,
          expectedPreviousLayoutTransitionId:
              expectedPreviousLayoutTransitionId,
          topologyTransitionId: topologyTransitionId,
          sectionStates: sectionStates,
        ))
            .hostState,
      ),
    );
  }

  Future<InterfaceHostState> applyAttentionLayoutTopologyTransition({
    required String clientIntentId,
    UuidValue? expectedPreviousTopologyTransitionId,
    required List<InterfaceAttentionLayoutTopologyTransitionSectionIntent>
        sectionStates,
  }) async {
    return _setStateFrom(
      () async => _withNamespaceRecovery(
        (namespace) async =>
            (await _client.applyAttentionLayoutTopologyTransition(
          namespace: namespace,
          clientIntentId: clientIntentId,
          expectedPreviousTopologyTransitionId:
              expectedPreviousTopologyTransitionId,
          sectionStates: sectionStates,
        ))
                .hostState,
      ),
    );
  }

  Future<InterfaceHostState> enterEnvironment({
    UuidValue? environmentId,
    UuidValue? environmentProfileId,
    UuidValue? actorConfigId,
    UuidValue? classInstanceIdentityId,
    String objectInstanceGraphBranchKey = 'all',
    UuidValue? objectInstanceGraphBranchId,
    List<UuidValue> requestedRoleConfigIds = const <UuidValue>[],
    List<String> requestedRoleConfigNames = const <String>[],
    EnvironmentActorAdmissionReceipt? environmentAdmissionReceipt,
    UuidValue? environmentSessionId,
    UuidValue? environmentSessionConfigId,
    String? sessionKey,
    String? title,
    String? description,
    String? purpose,
    String? sourceKind,
    String? sourceRef,
    String? reason,
    Map<String, dynamic> evidence = const <String, dynamic>{},
  }) async {
    return _setStateFrom(
      () async => _withNamespaceRecovery(
        (namespace) async => (await _client.enterEnvironment(
          namespace: namespace,
          environmentId: environmentId,
          environmentProfileId: environmentProfileId,
          actorConfigId: actorConfigId,
          classInstanceIdentityId: classInstanceIdentityId,
          objectInstanceGraphBranchKey: objectInstanceGraphBranchKey,
          objectInstanceGraphBranchId: objectInstanceGraphBranchId,
          requestedRoleConfigIds: requestedRoleConfigIds,
          requestedRoleConfigNames: requestedRoleConfigNames,
          environmentAdmissionReceipt: environmentAdmissionReceipt,
          environmentSessionId: environmentSessionId,
          environmentSessionConfigId: environmentSessionConfigId,
          sessionKey: sessionKey,
          title: title,
          description: description,
          purpose: purpose,
          sourceKind: sourceKind,
          sourceRef: sourceRef,
          reason: reason,
          evidence: evidence,
        ))
            .hostState,
      ),
    );
  }

  Future<InterfaceHostState> enterAppScreen({
    required UuidValue appPackageId,
    required UuidValue appPackageBranchId,
    required UuidValue appPackageObjectInstanceGraphCommitId,
    required UuidValue appConfigScreenConfigId,
    String? reason,
    Map<String, dynamic> evidence = const <String, dynamic>{},
  }) async {
    return _setStateFrom(
      () async => _withNamespaceRecovery(
        (namespace) async => (await _client.enterAppScreen(
          namespace: namespace,
          appPackageId: appPackageId,
          appPackageBranchId: appPackageBranchId,
          appPackageObjectInstanceGraphCommitId:
              appPackageObjectInstanceGraphCommitId,
          appConfigScreenConfigId: appConfigScreenConfigId,
          reason: reason,
          evidence: evidence,
        ))
            .hostState,
      ),
    );
  }

  Future<InterfaceHostState> selectEnvironmentNavigationTarget({
    UuidValue? environmentNavigationContextId,
    UuidValue? selectedProcessId,
    UuidValue? selectedThreadId,
    String? reason,
    Map<String, dynamic> evidence = const <String, dynamic>{},
  }) async {
    return _setStateFrom(
      () async => _withNamespaceRecovery(
        (namespace) async => (await _client.selectEnvironmentNavigationTarget(
          namespace: namespace,
          environmentNavigationContextId: environmentNavigationContextId,
          selectedProcessId: selectedProcessId,
          selectedThreadId: selectedThreadId,
          reason: reason,
          evidence: evidence,
        ))
            .hostState,
      ),
    );
  }

  Future<InterfaceHostState> _enterEnvironmentTarget({
    required String namespace,
    required InterfaceEnvironmentEntryTarget target,
    required InterfaceHostState fallback,
  }) async {
    final response = await _client.enterEnvironment(
      namespace: namespace,
      environmentId: target.environmentId,
      environmentProfileId: target.environmentProfileId,
      actorConfigId: target.actorConfigId,
      classInstanceIdentityId: target.classInstanceIdentityId,
      objectInstanceGraphBranchKey: target.objectInstanceGraphBranchKey,
      objectInstanceGraphBranchId: target.objectInstanceGraphBranchId,
      requestedRoleConfigIds: target.requestedRoleConfigIds,
      requestedRoleConfigNames: target.requestedRoleConfigNames,
      environmentSessionId: target.environmentSessionId,
      environmentSessionConfigId: target.environmentSessionConfigId,
      sessionKey: target.sessionKey,
      title: target.title,
      description: target.description,
      purpose: target.purpose,
      sourceKind: target.sourceKind,
      sourceRef: target.sourceRef,
      reason: target.reason,
      evidence: target.evidence,
    );
    return response.hostState;
  }

  Future<InterfaceHostState> activateRuntimeRepresentation({
    required String representationId,
  }) async {
    final normalizedRepresentationId = representationId.trim();
    if (normalizedRepresentationId.isEmpty) {
      throw ArgumentError.value(
        representationId,
        'representationId',
        'Representation id must not be empty.',
      );
    }
    return activateRuntimeFocus(
      representationId: UuidValue.fromString(normalizedRepresentationId),
    );
  }

  Future<InterfaceHostState> tailLocalNodeRuntimeLogs({
    int lineCount = 50,
  }) async {
    return _setStateFrom(
      () async => _withNamespaceRecovery(
        (namespace) async => (await _client.action(
          namespace: namespace,
          actionKey: 'tail_local_node_runtime_logs',
          payload: <String, dynamic>{'line_count': lineCount},
        ))
            .hostState,
      ),
    );
  }

  Future<InterfaceHostState> selectStep({String? stepId}) async {
    return _setStateFrom(
      () async => _withNamespaceRecovery(
        (namespace) async => (await _client.selectStep(
          namespace: namespace,
          stepId: stepId,
        ))
            .hostState,
      ),
    );
  }

  Future<InterfaceHostState> _ensureNamespace({String? namespace}) async {
    return _setStateFrom(() async {
      final response = await _client.ensureNamespace(
        namespace: namespace ?? await _namespace(),
        hostLabel: _hostLabel,
      );
      _invalidateHostBinding();
      return response.hostState;
    });
  }

  Future<InterfaceHostState?> _withNamespaceRecovery(
    Future<InterfaceHostState?> Function(String namespace) load,
  ) async {
    final namespace = await _namespace();
    try {
      return await load(namespace);
    } on InterfaceSdkClientError catch (error) {
      if (!_isUnknownNamespaceError(error, namespace: namespace)) {
        rethrow;
      }
      _logger.info(
        'Recovering missing Interface namespace $namespace via ensureNamespace before retry.',
      );
      await _recoverNamespaceSnapshot(namespace: namespace);
      if (!_disposed) {
        await _startFollow(namespace: namespace);
      }
      return await load(namespace);
    }
  }

  Future<InterfaceHostState?> _loadStatusWithNamespaceRecovery() async {
    final namespace = await _namespace();
    if (_requiresNamespaceReensure(state.valueOrNull)) {
      _logger.info(
        'Re-ensuring degraded Interface namespace $namespace during refresh.',
      );
      final hostState = await _recoverNamespaceSnapshot(namespace: namespace);
      if (!_disposed) {
        await _startFollow(namespace: namespace);
      }
      return hostState;
    }
    try {
      return (await _client.status(namespace: namespace)).hostState;
    } on InterfaceSdkClientError catch (error) {
      if (!_isUnknownNamespaceError(error, namespace: namespace)) {
        rethrow;
      }
      _logger.info(
        'Recovering missing Interface namespace $namespace during refresh via ensureNamespace snapshot.',
      );
      final hostState = await _recoverNamespaceSnapshot(namespace: namespace);
      if (!_disposed) {
        await _startFollow(namespace: namespace);
      }
      return hostState;
    }
  }

  Future<InterfaceHostState?> _recoverNamespaceSnapshot({
    required String namespace,
  }) async {
    final response = await _client.ensureNamespace(
      namespace: namespace,
      hostLabel: _hostLabel,
    );
    _invalidateHostBinding();
    return response.hostState;
  }

  bool _isUnknownNamespaceError(
    InterfaceSdkClientError error, {
    required String namespace,
  }) {
    final message = _normalizeControlPlaneErrorMessage(error.error);
    return message == 'Unknown namespace: $namespace';
  }

  bool _requiresNamespaceReensure(InterfaceHostState? hostState) {
    if (hostState == null) {
      return false;
    }
    final warnings = hostState.warnings.toSet();
    return warnings.contains('transport_unbound') &&
        warnings.contains('runtime_unbound') &&
        warnings.contains('host_runtime_unbound');
  }

  String _normalizeControlPlaneErrorMessage(String? raw) {
    if (raw == null) {
      return '';
    }
    var normalized = raw.trim();
    while (normalized.length >= 2) {
      final wrappedInSingleQuotes =
          normalized.startsWith("'") && normalized.endsWith("'");
      final wrappedInDoubleQuotes =
          normalized.startsWith('"') && normalized.endsWith('"');
      if (!wrappedInSingleQuotes && !wrappedInDoubleQuotes) {
        break;
      }
      normalized = normalized.substring(1, normalized.length - 1).trim();
    }
    return normalized;
  }

  Future<String?> _currentHostEndpoint() async {
    try {
      final hostConnection = await ref.read(
        interfaceHostConnectionProvider.future,
      );
      final endpoint = hostConnection.defaultEndpoint?.trim();
      if (endpoint != null && endpoint.isNotEmpty) {
        return endpoint;
      }
    } catch (_) {}
    return null;
  }

  Future<String?> _currentHostSocketPath() async {
    try {
      final hostConnection = await ref.read(
        interfaceHostConnectionProvider.future,
      );
      final socketPath = hostConnection.socketPath?.trim();
      if (socketPath != null && socketPath.isNotEmpty) {
        return socketPath;
      }
    } catch (_) {}
    return null;
  }

  Future<bool> _hostBlocksWorkspaceEntry({bool refresh = false}) async {
    try {
      if (refresh) {
        _invalidateHostBinding();
      }
      final hostConnection = await ref.read(
        interfaceHostConnectionProvider.future,
      );
      return hostConnection.blocksRuntimeEntry;
    } catch (_) {
      return false;
    }
  }

  Future<InterfaceHostState> _setStateFrom(
    Future<InterfaceHostState?> Function() load,
  ) async {
    try {
      final hostState = await load();
      if (hostState == null) {
        throw StateError(
          'Interface daemon did not return a host state snapshot.',
        );
      }
      state = AsyncValue.data(hostState);
      return hostState;
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
      rethrow;
    }
  }

  Future<void> _stopFollowing() async {
    _followReconnectTimer?.cancel();
    _followReconnectTimer = null;
    await _followSubscription?.cancel();
    _followSubscription = null;
  }

  Future<void> _startFollow({required String namespace}) async {
    if (_disposed) {
      return;
    }
    if (await _hostBlocksWorkspaceEntry()) {
      await _stopFollowing();
      return;
    }
    _followReconnectTimer?.cancel();
    _followReconnectTimer = null;
    await _followSubscription?.cancel();
    _followSubscription = _client
        .follow(
      namespace: namespace,
      pollIntervalMs: ref.read(
        interfaceHostStateFollowPollIntervalMsProvider,
      ),
    )
        .listen(
      (hostState) {
        if (_disposed) {
          return;
        }
        state = AsyncValue.data(hostState);
      },
      onError: (Object error, StackTrace stackTrace) {
        if (_disposed) {
          return;
        }
        if (error is InterfaceSdkClientError &&
            _isUnknownNamespaceError(error, namespace: namespace)) {
          _logger.info(
            'Follow stream lost missing Interface namespace $namespace; re-ensuring and restarting.',
          );
          unawaited(
            _recoverNamespaceAndRestartFollow(namespace: namespace),
          );
          return;
        }
        if (!state.hasValue) {
          state = AsyncValue.error(error, stackTrace);
        }
        _scheduleFollowReconnect(namespace: namespace);
      },
      onDone: () {
        if (_disposed) {
          return;
        }
        _scheduleFollowReconnect(namespace: namespace);
      },
      cancelOnError: false,
    );
  }

  void _scheduleFollowReconnect({required String namespace}) {
    if (_disposed) {
      return;
    }
    _followReconnectTimer?.cancel();
    _followReconnectTimer = Timer(
      Duration(
        milliseconds: ref.read(
          interfaceHostStateFollowReconnectDelayMsProvider,
        ),
      ),
      () {
        if (_disposed) {
          return;
        }
        unawaited(_startFollow(namespace: namespace));
      },
    );
  }

  Future<void> _recoverNamespaceAndRestartFollow({
    required String namespace,
  }) async {
    if (_disposed || _namespaceRecoveryInFlight) {
      return;
    }
    if (await _hostBlocksWorkspaceEntry(refresh: true)) {
      await _stopFollowing();
      return;
    }
    _namespaceRecoveryInFlight = true;
    try {
      final hostState = await _recoverNamespaceSnapshot(namespace: namespace);
      if (_disposed) {
        return;
      }
      if (hostState != null) {
        state = AsyncValue.data(hostState);
      }
      await _startFollow(namespace: namespace);
    } catch (error, stackTrace) {
      if (_disposed) {
        return;
      }
      if (!state.hasValue) {
        state = AsyncValue.error(error, stackTrace);
      }
      _scheduleFollowReconnect(namespace: namespace);
    } finally {
      _namespaceRecoveryInFlight = false;
    }
  }

  void _invalidateHostBinding() {
    ref.invalidate(interfaceHostBindingProvider);
    ref.invalidate(interfaceHostConnectionProvider);
  }
}
