const String _controlPlaneUrlEnv = 'AWARE_INTERFACE_CONTROL_PLANE_URL';
const String _controlPlaneWsUrlEnv = 'AWARE_INTERFACE_CONTROL_PLANE_WS_URL';
const String _remoteHostEntryEnv = 'AWARE_INTERFACE_REMOTE_HOST_ENTRY';

enum InterfaceControlPlaneTargetKind { localSocket, remoteWebSocket }

enum InterfaceControlPlaneBootstrapSource {
  explicit,
  environment,
  compileTime,
  defaultLocal,
}

class InterfaceControlPlaneTarget {
  const InterfaceControlPlaneTarget._({
    required this.kind,
    required this.source,
    required this.remoteEntryRequested,
    this.controlPlaneUrl,
    this.controlPlaneUri,
    this.socketPath,
  });

  const InterfaceControlPlaneTarget.local({
    required String socketPath,
    required InterfaceControlPlaneBootstrapSource source,
  }) : this._(
         kind: InterfaceControlPlaneTargetKind.localSocket,
         source: source,
         remoteEntryRequested: false,
         socketPath: socketPath,
       );

  const InterfaceControlPlaneTarget.remote({
    required String controlPlaneUrl,
    required Uri controlPlaneUri,
    required InterfaceControlPlaneBootstrapSource source,
    bool remoteEntryRequested = true,
  }) : this._(
         kind: InterfaceControlPlaneTargetKind.remoteWebSocket,
         source: source,
         remoteEntryRequested: remoteEntryRequested,
         controlPlaneUrl: controlPlaneUrl,
         controlPlaneUri: controlPlaneUri,
       );

  final InterfaceControlPlaneTargetKind kind;
  final InterfaceControlPlaneBootstrapSource source;
  final bool remoteEntryRequested;
  final String? controlPlaneUrl;
  final Uri? controlPlaneUri;
  final String? socketPath;

  bool get isRemote => kind == InterfaceControlPlaneTargetKind.remoteWebSocket;

  String get sourceLabel => switch (source) {
    InterfaceControlPlaneBootstrapSource.explicit => 'explicit',
    InterfaceControlPlaneBootstrapSource.environment => 'environment',
    InterfaceControlPlaneBootstrapSource.compileTime => 'compile_time',
    InterfaceControlPlaneBootstrapSource.defaultLocal => 'default_local',
  };

  String get transportLabel => switch (kind) {
    InterfaceControlPlaneTargetKind.localSocket => 'local_socket',
    InterfaceControlPlaneTargetKind.remoteWebSocket => 'remote_websocket',
  };
}

String? _normalizeEnvValue(Map<String, String> environment, String key) {
  final raw = environment[key]?.trim();
  if (raw == null || raw.isEmpty) {
    return null;
  }
  return raw;
}

String findAwareRoot({
  Map<String, String>? environment,
  String? currentDirectory,
}) {
  throw UnsupportedError(
    'Aware repository root discovery is not available in browsers.',
  );
}

String resolveDefaultStateHome({
  Map<String, String>? environment,
  String? currentDirectory,
}) {
  throw UnsupportedError(
    'Local Interface state-home resolution is not available in browsers.',
  );
}

String resolveControlSocketPath({
  String? socketPath,
  String? stateHome,
  Map<String, String>? environment,
  String? currentDirectory,
}) {
  throw UnsupportedError(
    'Local Interface control-plane sockets are not available in browsers.',
  );
}

({String url, InterfaceControlPlaneBootstrapSource source})?
_resolveRemoteControlPlaneUrlWithSource({
  String? controlPlaneUrl,
  Map<String, String>? environment,
}) {
  final explicit = controlPlaneUrl?.trim();
  if (explicit != null && explicit.isNotEmpty) {
    return (
      url: explicit,
      source: InterfaceControlPlaneBootstrapSource.explicit,
    );
  }

  final effectiveEnvironment = environment ?? const <String, String>{};
  for (final key in <String>[_controlPlaneUrlEnv, _controlPlaneWsUrlEnv]) {
    final override = _normalizeEnvValue(effectiveEnvironment, key);
    if (override != null) {
      return (
        url: override,
        source: InterfaceControlPlaneBootstrapSource.environment,
      );
    }
  }

  const compileTimeUrl = String.fromEnvironment(_controlPlaneUrlEnv);
  final normalizedCompileTimeUrl = compileTimeUrl.trim();
  if (normalizedCompileTimeUrl.isNotEmpty) {
    return (
      url: normalizedCompileTimeUrl,
      source: InterfaceControlPlaneBootstrapSource.compileTime,
    );
  }

  const compileTimeWsUrl = String.fromEnvironment(_controlPlaneWsUrlEnv);
  final normalizedCompileTimeWsUrl = compileTimeWsUrl.trim();
  if (normalizedCompileTimeWsUrl.isNotEmpty) {
    return (
      url: normalizedCompileTimeWsUrl,
      source: InterfaceControlPlaneBootstrapSource.compileTime,
    );
  }

  return null;
}

String? resolveControlPlaneUrl({
  String? controlPlaneUrl,
  Map<String, String>? environment,
}) {
  return _resolveRemoteControlPlaneUrlWithSource(
    controlPlaneUrl: controlPlaneUrl,
    environment: environment,
  )?.url;
}

Uri? resolveControlPlaneWebSocketUri({
  String? controlPlaneUrl,
  Map<String, String>? environment,
}) {
  final raw = resolveControlPlaneUrl(
    controlPlaneUrl: controlPlaneUrl,
    environment: environment,
  );
  if (raw == null) {
    return null;
  }
  return normalizeControlPlaneWebSocketUri(raw);
}

Uri normalizeControlPlaneWebSocketUri(String raw) {
  final normalized = raw.trim();
  if (normalized.isEmpty) {
    throw StateError('Interface control-plane URL cannot be empty.');
  }

  final candidate = normalized.contains('://')
      ? normalized
      : 'wss://$normalized';
  final parsed = Uri.parse(candidate);
  final scheme = parsed.scheme.toLowerCase();
  return switch (scheme) {
    'ws' || 'wss' => parsed,
    'http' => parsed.replace(scheme: 'ws'),
    'https' => parsed.replace(scheme: 'wss'),
    _ => throw StateError(
      'Unsupported Interface control-plane URL scheme `$scheme`.',
    ),
  };
}

InterfaceControlPlaneTarget resolveInterfaceControlPlaneTarget({
  String? socketPath,
  String? stateHome,
  String? controlPlaneUrl,
  Map<String, String>? environment,
  String? currentDirectory,
}) {
  final remoteBootstrap = _resolveRemoteControlPlaneUrlWithSource(
    controlPlaneUrl: controlPlaneUrl,
    environment: environment,
  );
  if (remoteBootstrap != null) {
    return InterfaceControlPlaneTarget.remote(
      controlPlaneUrl: remoteBootstrap.url,
      controlPlaneUri: normalizeControlPlaneWebSocketUri(remoteBootstrap.url),
      source: remoteBootstrap.source,
    );
  }

  throw UnsupportedError(
    'Browser Interface entry requires a remote Interface control-plane URL.',
  );
}

bool resolveRemoteInterfaceHostEntryEnabled({
  Map<String, String>? environment,
}) {
  final effectiveEnvironment = environment ?? const <String, String>{};
  final override = _normalizeEnvValue(
    effectiveEnvironment,
    _remoteHostEntryEnv,
  );
  if (override != null) {
    return _parseBoolFlag(override);
  }

  const compileTimeValue = String.fromEnvironment(_remoteHostEntryEnv);
  final normalizedCompileTimeValue = compileTimeValue.trim();
  if (normalizedCompileTimeValue.isNotEmpty) {
    return _parseBoolFlag(normalizedCompileTimeValue);
  }

  return resolveControlPlaneUrl(environment: effectiveEnvironment) != null;
}

bool _parseBoolFlag(String raw) {
  return switch (raw.trim().toLowerCase()) {
    '1' || 'true' || 'yes' || 'on' => true,
    _ => false,
  };
}
