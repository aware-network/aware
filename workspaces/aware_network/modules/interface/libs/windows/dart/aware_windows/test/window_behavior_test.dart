import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

const _testWindowVersion = 1;

void main() {
  testWidgets('applies custom palette background', (tester) async {
    const customColor = Color(0xFF112233);
    final config = WindowConfig(
      id: 'palette-window',
      name: 'Palette Window',
      mode: WindowLayoutMode.vertical,
      sections: const [
        WindowSectionConfig(id: 'section_a', paneId: 'process', flex: 1.0),
      ],
      version: _testWindowVersion,
    );

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: Scaffold(
            body: Window(
              config: config,
              paletteBuilder: (_) => const WindowPalette(
                background: customColor,
                card: Colors.white,
                divider: Colors.black26,
                border: Colors.black26,
                primary: Colors.blue,
                text: Colors.black,
                mutedText: Colors.black54,
              ),
              sectionBuilder: _sectionBodyBuilder,
            ),
          ),
        ),
      ),
    );

    expect(
      find.descendant(
        of: find.byType(Window),
        matching: find.byWidgetPredicate(
          (widget) =>
              widget is Container &&
              widget.decoration == null &&
              widget.color == customColor,
        ),
      ),
      findsOneWidget,
    );
  });

  testWidgets('uses custom divider builder when provided', (tester) async {
    final config = WindowConfig(
      id: 'divider-window',
      name: 'Divider Window',
      mode: WindowLayoutMode.vertical,
      sections: const [
        WindowSectionConfig(id: 'section_a', paneId: 'process', flex: 0.5),
        WindowSectionConfig(id: 'section_b', paneId: 'conversation', flex: 0.5),
      ],
      version: _testWindowVersion,
    );

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: Scaffold(
            body: Window(
              config: config,
              dividerBuilder: (context, isVertical, onDrag, palette) {
                return SizedBox(
                  key: Key('divider-${isVertical ? 'vertical' : 'horizontal'}'),
                );
              },
              sectionBuilder: _sectionBodyBuilder,
            ),
          ),
        ),
      ),
    );

    expect(find.byKey(const Key('divider-horizontal')), findsOneWidget);
  });

  testWidgets('toggling collapse hides and restores section content', (
    tester,
  ) async {
    final collapsedEvents = <String>[];
    final config = WindowConfig(
      id: 'collapse-window',
      name: 'Collapse Window',
      mode: WindowLayoutMode.vertical,
      sections: const [
        WindowSectionConfig(id: 'section_a', paneId: 'process', flex: 0.5),
        WindowSectionConfig(id: 'section_b', paneId: 'thread', flex: 0.5),
      ],
      version: _testWindowVersion,
    );

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: Scaffold(
            body: Window(
              config: config,
              onSectionCollapse: collapsedEvents.add,
              sectionBuilder: _sectionBodyBuilder,
            ),
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('body-section_a'), findsOneWidget);
    expect(find.text('body-section_b'), findsOneWidget);

    final state = tester.state(find.byType(Window)) as dynamic;
    state.toggleSection('section_b');
    await tester.pumpAndSettle();

    expect(find.text('body-section_b'), findsNothing);
    expect(collapsedEvents, ['section_b']);

    state.toggleSection('section_b');
    await tester.pumpAndSettle();

    expect(find.text('body-section_b'), findsOneWidget);
    expect(collapsedEvents, ['section_b', 'section_b']);
  });
}

Widget _sectionBodyBuilder(
  BuildContext context,
  WidgetRef ref,
  WindowSectionConfig config,
  HeaderControllerArgs headerArgs,
) {
  return Center(child: Text('body-${config.id}'));
}
