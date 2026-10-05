# Versioned agent experience

Authored template: [agent-fs/v1/AGENTS.md.in](agent-fs/v1/AGENTS.md.in).
Identity/version: **`aware.agent.fs.v1` / 1.0.0**; selected authority: filesystem.
The [contract manifest](agent-fs/v1/contract.json) declares its bootstrap and
modular operational, Issue and alignment docs.

The same identify → explicit Issue → preserve work → exact scope → verify →
commit → close/handoff discipline is used internally. This consumer contract
exposes only commands actually shipped: `aware` and its existing SDK/provider
operations. It does not copy resident `aware-dev` commands or materialization
requirements into a customer repository.

`render_agent_contract.py` projects these templates into packaged CLI assets and
this public repository. Installed `aware init` renders them using the actual
selected executable, with source/rendered hashes in `.aware/agent-bootstrap.json`.
`aware contract` reports the installed version and source template hashes.
Those are provenance observations, not Identity/WorkContext or admission authority.

## Compatibility and upgrade policy

- Template/contract version, CLI distribution version and record/profile versions
  are separate axes. A CLI update does not silently promote filesystem authority.
- Preserve published template bytes; substantive future changes require a new
  explicitly reviewed version and tests. Incompatible operational contracts get
  a separately declared major identity/profile instead of relabeling old behavior.
- Existing bootstrap manifests cause `init` to refuse, not overwrite or upgrade.
  Existing docs/AGENTS are preserved. An explicit managed link is additive only;
  customer conflicts and documentation merges remain visible integration work.
- No automatic upgrade command is claimed in this release. Review a new template
  and exact changes before a separately authorized migration.
- Service/API and ActorWorld are later admitted surfaces, not prerequisites or
  automatic fallbacks. No service engine or generated ontology is installed.

## Immediate product boundary

Existing committed Git repository → install → setup → real scoped agent task.
Repository creation/first-commit authority is **not shipped**. We will add a
supported owner-backed genesis operation separately rather than hiding raw Git
creation/commit behind a bootstrap workaround. No user must wait for that to
benefit from the existing-repository workflow today.
