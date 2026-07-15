# aware_pane Changelog

## 0.2.0
- Added `PaneSelectionPayload` metadata contract and updated `PaneSelectionHandler` signatures.
- Exposed manifest adapter utilities and bridge tests; strengthened ensure/save flow coverage.
- Exported the new selection payload from `aware_pane.dart` and refreshed unit tests.
- Introduced `PaneSelectionMetadataBuilder` / `PaneManifestMetadataBuilder` helpers and associated tests.
- Added `PaneBus.fromEventBus` and the `AwareMessagingPaneDispatcher` so hosts can route pane events through `aware_messaging`.
- Extended `PanePresenterHostAdapters` to support conversation overlays
  (`buildConversationOverlays`), enabling hosts to register overlays on the
  conversation window (used by aware_terminal integration).
- Presenter defaults and pane IDs moved to the host application; `aware_pane`
  now exposes only pane infrastructure types.

## 0.1.0
- Initial extraction of pane registry, context, presenters, and messaging helpers from the Studio app.
