import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  testWidgets('renders window with section content', (tester) async {
    const config = WindowConfig(
      id: 'test_window',
      name: 'Test Window',
      mode: WindowLayoutMode.horizontal,
      sections: [
        WindowSectionConfig(id: 'section_1', paneId: 'repository', flex: 1.0),
      ],
      version: 1,
    );

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: Scaffold(
            body: Window(
              config: config,
              sectionBuilder: (context, ref, section, headerArgs) {
                return Center(child: Text('content: ' + section.id));
              },
            ),
          ),
        ),
      ),
    );

    await tester.pump();

    expect(find.text('Test Window'), findsOneWidget);
    expect(find.text('content: section_1'), findsOneWidget);
  });
}
