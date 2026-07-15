import 'package:aware_windows/aware_windows.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  List<WindowLayoutSectionVectorState> sections({
    double first = 0.6,
    double second = 0.4,
  }) {
    return <WindowLayoutSectionVectorState>[
      WindowLayoutSectionVectorState(
        sectionId: 'section-a',
        order: 0,
        weight: first,
      ),
      WindowLayoutSectionVectorState(
        sectionId: 'section-b',
        order: 1,
        weight: second,
      ),
    ];
  }

  test('preview is local and one drag end emits one full vector', () async {
    final commits = <WindowLayoutTransitionCommitIntent>[];
    final controller = WindowLayoutTransitionController(
      committedSections: sections(),
      committedTransitionId: 'transition-1',
      committedTopologyTransitionId: 'topology-1',
      clientIntentIdFactory: () => 'drag-1',
      onCommit: (intent) async => commits.add(intent),
    );

    controller.beginPreview();
    controller.previewResizeGroups(
      leadingSectionIds: const <String>{'section-a'},
      trailingSectionIds: const <String>{'section-b'},
      deltaFraction: -0.05,
    );

    expect(commits, isEmpty);
    expect(controller.sections[0].weight, closeTo(0.55, 0.000000001));
    expect(controller.sections[1].weight, closeTo(0.45, 0.000000001));

    await controller.commitPreview();
    await controller.commitPreview();

    expect(commits, hasLength(1));
    expect(commits.single.clientIntentId, 'drag-1');
    expect(commits.single.expectedPreviousTransitionId, 'transition-1');
    expect(commits.single.topologyTransitionId, 'topology-1');
    expect(
      commits.single.sectionStates.map((section) => section.weightMicros),
      <int>[550000, 450000],
    );
  });

  test('largest remainder quantization is deterministic and exact', () {
    final result = WindowLayoutTransitionController.quantizeSections(
      const <WindowLayoutSectionVectorState>[
        WindowLayoutSectionVectorState(sectionId: 'a', order: 0, weight: 1),
        WindowLayoutSectionVectorState(sectionId: 'b', order: 1, weight: 1),
        WindowLayoutSectionVectorState(sectionId: 'c', order: 2, weight: 1),
      ],
    );

    expect(result.map((section) => section.weightMicros), <int>[
      333334,
      333333,
      333333,
    ]);
    expect(
      result.fold<int>(0, (sum, section) => sum + section.weightMicros),
      windowLayoutWeightMicrosTotal,
    );
  });

  test('every active row receives a positive ontology weight', () {
    final result = WindowLayoutTransitionController.quantizeSections(
      const <WindowLayoutSectionVectorState>[
        WindowLayoutSectionVectorState(
          sectionId: 'almost-all',
          order: 0,
          weight: 1,
        ),
        WindowLayoutSectionVectorState(
          sectionId: 'tiny',
          order: 1,
          weight: 1e-20,
        ),
      ],
    );

    expect(result[0].weightMicros, windowLayoutWeightMicrosTotal - 1);
    expect(result[1].weightMicros, 1);
  });

  test('collapse and reopen preserve an exact active vector', () {
    final controller = WindowLayoutTransitionController(
      committedSections: sections(),
      committedTransitionId: 'transition-1',
      clientIntentIdFactory: () => 'collapse-1',
      onCommit: (_) async {},
    );

    controller.beginPreview();
    controller.previewToggleCollapse('section-b');
    var quantized = WindowLayoutTransitionController.quantizeSections(
      controller.sections,
    );
    expect(quantized[0].weightMicros, windowLayoutWeightMicrosTotal);
    expect(quantized[1].weightMicros, 0);
    expect(quantized[1].isCollapsed, isTrue);

    controller.previewToggleCollapse('section-b');
    quantized = WindowLayoutTransitionController.quantizeSections(
      controller.sections,
    );
    expect(quantized[1].isCollapsed, isFalse);
    expect(
      quantized.fold<int>(0, (sum, section) => sum + section.weightMicros),
      windowLayoutWeightMicrosTotal,
    );
  });

  test('watched committed snapshot cancels stale preview', () {
    final controller = WindowLayoutTransitionController(
      committedSections: sections(),
      committedTransitionId: 'transition-1',
      clientIntentIdFactory: () => 'drag-1',
      onCommit: (_) async {},
    );
    controller.beginPreview();
    controller.previewResizeGroups(
      leadingSectionIds: const <String>{'section-a'},
      trailingSectionIds: const <String>{'section-b'},
      deltaFraction: -0.1,
    );

    controller.reconcile(
      committedSections: sections(first: 0.7, second: 0.3),
      committedTransitionId: 'transition-remote',
      committedTopologyTransitionId: 'topology-remote',
    );

    expect(controller.previewing, isFalse);
    expect(controller.committedTransitionId, 'transition-remote');
    expect(controller.committedTopologyTransitionId, 'topology-remote');
    expect(controller.sections.map((section) => section.weight), <double>[
      0.7,
      0.3,
    ]);
  });
}
