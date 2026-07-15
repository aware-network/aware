import 'dart:io';

import 'package:path/path.dart' as p;

const String _defaultStateHomeDir = '.aware/interface_service';
const String _defaultControlSocketFilename = 'interface-control.sock';
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
  final effectiveEnvironment = environment ?? Platform.environment;
  for (final key in <String>['AWARE_HOME', 'AWARE_ROOT', 'AWARE_REPO_ROOT']) {
    final override = _normalizeEnvValue(effectiveEnvironment, key);
    if (override == null) {
      continue;
    }
    final resolved = Directory(override).absolute.path;
    if (_isAwareRoot(resolved)) {
      return resolved;
    }
  }

  var current = Directory(currentDirectory ?? Directory.current.path).absolute;
  while (true) {
    if (_isAwareRoot(current.path)) {
      return current.path;
    }
    if (current.parent.path == current.path) {
      break;
    }
    current = current.parent;
  }

  throw StateError('Unable to resolve the Aware repository root.');
}

bool _isAwareRoot(String directoryPath) {
  final awareDir = Directory(p.join(directoryPath, '.aware'));
  if (awareDir.existsSync()) {
    return true;
  }

  final pyproject = File(p.join(directoryPath, 'pyproject.toml'));
  if (!pyproject.existsSync()) {
    return false;
  }

  try {
    final content = pyproject.readAsStringSync();
    if (!content.contains('name = "aware"')) {
      return false;
    }
  } catch (_) {
    return false;
  }

  return Directory(p.join(directoryPath, 'libs')).existsSync() &&
      Directory(p.join(directoryPath, 'apps')).existsSync() &&
      Directory(p.join(directoryPath, 'docs')).existsSync();
}

String resolveDefaultStateHome({
  Map<String, String>? environment,
  String? currentDirectory,
}) {
  final effectiveEnvironment = environment ?? Platform.environment;
  final interfaceOverride = _normalizeEnvValue(
    effectiveEnvironment,
    'AWARE_INTERFACE_SERVICE_STATE_HOME',
  );
  if (interfaceOverride != null) {
    return p.normalize(p.absolute(interfaceOverride));
  }

  final sharedStateHome = _normalizeEnvValue(
    effectiveEnvironment,
    'AWARE_STATE_HOME',
  );
  if (sharedStateHome != null) {
    return p.normalize(p.absolute(sharedStateHome));
  }

  return p.join(
    findAwareRoot(
      environment: effectiveEnvironment,
      currentDirectory: currentDirectory,
    ),
    _defaultStateHomeDir,
  );
}

String resolveControlSocketPath({
  String? socketPath,
  String? stateHome,
  Map<String, String>? environment,
  String? currentDirectory,
}) {
  if (socketPath != null && socketPath.trim().isNotEmpty) {
    return p.normalize(p.absolute(socketPath.trim()));
  }

  final effectiveEnvironment = environment ?? Platform.environment;
  final socketOverride = _normalizeEnvValue(
    effectiveEnvironment,
    'AWARE_INTERFACE_CONTROL_SOCKET',
  );
  if (socketOverride != null) {
    return p.normalize(p.absolute(socketOverride));
  }

  final effectiveStateHome = stateHome?.trim().isNotEmpty == true
      ? p.normalize(p.absolute(stateHome!.trim()))
      : resolveDefaultStateHome(
          environment: effectiveEnvironment,
          currentDirectory: currentDirectory,
        );
  return p.join(effectiveStateHome, _defaultControlSocketFilename);
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

  final effectiveEnvironment = environment ?? Platform.environment;
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
      : 'ws://$normalized';
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

  final effectiveEnvironment = environment ?? Platform.environment;
  final explicitSocketPath = socketPath?.trim();
  if (explicitSocketPath != null && explicitSocketPath.isNotEmpty) {
    return InterfaceControlPlaneTarget.local(
      socketPath: p.normalize(p.absolute(explicitSocketPath)),
      source: InterfaceControlPlaneBootstrapSource.explicit,
    );
  }

  final socketOverride = _normalizeEnvValue(
    effectiveEnvironment,
    'AWARE_INTERFACE_CONTROL_SOCKET',
  );
  if (socketOverride != null) {
    return InterfaceControlPlaneTarget.local(
      socketPath: p.normalize(p.absolute(socketOverride)),
      source: InterfaceControlPlaneBootstrapSource.environment,
    );
  }

  return InterfaceControlPlaneTarget.local(
    socketPath: resolveControlSocketPath(
      stateHome: stateHome,
      environment: effectiveEnvironment,
      currentDirectory: currentDirectory,
    ),
    source: InterfaceControlPlaneBootstrapSource.defaultLocal,
  );
}

bool resolveRemoteInterfaceHostEntryEnabled({
  Map<String, String>? environment,
}) {
  final effectiveEnvironment = environment ?? Platform.environment;
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

  return false;
}

bool _parseBoolFlag(String raw) {
  return switch (raw.trim().toLowerCase()) {
    '1' || 'true' || 'yes' || 'on' => true,
    _ => false,
  };
}
