import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('section focus binding tracks descendant focus', (tester) async {
    final container = ProviderContainer();

    final presenter = WindowPanePresenter(
      paneId: 'pane_repository',
      builder: (context, ref, config, headerArgs) {
        return const TextField();
      },
      header: (config) => const WindowPaneHeaderData(title: 'Repository'),
    );

    const config = WindowConfig(
      id: 'window_focus',
      name: 'Focus Window',
      mode: WindowLayoutMode.horizontal,
      sections: [
        WindowSectionConfig(
          id: 'section_repository',
          paneId: 'pane_repository',
          flex: 1.0,
        ),
      ],
      version: 1,
    );

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          home: WindowPanePresenterScope(
            presenters: [presenter],
            child: Scaffold(
              body: WindowFocusScope(
                windowId: 'window_focus',
                child: const Window(config: config),
              ),
            ),
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(
      container.read(windowFocusControllerProvider('window_focus')).hasFocus,
      isFalse,
    );

    await tester.tap(find.byType(TextField));
    await tester.pumpAndSettle();

    final state = container.read(windowFocusControllerProvider('window_focus'));
    expect(state.activePaneId, 'pane_repository');
    expect(state.activeSectionId, 'section_repository');
    expect(state.hasFocus, isTrue);
  });

  testWidgets('PaneFocusHandle requestFocus claims section focus', (
    tester,
  ) async {
    final container = ProviderContainer();

    final presenter = WindowPanePresenter(
      paneId: 'pane_repository',
      focusConfig: const PaneFocusConfig(canRequestFocus: true),
      builder: (context, ref, config, headerArgs) {
        return Builder(
          builder: (context) => ElevatedButton(
            key: const Key('request-focus'),
            onPressed: () {
              PaneFocusHandle.maybeOf(context)?.requestFocus();
            },
            child: const Text('Request focus'),
          ),
        );
      },
      header: (config) => const WindowPaneHeaderData(title: 'Repository'),
    );

    const config = WindowConfig(
      id: 'window_focus',
      name: 'Focus Window',
      mode: WindowLayoutMode.horizontal,
      sections: [
        WindowSectionConfig(
          id: 'section_repository',
          paneId: 'pane_repository',
          flex: 1.0,
        ),
      ],
      version: 1,
    );

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          home: WindowPanePresenterScope(
            presenters: [presenter],
            child: Scaffold(
              body: WindowFocusScope(
                windowId: 'window_focus',
                child: const Window(config: config),
              ),
            ),
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(
      container.read(windowFocusControllerProvider('window_focus')).hasFocus,
      isFalse,
    );

    expect(find.byType(ElevatedButton), findsOneWidget);

    await tester.tap(find.byKey(const Key('request-focus')));
    await tester.pumpAndSettle();

    final state = container.read(windowFocusControllerProvider('window_focus'));
    expect(state.activeSectionId, 'section_repository');
    expect(state.activePaneId, 'pane_repository');
    expect(state.hasFocus, isTrue);
  });
}
