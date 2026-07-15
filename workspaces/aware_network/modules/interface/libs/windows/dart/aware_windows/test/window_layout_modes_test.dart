import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('renders horizontal and vertical modes differently', (
    tester,
  ) async {
    final horizontalConfig = WindowConfig(
      id: 'horizontal-window',
      name: 'Horizontal',
      mode: WindowLayoutMode.horizontal,
      sections: const [
        WindowSectionConfig(id: 'left', paneId: 'process', flex: 0.4),
        WindowSectionConfig(id: 'right', paneId: 'conversation', flex: 0.6),
      ],
      version: 1,
    );

    final verticalConfig = WindowConfig(
      id: 'vertical-window',
      name: 'Vertical',
      mode: WindowLayoutMode.vertical,
      sections: const [
        WindowSectionConfig(id: 'top', paneId: 'process', flex: 0.3),
        WindowSectionConfig(id: 'bottom', paneId: 'conversation', flex: 0.7),
      ],
      version: 1,
    );

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: Scaffold(
            body: Column(
              children: [
                Expanded(
                  child: Window(
                    key: const Key('horizontal'),
                    config: horizontalConfig,
                    sectionBuilder: _sectionBuilder,
                  ),
                ),
                Expanded(
                  child: Window(
                    key: const Key('vertical'),
                    config: verticalConfig,
                    sectionBuilder: _sectionBuilder,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );

    final horizontalFinder = find.byKey(const Key('horizontal'));
    final verticalFinder = find.byKey(const Key('vertical'));

    expect(horizontalFinder, findsOneWidget);
    expect(verticalFinder, findsOneWidget);

    expect(
      find.descendant(of: horizontalFinder, matching: find.byType(Row)),
      findsWidgets,
    );

    expect(
      find.descendant(of: verticalFinder, matching: find.byType(Column)),
      findsWidgets,
    );
  });
}

Widget _sectionBuilder(
  BuildContext context,
  WidgetRef ref,
  WindowSectionConfig config,
  HeaderControllerArgs headerArgs,
) {
  return Container(key: Key('section-${config.id}'), color: Colors.blue);
}
