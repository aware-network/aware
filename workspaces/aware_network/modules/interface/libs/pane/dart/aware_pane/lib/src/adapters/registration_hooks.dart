import '../runtime/pane_registry.dart';

/// Utility mixin for modules that expose pane registration hooks.
mixin PaneRegistration {
  void registerPanes(PaneRegistry registry);
}

/// Helper to execute registration blocks with a registry instance.
typedef PaneRegistrationCallback = void Function(PaneRegistry registry);

void registerPanes(PaneRegistry registry, PaneRegistrationCallback callback) {
  callback(registry);
}
