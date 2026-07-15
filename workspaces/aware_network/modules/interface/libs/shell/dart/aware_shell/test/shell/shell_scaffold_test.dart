import 'package:aware_shell/aware_shell.dart';
import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('renders the shared shell sections on wide layouts', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(1440, 1200);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceShellScaffold(
          header: const Text('Interface Shell'),
          sections: const <WindowFullscreenSectionFrameSection>[
            WindowFullscreenSectionFrameSection(
              id: 'orchestration',
              region: WindowFullscreenSectionRegion.leading,
              order: 0,
              child: _ShellCard(label: 'Orchestration'),
            ),
            WindowFullscreenSectionFrameSection(
              id: 'workspace',
              region: WindowFullscreenSectionRegion.stage,
              order: 1,
              child: _ShellCard(label: 'Workspace'),
            ),
            WindowFullscreenSectionFrameSection(
              id: 'inspector',
              region: WindowFullscreenSectionRegion.trailing,
              order: 2,
              child: _ShellCard(label: 'Inspector'),
            ),
            WindowFullscreenSectionFrameSection(
              id: 'console',
              region: WindowFullscreenSectionRegion.dock,
              order: 3,
              child: _ShellCard(label: 'Console'),
            ),
          ],
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Interface Shell'), findsOneWidget);
    expect(
      find.byKey(const Key('window-fullscreen-section-orchestration')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('window-fullscreen-section-workspace')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('window-fullscreen-section-inspector')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('window-fullscreen-section-console')),
      findsOneWidget,
    );
  });

  testWidgets('renders an optional rail and forwards slot taps', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(1440, 1200);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    WindowSlot? tappedSlot;

    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceShellScaffold(
          railSlots: const <WindowSlot>[
            WindowSlot(
              slotId: 'workspace',
              paneId: 'workspace',
              label: 'Workspace',
              icon: Icons.dashboard_outlined,
              isActive: true,
            ),
            WindowSlot(
              slotId: 'inspector',
              paneId: 'inspector',
              label: 'Inspector',
              icon: Icons.tune,
            ),
          ],
          onRailSlotTapped: (slot) => tappedSlot = slot,
          sections: const <WindowFullscreenSectionFrameSection>[
            WindowFullscreenSectionFrameSection(
              id: 'workspace',
              child: _ShellCard(label: 'Workspace'),
            ),
          ],
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.byType(WindowSectionRail), findsOneWidget);

    await tester.tap(find.byTooltip('Inspector'));
    await tester.pumpAndSettle();

    expect(tappedSlot?.slotId, 'inspector');
    expect(tappedSlot?.paneId, 'inspector');
  });

  testWidgets(
      'previews a stable-id vector locally and commits once on drag end', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(1440, 900);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final commits = <WindowLayoutTransitionCommitIntent>[];

    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceShellScaffold(
          committedLayoutTransitionId: 'transition-1',
          committedTopologyTransitionId: 'topology-1',
          clientIntentIdFactory: () => 'drag-1',
          onLayoutTransitionCommit: (intent) async => commits.add(intent),
          sections: const <WindowFullscreenSectionFrameSection>[
            WindowFullscreenSectionFrameSection(
              id: 'navigation',
              transitionSectionId: 'config-section-navigation',
              region: WindowFullscreenSectionRegion.leading,
              order: 0,
              weightMicros: 300000,
              flex: 0.3,
              child: _ShellCard(label: 'Navigation'),
            ),
            WindowFullscreenSectionFrameSection(
              id: 'stage',
              transitionSectionId: 'config-section-stage',
              region: WindowFullscreenSectionRegion.stage,
              order: 1,
              weightMicros: 700000,
              flex: 0.7,
              child: _ShellCard(label: 'Stage'),
            ),
            WindowFullscreenSectionFrameSection(
              id: 'inspector',
              transitionSectionId: 'config-section-inspector',
              region: WindowFullscreenSectionRegion.trailing,
              order: 2,
              weightMicros: 0,
              flex: 0,
              isCollapsed: true,
              child: _ShellCard(label: 'Inspector'),
            ),
          ],
        ),
      ),
    );
    await tester.pumpAndSettle();

    final handle = find.byKey(const Key('window-layout-resize-leading-stage'));
    expect(handle, findsOneWidget);
    final gesture = await tester.startGesture(tester.getCenter(handle));
    await gesture.moveBy(const Offset(100, 0));
    await tester.pump();

    expect(commits, isEmpty);

    await gesture.up();
    await tester.pumpAndSettle();

    expect(commits, hasLength(1));
    expect(commits.single.clientIntentId, 'drag-1');
    expect(commits.single.expectedPreviousTransitionId, 'transition-1');
    expect(commits.single.topologyTransitionId, 'topology-1');
    expect(commits.single.sectionStates, hasLength(3));
    expect(commits.single.sectionStates.last.weightMicros, 0);
    expect(
      commits.single.sectionStates.fold<int>(
        0,
        (sum, section) => sum + section.weightMicros,
      ),
      windowLayoutWeightMicrosTotal,
    );
  });

  testWidgets('topology scope previews catalog membership and commits once', (
    tester,
  ) async {
    final commits = <WindowLayoutTopologyCommitIntent>[];

    await tester.pumpWidget(
      MaterialApp(
        home: InterfaceShellScaffold(
          committedTopologyTransitionId: 'topology-1',
          admittedTopologySections: const <WindowLayoutTopologyCatalogSection>[
            WindowLayoutTopologyCatalogSection(
              sectionId: 'config-section-a',
              catalogOrder: 0,
            ),
            WindowLayoutTopologyCatalogSection(
              sectionId: 'config-section-b',
              catalogOrder: 1,
            ),
            WindowLayoutTopologyCatalogSection(
              sectionId: 'config-section-c',
              catalogOrder: 2,
            ),
          ],
          clientIntentIdFactory: () => 'topology-intent-1',
          onLayoutTopologyCommit: (intent) async => commits.add(intent),
          sections: <WindowFullscreenSectionFrameSection>[
            WindowFullscreenSectionFrameSection(
              id: 'a',
              transitionSectionId: 'config-section-a',
              order: 0,
              child: Builder(
                builder: (context) => TextButton(
                  key: const Key('change-layout-topology'),
                  onPressed: () async {
                    final controller = WindowLayoutTopologyScope.of(context);
                    controller.beginPreview();
                    controller.previewRemove('config-section-b');
                    controller.previewReadd('config-section-c', atIndex: 0);
                    await controller.commitPreview();
                  },
                  child: const Text('Change topology'),
                ),
              ),
            ),
            const WindowFullscreenSectionFrameSection(
              id: 'b',
              transitionSectionId: 'config-section-b',
              order: 1,
              child: Text('Section B'),
            ),
          ],
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('change-layout-topology')));
    await tester.pumpAndSettle();

    expect(commits, hasLength(1));
    expect(commits.single.clientIntentId, 'topology-intent-1');
    expect(
      commits.single.expectedPreviousTopologyTransitionId,
      'topology-1',
    );
    expect(
      commits.single.sectionStates
          .map((section) => '${section.sectionId}:${section.order}'),
      <String>['config-section-c:0', 'config-section-a:1'],
    );
    expect(find.text('Section B'), findsNothing);
  });

  testWidgets('asserts if rail slots are provided without a tap callback', (
    tester,
  ) async {
    expect(
      () => InterfaceShellScaffold(
        railSlots: const <WindowSlot>[
          WindowSlot(
            slotId: 'workspace',
            paneId: 'workspace',
            label: 'Workspace',
            icon: Icons.dashboard_outlined,
          ),
        ],
        sections: const <WindowFullscreenSectionFrameSection>[
          WindowFullscreenSectionFrameSection(
            id: 'workspace',
            child: SizedBox.shrink(),
          ),
        ],
      ),
      throwsAssertionError,
    );
  });
}

class _ShellCard extends StatelessWidget {
  const _ShellCard({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 120,
      padding: const EdgeInsets.all(16),
      color: Colors.blueGrey,
      child: Align(
        alignment: Alignment.topLeft,
        child: Text(label, style: const TextStyle(color: Colors.white)),
      ),
    );
  }
}
