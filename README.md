# Aware

Coherent work between agents in your Git repository.

Aware provides shared rules and tooling so agents can understand the same work,
make bounded changes and leave evidence another execution can continue from.
Issues coordinate work; Specifications describe its intended shape. Coherence
is the value, not a promise of faster agents or conflict-free swarms.

Aware's direction: Don't watch your agents. Watch your goals. See [aware.run](https://aware.run).

The reviewed draft-preparation successor is selected locally; public delivery is
not yet authorized. Instructions are frozen locally pending independent review.
Use this reviewed checkout, not
unchanged public main. The [delivery pointer](releases/SELECTED.json) binds the
exact whole envelope; [local selection](releases/canonical-draft-preparation-fs-v1/LOCAL-SELECTION.md)
records the review boundaries. Do not overlay installations or silently migrate
contributor commands. [Instruction pins](releases/canonical-draft-preparation-fs-v1/INSTRUCTIONS.json)
bind exact guidance/examples, not operation authority. Publication remains separately governed.

## Understand the shared rules

Read [coherence](protocols/COHERENCE.md), [Issues](protocols/issues/README.md),
[repository publication](protocols/repository/README.md) and [SPEC drafts](protocols/specification/README.md).
Readable protocols explain shared rules; tooling applies separately admitted
operations. Installing tooling, configuring a repository and starting a service
are different decisions. This filesystem composition starts no service.

## Inspect terms and install once

Requires Linux x86-64, Git and an actual Python 3.12 interpreter. Read
[complete distribution terms and source](releases/canonical-draft-preparation-fs-v1/README.md)
before installing. Keep LICENSE, NOTICE, corresponding source, upstream inputs
and raw audit with the software. Six package-local legal gaps remain unresolved;
detached wheels, stripped bundles and registry publication are unaccepted.

From this reviewed checkout root:

```sh
set -eu
aware_parent="$(mktemp -d /tmp/aware-consumer.XXXXXXXX)"
aware_init_env="$aware_parent/env"
test ! -e "$aware_init_env"
test ! -L "$aware_init_env"
/usr/bin/python3.12 protocols/install.py \
  --python-executable /usr/bin/python3.12 --venv "$aware_init_env"
AWARE="$aware_init_env/bin/aware"
"$AWARE" --help
```

After acquisition installation is offline. The original installer verifies and
retains the whole envelope, including terms and source, then delegates to its
payload installer. It returns the absolute `retained_source_and_notices` directory.
Keep it; set `aware_envelope_root` to that exact directory when using the typed
input example. Reuse refuses. No editable checkout or development source is needed.

## Initialize and admit work

Use your genuine harness with exactly one nonblank `CODEX_THREAD_ID` or
`CLAUDE_CODE_SESSION_ID`. Do not fabricate or borrow identities. Set
`aware_repo_root` to an explicit absolute target under an existing parent:

```sh
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --format summary
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --apply --format json
```

New targets must be absent or empty. For existing Git repositories omit
`--create-repository`. Preview provides a Workspace preparation preview and
prospective Protocol inputs, not two admitted plans. Apply obtains fresh Protocol
admission after repository preparation. Existing configuration/guidance refuses.
Init normally prepares Issue directories, `aware.protocol.toml` and readable
`AGENTS.md`; read them. It stages nothing, creates no seed commit or remote,
opens no Issue, approves no SPEC and starts no service. Preserve both owner
receipts, effects and cleanup. Nonzero exit is not rollback or permission to retry.

`--issue-ref` is `fb/YYYY-MM-DD/lowercase-hyphenated-slug`, not a UUID, title or
Markdown path. Follow [the first-Issue example](protocols/issues/FIRST-ISSUE.md)
to create the record, observe its exact bytes, bind scope and start progress.
Choose outcome and scope first. Missing identity, invalid references and stale
guards refuse; retain diagnostics instead of guessing or silently refreshing.

## Prepare, review, explicitly invoke

Use [the complete workflow](protocols/WORKFLOW.md) for Issue-governed SPEC setup,
typed snapshot input creation, draft preparation, preview/apply and observation.
No prequalified package or approved iteration is needed. All families use one
installation: `aware issue`, `aware protocol`, `aware spec`.

`aware spec prepare-draft` consumes explicit existing Issue, manifest, snapshot,
author and intent coordinates through the original SDKs. It labels the observed
Issue bytes, Protocol-manifest bytes and input bytes, shows intended members,
and prints separate original preview/apply commands carrying those guards.
Add `--format json` for full observations and exact vectors.

Preparation is read-only assistance, **not write authority or an atomic snapshot**.
Review the outcome, coordinates, owner/lifecycle/scope and intended members.
Explicitly invoke the original preview, review it, then separately decide on apply.
Use your installed absolute executable in place of the printed leading `aware`;
preserve every other argument and guard. Never `eval` the lines, automatically
execute vectors, refresh guards while copying or retry a mutation. Stale state
requires preparation and review again. Manifests are repository-relative;
explicit absolute snapshot paths avoid cwd ambiguity. The three guards identify
different bytes; normalized semantics cannot replace exact-byte currentness.

## Publish and preserve evidence

Use [guarded publication and paired closeout](protocols/WORKFLOW.md#paired-publication-and-closeout).
Select exact admitted paths, configure an explicit Git author and dry-run before
identical apply. Preserve foreign work. Publication and closeout are two effects,
not atomic: late refusal may follow known publication. Keep commit/reference
update, index, closeout, cleanup and known/unknown effects. Do not republish to
recreate spent authority or assume rollback. Remote push is separately authorized.

## What comes next

Issues → Specifications → Goals → shared map. Approval, approved iterations,
durable binding, Goals tooling, service elevation and object/materialization
bridges are not supplied here. Workspace deltas are change evidence, not meaning
or authority. Currentness is observed state, not every-write detection or
continuous confinement. This successor still needs unassisted evaluation;
earlier U does not automatically qualify these instructions.

[Sources](workspaces/README.md) are one canonical `portable_protocols` snapshot,
not another package catalog. Historical source READMEs are not customer guidance.
Contributor governance and its command selection remain separate and unchanged.
