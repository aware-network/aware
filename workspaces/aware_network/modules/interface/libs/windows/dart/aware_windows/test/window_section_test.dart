import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  const palette = WindowPalette(
    background: Colors.white,
    card: Colors.white,
    divider: Colors.black12,
    border: Colors.black12,
    primary: Colors.blue,
    text: Colors.black,
    mutedText: Colors.black54,
  );

  const config = WindowSectionConfig(
    id: 'section',
    paneId: 'process',
    flex: 1.0,
  );

  const headerArgs = HeaderControllerArgs(
    windowId: 'section-window',
    initialData: WindowHeaderData(title: 'Initial'),
  );

  testWidgets('renders outer header when policy is outer', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: Scaffold(
            body: WindowSection(
              config: config,
              headerArgs: headerArgs,
              palette: palette,
              sectionBuilder: _noopBuilder,
              headerBuilder: _outerHeaderBuilder,
            ),
          ),
        ),
      ),
    );

    expect(find.text('Outer Header'), findsOneWidget);
  });

  testWidgets('omits header for WindowHeaderPolicy.none', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: Scaffold(
            body: WindowSection(
              config: config,
              headerArgs: headerArgs,
              palette: palette,
              sectionBuilder: _noopBuilder,
              headerBuilder: _noneHeaderBuilder,
            ),
          ),
        ),
      ),
    );

    expect(find.text('Hidden Header'), findsNothing);
  });
}

Widget _noopBuilder(
  BuildContext context,
  WidgetRef ref,
  WindowSectionConfig config,
  HeaderControllerArgs headerArgs,
) {
  return const SizedBox();
}

WindowPaneHeaderData _outerHeaderBuilder(WindowSectionConfig config) =>
    const WindowPaneHeaderData(
      title: 'Outer Header',
      policy: WindowHeaderPolicy.outer,
    );

WindowPaneHeaderData _noneHeaderBuilder(WindowSectionConfig config) =>
    const WindowPaneHeaderData(
      title: 'Hidden Header',
      policy: WindowHeaderPolicy.none,
    );
