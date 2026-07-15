/// Represents the outcome of a command execution.
sealed class CommandResult<T> {
  const CommandResult();

  /// Whether the result is a success.
  bool get isSuccess => this is CommandSuccess<T>;

  /// Whether the result is an error.
  bool get isError => this is CommandError<T>;

  /// Pattern match helper.
  R when<R>({
    required R Function(T value) success,
    required R Function(String message, String? details) error,
  }) => switch (this) {
    CommandSuccess<T>(:final value) => success(value),
    CommandError<T>(:final message, :final details) => error(message, details),
  };

  /// Maps the success value to a new type.
  CommandResult<U> map<U>(U Function(T value) mapper) => switch (this) {
    CommandSuccess<T>(:final value) => CommandSuccess<U>(mapper(value)),
    CommandError<T>(
      :final message,
      :final details,
      :final cause,
      :final stackTrace,
    ) =>
      CommandError<U>(
        message: message,
        details: details,
        cause: cause,
        stackTrace: stackTrace,
      ),
  };
}

/// Successful command execution result.
class CommandSuccess<T> extends CommandResult<T> {
  final T value;

  const CommandSuccess(this.value);

  @override
  String toString() => 'CommandSuccess($value)';
}

/// Failed command execution result.
class CommandError<T> extends CommandResult<T> {
  final String message;
  final String? details;
  final Object? cause;
  final StackTrace? stackTrace;

  const CommandError({
    required this.message,
    this.details,
    this.cause,
    this.stackTrace,
  });

  @override
  String toString() => 'CommandError(message: $message, details: $details)';
}
