# Neutral Agent CLI composition

Source preview **0.2.0a1** supplies one `aware` entrance over the accepted family
registrars and Kernel's command runtime. It is a composition library with a CLI
entrypoint, not a new Agent SDK, evaluator or authority provider.

```text
aware issue <existing Issue leaf> [original arguments]
aware protocol admit [original arguments]
aware protocol setup-specification [original arguments]
aware spec observe [original arguments]
aware spec iteration-identity [original arguments]
aware spec create-draft [original arguments]
```

Run `aware --help`, then `aware FAMILY --help` or
`aware FAMILY LEAF --help`. Only the selected family is imported. Each original
registrar supplies its own flags, path meanings, digest guards and result format.
Publication is `aware issue commit-workspace`, the existing Issue SDK operation;
there is no new Repository commit implementation or automatic Issue selection.
SPEC setup previews by default; setup and draft effects require explicit apply
and fresh owner admission. Observation does not approve iterations or work.

This is a breaking successor to public a6's `aware-agent-cli 0.1.0a6`, retaining
the distribution, import namespace and executable identity while moving its
single current authoring home to this Agent library. The old public snapshot
remains historical and unchanged. **This is not an in-place a6 upgrade.**
The first source slice does not carry a6's `init`, `contract`, repository-create
or bootstrap/template helpers. It neither copies those helpers nor claims their
migration is complete. Tooling-created input repositories/manifests remain a
separate prerequisite until their owning composition is qualified.

Package membership comes from the existing `portable_protocols` checkout
profile, via Agent's module-owned `agent_cli` Code entry and ordinary dependency
metadata. It does not select the full Agent module/Workspace, import Agent
ontology or require its Service-facing SDK. `aware.protocol.toml` configures
customer records and authority; it does not select software packages.

Missing registrar exports refuse before operation dispatch, without another
environment, PATH discovery, raw writer or Service/FS fallback. Generic context
is not execution identity, Issue admission or authorization. The composition
does not refresh guards or retry a failed publication. Family diagnostics and
unknown/applied effect evidence remain unchanged.

Source tests and canonical capture are distinct from a qualified installed
bundle. Do not change a repository's Environment-selected operational CLI or
overlay an evaluated a6 environment based on this source preview. Installation,
source/notice clearance, customer onboarding and publication follow separately.
