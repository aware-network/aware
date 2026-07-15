import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  testWidgets(
    'WindowShortcutScope routes commands to the current window by default',
    (tester) async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final router = container.read(windowCommandRouterProvider('data_window'));
      final events = <WindowCommandIntent>[];
      final sub = router.stream.listen(events.add);
      addTearDown(sub.cancel);

      final bindings = [
        globalShortcut(
          id: 'test.command',
          activator: LogicalKeySet(
            LogicalKeyboardKey.control,
            LogicalKeyboardKey.keyP,
          ),
          descriptor: const PaneShortcutDescriptor(
            commandId: 'search.repository.quick',
            title: 'Test',
            category: 'Global',
          ),
          commandPayload: const {'providerId': 'repository'},
        ),
      ];

      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: MaterialApp(
            home: WindowShortcutScope(
              windowId: 'data_window',
              globalBindings: bindings,
              child: const Focus(autofocus: true, child: SizedBox()),
            ),
          ),
        ),
      );

      await tester.pump();

      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyDownEvent(LogicalKeyboardKey.keyP);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.keyP);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pump();

      expect(events, hasLength(1));
      expect(events.single.commandId, 'search.repository.quick');
      expect(events.single.payload, {'providerId': 'repository'});
    },
  );

  testWidgets(
    'WindowShortcutScope forwards commands to the target window override',
    (tester) async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final router = container.read(windowCommandRouterProvider('data_window'));
      final events = <WindowCommandIntent>[];
      final sub = router.stream.listen(events.add);
      addTearDown(sub.cancel);

      final bindings = [
        globalShortcut(
          id: 'test.command.targeted',
          activator: LogicalKeySet(
            LogicalKeyboardKey.control,
            LogicalKeyboardKey.keyP,
          ),
          descriptor: const PaneShortcutDescriptor(
            commandId: 'search.repository.quick',
            title: 'Test',
            category: 'Global',
          ),
          commandPayload: const {
            'providerId': 'repository',
            'targetWindowId': 'data_window',
          },
        ),
      ];

      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: MaterialApp(
            home: WindowShortcutScope(
              windowId: 'process_window',
              globalBindings: bindings,
              child: const Focus(autofocus: true, child: SizedBox()),
            ),
          ),
        ),
      );

      await tester.pump();

      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyDownEvent(LogicalKeyboardKey.keyP);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.keyP);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pump();

      expect(events, hasLength(1));
      expect(events.single.commandId, 'search.repository.quick');
      expect(events.single.payload, {'providerId': 'repository'});
    },
  );
}
