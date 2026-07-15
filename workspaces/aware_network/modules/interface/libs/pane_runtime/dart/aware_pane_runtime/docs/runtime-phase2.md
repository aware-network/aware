---
id: 7b021f42-20a0-4fe4-845f-b7f208e4cf5e
title: "aware_pane_runtime Phase 2 Design"
slug: aware-pane-runtime-phase2
description: "Modular runtime plan for cross-host pane infrastructure"
created: "2025-10-21T19:00:21Z"
updated: "2025-10-21T19:00:21Z"
author:
  agent: "Codex"
  process: "app-panes-audit"
  thread: "Codex / conversation-audit"
summary: "Defines the API surface and migration steps for extracting Studio pane runtime logic into the new aware_pane_runtime package without breaking existing Studio behaviour."
---

## Goals
- Provide a reusable runtime layer (`aware_pane_runtime`) that hosts (Studio, CLI, external UIs) can adopt without inheriting Studio-specific code.
- Leave Studio behaviour unchanged during migration by mirroring existing logic first, then gradually swapping dependencies.
- Clarify lifecycle responsibilities and APIs so future hosts can register panes deterministically.

## Scope
1. Runtime package delivers:
   - Host-defined `PaneKey` strings (no shared enum).
   - `PaneRegistry` with module-based registration API.
   - Manifest/materialisation/delta/selection infrastructure (adapters, providers, runtime contexts).
   - Pane agreements/capabilities contract.
2. Studio transitions to the runtime package in phases:
   - Phase A: mirror code (current state).
   - Phase B: define `PaneModule` & `PaneRuntime.initialize` APIs.
   - Phase C: refactor Studio registrars to use modules & call runtime initialize.
   - Phase D: remove duplicated runtime files from Studio once validated.
3. Out of scope (for now): UI components, window presenters, pane card specs—they remain host-owned.

## Proposed Runtime API
```dart
class PaneModule {
  PaneKey kind;
  PaneFactory factory;
  runtime.PaneCapabilities capabilities;
  PaneAgreement? agreement;
  PaneManifestAdapter? manifestAdapter;
  PaneManifestDecoder? manifestDecoder;
  PaneSelectionHandler? selectionHandler;
  PaneDeltaWatcher? deltaWatcher;
  PaneOpgBinding? opgBinding;
  PaneMaterialisationConfig? materialisation;
  PaneFunctionProvider? functions;
}

class PaneRuntime {
  PaneRuntime({required PaneRegistry registry});

  void initialize({
    required List<PaneModule> modules,
    required ProviderReader providerReader,
    required PaneManifestRegistrations manifestRegistrations,
  });
}
```
- `PaneModule` encapsulates all per-pane registrations.
- `PaneRuntime.initialize` executes a deterministic sequence:
  1. Register manifest adapters/decoders.
  2. Register selection handlers and delta watchers.
  3. Register materialisation/function providers.
  4. Register pane factories & agreements.
  5. Call `registry.markReady()`.
- Additional structs (`PaneMaterialisationConfig`, `PaneFunctionProvider`) capture storage-specific providers.

## Migration Plan
### Phase B – API definition
- Implement `PaneModule`, `PaneRuntime`, and supporting structs in the runtime package.
- Port existing lifecycle guards/logging to runtime.
- Expose helper for hosts to convert old registration flow into modules.

### Phase C – Studio integration (no behaviour change)
- Build module lists for existing panes (conversation/task/repository/etc.).
- Update `PaneInitializationService` to compose modules and call `PaneRuntime.initialize`.
- Keep legacy registration path behind a flag for fallback during rollout.

### Phase D – Cleanup
- Remove duplicated runtime files from Studio (`pane_manifest_*`, `pane_delta_watcher.dart`, etc.).
- Avoid any shared `PaneKind` enumeration; keep pane identifiers host-defined (`PaneKey` strings).
- Document runtime usage in package README/docs with lifecycle diagrams (migrate `pane-registry-lifecycle.md`).

## Risks & Mitigations
- **Lifecycle mismatch:** Guard rails & logging already in place; during integration keep fallback path until confident.
- **Feature-specific logic:** Some runtime files still reference conversation/task behaviour. Shift these into modules (e.g., conversation functions stay with module, not runtime core).
- **ID conflicts:** Host-defined keys can drift; prefer canonical `PaneKey` strings derived from `.aware` or kernel metadata.

## Deliverables
- Runtime package updated with `PaneModule`/`PaneRuntime` APIs + docs (`packages/aware_pane_runtime/docs/`).
- Studio integration PR demonstrating module-based initialization with feature-by-feature roll-out.
- Lifecycle doc updated to reference runtime package and module usage.

## Next Steps
1. Implement runtime API skeleton (`PaneModule`, `PaneRuntime.initialize`).
2. Port manifest/materialisation registries to runtime package (removing direct Studio imports).
3. Prepare Studio modules for conversation/repository/task panes.
4. Test Studio boot with runtime initialization behind a feature flag.
