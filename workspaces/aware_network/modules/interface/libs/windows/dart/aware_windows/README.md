# aware_windows

Reusable window and overlay primitives shared across Aware desktop and web clients.

## Features
- Declarative `WindowConfig` / `WindowSectionConfig` models with Freezed serialization.
- Section, header, palette, and overlay builders so host apps inject their own UI.
- Built-in overlay registry + header controller with optional scrim builder overrides.
- Divider/resize handlers with a new `dividerBuilder` hook for custom styling.
- Presenter diagnostics that surface duplicate registrations via `WindowPaneRegistry.takeDiagnostics()`.

## Contract (Window → Pane → Widget)

The Interface app follows **One Window = One World**:

- A window host owns a **persistent background scene** (“world”) and shared physics.
- Panes/widgets recompose **on top** as glass surfaces; backgrounds do not hard-swap per screen.

Canonical contract: `docs/architecture/interface-window-world.md`.
Glass system directives: `docs/architecture/interface-glass-system.md`.

### `WindowWorld`

Use `WindowWorld` to mount a background once and render your window content above it:

```dart
return WindowWorld(
  windowId: 'aware_root',
  backgroundBuilder: (context, ref, windowId, hint) => const MyBackground(),
  child: Window(config: myConfig),
);
```

`WindowWorldHint` (per window) provides stable tuning knobs:

- `mood`: `calm | focused | charged | welcome`
- `scrimStrength`: 0..1 (defaults to a black scrim when non-zero)
- `focusPoint`: normalized 0..1 window space
- `graphDensity`: 0..1
- `accent`: `neutral | networkGreen | identityPurple`
- `energy`: 0..1

## Quick Start
```dart
final window = Window(
  config: const WindowConfig(
    id: 'workspace',
    name: 'Workspace',
    mode: WindowLayoutMode.horizontal,
    version: 1,
    sections: [
      WindowSectionConfig(
        id: 'process',
        paneId: 'process',
        flex: 0.25,
      ),
      WindowSectionConfig(
        id: 'conversation',
        paneId: 'conversation',
        flex: 0.75,
      ),
    ],
  ),
  sectionBuilder: (context, ref, section, headerArgs) => MyPane(section),
  headerBuilder: (section) => myHeaderResolver(section),
  paletteBuilder: (theme) => WindowPalette.fromTheme(theme),
  overlayScrimBuilder: (context, ref, descriptor, dismiss) => GestureDetector(
    onTap: dismiss,
    child: Container(color: Colors.black38),
  ),
  dividerBuilder: (context, isVertical, onDrag, palette) => WindowDivider(
    isVertical: isVertical,
    onDrag: onDrag,
    borderColor: palette.border,
  ),
);

// Or register presenters once and omit section/header builders.
final presenter = WindowPanePresenter(
  paneId: 'process',
  builder: (context, ref, config, headerArgs) => MyPane(config),
  header: (config) => const WindowPaneHeaderData(title: 'Process'),
  overlays: (ref, config, headerArgs) => [
    WindowOverlayDescriptor(
      overlayId: 'process_overlay',
      windowId: headerArgs.windowId,
      builder: (_, __, ___) => const SizedBox.shrink(),
    ),
  ],
);

return ProviderScope(
  child: WindowPanePresenterScope(
    presenters: [presenter],
    child: const MaterialApp(home: MyWindowShell()),
  ),
);
```

### Presenter diagnostics
During development you can inspect the registry for warnings (such as duplicate presenter IDs):

```dart
final container = ProviderScope.containerOf(context);
final registry = container.read(windowPaneRegistryProvider);
for (final message in registry.takeDiagnostics()) {
  debugPrint('aware_windows warning: $message');
}
```

Diagnostics are automatically emitted in debug builds when duplicates are detected.

## Testing
Run the package tests from the repository root:

```bash
cd apps/interface_flutter/aware_windows
flutter test
```

## Changelog
See [CHANGELOG.md](CHANGELOG.md) for version history.
