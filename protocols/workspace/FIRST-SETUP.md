# Create your first governed repository manifest

Use one installed `aware` to prepare a repository manifest under a genuine
Issue. This example creates **only `aware.repo.toml`** in a repository already
initialized with [the explicit init workflow](../WORKFLOW.md#harness-identity-and-explicit-initialization).
Choose a customer-approved name, license expression and Issue task before running
it. Licensing path declarations do not create their referenced documents.

Keep the complete installed envelope, sources and notices. Use Bash and the
same absolute `AWARE`, `aware_init_env` and `aware_repo_root` selected during
installation/init. No new installation, handwritten configuration, admission
JSON or private provider construction is required for this example. If init
did not finish or the original configuration is missing, stop; do not fabricate
it. This guide is not a repair/migration operation.

## Configuration is not admission

Init's `aware.protocol.toml` supplied the required authority-manifest binding
in the qualified fresh-repository case. Init does **not** create a working
Issue, admit its scope or authorize Workspace apply. Those are separate owner
operations below. Preview observes sources and a plan; even a completed preview
does not establish that Issue admission will permit apply.

| Coordinate | Use |
| --- | --- |
| Issue identifier | `aware issue ... --issue-ref fb/YYYY-MM-DD/slug` |
| Markdown record path | Governed `aware workspace setup ... --issue-ref`; obtain it from the Issue read projection, not a guessed path |
| Authority manifest | `--authority-manifest aware.protocol.toml` for this init-created configuration |
| Issue scope | Complete reviewed physical effect footprint, including exact temporary/auxiliary paths, plus the Issue record |
| Workspace allowlist | `--allowed-path` for final file transitions only |

Do not omit `--governed` to work around a refusal. Scope is a task's effect
ceiling, not a path reservation. Do not widen it to the repository root or a
wildcard. Declared actor evidence is metadata, not cryptographic authentication.

## Create and start the Issue

Run once for a new, approved Issue. This example initially scopes only its
record; Workspace effects are reviewed and explicitly admitted later. Existing
Issues with other approved work require a separately reviewed scope amendment,
not blind replacement by this example. The command receipts go outside the
repository. Keep this Bash session for the following sections.

```bash
set -euo pipefail
set -C
: "${AWARE:?Use the absolute installed aware command}"
: "${aware_init_env:?Use the same installed environment}"
: "${aware_repo_root:?Use the explicitly initialized absolute repository}"
if test -n "${CODEX_THREAD_ID-}" && test -z "${CLAUDE_CODE_SESSION_ID-}"; then
  a1_actor="codex-$CODEX_THREAD_ID"
elif test -n "${CLAUDE_CODE_SESSION_ID-}" && test -z "${CODEX_THREAD_ID-}"; then
  a1_actor="claude_code-$CLAUDE_CODE_SESSION_ID"
else
  echo 'Missing or ambiguous genuine harness identity; remain read-only.' >&2
  exit 2
fi
a1_issue_ref='fb/2026-10-16/first-workspace-repository'
a1_name='example-repository'
a1_license='Apache-2.0'
a1_evidence="$(mktemp -d "${TMPDIR:-/tmp}/aware-first-workspace.XXXXXXXX")"
a1_intent="$(basename "$a1_evidence")"
printf 'Retain full receipts at %s\n' "$a1_evidence"

a1_issue_value() {
  "$aware_init_env/bin/python" -I -B - "$1" "$a1_actor" "$2" <<'PY'
import json, re, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
if value.get("outcome") != "found":
    raise SystemExit("Issue read did not find the original record; stop.")
projection = value["projection"]
if projection["identity"]["owner_ref"] != sys.argv[2]:
    raise SystemExit("Issue execution differs; stop.")
source = projection["source"]
if not re.fullmatch(r"sha256:[0-9a-f]{64}", source["digest"]):
    raise SystemExit("Original Issue byte guard missing; stop.")
print(source[{"guard": "digest", "record": "path"}[sys.argv[3]]])
PY
}

"$AWARE" issue ensure-snapshot --repository-root "$aware_repo_root" \
  --issue-ref "$a1_issue_ref" --title 'Create the repository manifest' \
  --priority P1 --owner-ref "$a1_actor" \
  --source-description 'Customer-approved repository setup' \
  --problem 'The initialized repository has no authored Workspace manifest.' \
  --objective 'Review and create aware.repo.toml through governed Workspace setup.' \
  --acceptance 'Original Issue admission and cleanup evidence are retained.' \
  --client-intent-id "$a1_intent-create" --actor-ref "$a1_actor" \
  --actor-evidence-ref "harness:$a1_actor" --format json \
  > "$a1_evidence/create.json" 2> "$a1_evidence/create.stderr"
"$AWARE" issue resolve-read-projection --repository-root "$aware_repo_root" \
  --issue-ref "$a1_issue_ref" --format json > "$a1_evidence/scope-read.json"
a1_record="$(a1_issue_value "$a1_evidence/scope-read.json" record)"
a1_initial_guard="$(a1_issue_value "$a1_evidence/scope-read.json" guard)"
"$AWARE" issue bind-scope --repository-root "$aware_repo_root" \
  --issue-ref "$a1_issue_ref" --expected-source-sha256 "$a1_initial_guard" \
  --scope-path "$a1_record" --client-intent-id "$a1_intent-initial-scope" \
  --actor-ref "$a1_actor" --actor-evidence-ref "harness:$a1_actor" --format json \
  > "$a1_evidence/initial-scope.json" 2> "$a1_evidence/initial-scope.stderr"
"$AWARE" issue resolve-read-projection --repository-root "$aware_repo_root" \
  --issue-ref "$a1_issue_ref" --format json > "$a1_evidence/progress-read.json"
a1_progress_guard="$(a1_issue_value "$a1_evidence/progress-read.json" guard)"
"$AWARE" issue start-progress --repository-root "$aware_repo_root" \
  --issue-ref "$a1_issue_ref" --expected-source-sha256 "$a1_progress_guard" \
  --client-intent-id "$a1_intent-start" --actor-ref "$a1_actor" \
  --actor-evidence-ref "harness:$a1_actor" --format json \
  > "$a1_evidence/progress.json" 2> "$a1_evidence/progress.stderr"
```

## Preview and review the complete effect scope

The following function invokes only the original governed Workspace registrar.
The decoder reads public typed evidence; it does not acquire authority or write
configuration. Retain the full JSON even when using the readable projection.

```bash
a1_preview() {
  "$AWARE" workspace setup repository --repository-root "$aware_repo_root" \
    --name "$a1_name" --license-expression "$a1_license" --governed \
    --issue-ref "$a1_record" --authority-manifest aware.protocol.toml \
    --client-intent-id "$a1_intent-workspace" --actor-ref "$a1_actor" \
    --actor-evidence-ref "harness:$a1_actor" --json
}
a1_preview_value() {
  "$aware_init_env/bin/python" -I -B - "$1" "$2" <<'PY'
import json, sys
from aware_workspace_command.architecture_setup_a1_command_values import (
    WorkspaceSetupA1CommandEvidence, command_value_from_payload,
)
value = command_value_from_payload(
    WorkspaceSetupA1CommandEvidence, json.load(open(sys.argv[1], encoding="utf-8")),
)
if (value.command_status != "preview_completed" or not value.completion_verified
        or value.issue_observation is not None or value.workspace_observation is None
        or value.workspace_observation.binding is None):
    raise SystemExit("Original completed read-only preview required; stop.")
binding, guards = value.workspace_observation.binding, value.review_guards
if not all((guards.issue_source_sha256, guards.authority_manifest_sha256, guards.plan_sha256)):
    raise SystemExit("Original review guards missing; stop.")
if sys.argv[2] == "review":
    print("FINAL FILE ALLOWLIST:")
    for row in binding.file_transitions:
        print("  " + row.path)
    print("ISSUE EFFECT FOOTPRINT (not just final files):")
    for path in sorted({p for step in binding.ordered_effects
                        for p in (step.primary_path, *step.auxiliary_paths)}):
        print("  " + path)
    print("Review original request, ordered effects, guards and cleanup in the full receipt.")
    print("Completed preview is NOT Issue admission or permission to retry.")
else:
    print({"issue": guards.issue_source_sha256,
           "manifest": guards.authority_manifest_sha256,
           "plan": guards.plan_sha256}[sys.argv[2]])
PY
}
a1_preview > "$a1_evidence/initial-preview.json" 2> "$a1_evidence/initial-preview.stderr"
a1_preview_value "$a1_evidence/initial-preview.json" review
```

**Stop here.** Inspect the owner receipt and task. In this Bash session,
explicitly set the array `a1_reviewed_scope` to the Issue record (`$a1_record`)
plus every exact reviewed effect path. Do not copy a scratch path from another
run, admit a wildcard or use only the final-file list. Scope binding replaces
the scope; this new-Issue example has no other approved task paths to preserve.
No scope array is automatically populated or authorized by the decoder.

## Bind reviewed scope then review a separate preview

Run only after that explicit scope choice. The Issue guard comes from the
reviewed initial preview, not a silent new read. This intentional scope mutation
changes Issue bytes; a separate preview follows and requires a separate review.
It is not a retry or automatic refresh of a refused apply.

```bash
declare -p a1_reviewed_scope >/dev/null
test "${#a1_reviewed_scope[@]}" -gt 0
a1_scope_args=()
for a1_path in "${a1_reviewed_scope[@]}"; do
  a1_scope_args+=(--scope-path "$a1_path")
done
a1_scope_guard="$(a1_preview_value "$a1_evidence/initial-preview.json" issue)"
"$AWARE" issue bind-scope --repository-root "$aware_repo_root" \
  --issue-ref "$a1_issue_ref" --expected-source-sha256 "$a1_scope_guard" \
  "${a1_scope_args[@]}" --client-intent-id "$a1_intent-reviewed-scope" \
  --actor-ref "$a1_actor" --actor-evidence-ref "harness:$a1_actor" --format json \
  > "$a1_evidence/reviewed-scope.json" 2> "$a1_evidence/reviewed-scope.stderr"
a1_preview > "$a1_evidence/scoped-preview.json" 2> "$a1_evidence/scoped-preview.stderr"
a1_preview_value "$a1_evidence/scoped-preview.json" review
```

**Stop again.** Compare the target, ordered effects, effect scope and plan
digest with the earlier review. If the plan changed, stop and evaluate it; do
not apply by refreshing guards automatically. Inspect the new Issue-byte guard
and unchanged manifest guard. Explicitly set the array `a1_reviewed_files` to
the final-file allowlist from this second preview (only `aware.repo.toml` for
the qualified example), not the scratch/effect list.

## Explicit apply with unchanged reviewed guards

```bash
declare -p a1_reviewed_files >/dev/null
test "${#a1_reviewed_files[@]}" -gt 0
a1_allowed_args=()
for a1_path in "${a1_reviewed_files[@]}"; do
  a1_allowed_args+=(--allowed-path "$a1_path")
done
a1_apply_issue_guard="$(a1_preview_value "$a1_evidence/scoped-preview.json" issue)"
a1_apply_manifest_guard="$(a1_preview_value "$a1_evidence/scoped-preview.json" manifest)"
a1_apply_plan_guard="$(a1_preview_value "$a1_evidence/scoped-preview.json" plan)"
"$AWARE" workspace setup repository --repository-root "$aware_repo_root" \
  --name "$a1_name" --license-expression "$a1_license" --governed \
  --issue-ref "$a1_record" --authority-manifest aware.protocol.toml \
  --client-intent-id "$a1_intent-workspace" --actor-ref "$a1_actor" \
  --actor-evidence-ref "harness:$a1_actor" --apply \
  --issue-source-sha256 "$a1_apply_issue_guard" \
  --authority-manifest-sha256 "$a1_apply_manifest_guard" \
  --expected-plan-sha256 "$a1_apply_plan_guard" "${a1_allowed_args[@]}" --json \
  > "$a1_evidence/apply.json" 2> "$a1_evidence/apply.stderr"
```

Inspect `apply.json`: command status, completion, original Issue consumption,
publication effects, residue, durability and separate owner/client cleanup.
Keep original unknown snapshots unknown even when later cleanup is confirmed.
Any nonzero exit, interruption or stale guard means stop and retain the complete
evidence. No automatic refresh, mutation retry, deletion of published bytes or
assumed rollback. Do not rerun a whole block to regain authority.

This example does not commit/close the Issue, resolve packages, update locks,
materialize `.aware` or start a Service. Continue only through separately
admitted operations in the [Workspace entrance](README.md). Unassisted A1
onboarding remains unproved; this guide is based on scripted installed evidence.
