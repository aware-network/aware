import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets(
    'uses leading/stage/trailing rails and lower dock on wide screens',
    (tester) async {
      tester.view.devicePixelRatio = 1.0;
      tester.view.physicalSize = const Size(1440, 1200);
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: WindowFullscreenSectionFrame(
              mode: WindowLayoutMode.grid,
              header: const Text('Header'),
              sections: const [
                WindowFullscreenSectionFrameSection(
                  id: 'orchestration',
                  region: WindowFullscreenSectionRegion.leading,
                  order: 0,
                  child: _FrameCard(label: 'Orchestration'),
                ),
                WindowFullscreenSectionFrameSection(
                  id: 'workspace',
                  region: WindowFullscreenSectionRegion.stage,
                  order: 1,
                  child: _FrameCard(label: 'Workspace'),
                ),
                WindowFullscreenSectionFrameSection(
                  id: 'inspector',
                  region: WindowFullscreenSectionRegion.trailing,
                  order: 2,
                  child: _FrameCard(label: 'Inspector'),
                ),
                WindowFullscreenSectionFrameSection(
                  id: 'console',
                  region: WindowFullscreenSectionRegion.dock,
                  order: 3,
                  child: _FrameCard(label: 'Console'),
                ),
              ],
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      final orchestrationTopLeft = tester.getTopLeft(
        find.text('Orchestration'),
      );
      final workspaceTopLeft = tester.getTopLeft(find.text('Workspace'));
      final inspectorTopLeft = tester.getTopLeft(find.text('Inspector'));
      final consoleTopLeft = tester.getTopLeft(find.text('Console'));

      expect(orchestrationTopLeft.dx, lessThan(workspaceTopLeft.dx));
      expect(inspectorTopLeft.dx, greaterThan(workspaceTopLeft.dx));
      expect(consoleTopLeft.dy, greaterThan(workspaceTopLeft.dy));
      expect(consoleTopLeft.dy, greaterThan(inspectorTopLeft.dy));
    },
  );

  testWidgets(
    'can dock under the active work area without spanning the leading rail',
    (tester) async {
      tester.view.devicePixelRatio = 1.0;
      tester.view.physicalSize = const Size(1440, 1200);
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: WindowFullscreenSectionFrame(
              mode: WindowLayoutMode.grid,
              dockSpansLeadingRail: false,
              header: const Text('Header'),
              sections: const [
                WindowFullscreenSectionFrameSection(
                  id: 'orchestration',
                  region: WindowFullscreenSectionRegion.leading,
                  order: 0,
                  child: _FrameCard(label: 'Orchestration'),
                ),
                WindowFullscreenSectionFrameSection(
                  id: 'workspace',
                  region: WindowFullscreenSectionRegion.stage,
                  order: 1,
                  child: _FrameCard(label: 'Workspace'),
                ),
                WindowFullscreenSectionFrameSection(
                  id: 'inspector',
                  region: WindowFullscreenSectionRegion.trailing,
                  order: 2,
                  child: _FrameCard(label: 'Inspector'),
                ),
                WindowFullscreenSectionFrameSection(
                  id: 'console',
                  region: WindowFullscreenSectionRegion.dock,
                  order: 3,
                  child: _FrameCard(label: 'Console'),
                ),
              ],
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      final orchestrationTopLeft = tester.getTopLeft(
        find.text('Orchestration'),
      );
      final workspaceTopLeft = tester.getTopLeft(find.text('Workspace'));
      final consoleTopLeft = tester.getTopLeft(find.text('Console'));

      expect(consoleTopLeft.dy, greaterThan(workspaceTopLeft.dy));
      expect(consoleTopLeft.dx, greaterThan(orchestrationTopLeft.dx));
      expect(consoleTopLeft.dx, closeTo(workspaceTopLeft.dx, 24));
    },
  );

  testWidgets('sizes wide regional columns from section flex', (tester) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(1440, 900);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: WindowFullscreenSectionFrame(
            mode: WindowLayoutMode.grid,
            sections: const [
              WindowFullscreenSectionFrameSection(
                id: 'conversation',
                region: WindowFullscreenSectionRegion.leading,
                order: 0,
                flex: 0.8,
                child: _FrameCard(
                  key: ValueKey('conversation-card'),
                  label: 'Conversation',
                ),
              ),
              WindowFullscreenSectionFrameSection(
                id: 'goal',
                region: WindowFullscreenSectionRegion.stage,
                order: 1,
                flex: 2.4,
                child: _FrameCard(key: ValueKey('goal-card'), label: 'Goal'),
              ),
              WindowFullscreenSectionFrameSection(
                id: 'issue',
                region: WindowFullscreenSectionRegion.trailing,
                order: 2,
                flex: 1.2,
                child: _FrameCard(key: ValueKey('issue-card'), label: 'Issue'),
              ),
            ],
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    final conversationWidth = tester
        .getSize(find.byKey(const ValueKey('conversation-card')))
        .width;
    final goalWidth = tester
        .getSize(find.byKey(const ValueKey('goal-card')))
        .width;
    final issueWidth = tester
        .getSize(find.byKey(const ValueKey('issue-card')))
        .width;

    expect(goalWidth, greaterThan(conversationWidth * 2));
    expect(issueWidth, greaterThan(conversationWidth));
    expect(issueWidth, lessThan(goalWidth));
  });

  testWidgets('can use the full viewport when max content width is uncapped', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(1848, 900);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: WindowFullscreenSectionFrame(
            mode: WindowLayoutMode.grid,
            maxContentWidth: double.infinity,
            sections: const [
              WindowFullscreenSectionFrameSection(
                id: 'goal',
                region: WindowFullscreenSectionRegion.stage,
                order: 0,
                child: _FrameCard(
                  key: ValueKey('full-width-goal-card'),
                  label: 'Goal',
                ),
              ),
            ],
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    final goalWidth = tester
        .getSize(find.byKey(const ValueKey('full-width-goal-card')))
        .width;

    expect(goalWidth, greaterThan(1700));
  });

  testWidgets('fills wide regional columns to the available viewport height', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(1440, 900);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: WindowFullscreenSectionFrame(
            mode: WindowLayoutMode.grid,
            sections: const [
              WindowFullscreenSectionFrameSection(
                id: 'conversation',
                region: WindowFullscreenSectionRegion.leading,
                order: 0,
                child: _FrameCard(label: 'Conversation'),
              ),
              WindowFullscreenSectionFrameSection(
                id: 'goal',
                region: WindowFullscreenSectionRegion.stage,
                order: 1,
                child: _FrameCard(label: 'Goal'),
              ),
              WindowFullscreenSectionFrameSection(
                id: 'issue',
                region: WindowFullscreenSectionRegion.trailing,
                order: 2,
                child: _FrameCard(label: 'Issue'),
              ),
            ],
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    final conversationHeight = tester
        .getSize(
          find.byKey(const Key('window-fullscreen-section-conversation')),
        )
        .height;
    final goalHeight = tester
        .getSize(find.byKey(const Key('window-fullscreen-section-goal')))
        .height;
    final issueHeight = tester
        .getSize(find.byKey(const Key('window-fullscreen-section-issue')))
        .height;

    expect(conversationHeight, greaterThan(800));
    expect(goalHeight, greaterThan(800));
    expect(issueHeight, greaterThan(800));
  });

  testWidgets('stacks sections in a single column on narrow screens', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(720, 1200);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: WindowFullscreenSectionFrame(
            mode: WindowLayoutMode.grid,
            header: const Text('Header'),
            sections: const [
              WindowFullscreenSectionFrameSection(
                id: 'orchestration',
                region: WindowFullscreenSectionRegion.leading,
                order: 0,
                child: _FrameCard(label: 'Orchestration'),
              ),
              WindowFullscreenSectionFrameSection(
                id: 'workspace',
                region: WindowFullscreenSectionRegion.stage,
                order: 1,
                child: _FrameCard(label: 'Workspace'),
              ),
              WindowFullscreenSectionFrameSection(
                id: 'console',
                region: WindowFullscreenSectionRegion.dock,
                order: 2,
                child: _FrameCard(label: 'Console'),
              ),
            ],
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    final orchestrationTopLeft = tester.getTopLeft(find.text('Orchestration'));
    final workspaceTopLeft = tester.getTopLeft(find.text('Workspace'));
    final consoleTopLeft = tester.getTopLeft(find.text('Console'));

    expect(workspaceTopLeft.dx, closeTo(orchestrationTopLeft.dx, 1));
    expect(consoleTopLeft.dx, closeTo(orchestrationTopLeft.dx, 1));
    expect(workspaceTopLeft.dy, greaterThan(orchestrationTopLeft.dy));
    expect(consoleTopLeft.dy, greaterThan(workspaceTopLeft.dy));
  });
}

class _FrameCard extends StatelessWidget {
  const _FrameCard({super.key, required this.label});

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
