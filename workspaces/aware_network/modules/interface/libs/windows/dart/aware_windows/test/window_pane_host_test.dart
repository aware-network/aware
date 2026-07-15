import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show LogicalKeyboardKey, SingleActivator;
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  testWidgets(
    'WindowPaneHost wires presenter shortcuts and focus integration',
    (tester) async {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final section = const WindowSectionConfig(
        id: 'data_section',
        paneId: 'data',
        flex: 1.0,
      );

      final headerArgs = HeaderControllerArgs(
        windowId: 'window',
        initialData: const WindowHeaderData(title: 'Data'),
      );

      final presenter = WindowPanePresenter(
        paneId: 'repository',
        builder: (context, ref, config, headerArgs) {
          return Text('pane ${config.paneId}');
        },
        shortcuts: (ref, config, headerArgs) => [
          paneShortcut(
            id: 'repository.quickOpen',
            activator: SingleActivator(LogicalKeyboardKey.keyP, control: true),
            onInvoke: (_) {},
          ),
        ],
      );

      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: MaterialApp(
            home: WindowShortcutScope(
              windowId: 'window',
              child: WindowFocusScope(
                windowId: 'window',
                child: WindowPanePresenterScope(
                  presenters: [presenter],
                  child: Scaffold(
                    body: WindowPaneHost(
                      windowId: 'window',
                      sectionConfig: section,
                      headerArgs: headerArgs,
                      paneId: 'repository',
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      );

      // Activate focus to simulate the pane gaining focus inside the window.
      container
          .read(windowFocusControllerProvider('window').notifier)
          .setSectionFocus(sectionId: section.id, paneId: presenter.paneId);

      await tester.pump();

      expect(find.byType(WindowPaneHost), findsOneWidget);

      final shortcutState = container.read(
        windowShortcutRegistryProvider('window'),
      );

      expect(
        shortcutState.activeBindings.values.any(
          (binding) => binding.id == 'repository.quickOpen',
        ),
        isTrue,
      );
    },
  );
}
