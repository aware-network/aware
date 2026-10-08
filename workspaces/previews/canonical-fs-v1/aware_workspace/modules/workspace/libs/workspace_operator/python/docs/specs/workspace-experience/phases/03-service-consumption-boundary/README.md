# Phase 03 — Service Consumption Boundary

State: `Planned`
Owner: `codex-019cd2a5-c937-72a2-8675-8042b4bfdfaf`

## Gate

Structure workspace service can expose workspace setup through a stable backend/provider contract over workspace-operator outputs without semantic Python-package coupling.

## Goal

Lock the boundary so workspace-operator stays the owner of seed/profile/experience semantics while Structure workspace service owns the operator-facing setup boundary and consumes only the outputs it needs for setup plus topology and compile/test/diagnostic orchestration.

## Scope In

- provider/artifact contract between workspace-operator and Structure workspace service
- setup backend/provider boundary for Workspace service
- ownership split documentation
- consumer-side insertion points for workspace-service features

## Scope Out

- direct runtime imports from Structure into `aware_workspace_operator`
- Structure service implementation details beyond the consumed contract
- broader service transport freeze

## Acceptance (Gate Checklist)

- [ ] The interop contract is artifact-based and explicit.
- [ ] Workspace setup can be exposed by Structure as a service feature while backend semantics remain in workspace-operator.
- [ ] Structure workspace service does not claim workspace-operator seed/profile ownership.
- [ ] workspace-operator does not claim Structure compile/test/diagnostic ownership.

## Iterations

- `TBD`
