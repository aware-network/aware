## 0.4.0
- Added `WindowFocusController` and `WindowSectionFocusBinding` so focus state (active pane, overlay suspension) is tracked centrally and surfaced via pane events.
- Introduced a shared shortcut system: `WindowShortcutRegistry`, `WindowShortcutScope`, and pane shortcut contributors on `WindowPanePresenter` for scope-aware bindings (with diagnostics available via the registry state).
- Exported new focus/shortcut APIs and updated Studio host wiring; expanded tests covering focus lifecycle, registry activation, and window-level shortcut behaviour.

## 0.3.0
- Moved `WorkspacePresets` and pane-specific defaults out of the package; host apps now provide their own preset catalogs and header metadata.
- Simplified the fallback header builder to derive titles purely from pane identifiers (no built-in icons or policies).
- Updated documentation and tests to use package-local fixtures, keeping examples pane-agnostic.

## 0.2.0
- Removed the `PaneType` enum; `WindowSectionConfig` now uses opaque `paneId` strings so window shell stays client-agnostic.
- Added `WindowPanePresenter` + registry APIs (including overlay contributor support) and a presenter scope helper for host registration.
- Added overlay scrim and divider builder extension points on `Window`/`WindowOverlayHost`.
- Refactored layout sizing to use flex-based sections; fixed collapse state toggling and overlay header updates.
- Expanded test suite (overlay behaviour, presenter fallback/overlays, header policies, palette overrides, collapse handling).
- Documented usage in README; raised SDK minimum to Dart 3.8.

## 0.1.0
- Initial package skeleton extracted from the app: window models, controllers, and base widgets.
