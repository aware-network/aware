import 'package:aware_pane/aware_pane.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('PaneSelectionMetadataBuilder', () {
    test('composes metadata with provided fields', () {
      final metadata = PaneSelectionMetadataBuilder.compose(
        threadId: 'thread-1',
        processId: 'process-1',
        branchId: 'branch-1',
        paneInstanceId: 'instance-1',
        origin: 'unit-test',
        extras: const {'custom': 42},
      );

      expect(metadata[PaneSelectionMetadataKeys.threadId], 'thread-1');
      expect(metadata[PaneSelectionMetadataKeys.processId], 'process-1');
      expect(metadata[PaneSelectionMetadataKeys.branchId], 'branch-1');
      expect(metadata[PaneSelectionMetadataKeys.paneInstanceId], 'instance-1');
      expect(metadata[PaneSelectionMetadataKeys.origin], 'unit-test');
      expect(metadata['custom'], 42);
    });
  });

  group('PaneManifestMetadataBuilder', () {
    test('composes manifest metadata with extras', () {
      final metadata = PaneManifestMetadataBuilder.compose(
        threadDirectory: '/tmp/thread',
        threadSnapshot: 'snapshot',
        branch: 'branch-object',
        extras: const {'foo': 'bar'},
      );

      expect(metadata[PaneManifestMetadataKeys.threadDirectory], '/tmp/thread');
      expect(metadata[PaneManifestMetadataKeys.threadSnapshot], 'snapshot');
      expect(metadata[PaneManifestMetadataKeys.branch], 'branch-object');
      expect(metadata['foo'], 'bar');
    });
  });
}
