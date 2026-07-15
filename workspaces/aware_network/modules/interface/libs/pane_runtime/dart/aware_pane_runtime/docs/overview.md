---
id: aware-pane-runtime-overview
code_path:
  - lib/aware_pane_runtime.dart
  - lib/src/pane_manifest_adapter.dart
test_path: []
code_sha: TBD
test_sha: TBD
last_validated: "2025-10-21T18:55:00Z"
---

# aware_pane_runtime Overview

This package mirrors Studio's pane runtime infrastructure (manifest adapters, delta watchers, pane kind definitions) so we can iteratively extract a host-agnostic runtime.

> **Status:** Prototype. No automated tests yet. APIs are unstable.

## Canonical goal

Make Studio a **thin shell**:
- Studio owns window chrome + layout only.
- Modules own all pane logic.
- Pane selection is derived from canonical graph navigation (`FocusScope` + views), not ad-hoc UI routing.

## Key contracts

### 1) One pane per projection

Each domain module should provide:
- a single projection pane (renderer) per projection family, and
- a set of projection-scoped views, selected by `ObjectProjectionGraphView.view_key`.

This aligns with the graph-level attention model:
- `ObjectProjectionGraphIdentity` (OPGI) = “what can be shown” (projection family)
- `ObjectProjectionGraphView.view_key` = “what is shown” (view/step within the family)
- `Pane` = renderer for `(OPGI.key, view_key)`

### 2) View bindings are explicit (no heuristics)

In v0, modules declare which views they can render using `PaneRegistry.registerOpgViewBinding(...)`.
The host resolves the current `(opgIdentityKey, viewKey)` from the active FocusScope and mounts the matching pane.

See: `apps/interface_flutter/aware_pane_runtime/docs/projection-views.md`.
