# Aware Control Experience

Canonical bootstrap experience package for the core Interface control surface.

`aware_control` is intentionally small. It gives Interface packages stable
projection views for admission, Hub package selection, Workspace revision
selection, Interface mount status, and local node/session status without
introducing host-local action shortcuts.

## Programs

- `aware_control:EnsureBootInterfaceGraph` owns the first-frame Interface boot
  program for Aware Control. Program identity is semantic and unversioned;
  evolution is carried by committed `ProgramConfig` / `ProgramImpl` history.
- `modules/interface/experience/default` is compatibility-only while legacy
  `interface:EnsureBootInterfaceGraph_v0` callers are migrated to the committed
  `run_program` rail.
