import 'dart:io';

import 'path_resolution.dart';

typedef InterfaceDaemonCommandRunner =
    Future<ProcessResult> Function(
      String executable,
      List<String> arguments, {
      String? workingDirectory,
      Map<String, String>? environment,
      bool runInShell,
    });

const double defaultInterfaceDaemonRestartWaitTimeoutS = 30.0;

const Set<String> _daemonCommandPassthroughEnvKeys = <String>{
  'HOME',
  'PATH',
  'LANG',
  'LC_ALL',
  'LC_CTYPE',
  'LC_MESSAGES',
  'LOGNAME',
  'USER',
  'SHELL',
  'TMPDIR',
  'TEMP',
  'TMP',
  'XDG_RUNTIME_DIR',
};

class InterfaceDaemonCommandError implements Exception {
  InterfaceDaemonCommandError({
    required this.executable,
    required this.arguments,
    required this.exitCode,
    required this.stdout,
    required this.stderr,
  });

  final String executable;
  final List<String> arguments;
  final int exitCode;
  final String stdout;
  final String stderr;

  @override
  String toString() {
    final command = ([executable, ...arguments]).join(' ');
    final detail = stderr.trim().isNotEmpty ? stderr.trim() : stdout.trim();
    if (detail.isEmpty) {
      return 'Interface daemon command failed (exit=$exitCode): $command';
    }
    return 'Interface daemon command failed (exit=$exitCode): $command\n$detail';
  }
}

class InterfaceDaemonRestartResult {
  const InterfaceDaemonRestartResult({
    required this.stateHome,
    required this.repositoryRoot,
    required this.endpoint,
    required this.stdout,
    required this.stderr,
  });

  final String stateHome;
  final String repositoryRoot;
  final String? endpoint;
  final String stdout;
  final String stderr;
}

Future<ProcessResult> _defaultCommandRunner(
  String executable,
  List<String> arguments, {
  String? workingDirectory,
  Map<String, String>? environment,
  bool runInShell = false,
}) {
  return Process.run(
    executable,
    arguments,
    workingDirectory: workingDirectory,
    environment: environment,
    runInShell: runInShell,
  );
}

String _resolveUvExecutable() {
  return Platform.isWindows ? 'uv.exe' : 'uv';
}

Map<String, String> _buildDaemonCommandEnvironment({
  required Map<String, String> sourceEnvironment,
  required String resolvedRepositoryRoot,
  required String resolvedStateHome,
  String? endpoint,
  String? socketPath,
}) {
  final sanitized = <String, String>{};
  for (final entry in sourceEnvironment.entries) {
    if (_daemonCommandPassthroughEnvKeys.contains(entry.key) ||
        entry.key.startsWith('AWARE_')) {
      sanitized[entry.key] = entry.value;
    }
  }

  sanitized['AWARE_HOME'] = resolvedRepositoryRoot;
  sanitized['AWARE_REPO_ROOT'] = resolvedRepositoryRoot;
  sanitized['AWARE_ROOT'] = resolvedRepositoryRoot;
  sanitized['AWARE_STATE_HOME'] = resolvedStateHome;
  sanitized['AWARE_INTERFACE_SERVICE_STATE_HOME'] = resolvedStateHome;

  if (socketPath != null && socketPath.trim().isNotEmpty) {
    sanitized['AWARE_INTERFACE_CONTROL_SOCKET'] = socketPath.trim();
  } else {
    sanitized.remove('AWARE_INTERFACE_CONTROL_SOCKET');
  }

  if (endpoint != null && endpoint.trim().isNotEmpty) {
    sanitized['AWARE_INTERFACE_SERVICE_ENDPOINT'] = endpoint.trim();
  } else {
    sanitized.remove('AWARE_INTERFACE_SERVICE_ENDPOINT');
  }

  return sanitized;
}

Future<InterfaceDaemonRestartResult> restartInterfaceDaemon({
  String? socketPath,
  String? stateHome,
  String? repositoryRoot,
  String? endpoint,
  double waitTimeoutS = defaultInterfaceDaemonRestartWaitTimeoutS,
  Map<String, String>? environment,
  String? currentDirectory,
  InterfaceDaemonCommandRunner commandRunner = _defaultCommandRunner,
}) async {
  final effectiveEnvironment = environment ?? Platform.environment;
  final normalizedSocketPath = socketPath?.trim();
  final derivedStateHome =
      normalizedSocketPath != null && normalizedSocketPath.isNotEmpty
      ? File(normalizedSocketPath).absolute.parent.path
      : null;
  final resolvedStateHome = stateHome?.trim().isNotEmpty == true
      ? stateHome!.trim()
      : derivedStateHome != null && derivedStateHome.isNotEmpty
      ? derivedStateHome
      : resolveDefaultStateHome(
          environment: effectiveEnvironment,
          currentDirectory: currentDirectory,
        );
  final resolvedRepositoryRoot = repositoryRoot?.trim().isNotEmpty == true
      ? repositoryRoot!.trim()
      : findAwareRoot(
          environment: effectiveEnvironment,
          currentDirectory: currentDirectory,
        );
  final arguments = <String>[
    'run',
    'aware-cli',
    'interface',
    '--state-home',
    resolvedStateHome,
    'daemon',
    'restart',
    '--daemon-repository-root',
    resolvedRepositoryRoot,
    '--wait-timeout-s',
    waitTimeoutS.toString(),
  ];
  if (endpoint != null && endpoint.trim().isNotEmpty) {
    arguments.addAll(<String>['--endpoint', endpoint.trim()]);
  }
  final commandEnvironment = _buildDaemonCommandEnvironment(
    sourceEnvironment: effectiveEnvironment,
    resolvedRepositoryRoot: resolvedRepositoryRoot,
    resolvedStateHome: resolvedStateHome,
    endpoint: endpoint,
    socketPath: normalizedSocketPath,
  );

  final result = await commandRunner(
    _resolveUvExecutable(),
    arguments,
    workingDirectory: resolvedRepositoryRoot,
    environment: commandEnvironment,
    runInShell: false,
  );
  if (result.exitCode != 0) {
    throw InterfaceDaemonCommandError(
      executable: _resolveUvExecutable(),
      arguments: arguments,
      exitCode: result.exitCode,
      stdout: '${result.stdout}',
      stderr: '${result.stderr}',
    );
  }

  return InterfaceDaemonRestartResult(
    stateHome: resolvedStateHome,
    repositoryRoot: resolvedRepositoryRoot,
    endpoint: endpoint?.trim().isNotEmpty == true ? endpoint!.trim() : null,
    stdout: '${result.stdout}',
    stderr: '${result.stderr}',
  );
}
