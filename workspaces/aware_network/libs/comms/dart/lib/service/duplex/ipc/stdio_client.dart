import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:aware_comms/service/duplex/ipc/client.dart';
import 'package:aware_comms/service/duplex/ipc/codec.dart';
import 'package:aware_comms/service/duplex/ipc/models.dart';
import 'package:aware_comms/service/duplex/protocol/models.dart';

class StdioDuplexIpcClient implements DuplexIpcClient {
  StdioDuplexIpcClient({
    required DuplexIpcEndpoint endpoint,
    DuplexIpcFrameCodec codec = const DuplexIpcFrameCodec(),
  })  : _endpoint = endpoint,
        _codec = codec {
    if (_endpoint.transport != DuplexIpcTransportKind.stdio) {
      throw ArgumentError.value(
        endpoint.transport,
        'endpoint.transport',
        'StdioDuplexIpcClient requires a stdio endpoint',
      );
    }
  }

  final DuplexIpcEndpoint _endpoint;
  final DuplexIpcFrameCodec _codec;

  Process? _process;
  StreamIterator<String>? _stdoutLines;
  Future<void>? _stderrDrain;

  Future<void> start() async {
    if (_process != null) {
      return;
    }
    final process = await Process.start(
      _endpoint.command.first,
      _endpoint.command.skip(1).toList(),
      workingDirectory: _endpoint.workingDirectory,
      environment: _endpoint.environment.isEmpty ? null : _endpoint.environment,
      runInShell: false,
    );
    _process = process;
    _stdoutLines = StreamIterator<String>(
      process.stdout.transform(utf8.decoder).transform(const LineSplitter()),
    );
    _stderrDrain = process.stderr.drain<void>();
  }

  Future<void> sendFrame(DuplexMessageFrame frame) async {
    await start();
    final process = _requireProcess();
    process.stdin.write(_codec.encodeFrame(frame));
    await process.stdin.flush();
  }

  @override
  Future<DuplexMessageFrame> readFrame({
    Duration timeout = const Duration(seconds: 5),
  }) async {
    await start();
    final stdoutLines = _requireStdoutLines();
    final hasLine = await stdoutLines.moveNext().timeout(timeout);
    if (!hasLine) {
      throw StateError('stdio IPC process closed stdout');
    }
    return _codec.decodeFrame(stdoutLines.current);
  }

  @override
  Future<DuplexMessageFrame> sendAndReceive(
    DuplexMessageFrame frame, {
    Duration timeout = const Duration(seconds: 5),
  }) async {
    await sendFrame(frame);
    return readFrame(timeout: timeout);
  }

  @override
  Future<void> close() async {
    final process = _process;
    if (process == null) {
      return;
    }

    await process.stdin.close();
    if (process.kill()) {
      await process.exitCode;
    } else {
      await process.exitCode;
    }
    if (_stderrDrain != null) {
      await _stderrDrain;
    }

    _stderrDrain = null;
    _stdoutLines = null;
    _process = null;
  }

  Process _requireProcess() {
    final process = _process;
    if (process == null) {
      throw StateError('stdio IPC process is not started');
    }
    return process;
  }

  StreamIterator<String> _requireStdoutLines() {
    final stdoutLines = _stdoutLines;
    if (stdoutLines == null) {
      throw StateError('stdio IPC stdout iterator is not started');
    }
    return stdoutLines;
  }
}
