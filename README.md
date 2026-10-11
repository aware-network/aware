# Aware

Coherent work between agents in your Git repository.

Aware provides shared rules and tooling so agents can understand the same work,
make bounded changes and leave evidence another execution can continue from.
Issues organize work; Specifications describe its intended shape. Coherence is
the value, not a promise of faster agents or conflict-free swarms.

Aware's direction: Don't watch your agents. Watch your goals. See [aware.run](https://aware.run).

The reviewed Issue083 successor is selected locally; public delivery is not yet
authorized. Instructions are frozen locally, pending independent freeze review.
Use this reviewed checkout, not unchanged public main. The
[delivery pointer](releases/SELECTED.json) binds its exact whole envelope;
[instruction pins](releases/canonical-issue083-fs-v1/INSTRUCTIONS.json) bind the
customer guidance, not another package catalog. See
[local selection](releases/canonical-issue083-fs-v1/LOCAL-SELECTION.md) and
[freeze evidence](releases/canonical-issue083-fs-v1/INSTRUCTION-FREEZE.md).
Do not overlay installations or migrate contributor tools. Publication remains
separately authorized.

## Understand the protocols

Read [coherence](protocols/COHERENCE.md), [Issue coordination](protocols/issues/README.md),
[repository publication](protocols/repository/README.md) and [SPEC drafts](protocols/specification/README.md).
Readable guidance explains shared rules; tooling applies separately admitted
operations. Installation, repository configuration and service startup are
different decisions. This filesystem composition does not start a service.

## Inspect terms and install once

Requires Linux x86-64, Git and an actual Python 3.12 interpreter. Before installing,
read [distribution terms and source](releases/canonical-issue083-fs-v1/README.md).
Keep complete LICENSE, NOTICE, corresponding source, upstream attachments and
the raw audit with the software. Six Code/Workspace wheels lack local legal
files; acceptance is for the complete envelope, not detached wheels or a stripped
inner bundle. The reviewed source-derived jsonschema recipe and publisher URL/hash
are attached; its original source archive is not.

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

Choose Python 3.12 explicitly. After acquisition installation is offline; no
editable checkout or development source is needed. The existing installer
verifies and retains the whole envelope before delegating to its payload's
installer. It prints the full retained source/notice directory. Keep it.
Reuse refuses; do not silently replace another execution's command.

## Initialize an explicit repository

Use your genuine harness with exactly one nonblank `CODEX_THREAD_ID` or
`CLAUDE_CODE_SESSION_ID`; do not fabricate or borrow session identities.
Set `aware_repo_root` to an explicit absolute target under an existing parent.
A new target must be absent or empty:

```sh
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --format summary
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --apply --format json
```

Preview has no effects: it returns a Workspace preparation preview and prospective
Protocol inputs (`prospective_only`, `completion_verified=false`), not two admitted
plans. Apply obtains fresh Protocol admission after repository preparation.
For existing Git repositories omit `--create-repository`. Existing configuration
or guidance refuses rather than being overwritten.

Init preserves both owner receipts and normally prepares Issue directories,
`aware.protocol.toml` and readable `AGENTS.md`. Read that guidance. It does not
open an Issue, create a seed commit, stage files, add a remote, approve a document
or start a service. Late refusals may follow known creation; retain effects,
completion and cleanup evidence. Nonzero exit is not rollback or permission to retry.

## Admit your first Issue

`--issue-ref` is `fb/YYYY-MM-DD/lowercase-hyphenated-slug`, for example
`fb/2026-10-11/json-checker-draft`, not a UUID, title or Markdown path. With the
default Issue root its record is
`docs/issues/2026/10/11/fb-2026-10-11-json-checker-draft.md`; that path belongs in
scope, not in `--issue-ref`.

Follow [the complete first-Issue example](protocols/issues/FIRST-ISSUE.md), choosing
your outcome and scope first. It creates a snapshot, reads the current Issue,
binds scope and starts progress with separately observed Issue-byte guards.
Missing identity, invalid references and stale guards refuse; do not guess,
silently refresh or repeat a failed mutation.

Then use [the workflow](protocols/WORKFLOW.md) for Issue-governed SPEC setup,
typed draft preparation, preview/apply and observation. All families use this
one installation: `aware issue`, `aware protocol`, `aware spec`. Issue guards,
exact Protocol-manifest byte guards and draft-input guards identify different
artifacts; normalized manifest semantics are not byte currentness. Manifest
locators are repository-relative; explicit absolute snapshot inputs avoid cwd
ambiguity. Automatic guard discovery remains unfinished.

## Publish and preserve evidence

Establish a local Git author separately from init. Dry-run the exact admitted
paths before apply. `aware issue publish-close` pairs publication and closeout in
one live owner lifetime, but is not atomic. Preserve both receipts and any
reference-update, index, closure, cleanup or uncertain-effects evidence.
A later refusal does not undo a known commit. A saved Git receipt cannot recreate
the live capability required by standalone `close`; do not republish to regain
authority. Durable cross-execution closeout migration is not supplied here.

See [publication boundaries](protocols/repository/README.md) and
[initialization](protocols/INITIALIZATION.md). Scope is not a reservation;
preserve foreign work. Observed currentness is not every-write detection, and
cooperative descriptor confinement is not continuous confinement.

## Source and next steps

[Workspace source](workspaces/README.md) is one canonical copy selected by
`portable_protocols`, not another package catalog. [Complete carriage](releases/canonical-issue083-fs-v1/README.md)
and [review status](releases/canonical-issue083-fs-v1/REVIEW-STATUS.md) retain terms,
sources, all twelve raw fixture findings and conservative native coverage.
Historical source READMEs and pending labels do not expand current capabilities.
[Contributor governance](CONTRIBUTING.md) and root `AGENTS.md` remain unchanged;
the customer guidance template belongs to the original Protocol supplier.

Fresh unassisted onboarding follows qualified delivery; these scripted proofs do
not establish it. Report observations through [evaluations](protocols/evaluations/README.md).
Issues come first, then Specifications, Goals and a shared map. Draft creation is
not approval: approved iterations, durable binding, Goal writers, Service/API,
native receiving and object/materialization routes are not offered by this
filesystem composition. Those lanes advance independently.
