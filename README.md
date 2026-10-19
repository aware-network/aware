# Aware

Agent **0.2.0a14** software was published at `08a598fdeb8f960bf30fb8e85229e820286e67be`.
Acquire that exact revision and retain its complete source/notice envelope.
This alignment changes current wording and pins, not software or operation authority.
Both reviews and original guards remain required.

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
customer's application. Project/Goal direction and language/Meta materialization
are parallel future elevations, not prerequisites for this path.

## Locally selected Issue observation input

Issue CLI **0.8.4** is selected locally; public delivery is not yet authorized.
Instructions remain draft. Use this reviewed checkout, not unchanged public main.
The [delivery pointer](releases/SELECTED.json) binds the complete envelope;
[local selection](releases/canonical-issue084-fs-v1/LOCAL-SELECTION.md) records its limits.
[Observation input](protocols/issues/OBSERVATION-INPUT.md) carries one explicit
Issue snapshot into original scope, progress and publish-close commands.
The same observation does not freeze previewed HEAD or source bytes; apply plans
afresh. Customer implementation and optional SPEC branches, both review decisions
and contributor commands remain unchanged. Instruction freeze and publication
remain separate; no automatic guard refresh, approval or retry.

## Delivered a14 resource summaries

Agent **0.2.0a14** is publicly delivered at the exact revision above.
The original local selection and freeze records remain historical checkpoints.
The [delivery pointer](releases/SELECTED.json) binds the complete envelope;
[local selection](releases/canonical-a14-fs-v1/LOCAL-SELECTION.md) records its limits.
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

Agent **0.2.0a11**, with its 42-package closure, was published at
[`faed3f46668a3ec111d8fbf4cf1d5a287d5e1b89`](https://github.com/aware-network/aware/tree/faed3f46668a3ec111d8fbf4cf1d5a287d5e1b89).
That predecessor remains available as history. For current a14, acquire the exact
`08a598fdeb8f960bf30fb8e85229e820286e67be` revision and use its whole-envelope
installer; do not mix predecessor commands with successor guidance.
Verify exact payload/envelope provenance before reusing any installation;
a matching version label alone is insufficient. No operation authority follows.

Requires Linux x86-64, Git and an actual Python 3.12 interpreter. Inspect
[complete terms and sources](releases/canonical-a14-fs-v1/README.md)
and keep the whole envelope. Six detached-wheel legal gaps remain unresolved;
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

[Current instruction pins](releases/canonical-a14-fs-v1/PUBLIC-INSTRUCTIONS.json)
and [delivery/status provenance](releases/canonical-a14-fs-v1/PUBLIC-STATUS.md)
are distinct from the unchanged [historical freeze](releases/canonical-reference-fs-v1/INSTRUCTION-FREEZE.md).
`portable_protocols` remains the sole package
selector; the delivery pointer is not operation authority.

The source checkout's contributor `AGENTS.md` and a6 command selection govern
contributions there, not customer work. Do not copy that bootstrap or replace an
existing repository's selected command. Read [coherence](protocols/COHERENCE.md)
before effects. A2/tree completion, objects, materialization, services and
activation are not admitted by this release.
