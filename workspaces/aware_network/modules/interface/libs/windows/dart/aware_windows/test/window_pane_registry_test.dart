import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('WindowPaneRegistry diagnostics', () {
    test('records duplicate presenter registrations', () {
      final registry = WindowPaneRegistry();

      final presenterA = WindowPanePresenter(
        paneId: 'duplicate',
        builder: (_, __, ___, ____) => const SizedBox(),
      );
      final presenterB = WindowPanePresenter(
        paneId: 'duplicate',
        builder: (_, __, ___, ____) => const SizedBox(),
      );

      final firstRegistration = registry.register(presenterA);
      final secondRegistration = registry.register(presenterB);

      expect(firstRegistration, isTrue);
      expect(secondRegistration, isFalse);

      final diagnostics = registry.takeDiagnostics();
      expect(diagnostics.length, 1);
      expect(diagnostics.first, contains('Duplicate presenter registration'));
    });

    test('clears diagnostics after takeDiagnostics', () {
      final registry = WindowPaneRegistry();
      final presenter = WindowPanePresenter(
        paneId: 'demo',
        builder: (_, __, ___, ____) => const SizedBox(),
      );

      registry.register(presenter);
      expect(registry.takeDiagnostics(), isEmpty);
      expect(registry.takeDiagnostics(), isEmpty);
    });
  });
}
