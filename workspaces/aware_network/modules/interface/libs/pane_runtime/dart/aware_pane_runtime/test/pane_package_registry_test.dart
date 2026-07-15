import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uuid/uuid_value.dart';

import 'package:aware_pane/aware_pane.dart' as runtime;
import 'package:aware_pane_runtime/aware_pane_runtime.dart';

void main() {
  group('PanePackageRegistry', () {
    test(
      'builds a pane by pane_package_id and rewrites paneKey to paneKind',
      () {
        final registry = PanePackageRegistry();
        final panePackageId = UuidValue.fromString(
          '11111111-1111-1111-1111-111111111111',
        );
        registry.registerPanePackage(
          panePackageId: panePackageId,
          panePackageName: 'home-overview',
          paneKind: 'home',
          capabilities: const runtime.PaneCapabilities(),
          factory: (context) =>
              Text('kind=${context.kind}', textDirection: TextDirection.ltr),
        );

        final widget = registry.build(
          panePackageId,
          PaneContext(paneId: 'pane-1', kind: 'generic'),
        );

        expect(widget, isA<Text>());
        expect((widget as Text).data, 'kind=home');
        expect(registry.isRegistered(panePackageId), isTrue);
        expect(registry.displayInfoFor(panePackageId)?.title, 'home-overview');
      },
    );

    test('same pane kind can be registered by multiple pane package ids', () {
      final registry = PanePackageRegistry();
      final firstPackageId = UuidValue.fromString(
        '22222222-2222-2222-2222-222222222222',
      );
      final secondPackageId = UuidValue.fromString(
        '33333333-3333-3333-3333-333333333333',
      );

      registry.registerPanePackage(
        panePackageId: firstPackageId,
        panePackageName: 'door-control-a',
        paneKind: 'door',
        capabilities: const runtime.PaneCapabilities(),
        factory: (_) => const Text('A', textDirection: TextDirection.ltr),
      );
      registry.registerPanePackage(
        panePackageId: secondPackageId,
        panePackageName: 'door-control-b',
        paneKind: 'door',
        capabilities: const runtime.PaneCapabilities(),
        factory: (_) => const Text('B', textDirection: TextDirection.ltr),
      );

      final firstWidget = registry.build(
        firstPackageId,
        PaneContext(paneId: 'pane-2', kind: 'generic'),
      );
      final secondWidget = registry.build(
        secondPackageId,
        PaneContext(paneId: 'pane-3', kind: 'generic'),
      );

      expect((firstWidget as Text).data, 'A');
      expect((secondWidget as Text).data, 'B');
      expect(registry.registeredPanePackageIds(), hasLength(2));
    });

    test(
      'duplicate pane package registration replaces the entry and records a diagnostic',
      () {
        final registry = PanePackageRegistry();
        final panePackageId = UuidValue.fromString(
          '44444444-4444-4444-4444-444444444444',
        );

        registry.registerPanePackage(
          panePackageId: panePackageId,
          panePackageName: 'tv-status',
          paneKind: 'tv',
          capabilities: const runtime.PaneCapabilities(),
          factory: (_) => const Text('first', textDirection: TextDirection.ltr),
        );
        registry.registerPanePackage(
          panePackageId: panePackageId,
          panePackageName: 'tv-status-v2',
          paneKind: 'tv',
          capabilities: const runtime.PaneCapabilities(),
          factory: (_) =>
              const Text('second', textDirection: TextDirection.ltr),
        );

        final widget = registry.build(
          panePackageId,
          PaneContext(paneId: 'pane-4', kind: 'generic'),
        );

        expect((widget as Text).data, 'second');
        expect(registry.takeDiagnostics(), hasLength(1));
        expect(registry.displayInfoFor(panePackageId)?.title, 'tv-status-v2');
      },
    );
  });
}
