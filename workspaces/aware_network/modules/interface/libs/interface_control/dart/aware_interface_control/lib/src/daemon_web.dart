typedef InterfaceDaemonCommandRunner =
    Future<Object?> Function(
      String executable,
      List<String> arguments, {
      String? workingDirectory,
      Map<String, String>? environment,
      bool runInShell,
    });

const double defaultInterfaceDaemonRestartWaitTimeoutS = 30.0;

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

Future<InterfaceDaemonRestartResult> restartInterfaceDaemon({
  String? socketPath,
  String? stateHome,
  String? repositoryRoot,
  String? endpoint,
  double waitTimeoutS = defaultInterfaceDaemonRestartWaitTimeoutS,
  Map<String, String>? environment,
  String? currentDirectory,
  InterfaceDaemonCommandRunner? commandRunner,
}) async {
  throw UnsupportedError(
    'Interface daemon restart is a local host operation and is not available '
    'from browser renderers.',
  );
}
