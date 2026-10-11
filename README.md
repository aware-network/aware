# Aware

Coherent work between agents in your Git repository.

Aware provides shared protocols and tooling so agents can understand the same
work, make bounded changes and leave evidence another execution can continue
from. Issues organize work; Specifications describe its intended shape.
Coherence is the value, not a promise of faster agents or conflict-free swarms.

Aware's direction: Don't watch your agents. Watch your goals. See [aware.run](https://aware.run).

This initializer distribution is selected locally; public delivery is not yet
authorized. Instructions are frozen for this local candidate, pending independent
review. Use this reviewed checkout, not unchanged public main. See the
[exact instruction freeze](releases/canonical-initializer-fs-v1/INSTRUCTION-FREEZE.md).

## Understand the protocols

Read [coherence between agents](protocols/COHERENCE.md), [Issue coordination](protocols/issues/README.md),
[repository publication](protocols/repository/README.md) and [SPEC drafts](protocols/specification/README.md).
Understanding shared rules and admitting operations are different steps.

## Inspect terms and install once

Requires Linux x86-64, Git and an actual Python 3.12 interpreter. Before installing,
read [distribution terms and source](releases/canonical-initializer-fs-v1/README.md):
the complete LICENSE, NOTICE, corresponding source and upstream attachments
accompany this software. Six Code/Workspace wheels lack package-local legal
files; this delivery is accepted only as the complete envelope, not detached wheels.

From this reviewed checkout root:

```sh
set -eu
aware_parent="$(mktemp -d /tmp/aware-consumer.XXXXXXXX)"
aware_env="$aware_parent/env"
test ! -e "$aware_env"
test ! -L "$aware_env"
/usr/bin/python3.12 protocols/install.py \
  --python-executable /usr/bin/python3.12 --venv "$aware_env"
AWARE="$aware_env/bin/aware"
"$AWARE" --help
```

Choose your actual Python 3.12 executable explicitly. After acquisition,
installation is offline; no editable checkout or development source is needed.
The installer verifies and retains the whole envelope before delegating to the
unchanged payload installer. It prints the retained source/notice directory.
Do not overlay an old preview or silently replace an existing execution's CLI.
Installation does not initialize a repository or start a service.

## Initialize an explicit repository

Run inside your genuine supported harness, supplying its own unambiguous stable
execution identity. Do not fabricate or borrow session variables.
Set `aware_repo_root` to an explicit absolute target under an existing parent.
For a new repository, the target must be absent or empty:

```sh
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --format summary
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --apply --format json
```

Preview is default and has no source effects. For a new repository it returns
a Workspace preparation preview and prospective Protocol inputs, not two
admitted plans. Apply gets fresh Protocol admission after repository preparation.
For existing Git repositories omit `--create-repository`; existing guidance or
configuration refuses rather than being overwritten.

Init preserves both owners' receipts. By default it prepares Issue directories,
`aware.protocol.toml` and readable `AGENTS.md` guidance. It does not create a
seed commit, stage changes, add a remote, open an Issue, approve a document or
start a service. A late refusal may follow known creation: retain effects and
cleanup evidence; never retry automatically or assume rollback.

Read [initialization and its boundaries](protocols/INITIALIZATION.md), then
[the supported workflow](protocols/WORKFLOW.md). All commands use this one
installation: `aware issue`, `aware protocol` and `aware spec`.
Init starts with Issues; SPEC setup remains separately Issue-governed.
Automatic guard discovery and unassisted customer onboarding are still unproved.

## Source and distribution

- [Protocols](protocols/README.md): shared guidance and supported operation boundaries.
- [Workspace source](workspaces/README.md): one canonical copy selected by `portable_protocols`.
- [Complete distribution](releases/canonical-initializer-fs-v1/README.md): exact software, terms, notices and source.
- [External evaluations](protocols/evaluations/README.md): report observations, including blockers.
- [Contribution](CONTRIBUTING.md): retained contributor governance, distinct from customer initialization.
- [History](docs/HISTORY.md): pinned predecessors, not competing current source trees.

Source history and old README wording do not expand current capabilities.
Root contributor `AGENTS.md` and its selected command remain unchanged.
The generated customer guidance belongs to the original Protocol supplier;
this public tree does not replace its template.

Draft creation is not approval. Approved iterations, durable binding, Goals,
Service/API, native receiving and object/materialization routes are not offered
by this filesystem composition. Those lanes advance independently.
