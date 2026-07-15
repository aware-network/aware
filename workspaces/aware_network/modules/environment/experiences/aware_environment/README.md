# Aware Environments Experience

This directory is the Environment module-owned `aware-environment-experience` experience package.

Current scope:

- canonical `aware.experience.toml` + `.aware` experience source
- versioned Environment navigator, Process workspace, and Thread layout view contracts
- generated Dart/Python view DTO packages under `languages/<lang>/aware_environment_experience`
- bounded `environments.*` section-graph-binding proofs over the canonical Orchestrator Environment rail
- SDK-owned view-state providers in `aware-environment-sdk`

Canonical direction:

- Environment is the first real OS navigation surface after Control and Identity admission.
- Interface shells resolve Environment -> Process -> Thread -> Layout from typed host/view truth, not shell-local inference.
- Conversation, Feed, and Issue remain product panes mounted by layout/attention selection after Environment resolution.
- `aware-environment-sdk` owns the runtime view-state provider for Environment views while the Environment service remains the source for topology, status, and graph operation routing.
