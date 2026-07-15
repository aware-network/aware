# aware_pane_runtime

Module-driven pane runtime for AWARE Studio.

This package layers on top of `aware_pane`:
- `aware_pane` provides the stable host-facing contracts (capabilities, selection payloads, messaging).
- `aware_pane_runtime` adds module-first concepts (host-defined `PaneKey` strings, OPG bindings, manifest/selection/delta helpers).

Canonical contract: `docs/architecture/interface-window-world.md`.
Glass system directives: `docs/architecture/interface-glass-system.md`.
Projection/view standards: `apps/interface_flutter/aware_pane_runtime/docs/projection-views.md`.

## Status
- v0 runtime; APIs may evolve, but it is the canonical bridge for **module-owned panes**.
- Designed to keep the Studio shell thin: modules register panes + OPG bindings; the host composes layout only.

## World Hints (WindowWorld)
Modules can influence the persistent `WindowWorld` (background + scrims) without owning any fullscreen background by declaring a
`PaneCapabilities.worldHint` for each pane kind.

The host/runtime is responsible for mapping the active pane’s `PaneWorldHint` → `WindowWorldHint` (a *request*, interpreted by
the window’s world controller).

## Getting Started
```
flutter pub get
```
