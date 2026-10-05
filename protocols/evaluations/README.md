# External agent evaluations

Help us improve the installed product using a real customer-approved outcome.
This is **external evidence only**, never Issue/Goal authority or release acceptance.
No Aware development checkout, services, internal reports or private answer keys
are needed. The public consumer checkout and published user docs are legitimate
installation inputs; disclose any reading of implementation/tests during U.

## Start small

Report installation or onboarding failures immediately through
[GitHub Issues](https://github.com/aware-network/aware/issues). You do not have to
complete a workflow, invent a Goal or run a second agent to report a blocker.
Include public revision, archive SHA-256, installed version, platform/Python,
approved outcome, exact sanitized command, exit code, diagnostic, expected versus
observed behavior and what was **not run**. Never include credentials, private
paths, customer source/records or hidden prompts. Security disclosures follow
[SECURITY.md](../../SECURITY.md), not a public issue.

Choose one subject: `installation`, `existing_issue`, `new_issue`, or
`goal_readonly`. The first three do not require a Goal. A missing repository,
unborn HEAD or not-yet-created manifest has no digest to invent: record null.
An unsupported requested workflow can be blocked without implying an advertised
supported workflow regressed. A raw error can separately be a clarity defect.

## Evaluation passes

- **I — Installation/setup:** acquire the pinned public candidate and observe
  prerequisites, installation, interface activation and target setup.
- **U — Unassisted outcome:** a fresh agent gets only the approved outcome,
  customer target, installed command and public consumer instructions. No supplied
  command choreography or internal test driver. Record questions and first Human
  hint; assistance is not silently relabeled unassisted success.
- **V — Guided verification:** freeze U before giving probes. For Issue workflows
  test actual scope/stale/former-owner refusals, unrelated work preservation and
  receipt-based closeout. Name the real rejecting component and diagnostic.
  Agent voluntary non-action is not enforcement. Goal-only probes apply only to
  a supported pinned Goal reader and qualified input, not the Issue-only bundle.
- **R — Fresh recovery:** a different genuine execution receives durable records,
  not U/V transcripts or process state. Establish owner/status/scope, evidence and
  next lawful action. An installer-only report may leave U/V/R `not_run`.

Media is optional unless the claim depends on perception or timing. Keep ordinary
CLI feedback lightweight. Evaluation reports may be authored directly: they are
evidence, not manual edits to customer Issue/Goal authority.

## Capture the interpreter actually used for task tests

Record the Aware installation interpreter separately from every task-test
interpreter. In the execution that runs the tests, resolve its chosen executable,
capture its version and `sys.executable`, then run the tests with that recorded
absolute executable. For example, if that task has chosen `python3`:

```sh
task_python="$(command -v python3)" || exit 1
"$task_python" -c 'import sys; print(sys.executable); print(sys.version)'
"$task_python" -m unittest discover -v
```

Use the task's actual test invocation; this example does not prescribe unittest
or the Aware environment. Retain command, exit status and interpreter evidence
in the same pass. Never infer the task version from installation or a different
execution. Before transfer, sanitize private paths to stable symbolic coordinates
without dropping the version or the link between observation and test command.
Missing historical evidence stays unknown; do not rewrite a frozen evaluation.

## Interpret Issue and publication evidence separately

Issue `issue_day_index:pending` and `feed:unavailable` are not the Git index.
Publication `shared_index_projection` and `index_reconciliation_pending` report
that operation's Git-index reconciliation; a read projection is not a fresh Git
status observation. Retain each result independently, including unknowns.
Authored acceptance boxes start unchecked and have no checking operation in this
profile. Passing tests or closing an Issue does not mark them, nor grant Goal or
Specification acceptance. Report actual verification; do not manually check them.

## Structured submission v2

Use a new immutable coordinate `evaluations/YYYY/MM/DD/<slug>/` containing:

```text
manifest.json
evaluation.md
findings.json
interactions.jsonl
artifacts/                  # optional sanitized evidence
```

The schemas in [v2](v2) version the evidence shape independently from the product
profile, CLI and agent contract. Historical v1 records remain unchanged. One
actual execution is sufficient for an early failure; only a completed R requires
a distinct execution. Distinguish `not_run`, `not_applicable`, `unsupported`,
`blocked`, `failed` and `passed`. Never fabricate timestamps for unrun passes.

Every file except manifest is digest-bound; paths must be regular, relative and
fully accounted. Interactions are append-only and contiguous from 1. Findings
link to actual artifacts/interactions and explicitly retain limitations.

Validate with the installed consumer interpreter (already contains jsonschema):

```sh
/absolute/aware-env/bin/python -I -B protocols/evaluations/v2/validate.py \
  /absolute/sanitized-evaluation
```

Validation checks format, references and byte accounting, **not** claim truth,
authorship, sanitization completeness or installed enforcement. Aware reproduces
applicable findings independently before admitting them through a scoped Issue.

The existing `aware-network/aware-client-evaluations` repository is a separate,
currently private evidence archive—not a required customer dependency. Maintainers
can admit sanitized public feedback there with its exact source/commit citation.
Publishing an evaluation or correcting a finding never overwrites an old
coordinate; corrections point to the predecessor commit. Customer content and
private transcripts stay private. No transfer or release follows from validation.
