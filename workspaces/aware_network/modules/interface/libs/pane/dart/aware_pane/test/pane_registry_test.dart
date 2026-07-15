import 'package:aware_pane/aware_pane.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _TestManifestAdapter extends PaneManifestAdapterContract<String> {
  _TestManifestAdapter(this._key);

  final PaneKey _key;

  @override
  PaneKey get paneKey => _key;

  @override
  Future<String?> load(PaneBranchContext context) async {
    return null;
  }

  @override
  Future<String> build(PaneBranchContext context) async {
    return 'payload-from-${context.branchId}';
  }

  @override
  Future<void> save(PaneBranchContext context, String payload) async {}
}

class _TestSelectionHandler extends PaneSelectionHandler<String> {
  _TestSelectionHandler(String paneKey) : super(paneKey: paneKey);

  PaneContext? lastContext;
  String? lastPayload;
  Map<String, Object?>? lastMetadata;

  @override
  Future<void> handle(
    PaneContext paneContext,
    String payload,
    Map<String, Object?> metadata,
  ) async {
    lastContext = paneContext;
    lastPayload = payload;
    lastMetadata = metadata;
  }
}

void main() {
  group('PaneRegistry', () {
    testWidgets('build passes context metadata and parameters', (tester) async {
      final registry = PaneRegistry();
      PaneContext? received;

      registry.registerPane(
        key: 'demo',
        factory: (ctx) {
          received = ctx;
          return const SizedBox();
        },
        capabilities: const PaneCapabilities(layout: PaneLayoutPreferences()),
      );

      final widget = registry.build(
        'demo',
        const PaneContext(
          paneKey: 'demo',
          instanceId: 'instance-1',
          parameters: {'foo': 'bar'},
          metadata: {'projectId': 'project-1'},
        ),
      );

      expect(widget, isA<SizedBox>());
      expect(received, isNotNull);
      expect(received!.paneKey, 'demo');
      expect(received!.instanceId, 'instance-1');
      expect(received!.parameters['foo'], 'bar');
      expect(received!.metadata['projectId'], 'project-1');
    });

    test('registers manifest adapters and selection handlers', () async {
      final registry = PaneRegistry();

      final manifestAdapter = _TestManifestAdapter('demo');
      registry.registerManifestAdapter(manifestAdapter);
      expect(
        registry.manifestAdapterFor<String>('demo'),
        same(manifestAdapter),
      );

      final handler = _TestSelectionHandler('demo');
      registry.registerSelectionHandler(handler);
      final resolved = registry.selectionHandlerFor<String>('demo');
      expect(resolved, isNotNull);

      await resolved!.handle(
        const PaneContext(
          paneKey: 'demo',
          parameters: {'foo': 'bar'},
          metadata: {'projectId': 'p-1'},
        ),
        'payload',
        const {'projectId': 'p-1'},
      );

      expect(handler.lastContext, isNotNull);
      expect(handler.lastContext!.parameters['foo'], 'bar');
      expect(handler.lastPayload, 'payload');
      expect(handler.lastMetadata, const {'projectId': 'p-1'});
    });

    test('clear removes registered panes and adapters', () {
      final registry = PaneRegistry();

      registry.registerPane(
        key: 'demo',
        factory: (_) => const SizedBox(),
        capabilities: const PaneCapabilities(layout: PaneLayoutPreferences()),
      );
      registry.registerManifestAdapter(_TestManifestAdapter('demo'));
      registry.registerSelectionHandler(_TestSelectionHandler('demo'));

      expect(registry.isRegistered('demo'), isTrue);
      expect(registry.manifestAdapterFor<String>('demo'), isNotNull);
      expect(registry.selectionHandlerFor<String>('demo'), isNotNull);

      registry.clear();

      expect(registry.isRegistered('demo'), isFalse);
      expect(registry.manifestAdapterFor<String>('demo'), isNull);
      expect(registry.selectionHandlerFor<String>('demo'), isNull);
    });

    test('records diagnostics for duplicate registrations', () {
      final registry = PaneRegistry();

      registry.registerPane(
        key: 'duplicate',
        factory: (_) => const SizedBox(),
        capabilities: const PaneCapabilities(layout: PaneLayoutPreferences()),
      );
      registry.registerPane(
        key: 'duplicate',
        factory: (_) => const SizedBox(),
        capabilities: const PaneCapabilities(layout: PaneLayoutPreferences()),
      );

      registry.registerManifestAdapter(_TestManifestAdapter('duplicate'));
      registry.registerManifestAdapter(_TestManifestAdapter('duplicate'));

      registry.registerSelectionHandler(_TestSelectionHandler('duplicate'));
      registry.registerSelectionHandler(_TestSelectionHandler('duplicate'));

      final diagnostics = registry.takeDiagnostics();
      expect(diagnostics.length, 3);
      expect(diagnostics.first, contains('Duplicate pane registration'));
      expect(
        diagnostics[1],
        contains('Duplicate manifest adapter registration'),
      );
      expect(
        diagnostics[2],
        contains('Duplicate selection handler registration'),
      );
      expect(registry.takeDiagnostics(), isEmpty);
    });
  });
}
