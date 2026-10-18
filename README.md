# Aware

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

## Prepared reference successor

Agent **0.2.0a12** is selected locally; public delivery is not yet authorized.
Instructions remain draft. Use this reviewed checkout, not unchanged public main.
The [delivery pointer](releases/SELECTED.json) binds the complete envelope;
[local selection](releases/canonical-reference-fs-v1/LOCAL-SELECTION.md) records
the limits. Existing useful-task and implementation/draft branches are unchanged.
Workspace stdin/focus does not automate Issue guards. Instruction freeze and
publication remain separate; do not overlay installations or migrate contributor commands.

## Start with the shipped software

Agent **0.2.0a11**, with its 42-package closure, was published at
[`faed3f46668a3ec111d8fbf4cf1d5a287d5e1b89`](https://github.com/aware-network/aware/tree/faed3f46668a3ec111d8fbf4cf1d5a287d5e1b89).
This guidance alignment changes no software and authorizes no customer operation.
Acquire that exact revision. Verify exact payload/envelope provenance before
reusing any installation; a matching version label alone is insufficient.

Requires Linux x86-64, Git and an actual Python 3.12 interpreter. Inspect
[complete terms and sources](releases/canonical-init-summary-fs-v1/README.md)
and keep the whole envelope. Six detached-wheel legal gaps remain unresolved;
wheel-only delivery, stripped bundles and registry publication are unaccepted.
From the acquired checkout root, use the original installer once:

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
Exact-reference stdin/focus navigation remains an unshipped parallel successor.

[Current guidance pins](releases/canonical-init-summary-fs-v1/PUBLIC-INSTRUCTIONS.json)
and [status](releases/canonical-init-summary-fs-v1/PUBLIC-STATUS.md) are distinct
from unchanged historical freezes. `portable_protocols` remains the sole package
selector; the delivery pointer is not operation authority.

The source checkout's contributor `AGENTS.md` and a6 command selection govern
contributions there, not customer work. Do not copy that bootstrap or replace an
existing repository's selected command. Read [coherence](protocols/COHERENCE.md)
before effects. A2/tree completion, objects, materialization, services and
activation are not admitted by this release.
