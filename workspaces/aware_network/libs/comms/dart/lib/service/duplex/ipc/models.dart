enum DuplexIpcTransportKind {
  stdio,
  unixSocket,
}

String _transportKindToWire(DuplexIpcTransportKind transport) {
  return switch (transport) {
    DuplexIpcTransportKind.stdio => 'stdio',
    DuplexIpcTransportKind.unixSocket => 'unix_socket',
  };
}

DuplexIpcTransportKind _transportKindFromWire(String value) {
  return switch (value) {
    'stdio' => DuplexIpcTransportKind.stdio,
    'unix_socket' => DuplexIpcTransportKind.unixSocket,
    _ => throw ArgumentError.value(
        value,
        'value',
        'Unsupported IPC transport kind',
      ),
  };
}

class DuplexIpcEndpoint {
  const DuplexIpcEndpoint._({
    required this.transport,
    required this.command,
    required this.socketPath,
    required this.workingDirectory,
    required this.environment,
  });

  factory DuplexIpcEndpoint.stdio({
    required List<String> command,
    String? workingDirectory,
    Map<String, String> environment = const <String, String>{},
  }) {
    if (command.isEmpty) {
      throw ArgumentError.value(
        command,
        'command',
        'stdio IPC endpoints require at least one command item',
      );
    }
    return DuplexIpcEndpoint._(
      transport: DuplexIpcTransportKind.stdio,
      command: List<String>.unmodifiable(command),
      socketPath: null,
      workingDirectory: workingDirectory,
      environment: Map<String, String>.unmodifiable(environment),
    );
  }

  factory DuplexIpcEndpoint.unixSocket({
    required String socketPath,
  }) {
    if (socketPath.isEmpty) {
      throw ArgumentError.value(
        socketPath,
        'socketPath',
        'unixSocket IPC endpoints require socketPath',
      );
    }
    return DuplexIpcEndpoint._(
      transport: DuplexIpcTransportKind.unixSocket,
      command: const <String>[],
      socketPath: socketPath,
      workingDirectory: null,
      environment: const <String, String>{},
    );
  }

  factory DuplexIpcEndpoint.fromJson(Map<String, dynamic> json) {
    final transport = _transportKindFromWire(json['transport'] as String);
    return switch (transport) {
      DuplexIpcTransportKind.stdio => DuplexIpcEndpoint.stdio(
          command: List<String>.from(json['command'] as List<dynamic>),
          workingDirectory: json['working_directory'] as String?,
          environment: Map<String, String>.from(
            (json['environment'] as Map<dynamic, dynamic>? ??
                    const <dynamic, dynamic>{})
                .map(
              (key, value) => MapEntry(
                key.toString(),
                value.toString(),
              ),
            ),
          ),
        ),
      DuplexIpcTransportKind.unixSocket => DuplexIpcEndpoint.unixSocket(
          socketPath: json['socket_path'] as String,
        ),
    };
  }

  final DuplexIpcTransportKind transport;
  final List<String> command;
  final String? socketPath;
  final String? workingDirectory;
  final Map<String, String> environment;

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'transport': _transportKindToWire(transport),
      'command': command,
      'socket_path': socketPath,
      'working_directory': workingDirectory,
      'environment': environment,
    };
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        other is DuplexIpcEndpoint &&
            runtimeType == other.runtimeType &&
            transport == other.transport &&
            _listEquals(command, other.command) &&
            socketPath == other.socketPath &&
            workingDirectory == other.workingDirectory &&
            _mapEquals(environment, other.environment);
  }

  @override
  int get hashCode => Object.hash(
        transport,
        Object.hashAll(command),
        socketPath,
        workingDirectory,
        Object.hashAll(
          environment.entries
              .map((entry) => Object.hash(entry.key, entry.value)),
        ),
      );
}

bool _listEquals<T>(List<T> a, List<T> b) {
  if (identical(a, b)) {
    return true;
  }
  if (a.length != b.length) {
    return false;
  }
  for (var index = 0; index < a.length; index += 1) {
    if (a[index] != b[index]) {
      return false;
    }
  }
  return true;
}

bool _mapEquals<K, V>(Map<K, V> a, Map<K, V> b) {
  if (identical(a, b)) {
    return true;
  }
  if (a.length != b.length) {
    return false;
  }
  for (final entry in a.entries) {
    if (b[entry.key] != entry.value) {
      return false;
    }
  }
  return true;
}
