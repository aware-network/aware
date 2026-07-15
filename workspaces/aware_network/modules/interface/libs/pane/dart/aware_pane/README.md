# aware_pane

Shared pane runtime utilities for Aware apps. The package provides a registry, manifest/selection contracts, and presenter helpers that let host applications render panes without inheriting Studio-specific code.

## Contract (Window → Pane → Widget)

- **Window** (`aware_windows`) owns layout, overlays, focus, and the persistent “world” background.
- **Pane** (`aware_pane` + `aware_pane_runtime`) is a module-owned projection surface; it declares capabilities + selection contracts and renders glass widgets.
- **Widgets** (`aware_widgets`) provide the shared glass materials + physics (`GlassLayout`, `GlassFieldScope`).

Panes may provide **world hints** via `PaneCapabilities.worldHint` (mood/scrim/focus), but must not replace backgrounds.

Canonical contract: `docs/architecture/interface-window-world.md`.
Glass system directives: `docs/architecture/interface-glass-system.md`.

### World hints (v0)

`PaneWorldHint` fields are intentionally small and declarative:

- `mood`: `calm | focused | charged | welcome`
- `scrimStrength`: 0..1
- `focusPoint`: normalized 0..1 window space
- `graphDensity`: 0..1
- `accent`: `neutral | networkGreen | identityPurple`
- `energy`: 0..1

## Features
- Pane registry with capability metadata, manifest adapters, and selection handlers.
- Metadata builders (`PaneSelectionMetadataBuilder`, `PaneManifestMetadataBuilder`) so hosts emit consistent IDs and thread context.
- Presenter hooks that work with `aware_windows` but stay agnostic of host widgets/state management (only Flutter + Riverpod).
- Lightweight testing surface: helper APIs for dispatching selection/manifest events in unit tests.

## Quick Start
```dart
final registry = PaneRegistry();

registry.registerPane(
  key: 'repository',
  factory: (context) => RepositoryPane(context),
  capabilities: const PaneCapabilities(
    layout: PaneLayoutPreferences(preferredWidth: 400),
  ),
);

registry.registerSelectionHandler(
  RepositoryPaneSelectionHandler(),
);

registry.registerManifestAdapter(RepositoryPaneManifestAdapter());

// Wire the pane bus to aware_messaging's EventBus
final eventBus = EventBus();
final paneBus = PaneBus.fromEventBus(eventBus);
paneBus.emit(RepositoryPaneInitializedEvent());
```

Populate selection metadata using the shared helper:

```dart
final metadata = PaneSelectionMetadataBuilder.compose(
  threadId: threadId,
  processId: processId,
  branchId: branchId,
  origin: 'thread_branch_list',
);

final payload = PaneSelectionPayload(
  paneKey: paneKind.name,
  payload: paneContextPayload,
  parameters: {'branchId': branchId},
  metadata: metadata,
);

await handler.handle(read: ref.read, selection: payload);
```

## Testing
Use the exposed helpers to drive runtime behaviour in tests:

```dart
final registry = PaneRegistry();
registry.registerSelectionHandler(handler);

await registry.dispatchSelectionForTest(
  kind: PaneKind.repository,
  context: PaneContext(paneKey: 'repository'),
  payload: somePayload,
  metadata: PaneSelectionMetadataBuilder.compose(origin: 'test'),
);
```

Run the package tests from the repository root:

```bash
cd apps/interface_flutter/aware_pane
flutter test
```

## Changelog
See [CHANGELOG.md](CHANGELOG.md) for version history.
