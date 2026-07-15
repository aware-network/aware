import 'package:aware_windows/aware_windows.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  const catalog = <WindowLayoutTopologyCatalogSection>[
    WindowLayoutTopologyCatalogSection(sectionId: 'a', catalogOrder: 0),
    WindowLayoutTopologyCatalogSection(sectionId: 'b', catalogOrder: 1),
    WindowLayoutTopologyCatalogSection(sectionId: 'c', catalogOrder: 2),
  ];

  test(
    'remove and reorder preview commits one complete active vector',
    () async {
      final commits = <WindowLayoutTopologyCommitIntent>[];
      final controller = WindowLayoutTopologyTransitionController(
        admittedSections: catalog,
        committedActiveSectionIds: const <String>['a', 'b', 'c'],
        committedTopologyTransitionId: 'topology-1',
        clientIntentIdFactory: () => 'topology-intent-1',
        onCommit: (intent) async => commits.add(intent),
      );

      controller.beginPreview();
      controller.previewRemove('b');
      controller.previewMove('c', 0);

      expect(commits, isEmpty);
      expect(controller.activeSectionIds, <String>['c', 'a']);

      await controller.commitPreview();
      await controller.commitPreview();

      expect(commits, hasLength(1));
      expect(commits.single.clientIntentId, 'topology-intent-1');
      expect(commits.single.expectedPreviousTopologyTransitionId, 'topology-1');
      expect(
        commits.single.sectionStates.map(
          (section) => '${section.sectionId}:${section.order}',
        ),
        <String>['c:0', 'a:1'],
      );
      expect(
        controller.admittedSections.map((section) => section.sectionId),
        <String>['a', 'b', 'c'],
      );
    },
  );

  test('removed admitted section can be re-added with the same anchor', () {
    final controller = WindowLayoutTopologyTransitionController(
      admittedSections: catalog,
      committedActiveSectionIds: const <String>['a', 'c'],
      committedTopologyTransitionId: 'topology-2',
      clientIntentIdFactory: () => 'topology-intent-2',
      onCommit: (_) async {},
    );

    controller.previewReadd('b', atIndex: 1);

    expect(controller.activeSectionIds, <String>['a', 'b', 'c']);
    expect(controller.admittedSections, hasLength(3));
  });

  test('watched topology replaces local preview without retry', () {
    final controller = WindowLayoutTopologyTransitionController(
      admittedSections: catalog,
      committedActiveSectionIds: const <String>['a', 'b', 'c'],
      committedTopologyTransitionId: 'topology-1',
      clientIntentIdFactory: () => 'topology-intent-3',
      onCommit: (_) async {},
    );
    controller.previewRemove('b');

    controller.reconcile(
      admittedSections: catalog,
      committedActiveSectionIds: const <String>['b', 'a'],
      committedTopologyTransitionId: 'topology-remote',
    );

    expect(controller.previewing, isFalse);
    expect(controller.activeSectionIds, <String>['b', 'a']);
    expect(controller.committedTopologyTransitionId, 'topology-remote');
  });
}
