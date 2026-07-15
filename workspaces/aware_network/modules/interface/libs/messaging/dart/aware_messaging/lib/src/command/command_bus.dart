import 'dart:async';

import 'command.dart';
import 'command_result.dart';

/// Middleware contract for command execution.
abstract class CommandMiddleware {
  /// Invoked before the command handler executes.
  /// Return `false` to prevent execution.
  Future<bool> before(Command command) async => true;

  /// Invoked after the command handler completes (success or error).
  Future<void> after(Command command, CommandResult<dynamic> result) async {}
}

/// Core command bus responsible for dispatching commands to single handlers.
typedef _UntypedHandler =
    Future<CommandResult<dynamic>> Function(Command<dynamic> command);

class CommandBus {
  final Map<Type, _UntypedHandler> _handlers = {};
  final List<CommandMiddleware> _middleware = [];

  /// Registers a handler for the provided command type.
  void register<C extends Command<R>, R>(CommandHandler<C, R> handler) {
    if (_handlers.containsKey(C)) {
      throw StateError('Handler already registered for command type $C');
    }
    _handlers[C] = (command) => handler(command as C);
  }

  /// Removes a previously registered handler.
  void unregister<C extends Command<Object?>>() {
    _handlers.remove(C);
  }

  /// Executes the command using its registered handler.
  Future<CommandResult<R>> execute<C extends Command<R>, R>(C command) async {
    final handler = _handlers[C];
    if (handler == null) {
      return CommandError<R>(
        message: 'No handler registered for ${command.commandType}',
      );
    }

    for (final middleware in _middleware) {
      final shouldContinue = await middleware.before(command);
      if (!shouldContinue) {
        return CommandError<R>(
          message: 'Execution blocked by middleware for ${command.commandType}',
        );
      }
    }

    CommandResult<R> result;
    try {
      final untyped = await handler(command);
      result = untyped as CommandResult<R>;
    } catch (error, stackTrace) {
      result = CommandError<R>(
        message: 'Unhandled error executing ${command.commandType}',
        details: error.toString(),
        cause: error,
        stackTrace: stackTrace,
      );
    }

    for (final middleware in _middleware.reversed) {
      await middleware.after(command, result);
    }
    return result;
  }

  /// Adds middleware to the execution pipeline.
  void addMiddleware(CommandMiddleware middleware) {
    _middleware.add(middleware);
  }

  /// Removes middleware from the execution pipeline.
  void removeMiddleware(CommandMiddleware middleware) {
    _middleware.remove(middleware);
  }

  /// Returns `true` if a handler is registered for the command type.
  bool hasHandler<C extends Command<Object?>>() => _handlers.containsKey(C);

  /// Number of registered handlers.
  int get handlerCount => _handlers.length;

  /// Clears registered handlers and middleware; useful for tests.
  void clear() {
    _handlers.clear();
    _middleware.clear();
  }
}

extension CommandBusX on CommandBus {
  /// Convenience invocation to execute a command via `await bus(command)`.
  Future<CommandResult<R>> call<C extends Command<R>, R>(C command) =>
      execute<C, R>(command);
}
