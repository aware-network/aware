import 'command_result.dart';

/// Base type for all commands.
abstract class Command<TResult> {
  const Command();

  /// Human-readable type name used for logging and diagnostics.
  String get commandType => runtimeType.toString();
}

/// Signature for command handlers.
typedef CommandHandler<C extends Command<R>, R> =
    Future<CommandResult<R>> Function(C command);
