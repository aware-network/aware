import 'dart:developer' as developer;

import '../command/command.dart';
import '../command/command_bus.dart';
import '../command/command_result.dart';
import '../event/event.dart';
import '../event/event_bus.dart';

/// Debug logging middleware for command execution.
class LoggingMiddleware extends CommandMiddleware {
  final String loggerName;

  LoggingMiddleware({this.loggerName = 'aware_messaging.command'});

  @override
  Future<bool> before(Command command) async {
    developer.log(
      'Executing ${command.commandType}',
      name: loggerName,
      level: 800, // info
    );
    return true;
  }

  @override
  Future<void> after(Command command, CommandResult<dynamic> result) async {
    if (result is CommandError) {
      developer.log(
        'Error ${command.commandType}: ${result.message}',
        name: loggerName,
        level: 900,
        error: result.cause,
        stackTrace: result.stackTrace,
      );
      return;
    }

    developer.log(
      'Success ${command.commandType}',
      name: loggerName,
      level: 800,
    );
  }
}

/// Debug logging middleware for event publication.
class LoggingEventMiddleware extends EventMiddleware {
  final String loggerName;

  LoggingEventMiddleware({this.loggerName = 'aware_messaging.event'});

  @override
  Future<bool> before(Event event) async {
    developer.log(
      'Publishing ${event.eventType}',
      name: loggerName,
      level: 800,
    );
    return true;
  }

  @override
  Future<void> after(Event event) async {
    developer.log('Published ${event.eventType}', name: loggerName, level: 800);
  }
}

/// Backwards compatible alias.
typedef LoggingCommandMiddleware = LoggingMiddleware;
