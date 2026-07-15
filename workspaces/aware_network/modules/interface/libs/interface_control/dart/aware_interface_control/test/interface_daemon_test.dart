import 'dart:io';

import 'package:aware_interface_control/aware_interface_control.dart';
import 'package:test/test.dart';

void main() {
  test(
    'restartInterfaceDaemon invokes aware-cli daemon restart with state-home',
    () async {
      late String executable;
      late List<String> arguments;
      late String? capturedWorkingDirectory;
      late Map<String, String>? capturedEnvironment;

      final result = await restartInterfaceDaemon(
        stateHome: '/tmp/aware-interface-state',
        repositoryRoot: '/home/luis/aware',
        endpoint: 'ws://localhost:8000',
        environment: <String, String>{
          'PATH': '/usr/bin',
          'HOME': '/home/luis',
          'LANG': 'en_US.UTF-8',
          'AWARE_HOME': '/tmp/old-aware-home',
          'LD_LIBRARY_PATH': '/tmp/flutter-libs',
          'PYTHONPATH': '/tmp/pythonpath',
        },
        waitTimeoutS: 30,
        commandRunner:
            (
              String nextExecutable,
              List<String> nextArguments, {
              String? workingDirectory,
              Map<String, String>? environment,
              bool runInShell = false,
            }) async {
              executable = nextExecutable;
              arguments = List<String>.from(nextArguments);
              capturedWorkingDirectory = workingDirectory;
              capturedEnvironment = environment == null
                  ? null
                  : Map<String, String>.from(environment);
              return ProcessResult(1, 0, '{"status":"ok"}', '');
            },
      );

      expect(executable, Platform.isWindows ? 'uv.exe' : 'uv');
      expect(arguments, <String>[
        'run',
        'aware-cli',
        'interface',
        '--state-home',
        '/tmp/aware-interface-state',
        'daemon',
        'restart',
        '--daemon-repository-root',
        '/home/luis/aware',
        '--wait-timeout-s',
        '30.0',
        '--endpoint',
        'ws://localhost:8000',
      ]);
      expect(capturedWorkingDirectory, '/home/luis/aware');
      expect(capturedEnvironment?['PATH'], '/usr/bin');
      expect(capturedEnvironment?['HOME'], '/home/luis');
      expect(capturedEnvironment?['LANG'], 'en_US.UTF-8');
      expect(capturedEnvironment?['AWARE_HOME'], '/home/luis/aware');
      expect(capturedEnvironment?['AWARE_REPO_ROOT'], '/home/luis/aware');
      expect(capturedEnvironment?['AWARE_ROOT'], '/home/luis/aware');
      expect(
        capturedEnvironment?['AWARE_INTERFACE_SERVICE_STATE_HOME'],
        '/tmp/aware-interface-state',
      );
      expect(
        capturedEnvironment?['AWARE_INTERFACE_SERVICE_ENDPOINT'],
        'ws://localhost:8000',
      );
      expect(capturedEnvironment, isNot(contains('LD_LIBRARY_PATH')));
      expect(capturedEnvironment, isNot(contains('PYTHONPATH')));
      expect(result.stateHome, '/tmp/aware-interface-state');
    },
  );

  test('restartInterfaceDaemon derives state-home from socket path', () async {
    late List<String> arguments;

    final result = await restartInterfaceDaemon(
      socketPath: '/tmp/aware-interface-state/interface-control.sock',
      repositoryRoot: '/home/luis/aware',
      commandRunner:
          (
            String executable,
            List<String> nextArguments, {
            String? workingDirectory,
            Map<String, String>? environment,
            bool runInShell = false,
          }) async {
            arguments = List<String>.from(nextArguments);
            return ProcessResult(1, 0, '{"status":"ok"}', '');
          },
    );

    expect(
      arguments,
      containsAllInOrder(<String>[
        '--state-home',
        '/tmp/aware-interface-state',
        '--wait-timeout-s',
        '30.0',
      ]),
    );
    expect(result.stateHome, '/tmp/aware-interface-state');
  });

  test('restartInterfaceDaemon throws when the command fails', () async {
    expect(
      () => restartInterfaceDaemon(
        stateHome: '/tmp/aware-interface-state',
        repositoryRoot: '/home/luis/aware',
        commandRunner:
            (
              String executable,
              List<String> arguments, {
              String? workingDirectory,
              Map<String, String>? environment,
              bool runInShell = false,
            }) async {
              return ProcessResult(1, 2, '', 'restart failed');
            },
      ),
      throwsA(isA<InterfaceDaemonCommandError>()),
    );
  });
}
