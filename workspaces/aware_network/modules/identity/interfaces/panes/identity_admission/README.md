# Identity Admission Pane

Canonical pane package for Interface-hosted Identity admission and actor
readiness actions. Renderers expose these actions through mounted pane
descriptors; host implementations call the Identity API boundary.

`identity_admission.aware` owns the pane-local declarative render spec consumed
by Interface package generation. The Interface compiler enriches the authored
render declaration with canonical pane/view/state/action IDs before emitting
`InterfacePackageRuntime.renderSpecs`.

This pane intentionally has no Dart pane package. The Flutter Shell renders the
native `PaneRenderSpec` via `PaneRenderSpecWidget`; Dart pane package fallback is
not part of the Identity admission rail.
