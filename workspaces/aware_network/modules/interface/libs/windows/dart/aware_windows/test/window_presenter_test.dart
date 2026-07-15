import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

const _testWindowVersion = 1;

void main() {
  testWidgets('Window falls back to registered presenter', (tester) async {
    final config = WindowConfig(
      id: 'presenter-window',
      name: 'Presenter',
      mode: WindowLayoutMode.vertical,
      sections: const [
        WindowSectionConfig(id: 'primary', paneId: 'example-pane', flex: 1.0),
      ],
      version: _testWindowVersion,
    );

    final presenter = WindowPanePresenter(
      paneId: 'example-pane',
      builder: (context, ref, sectionConfig, headerArgs) {
        return const Center(child: Text('Presenter body'));
      },
      header: (config) => const WindowPaneHeaderData(title: 'Presenter header'),
      overlays: (ref, config, headerArgs) => [
        WindowOverlayDescriptor(
          overlayId: 'presenter_overlay',
          windowId: headerArgs.windowId,
          builder: (context, overlayRef, arguments) => const SizedBox.shrink(),
        ),
      ],
    );

    await tester.pumpWidget(
      ProviderScope(
        child: WindowPanePresenterScope(
          presenters: [presenter],
          child: const MaterialApp(home: Scaffold(body: _PresenterWindow())),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Presenter body'), findsOneWidget);
    expect(find.text('Presenter header'), findsOneWidget);

    final registry = ProviderScope.containerOf(
      tester.element(find.byType(Window)),
    ).read(windowOverlayRegistryProvider);
    expect(registry.descriptorFor('presenter_overlay'), isNotNull);
  });

  testWidgets('WindowPanePresenterScope consumes diagnostics', (tester) async {
    final duplicatePresenters = [
      WindowPanePresenter(
        paneId: 'duplicate',
        builder: (context, ref, sectionConfig, headerArgs) =>
            const SizedBox.shrink(),
      ),
      WindowPanePresenter(
        paneId: 'duplicate',
        builder: (context, ref, sectionConfig, headerArgs) =>
            const SizedBox.shrink(),
      ),
    ];

    await tester.pumpWidget(
      ProviderScope(
        child: WindowPanePresenterScope(
          presenters: duplicatePresenters,
          child: const MaterialApp(home: Scaffold(body: SizedBox())),
        ),
      ),
    );

    final container = ProviderScope.containerOf(
      tester.element(find.byType(MaterialApp)),
    );
    final registry = container.read(windowPaneRegistryProvider);
    expect(registry.takeDiagnostics(), isEmpty);
  });
}

class _PresenterWindow extends ConsumerWidget {
  const _PresenterWindow();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final config = WindowConfig(
      id: 'presenter-window',
      name: 'Presenter',
      mode: WindowLayoutMode.vertical,
      sections: const [
        WindowSectionConfig(id: 'primary', paneId: 'example-pane', flex: 1.0),
      ],
      version: _testWindowVersion,
    );

    return Window(config: config);
  }
}
