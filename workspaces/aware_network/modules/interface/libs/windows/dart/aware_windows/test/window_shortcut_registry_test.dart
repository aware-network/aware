import 'package:aware_windows/aware_windows.dart';
import 'package:flutter/services.dart' show LogicalKeyboardKey;
import 'package:flutter/widgets.dart' show SingleActivator;
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  group('WindowShortcutRegistry', () {
    late ProviderContainer container;
    const windowId = 'test_window';

    setUp(() {
      container = ProviderContainer();
    });

    tearDown(() {
      container.dispose();
    });

    test('activates pane bindings when pane gains focus', () {
      final registry = container.read(
        windowShortcutRegistryProvider(windowId).notifier,
      );

      registry.registerGlobalBindings([
        globalShortcut(
          id: 'global.refresh',
          activator: SingleActivator(LogicalKeyboardKey.f5),
          onInvoke: (_) {},
        ),
      ]);

      registry.registerPaneBindings('repository', [
        paneShortcut(
          id: 'repository.quickOpen',
          activator: SingleActivator(LogicalKeyboardKey.keyP),
          onInvoke: (_) {},
        ),
      ]);

      registry.updateFocus(
        const WindowFocusState(
          windowId: windowId,
          activeSectionId: 'section_repo',
          activePaneId: 'repository',
        ),
      );

      final state = container.read(windowShortcutRegistryProvider(windowId));
      expect(state.activeBindings.length, 2);
      expect(
        state.activeBindings.values.any(
          (binding) => binding.id == 'repository.quickOpen',
        ),
        isTrue,
      );
    });

    test('overlay bindings override pane when suspended', () {
      final registry = container.read(
        windowShortcutRegistryProvider(windowId).notifier,
      );

      registry.registerPaneBindings('repository', [
        paneShortcut(
          id: 'repository.contentSearch',
          activator: SingleActivator(LogicalKeyboardKey.keyF, control: true),
          onInvoke: (_) {},
          priority: ShortcutPriority.high,
        ),
      ]);

      registry.registerOverlayBindings('search_overlay', [
        overlayShortcut(
          id: 'overlay.close',
          activator: SingleActivator(LogicalKeyboardKey.escape),
          onInvoke: (_) {},
        ),
      ]);

      registry.updateFocus(
        const WindowFocusState(
          windowId: windowId,
          activeSectionId: 'section_repo',
          activePaneId: 'repository',
          overlayCapture: 'search_overlay',
          isSuspended: true,
        ),
      );

      final state = container.read(windowShortcutRegistryProvider(windowId));
      expect(state.activeBindings.length, 1);
      expect(
        state.activeBindings.values.any(
          (binding) => binding.id == 'overlay.close',
        ),
        isTrue,
      );
    });

    test('records diagnostics on collisions', () {
      final registry = container.read(
        windowShortcutRegistryProvider(windowId).notifier,
      );

      registry.registerGlobalBindings([
        globalShortcut(
          id: 'global.toggle',
          activator: SingleActivator(LogicalKeyboardKey.keyT),
          onInvoke: (_) {},
        ),
      ]);

      registry.registerWindowBindings([
        windowShortcut(
          id: 'window.toggle',
          activator: SingleActivator(LogicalKeyboardKey.keyT),
          onInvoke: (_) {},
        ),
      ]);

      expect(registry.takeDiagnostics(), isNotEmpty);

      // Re-register diagnostics to ensure state still reports messages.
      registry.registerGlobalBindings([
        globalShortcut(
          id: 'global.toggle',
          activator: SingleActivator(LogicalKeyboardKey.keyT),
          onInvoke: (_) {},
        ),
      ]);

      registry.registerWindowBindings([
        windowShortcut(
          id: 'window.toggle',
          activator: SingleActivator(LogicalKeyboardKey.keyT),
          onInvoke: (_) {},
        ),
      ]);

      registry.updateFocus(
        const WindowFocusState(
          windowId: windowId,
          activeSectionId: 'section',
          activePaneId: 'pane',
        ),
      );

      final finalState = container.read(
        windowShortcutRegistryProvider(windowId),
      );
      expect(finalState.diagnostics, isNotEmpty);

      final diagnostics = registry.takeDiagnostics();
      expect(
        finalState.activeBindings.values.any(
          (binding) => binding.id == 'window.toggle',
        ),
        isTrue,
      );
      expect(diagnostics, isNotEmpty);
      final clearedState = container.read(
        windowShortcutRegistryProvider(windowId),
      );
      expect(clearedState.diagnostics, isEmpty);
    });

    test(
      'unregisterOverlayBindings removes overlay shortcuts when overlays close',
      () {
        final registry = container.read(
          windowShortcutRegistryProvider(windowId).notifier,
        );

        registry.registerOverlayBindings('search_overlay', [
          overlayShortcut(
            id: 'overlay.dismiss',
            activator: SingleActivator(LogicalKeyboardKey.escape),
            onInvoke: (_) {},
          ),
        ]);

        registry.updateFocus(
          const WindowFocusState(
            windowId: windowId,
            overlayCapture: 'search_overlay',
            isSuspended: true,
          ),
        );

        final withOverlay = container.read(
          windowShortcutRegistryProvider(windowId),
        );
        expect(
          withOverlay.activeBindings.values.any(
            (binding) => binding.id == 'overlay.dismiss',
          ),
          isTrue,
        );

        registry.unregisterOverlayBindings('search_overlay');
        registry.updateFocus(
          const WindowFocusState(
            windowId: windowId,
            overlayCapture: 'search_overlay',
            isSuspended: true,
          ),
        );

        final cleared = container.read(
          windowShortcutRegistryProvider(windowId),
        );
        expect(
          cleared.activeBindings.values.any(
            (binding) => binding.id == 'overlay.dismiss',
          ),
          isFalse,
        );
      },
    );
  });
}
