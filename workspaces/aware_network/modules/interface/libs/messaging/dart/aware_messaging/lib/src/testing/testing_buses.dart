import '../command/command.dart';
import '../command/command_bus.dart';
import '../command/command_result.dart';
import '../event/event.dart';
import '../event/event_bus.dart';

/// Command bus that records executed commands for assertions.
class RecordingCommandBus extends CommandBus {
  final List<Command<dynamic>> executed = [];

  @override
  Future<CommandResult<R>> execute<C extends Command<R>, R>(C command) async {
    executed.add(command);
    return super.execute(command);
  }
}

/// Event bus that records published events.
class RecordingEventBus extends EventBus {
  final List<Event> published = [];

  @override
  Future<void> publish(Event event) async {
    published.add(event);
    await super.publish(event);
  }
}

/// Command bus stub that returns a fixed result.
class StubCommandBus extends CommandBus {
  final CommandResult<dynamic> result;

  StubCommandBus(this.result);

  @override
  Future<CommandResult<R>> execute<C extends Command<R>, R>(C command) async {
    return result as CommandResult<R>;
  }
}
