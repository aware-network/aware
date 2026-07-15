import 'package:aware_windows/aware_windows.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('WindowFocusController', () {
    late ProviderContainer container;
    const windowId = 'window-focus-test';

    setUp(() {
      container = ProviderContainer();
    });

    tearDown(() {
      container.dispose();
    });

    test('setSectionFocus updates active pane', () {
      final controller = container.read(
        windowFocusControllerProvider(windowId).notifier,
      );

      controller.setSectionFocus(sectionId: 'section_a', paneId: 'pane_a');

      final state = container.read(windowFocusControllerProvider(windowId));
      expect(state.activeSectionId, 'section_a');
      expect(state.activePaneId, 'pane_a');
      expect(state.isSuspended, isFalse);
      expect(state.hasFocus, isTrue);
    });

    test('clearSectionFocus resets state when not suspended', () {
      final controller = container.read(
        windowFocusControllerProvider(windowId).notifier,
      );

      controller.setSectionFocus(sectionId: 'section_a', paneId: 'pane_a');
      controller.clearSectionFocus('section_a');

      final state = container.read(windowFocusControllerProvider(windowId));
      expect(state.activeSectionId, isNull);
      expect(state.activePaneId, isNull);
      expect(state.isSuspended, isFalse);
    });

    test('suspendForOverlay marks state as suspended', () {
      final controller = container.read(
        windowFocusControllerProvider(windowId).notifier,
      );

      controller.setSectionFocus(sectionId: 'section_a', paneId: 'pane_a');
      controller.suspendForOverlay('overlay_a');

      final state = container.read(windowFocusControllerProvider(windowId));
      expect(state.overlayCapture, 'overlay_a');
      expect(state.isSuspended, isTrue);
      expect(state.hasFocus, isFalse);
    });

    test('resumeFromOverlay clears suspension when ids match', () {
      final controller = container.read(
        windowFocusControllerProvider(windowId).notifier,
      );

      controller.setSectionFocus(sectionId: 'section_a', paneId: 'pane_a');
      controller.suspendForOverlay('overlay_a');
      controller.resumeFromOverlay('overlay_a');

      final state = container.read(windowFocusControllerProvider(windowId));
      expect(state.overlayCapture, isNull);
      expect(state.isSuspended, isFalse);
      expect(state.activeSectionId, 'section_a');
    });

    test('clearSectionFocus ignored while overlay suspended', () {
      final controller = container.read(
        windowFocusControllerProvider(windowId).notifier,
      );

      controller.setSectionFocus(sectionId: 'section_a', paneId: 'pane_a');
      controller.suspendForOverlay('overlay_a');
      controller.clearSectionFocus('section_a');

      final state = container.read(windowFocusControllerProvider(windowId));
      expect(state.activeSectionId, 'section_a');
      expect(state.activePaneId, 'pane_a');
      expect(state.isSuspended, isTrue);
    });
  });
}
