import 'package:aware_messaging/aware_messaging.dart';
import 'package:test/test.dart';

class _PingCommand extends Command<String> {
  final String value;

  const _PingCommand(this.value);
}

class _RecordingMiddleware extends CommandMiddleware {
  final List<String> calls;

  _RecordingMiddleware(this.calls);

  @override
  Future<bool> before(Command command) async {
    calls.add('before:${command.commandType}');
    return true;
  }

  @override
  Future<void> after(Command command, CommandResult result) async {
    calls.add('after:${command.commandType}:${result.isSuccess}');
  }
}

void main() {
  group('CommandBus', () {
    test('executes registered handler and returns success', () async {
      final bus = CommandBus();
      bus.register<_PingCommand, String>((command) async {
        return CommandSuccess('echo:${command.value}');
      });

      final result = await bus.execute<_PingCommand, String>(
        const _PingCommand('hello'),
      );

      expect(result.isSuccess, isTrue);
      expect(
        result.when(success: (value) => value, error: (_, __) => null),
        'echo:hello',
      );
    });

    test('runs middleware before and after handler', () async {
      final calls = <String>[];
      final middleware = _RecordingMiddleware(calls);

      final bus = CommandBus()
        ..addMiddleware(middleware)
        ..register<_PingCommand, String>((command) async {
          calls.add('handler:${command.value}');
          return const CommandSuccess('ok');
        });

      await bus(const _PingCommand('payload'));

      expect(calls, [
        'before:_PingCommand',
        'handler:payload',
        'after:_PingCommand:true',
      ]);
    });

    test('returns error when handler throws', () async {
      final bus = CommandBus()
        ..register<_PingCommand, String>((_) async {
          throw StateError('boom');
        });

      final result = await bus(const _PingCommand('x'));

      expect(result.isError, isTrue);
      final message = result.when(
        success: (_) => 'ok',
        error: (msg, details) => '$msg|$details',
      );
      expect(message, contains('Unhandled error executing _PingCommand'));
    });
  });
}
