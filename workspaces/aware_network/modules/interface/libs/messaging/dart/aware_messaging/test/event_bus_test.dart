import 'package:aware_messaging/aware_messaging.dart';
import 'package:test/test.dart';

class _TestEvent extends Event {
  final String payload;

  _TestEvent(this.payload);
}

class _RecordingEventMiddleware extends EventMiddleware {
  final List<String> calls;

  _RecordingEventMiddleware(this.calls);

  @override
  Future<bool> before(Event event) async {
    calls.add('before:${event.eventType}');
    return true;
  }

  @override
  Future<void> after(Event event) async {
    calls.add('after:${event.eventType}');
  }
}

void main() {
  group('EventBus', () {
    test('publishes events to subscribers', () async {
      final bus = EventBus();
      final received = <String>[];

      bus.subscribe<_TestEvent>((event) async {
        received.add(event.payload);
      });

      await bus.publish(_TestEvent('hello'));

      expect(received, ['hello']);
    });

    test('provides typed event streams', () async {
      final bus = EventBus();
      final captured = <String>[];

      final sub = bus.events<_TestEvent>().listen((event) {
        captured.add(event.payload);
      });

      await bus.publish(_TestEvent('a'));
      await bus.publish(_TestEvent('b'));

      await Future<void>.delayed(const Duration(milliseconds: 10));
      await sub.cancel();

      expect(captured, ['a', 'b']);
    });

    test('middleware observes events', () async {
      final calls = <String>[];
      final bus = EventBus()..addMiddleware(_RecordingEventMiddleware(calls));

      await bus.publish(_TestEvent('payload'));

      expect(calls, ['before:_TestEvent', 'after:_TestEvent']);
    });
  });
}
