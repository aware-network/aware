# Aware

Coherent work between agents in your Git repository.

Aware provides shared rules and tooling so agents understand the same work,
make bounded changes and leave evidence another execution can continue from.
Issues coordinate work; Specifications describe its intended shape. Coherence
is the value, not a promise of faster agents or conflict-free swarms.

Aware's direction: Don't watch your agents. Watch your goals. See [aware.run](https://aware.run).

The reviewed-workflow software was published at
[`42a6740e29bb39ec9d332a63d52cb59540655ccd`](https://github.com/aware-network/aware/blob/42a6740e29bb39ec9d332a63d52cb59540655ccd/README.md).
The [delivery pointer](releases/SELECTED.json)
binds the accepted whole envelope; [public status](releases/canonical-reviewed-workflow-fs-v1/PUBLIC-STATUS.md)
and [successor instruction pins](releases/canonical-reviewed-workflow-fs-v1/PUBLIC-INSTRUCTIONS.json)
distinguish delivered software from this wording update and record its review checkpoint. Historical freeze
records remain unchanged. Instructions and delivery records grant no operation authority.
Do not overlay installations or migrate contributor commands.

## Understand the rules

Read [coherence](protocols/COHERENCE.md), [Issues](protocols/issues/README.md),
[publication](protocols/repository/README.md) and [SPEC drafts](protocols/specification/README.md).
Readable guidance explains shared rules; tooling invokes separately admitted
operations. Tool installation, repository configuration and service startup are
distinct. This filesystem composition starts no service.

## Inspect terms and install once

Requires Linux x86-64, Git and an actual Python 3.12 interpreter. Read
[complete distribution terms and source](releases/canonical-reviewed-workflow-fs-v1/README.md)
before installation. Keep the entire envelope: terms, sources, corresponding
source, component evidence and raw audit. Six detached-wheel legal gaps remain
unrepaired; wheel-only acquisition, stripped bundles and registry publication
are unaccepted.

From the root of this reviewed checkout:

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

Installation is offline after acquisition. The original installer verifies and
retains the whole envelope, prints its absolute `retained_source_and_notices`
directory, and delegates to the existing payload installer. Keep that directory;
the workflow's `aware_envelope_root` names it for the typed input example.
Environment reuse refuses. No editable checkout or development source is needed.

## Initialize and admit an Issue

Use a genuine harness with exactly one nonblank `CODEX_THREAD_ID` or
`CLAUDE_CODE_SESSION_ID`; do not borrow or invent identities. Set
`aware_repo_root` to your explicit absolute target under an existing parent:

```sh
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --format summary
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --apply --format json
```

For an existing Git repository omit `--create-repository`. Existing configuration
or guidance refuses rather than overwriting. Preview gives Workspace preparation
and prospective Protocol inputs, not two admitted owner plans. Apply obtains
fresh Protocol admission after repository preparation.

Init supplies the Protocol configuration used by this qualified fresh-repository
workflow. It does not admit an Issue, approve scope or authorize Workspace apply.
It stages nothing, creates no seed commit or remote and starts no service.
Preserve both owners' effects and cleanup; non-success is not rollback or retry
permission. Read the init-created `AGENTS.md` and `aware.protocol.toml`.

`--issue-ref` is `fb/YYYY-MM-DD/lowercase-hyphenated-slug`, not a UUID, title or
Markdown path. Follow [the first-Issue guide](protocols/issues/FIRST-ISSUE.md)
to create/observe the record, choose scope and start progress. Keep reference and
record path distinct. Missing identity, invalid references and stale guards stop;
do not guess retries, fabricate authority or silently refresh guards.

## Review Workspace setup in two decisions

Follow [reviewed repository setup](protocols/workspace/REVIEWED-SETUP.md).
The original SDKs retain guards, complete physical scope, final files and evidence.
First review the physical effect scope and explicitly bind it. Then inspect the
second preview and separately authorize final-file apply. Reuse exact SDK-issued
references; do not handwrite records or copy guards into new requests.

The qualified fresh-repository route uses init-created `aware.protocol.toml`
directly, without another configuration step. Issue admission and both decisions
remain necessary. Missing inputs mean stop, not fabrication or governance bypass.
Stale/spent requests do not refresh or retry automatically. The newly qualified
review route creates a repository manifest, not a complete package/application.

## Use the existing SPEC and publication owners

[The complete workflow](protocols/WORKFLOW.md) preserves the original first-Issue,
SPEC setup, typed input, target-fit preparation, explicit draft preview/apply,
observation and paired publication/closeout commands. A target match is layout
evidence, not Issue eligibility or write authority. Manifests are repository-relative;
explicit absolute snapshot paths avoid cwd ambiguity. Guard labels identify
different exact bytes; a stale request needs a new preparation and review decision.

Publication and closeout are distinct effects, not an atomic transaction. Preserve
known commits, closeout refusals, foreign work, index state and unknown outcomes.
Do not republish to recover spent authority. Remote push is separately authorized.
[Saved-receipt presentation](protocols/WORKFLOW.md#review-a-saved-receipt-without-repeating-the-operation)
reads full evidence or validated summaries without replay or renewed authority.

## Read the result honestly

Reviewed Workspace summaries separate final files, complete effect scope,
original admission/release and client cleanup. Original release uncertainty
remains unknown after later client cleanup succeeds. Incomplete retention or
output does not erase completed effects or authorize redispatch. Preserve the
full evidence; use `show --json` or `evidence` when concise output is insufficient.

This successor has a bounded scripted installed proof, not unassisted onboarding
or the historical 2,819-case aggregate. Carried code, help and scripts do not
admit A2, tree completion, materialization, Meta/Object execution, services,
approval, iterations or native performance. Workspace deltas are change evidence,
not inferred meaning or authority.

Issues → Specifications → Goals → shared map remains the direction, not a claim
that all those features are delivered here. [Sources](workspaces/README.md) are
the canonical `portable_protocols` snapshot with composite supplier revisions,
not a second catalog or editable operational installation. Contributor governance
and its command selection remain separate and unchanged.
