import 'package:aware_pane/aware_pane.dart';
import 'package:flutter_test/flutter_test.dart';

class _StubManifestAdapter extends PaneManifestAdapterContract<String> {
  _StubManifestAdapter({
    required this.paneKey,
    this.loadResult,
    required this.buildResult,
  });

  @override
  final PaneKey paneKey;

  final String? loadResult;
  final String buildResult;
  int loadCalls = 0;
  int buildCalls = 0;
  int saveCalls = 0;
  String? lastSavedPayload;

  @override
  Future<String?> load(PaneBranchContext context) async {
    loadCalls += 1;
    return loadResult;
  }

  @override
  Future<String> build(PaneBranchContext context) async {
    buildCalls += 1;
    return buildResult;
  }

  @override
  Future<void> save(PaneBranchContext context, String payload) async {
    saveCalls += 1;
    lastSavedPayload = payload;
  }
}

void main() {
  group('PaneManifestAdapterContract.ensure', () {
    test('returns existing manifest without rebuilding', () async {
      final adapter = _StubManifestAdapter(
        paneKey: 'demo',
        loadResult: 'existing',
        buildResult: 'rebuilt',
      );

      final context = PaneBranchContext(branchId: 'branch-1');
      final result = await adapter.ensure(context);

      expect(result, 'existing');
      expect(adapter.loadCalls, 1);
      expect(adapter.buildCalls, 0);
      expect(adapter.saveCalls, 0);
    });

    test('builds and saves when manifest missing', () async {
      final adapter = _StubManifestAdapter(
        paneKey: 'demo',
        loadResult: null,
        buildResult: 'rebuilt',
      );

      final context = PaneBranchContext(branchId: 'branch-1');
      final result = await adapter.ensure(context);

      expect(result, 'rebuilt');
      expect(adapter.loadCalls, 1);
      expect(adapter.buildCalls, 1);
      expect(adapter.saveCalls, 1);
      expect(adapter.lastSavedPayload, 'rebuilt');
    });
  });
}
