# aware-experience

Runtime package for the `experience` module.

## Internal Supervisor

`aware_experience.supervisor` contains the internal always-on supervisor manager
model. It does not expose public API/SDK lifecycle operations. Sessions declare
feature needs through scoped leases, and Experience owns the worker execution and
health snapshots.

The first supported feature key is `reactivity_transition_dispatch`, which wraps
the existing Reactivity transition supervisor worker.

`aware_experience_service.session_feature_service` is the internal service
boundary for declaring, reading, and releasing session feature leases. It is not
a generated public Experience API/SDK surface.

The same internal boundary owns Experience session actor admission. Feature
ensure/release requires admitted actor evidence for the session scope; missing or
invalid actor context returns blocker evidence and does not start feature work.

Canonical module docs live in:

- `workspaces/aware_network/modules/experience/docs/README.md`
- `workspaces/aware_network/modules/experience/docs/authoring_contract.md`
- `workspaces/aware_network/modules/experience/docs/compile_runtime_contract.md`
