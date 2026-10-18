# Reviewed repository setup

Agent 0.2.0a12 instructions are frozen locally pending independent review;
public delivery is not yet authorized. Use `aware workspace review` for one bounded
A1 task: creating `aware.repo.toml` through the original Workspace, FileSystem
and Issue owners. Start with [the entrance](../../README.md),
[init guidance](../INIT.md) and [first Issue](../issues/FIRST-ISSUE.md).
[Qualification bounds](../../releases/canonical-reference-fs-v1/REVIEW-STATUS.md)
retain the exact candidate limits. This is not package creation, application
implementation, A2/tree completion or unassisted onboarding acceptance.

## Inputs and configuration

Use one installed `aware`, an explicit absolute repository root, a genuine
In Progress Issue reference and its exact repository-relative Markdown path.
Init supplies the Protocol configuration used by this qualified fresh-repository
workflow. It does not admit an Issue, approve scope or authorize Workspace apply.
The qualified journey uses init-created `aware.protocol.toml` directly, without
another configuration step. Missing or unsuitable configuration/Issue inputs
still mean stop—not fabricated records or bypassing governance.

Choose the repository name, SPDX license expression, declared actor/evidence
and each action's intent explicitly. Preserve unrelated work and existing Issue
scope. The destination repository manifest must be absent; no overwrite fallback
or implicit commit is supplied.

The evidence root must already exist as a private, owned directory outside and
disjoint from the repository. Choose or create that directory explicitly. Do
not share it, author SDK evidence records, or treat its historical files as a
new execution's current authority. The original SDK enforces its requirements.

```sh
"$AWARE" workspace review prepare --help
"$AWARE" workspace review show --help
"$AWARE" workspace review scope --help
"$AWARE" workspace review apply --help
"$AWARE" workspace review evidence --help
```

## Prepare and review physical scope

Set every variable to your selected coordinate or intent. `first_issue_ref` is
the admitted reference, not `first_issue_path`. This example explicitly requests
Issue-lifecycle participation; inspect those effects in the first preview too.

```sh
set -eu
: "${AWARE:?Use the absolute installed command}"
: "${aware_repo_root:?Set the absolute repository root}"
: "${workspace_evidence_root:?Set an existing private evidence directory outside the repository}"
: "${first_issue_ref:?Set the admitted Issue reference}"
: "${first_issue_path:?Set its exact repository-relative Markdown path}"
: "${workspace_name:?Set the reviewed repository name}"
: "${workspace_license:?Set the reviewed SPDX license expression}"
: "${workspace_actor_ref:?Set the declared actor coordinate}"
: "${workspace_actor_evidence_ref:?Set its declared evidence coordinate}"
: "${workspace_prepare_intent:?Set this preparation intent}"
"$AWARE" workspace review prepare \
  --repository-root "$aware_repo_root" \
  --evidence-root "$workspace_evidence_root" \
  --issue-ref "$first_issue_ref" --issue-path "$first_issue_path" \
  --name "$workspace_name" --license-expression "$workspace_license" \
  --actor-ref "$workspace_actor_ref" \
  --actor-evidence-ref "$workspace_actor_evidence_ref" \
  --include-issue-lifecycle --client-intent-id "$workspace_prepare_intent"
```

Preparation retains the first review. It does not bind Issue scope or apply
Workspace setup. Inspect the selected repository/Issue/configuration, original
scope and lifecycle, requested final files, complete physical effect scope,
guards and cleanup. Temporary effects belong to physical scope; that set is
not interchangeable with the proposed final-file set.

Retain the exact SDK-issued Reference JSON from the response as
`workspace_first_reference`. It is an opaque returned value, not a file path,
hand-authored record or package catalog. Human output labels the reference;
`show --json` can expose the complete original record when long summaries omit
details. Do not invent fields, execute vectors or use `eval`.

## Bind reviewed scope then review again

Only after accepting the complete physical effect scope, invoke this distinct
action with the unchanged first reference and a new explicit scope intent:

```sh
set -eu
: "${workspace_first_reference:?Use the exact first SDK-issued Reference JSON}"
: "${workspace_scope_intent:?Set this explicit scope decision intent}"
"$AWARE" workspace review scope \
  --repository-root "$aware_repo_root" \
  --evidence-root "$workspace_evidence_root" \
  --reference "$workspace_first_reference" \
  --client-intent-id "$workspace_scope_intent" \
  --accept-reviewed-effect-scope
```

The original Issue SDK binds the SDK-generated scope union while preserving
existing work. Workspace retains that actual outcome and supplies a second
preview. A scope result followed by second-preview failure remains a completed
scope effect plus a later failure—not rollback or permission to repeat scope.

Review the second preview and final files independently. It must be ready for
the apply review. Retain its exact Reference JSON as
`workspace_second_reference`. Scope acceptance is not automatic apply approval.

## Explicitly apply the reviewed final files

Only after that second decision, invoke apply using the unchanged second
reference and its own explicit intent:

```sh
set -eu
: "${workspace_second_reference:?Use the exact second SDK-issued Reference JSON}"
: "${workspace_apply_intent:?Set this explicit final-file decision intent}"
"$AWARE" workspace review apply \
  --repository-root "$aware_repo_root" \
  --evidence-root "$workspace_evidence_root" \
  --reference "$workspace_second_reference" \
  --client-intent-id "$workspace_apply_intent" \
  --accept-reviewed-final-files
```

The owners use the reviewed guards and final-file set. The client does not copy
guards, compute a replacement allowlist or select another writer. Missing intent,
stale inputs, spent evidence or foreign current-use requests stop. A new attempt
requires an explicit preparation/review decision, never automatic refresh/retry.

## Inspect evidence without replay

Human summaries answer **What happened**, **What changed**,
**What remains uncertain**, **What next (guidance, not authority)** and
**Where is full evidence**. Read each separately. The original Issue scope
mutation outcome is not its retention status or a later manifest-apply result.
A known applied scope stays applied when capture fails; a missing observation
is not proof of no effects. Scope completion followed by failed retention or a
second-preview failure never authorizes repeating scope.

Use `show` only for historical review records and `show --json` for their
complete SDK record. It is not a generic receipt reader. For supported retained
refusals, outcomes and other evidence kinds use `evidence`, with the same explicit
repository/evidence roots and exact returned reference. It emits original UTF-8
capture bytes; independent client cleanup is reported separately. The reference
container kind is not necessarily the schema of the captured bytes.
Historical reading does not restore current-use authority or repeat an operation.

If no SDK evidence reference is returned, keep available full JSON and original
evidence; do not invent a reference or redispatch to manufacture a receipt.
With incomplete retention a returned reference may name earlier evidence, not
a complete capture of the current failure. Human explanation failure preserves
full JSON when available and the original non-success/interruption exit.

Keep both review references and all original effect/cleanup receipts. Original
release uncertainty remains unknown even if later client cleanup completes.
Read the primary owner code/reason separately from evidence retention and client
cleanup. Clean stale Issue/authority refusals retain complete evidence and exit
2. Spent-reference incompleteness remains 3; current retention/output or client
cleanup failure remains non-success. Interruption stays 130 even after output
failure. Original release unknown alone does not force a nonzero exit: qualified
successful apply can exit 0 with that unknown still visible. A completed effect
can coexist with exit 3 or 130. Preserve evidence; never replay for a nicer receipt.

Repository publication and Issue closeout remain separate original operations;
reviewed setup neither commits customer files nor closes the Issue. This guide
is supported by scripted installed cases, not fresh unassisted onboarding,
multi-agent coherence, crash recovery or application correctness acceptance.

## Prepared reference navigation

The a12 [reference-navigation guide](REFERENCE-NAVIGATION.md) adds explicit captured-result stdin and historical focus. It grants no authority, approval or Issue-guard automation.
