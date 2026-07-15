---
id: aware-pane-runtime-projection-views
code_path:
  - lib/src/domain/service/pane_registry.dart
test_path: []
code_sha: TBD
test_sha: TBD
last_validated: "2026-02-03T00:00:00Z"
---

# Projection Views (OPGI + ObjectProjectionGraphView) — Pane Standards

Status note:

- this document is the active v0 compatibility contract for the current Flutter/Studio pane rail
- it is not the final canonical mount contract
- the canonical target now moves pane mounting behind Interface runtime descriptors, package-owned pane identity, and generated Dart registrar bundling on a parallel rail

This doc defines the active v0 representation-side architecture for Aware modules and where the current compatibility contracts live.

## Why this exists

We want the Interface app to be a small, stable shell:
- it owns window chrome + layout,
- it mounts module panes via the Window→Pane system,
- and it **does not** own domain routing logic.

So the current v0 rules for how panes map to canonical graph navigation live in:
- `aware_pane_runtime` (this package),
- plus module-owned registrars in `modules/**/representation`.

The target architecture is now different:

- Interface runtime owns semantic pane descriptors
- pane packages own registrar linkage
- generated Dart registrar bundles bridge package manifests into AOT-safe imports
- the app shell stops being the owner of pane registration policy

## Canonical mapping (graph → UI)

- **OPGI (ObjectProjectionGraphIdentity)** is the stable identity for a projection family (what can be shown).
- **ObjectProjectionGraphView.view_key** selects which view/step to render inside that projection family (what is shown).
- **ObjectProjectionGraphView.kind** declares whether the view is:
  - `construct` (no branch state required; gate-friendly), or
  - `instance` (requires branch state / materialized OIGB).
- **Pane** is a renderer for `(OPGI.key, view_key)`.

This aligns with the attention rail:

`Window → FocusScope → Focus → (OPGI xor OIGB)`

and the co-navigation granularity:

`FocusScope.view_id → ObjectProjectionGraphView`

## Folder architecture (module representation)

Module representation packages should be organized by **projection**, not by “feature vibes”.

Recommended layout:

```
<module>/representation/lib/src/
  projections/
    <projection_name>/
      <projection_name>_pane.dart
      views/
        <view_name>.dart
      <projection_name>_routes.dart
      <projection_name>_view_registry.dart
    _shared/
      projection_view_contract.dart
      projection_view_resolver.dart
```

### Hard rules

1. **One pane per projection**: `<projection>_pane.dart` is the single renderer for that projection family.
2. **Views are projection-scoped**: `views/<view>.dart` contains only view widgets for that projection.
3. **No cross-projection imports** except `projections/_shared/**`.
4. **The only routing inputs are**:
   - resolved projection identity key (`ObjectProjectionGraphIdentity.key`),
   - resolved view key (`ObjectProjectionGraphView.view_key`),
   - materialized state (when Focus targets an OIGB),
   - optional capabilities/schema version (for compatibility gating).

## Host/runtime contract (v0 → v1)

### v0 (host-owned view bindings)

In v0, the host (Studio) mounts panes by consulting the module registrations in `PaneRegistry`:

- Modules bind a pane to a projection lane by name:
  - `PaneRegistry.registerOpgBinding(PaneKey, PaneOpgBinding(opgName: ...))`
- Modules bind a pane to a canonical projection view (gate or within-branch view):
  - `PaneRegistry.registerOpgViewBinding(PaneKey, PaneOpgViewBinding(opgIdentityKey: ..., viewKey: ...))`

The host must:
1) resolve `(opgIdentityKey, viewKey)` from the active window’s FocusScope, and
2) select a pane by matching those view bindings (no heuristics).

#### v0 additional requirements (to stay deterministic)

- **Default view per pane:** modules should register a deterministic default view binding via:
  - `PaneRegistry.registerDefaultOpgViewBinding(PaneKey, PaneOpgViewBinding)`
  - Environment uses this when opening a branch (the OS must never guess).

- **View-id resolution:** `FocusScope.view_id` is a UUID (not a string key). Until cross-OPG
  portal edges are guaranteed to materialize `FocusScope.view` directly, the host resolves
  the active selection by matching `view_id` against its registered `PaneOpgViewBinding`s
  using stable-id derivations (`GraphIdentityIdDerivation.stableObjectProjectionGraphViewId`).

- **View seeding (deprecated):** older environments relied on host-side creation via
  `ObjectProjectionGraphIdentity.create_view(...)`. This is no longer the canonical path and
  should be treated as legacy-only during migration.

**Compiler-owned identities (hard rule):**
- The Interface must **never** create `ObjectConfigGraphIdentity` or `ObjectProjectionGraphIdentity`.
- If the OPGI lane is missing, the correct behavior is to fail fast and re-run compilation/seed.

### v1 (bundle-provided views)

In v1+, available views should be seeded/materialized by the environment (compile-time), so:
- the host can list available views,
- modules can rely less on ad-hoc view registration,
- and view compatibility becomes part of environment composition.

Canonical rule (v1+):
- The Interface host must not create projection views at runtime.
- Missing views are a compile/seed failure; re-run compilation (emit seed commits) rather than minting views.

## Deterministic fallbacks (required)

If a FocusScope selects a view that the host cannot render:
- mount a deterministic “Unsupported view” fallback pane,
- show the missing `(opgIdentityKey, viewKey)` pair,
- do not silently substitute another view.

## Naming conventions

- `ObjectProjectionGraphIdentity.key` should follow: `{ocg_key}:{projection_name}`.
- `view_key` is scoped within the projection family; prefer dotted keys:
  - `onboarding.welcome`
  - `profile.home`
  - `connections.list`

Avoid prefixing view keys with the projection name (redundant with OPGI).

For multi-step onboarding flows, prefer explicit, descriptive tokens (avoid encoding policy like "required"):
- `onboarding.profile.photo-name`

## Host chrome (context header)

The Interface host may render shell chrome (e.g. a top context header and orchestration affordances)
outside the pane surface. This must not interfere with the deterministic graph→view→pane contract above.

Pane rule:
- panes must not assume full-screen space; treat their surface as constrained by the host.
