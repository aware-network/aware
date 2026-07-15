import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

const _testWindowVersion = 1;

void main() {
  group('Window overlay behaviour', () {
    testWidgets('shows overlay content and updates header', (tester) async {
      const windowId = 'overlay_window';
      final config = WindowConfig(
        id: windowId,
        name: 'Base Header',
        mode: WindowLayoutMode.vertical,
        sections: const [
          WindowSectionConfig(id: 'primary', paneId: 'repository', flex: 1.0),
        ],
        version: _testWindowVersion,
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: OverlayHarness(
              registerOverlay: (registry) {
                registry.register(
                  WindowOverlayDescriptor(
                    overlayId: 'sample_overlay',
                    windowId: windowId,
                    dismissPolicy: OverlayDismissPolicy.manual,
                    builder: (context, ref, arguments) =>
                        const Center(child: Text('Overlay Payload')),
                    headerBuilder: (_) =>
                        const WindowHeaderData(title: 'Overlay Header'),
                  ),
                );
              },
              onReady: (ref) {
                ref
                    .read(windowOverlayControllerProvider(windowId).notifier)
                    .showOverlay('sample_overlay');
              },
              child: Scaffold(
                body: Window(
                  config: config,
                  sectionBuilder: (context, ref, section, headerArgs) =>
                      const SizedBox(),
                ),
              ),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Overlay Payload'), findsOneWidget);
      expect(find.text('Overlay Header'), findsOneWidget);

      // Tap scrim to close overlay (manual policy allows tap dismissal).
      final windowElement = tester.element(find.byType(Window));
      final container = ProviderScope.containerOf(windowElement);
      container
          .read(windowOverlayControllerProvider(windowId).notifier)
          .hideOverlay();
      await tester.pumpAndSettle();

      expect(find.text('Overlay Payload'), findsNothing);
      expect(find.text('Overlay Header'), findsNothing);
      expect(find.text('Base Header'), findsOneWidget);
    });

    testWidgets('auto dismiss overlay when policy is autoOnSectionChange', (
      tester,
    ) async {
      const windowId = 'auto-dismiss';
      final config = WindowConfig(
        id: windowId,
        name: 'Window',
        mode: WindowLayoutMode.vertical,
        sections: const [
          WindowSectionConfig(id: 'primary', paneId: 'a', flex: 0.5),
          WindowSectionConfig(id: 'secondary', paneId: 'b', flex: 0.5),
        ],
        version: _testWindowVersion,
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: OverlayHarness(
              registerOverlay: (registry) {
                registry.register(
                  WindowOverlayDescriptor(
                    overlayId: 'auto-overlay',
                    windowId: windowId,
                    dismissPolicy: OverlayDismissPolicy.autoOnSectionChange,
                    builder: (context, ref, arguments) =>
                        const Center(child: Text('Auto Overlay')),
                  ),
                );
              },
              onReady: (ref) {
                final controller = ref.read(
                  windowOverlayControllerProvider(windowId).notifier,
                );
                controller.showOverlay('auto-overlay');
                controller.dismissForPolicy();
              },
              child: Scaffold(
                body: Window(config: config, sectionBuilder: _sectionBuilder),
              ),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();
      expect(find.text('Auto Overlay'), findsNothing);
    });

    testWidgets('uses custom overlay scrim builder with dismiss callback', (
      tester,
    ) async {
      const windowId = 'custom_scrim_window';
      final config = WindowConfig(
        id: windowId,
        name: 'Window',
        mode: WindowLayoutMode.vertical,
        sections: const [
          WindowSectionConfig(id: 'primary', paneId: 'repository', flex: 1.0),
        ],
        version: _testWindowVersion,
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: OverlayHarness(
              registerOverlay: (registry) {
                registry.register(
                  WindowOverlayDescriptor(
                    overlayId: 'custom_overlay',
                    windowId: windowId,
                    dismissPolicy: OverlayDismissPolicy.manual,
                    builder: (context, ref, arguments) =>
                        const Center(child: Text('Overlay Content')),
                  ),
                );
              },
              onReady: (ref) {
                ref
                    .read(windowOverlayControllerProvider(windowId).notifier)
                    .showOverlay('custom_overlay');
              },
              child: Scaffold(
                body: Window(
                  config: config,
                  overlayScrimBuilder: (context, ref, descriptor, dismiss) {
                    return GestureDetector(
                      key: const Key('custom-scrim'),
                      onTap: dismiss,
                      child: Container(
                        color: Colors.purple.withValues(alpha: 0.4),
                      ),
                    );
                  },
                  sectionBuilder: _sectionBuilder,
                ),
              ),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Overlay Content'), findsOneWidget);
      expect(find.byKey(const Key('custom-scrim')), findsOneWidget);

      final windowElement = tester.element(find.byType(Window));
      final container = ProviderScope.containerOf(windowElement);
      container
          .read(windowOverlayControllerProvider(windowId).notifier)
          .hideOverlay();
      await tester.pumpAndSettle();

      expect(find.text('Overlay Content'), findsNothing);
    });

    testWidgets(
      'pane host overlay session manages shortcuts and focus transitions',
      (tester) async {
        const windowId = 'session_window';
        const overlayId = 'session_overlay';
        final config = WindowConfig(
          id: windowId,
          name: 'Window',
          mode: WindowLayoutMode.vertical,
          sections: const [
            WindowSectionConfig(id: 'primary', paneId: 'repository', flex: 1.0),
          ],
          version: _testWindowVersion,
        );

        final presenter = WindowPanePresenter(
          paneId: 'repository',
          builder: (context, ref, config, headerArgs) =>
              const SizedBox.shrink(),
          shortcuts: (ref, config, headerArgs) => [
            overlayShortcut(
              id: 'overlay.close',
              activator: SingleActivator(LogicalKeyboardKey.escape),
              onInvoke: (_) {},
            ),
          ],
        );

        await tester.pumpWidget(
          ProviderScope(
            child: MaterialApp(
              home: OverlayHarness(
                registerOverlay: (registry) {
                  registry.register(
                    WindowOverlayDescriptor(
                      overlayId: overlayId,
                      windowId: windowId,
                      dismissPolicy: OverlayDismissPolicy.manual,
                      builder: (context, ref, arguments) {
                        return WindowOverlayPaneHost(
                          windowId: windowId,
                          overlayId: overlayId,
                          paneId: 'repository',
                          headerArgs: HeaderControllerArgs(
                            windowId: windowId,
                            initialData: const WindowHeaderData(
                              title: 'Overlay',
                            ),
                          ),
                        );
                      },
                    ),
                  );
                },
                onReady: (ref) {
                  ref
                      .read(windowOverlayControllerProvider(windowId).notifier)
                      .showOverlay(overlayId);
                },
                child: WindowShortcutScope(
                  windowId: windowId,
                  child: WindowFocusScope(
                    windowId: windowId,
                    child: WindowPanePresenterScope(
                      presenters: [presenter],
                      child: Scaffold(
                        body: Window(
                          config: config,
                          sectionBuilder: (context, ref, section, headerArgs) =>
                              const SizedBox(),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        );

        await tester.pumpAndSettle();

        final windowElement = tester.element(find.byType(Window));
        final container = ProviderScope.containerOf(windowElement);

        container
            .read(windowFocusControllerProvider(windowId).notifier)
            .suspendForOverlay(overlayId);
        await tester.pump();

        final shortcutState = container.read(
          windowShortcutRegistryProvider(windowId),
        );
        expect(
          shortcutState.activeBindings.values.any(
            (binding) => binding.id == 'overlay.close',
          ),
          isTrue,
        );

        final controller = container.read(
          windowOverlayControllerProvider(windowId).notifier,
        );
        controller.hideOverlay();
        await tester.pumpAndSettle();

        container
            .read(windowFocusControllerProvider(windowId).notifier)
            .resumeFromOverlay(overlayId);
        await tester.pump();

        final clearedState = container.read(
          windowShortcutRegistryProvider(windowId),
        );
        expect(
          clearedState.activeBindings.values.any(
            (binding) => binding.id == 'overlay.close',
          ),
          isFalse,
        );

        final transitions = container.read(
          windowFocusTransitionsProvider(windowId),
        );
        final overlayTransitions = transitions.where(
          (transition) => transition.overlayId == overlayId,
        );
        final suspendedCount = overlayTransitions
            .where(
              (transition) =>
                  transition.phase == FocusTransitionPhase.suspended,
            )
            .length;
        final resumedCount = overlayTransitions
            .where(
              (transition) => transition.phase == FocusTransitionPhase.resumed,
            )
            .length;

        expect(suspendedCount, equals(1));
        expect(resumedCount, equals(1));
      },
    );
  });
}

class OverlayHarness extends ConsumerStatefulWidget {
  const OverlayHarness({
    super.key,
    required this.registerOverlay,
    required this.onReady,
    required this.child,
  });

  final void Function(WindowOverlayRegistry registry) registerOverlay;
  final void Function(WidgetRef ref) onReady;
  final Widget child;

  @override
  ConsumerState<OverlayHarness> createState() => _OverlayHarnessState();
}

class _OverlayHarnessState extends ConsumerState<OverlayHarness> {
  @override
  void initState() {
    super.initState();
    final registry = ref.read(windowOverlayRegistryProvider);
    widget.registerOverlay(registry);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      widget.onReady(ref);
    });
  }

  @override
  Widget build(BuildContext context) {
    return widget.child;
  }
}

Widget _sectionBuilder(
  BuildContext context,
  WidgetRef ref,
  WindowSectionConfig config,
  HeaderControllerArgs headerArgs,
) {
  return SizedBox(key: Key('section-${config.id}'));
}
