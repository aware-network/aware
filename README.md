# Aware

For a fresh installation, acquire corrected revision `55de18317dcb77ed879b36aaeed43691ce4d3342`
or a separately approved successor carrying the same corrected installer.
Use its original `protocols/install.py` and retain complete sources/notices.
Agent **0.2.0a16** / Issue CLI **0.8.4** software was first delivered at
`704b5943931fcac23bcc748a574e112d20884017`; that is historical software provenance, not a fresh-install target.
Older guide preambles at the acquisition revision may still name that software
checkpoint: do not follow them back to its broken installer. This current guide
supplies the corrected acquisition coordinate; both reviews and original guards remain.
This additional guidance/pin alignment requires independent review and separate
publication authorization. It changes no software, command or operation authority.

Coherent work between agents in your Git repository.

Aware helps an agent make a bounded change and leave evidence another execution
can review and lawfully continue. Issues coordinate the work; a Specification
draft is optional when the task needs shared intent. The agent still implements
and tests the customer's change. Aware is not a sandbox or an application
correctness checker, and coherence is not a promise of faster agents.

## Complete something useful

Start with a small customer-approved outcome: a bug fix, a read-only tool or a
tested improvement to an owned repository. Follow
[your first useful task](protocols/FIRST-USEFUL-TASK.md). A starter
[JSON-checker task](protocols/tasks/JSON-CHECKER.md) gives explicit acceptance
criteria, not a prewritten implementation or mandatory task.

Today's path is **Issue → optional SPEC → bounded work → verification → local
publication and closeout**. A generated manifest is setup, not completion of the
customer's application. Optional delivered Project/Goal direction is a separate fresh-repository branch.
Language/Meta elevation remains parallel; neither is a prerequisite for this path.

## Delivered optional Project/Goal and original-intent presentation

Agent **0.2.0a16** / Issue CLI **0.8.4**, 49 payload distributions, was published at `704b5943931fcac23bcc748a574e112d20884017`. Start with
[useful customer code](protocols/FIRST-USEFUL-TASK.md); Issue-first and optional
SPEC remain independent. For a fresh repository only, see the separate
[optional Project/Goal branch](protocols/PROJECT-GOAL.md). It creates direction,
not work authority, and does not provide Goal-to-Issue, decomposition or RUN.

The delivered predecessor is Agent a15 at
`5af88a6b95b928811022e5cd0255e4bb5c77bd87`; local wording baseline is
`3f70fcf57e56708a1e1f8c0b52a10e2eb812da6d` remains historical.
The current delivery is pinned explicitly above; the original installer retains its entire envelope.
The [delivery pointer](releases/SELECTED.json) binds the complete envelope;
[local selection](releases/canonical-project-goal-fs-v1/LOCAL-SELECTION.md) records its limits.
Independent current-wording review and additional publication remain separate from new client trials.

## Delivered historical action observation

Agent **0.2.0a15** was published at `5af88a6b95b928811022e5cd0255e4bb5c77bd87`.
The original local selection and freeze records remain historical checkpoints.
The [delivery pointer](releases/SELECTED.json) binds the complete envelope;
[local selection](releases/canonical-action-observer-fs-v1/LOCAL-SELECTION.md) records its limits.
[Historical action observation](protocols/workspace/ACTION-OBSERVATION.md)
validates original intent, not completion, current admission or retry authority.
Useful work, optional SPEC and both explicit review decisions stay unchanged.
Independent wording review and additional publication are separate; no automatic refresh or retry.

## Historical Issue observation input

Issue CLI **0.8.4** was published at `813ab2e82f7ff0fa24403c6889bf82e2c8b121fb`.
The original local selection and freeze records remain historical checkpoints.
The [predecessor selection](releases/canonical-issue084-fs-v1/LOCAL-SELECTION.md)
records that historical delivery; that is historical delivery; the current pointer identifies delivered a16, not operation authority.
[Observation input](protocols/issues/OBSERVATION-INPUT.md) carries one explicit
Issue snapshot into original scope, progress and publish-close commands.
The same observation does not freeze previewed HEAD or source bytes; apply plans
afresh. Customer implementation and optional SPEC branches, both review decisions
and contributor commands remain unchanged. Independent alignment review and publication
remain separate; no automatic guard refresh, approval or retry.

## Historical a14 predecessor resource summaries

The Agent **0.2.0a14** predecessor distribution was published at
[`08a598fdeb8f960bf30fb8e85229e820286e67be`](https://github.com/aware-network/aware/tree/08a598fdeb8f960bf30fb8e85229e820286e67be).
That historical delivery is distinct from the Issue CLI 0.8.4 successor published at `813ab2e82f7ff0fa24403c6889bf82e2c8b121fb`.
The original local selection and freeze records remain historical checkpoints.
The [predecessor selection record](releases/canonical-a14-fs-v1/LOCAL-SELECTION.md)
records that historical distribution. The [current delivery pointer](releases/SELECTED.json)
identifies delivered a16; the explicit publication pin establishes delivery. Explicit predecessor publication pins remain historical evidence.
[Resource summaries](protocols/workspace/RESOURCE-RELEASES.md) distinguish reported
closes from ledger completeness and historical unknowns. Optional Goal and positive
create-first remain unqualified; useful work, optional SPEC, both explicit reviews
and manual Issue guards remain. Do not overlay installations or change contributor
commands. This wording alignment requires independent review and separate publication authorization.

## Historical a12 reference navigation

Agent **0.2.0a12** software was published at
[`f372cf75aaa228f059ab12e4095cec598e998541`](https://github.com/aware-network/aware/tree/f372cf75aaa228f059ab12e4095cec598e998541).
This status alignment changes wording and pins, not software or operation authority.
The [delivery pointer](releases/SELECTED.json) binds the complete envelope;
[local selection](releases/canonical-reference-fs-v1/LOCAL-SELECTION.md) records
the limits. Existing useful-task and implementation/draft branches are unchanged.
Workspace stdin/focus does not automate Issue guards. Review provenance does not
grant authority; do not overlay installations or migrate contributor commands.

## Acquire and install the exact delivered revision

Acquire corrected installer revision `55de18317dcb77ed879b36aaeed43691ce4d3342`.
The unchanged operational block below targets its delivered a16 envelope through
the original installer. Verify exact
envelope/payload provenance before reusing an installation; version labels alone
are insufficient. Do not mix predecessor installations with this distribution.

Requires Linux x86-64, Git and an actual Python 3.12 interpreter. Inspect
[complete terms and sources](releases/canonical-project-goal-fs-v1/README.md)
and keep the whole envelope. Nine detached-wheel legal gaps remain unresolved;
wheel-only delivery, stripped bundles and registry publication are unaccepted.
From this reviewed checkout root, use the original installer once:

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

Keep the printed `retained_source_and_notices` directory with the installation.
The installer refuses existing destinations; never overlay a retained environment
or substitute development-checkout imports.

## Initialize then admit the customer's Issue

Read [init streams and explicit decisions](protocols/INIT.md), select the absolute
customer repository and use your genuine supported harness identity. Stop after
preview and review it before the separate apply decision; do not execute this
block unattended:

```sh
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --format summary
"$AWARE" init --repo-root "$aware_repo_root" \
  --create-repository --apply --format json
```

Init supplies configuration, not Issue admission, scope approval or Workspace
apply authority. It creates no seed commit or remote and starts no service. Read
the target's `AGENTS.md` and `aware.protocol.toml`. Follow the original
[first-Issue operations](protocols/issues/FIRST-ISSUE.md), replacing its draft-only
example with the customer's actual outcome and exact source/test/document scope.
Do not use the sample draft scope unchanged for application edits.

Use approved engineering tools for source changes and task tests. If repository
manifest setup is needed, preserve [both review decisions](protocols/workspace/REVIEWED-SETUP.md).
If shared design is needed, follow [SPEC setup and drafting](protocols/WORKFLOW.md).
Neither is compulsory setup for every task. After verification and explicit local
publication authorization, use the original
[publication and closeout owners](protocols/repository/README.md), with exact paths
and dry-run before apply. Publication and closeout are not atomic; preserve both
receipts. Remote push needs separate authorization.

## Inspect the evidence and boundaries

The following client evidence remains bound to earlier releases; it is not a new a14 U/V/R or productivity claim.

[The evidence map](protocols/EVIDENCE-MAP.json) links exact public U/V/R reports.
U completed bounded manifest setup with coordinator-prepared installation, not
application implementation or publication. Guided V established specific stale
refusals and measured state preservation; spent reuse still exits 3 with genuine
incompleteness. Planned R established lawful continuation, with an intended-name
mismatch qualification. These do not establish customer-code productivity, broad
onboarding, crash recovery or conflict-free swarms.

Keep full original receipts from the same invocation. Stale requests require
new explicit review, never automatic refresh or mutation retry. Incompleteness
does not erase known effects. Original release unknown remains unknown even after
later client cleanup. Historical references do not restore live authority.
Exact-reference stdin/focus navigation is included in the delivered a12 candidate;
historical inspection does not restore current-use authority or automate Issue guards.

[Current instruction pins](releases/canonical-action-observer-fs-v1/PUBLIC-INSTRUCTIONS.json)
and [delivery/status provenance](releases/canonical-action-observer-fs-v1/PUBLIC-STATUS.md)
are distinct from the unchanged [historical freeze](releases/canonical-reference-fs-v1/INSTRUCTION-FREEZE.md).
`portable_protocols` remains the sole package
selector; the delivery pointer is not operation authority.

The source checkout's contributor `AGENTS.md` and a6 command selection govern
contributions there, not customer work. Do not copy that bootstrap or replace an
existing repository's selected command. Read [coherence](protocols/COHERENCE.md)
before effects. A2/tree completion, objects, materialization, services and
activation are not admitted by this release.

## Adopting an existing repository

[Candidate adoption instructions](protocols/EXISTING-REPOSITORY.md) explain custom record roots,
compatible configuration reuse and preserving existing guidance and foreign work.
They qualify a scripted installed workflow, not generic migration or
unassisted customer adoption. Project and Goal are not prerequisites.
