# Admit your first filesystem Issue

After [installation and explicit initialization](../WORKFLOW.md), use the same
installed `aware` command to create a snapshot, bind approved paths and start
progress. These are three separate SDK operations, not one transaction. Init
does not admit an Issue, and this example does not grant task authorization.

## Choose one task branch

For the approved JSON-checker implementation, use the complete [implementation branch](#implementation-branch-for-a-tested-json-checker). For a draft-only task, use the preserved draft example below. Choose intent before creating a snapshot; do not execute both examples.

## Reference versus record path

For the `aware issue` family in this filesystem profile, `--issue-ref` is an identifier:

```text
fb/YYYY-MM-DD/lowercase-hyphenated-slug
```

Use a four-digit year, two-digit month and day, then lowercase letters/digits
separated by single hyphens. For example, `fb/2026-10-11/json-checker-draft`.
There is no `.md` suffix. Do not supply a UUID, title, URL or filesystem path.
The provider maps that reference through the configured Issue root. With init's
default `docs/issues` root, this example becomes:

```text
docs/issues/2026/10/11/fb-2026-10-11-json-checker-draft.md
```

The Issue-family `--issue-ref` uses the identifier; `--scope-path` uses a
repository-relative path. In contrast, governed `aware workspace setup` uses
the Markdown record path for its `--issue-ref`. Obtain that original path from
`resolve-read-projection` (`projection.source.path`); do not guess it or pass
the identifier to Workspace. See [first governed Workspace setup](../workspace/FIRST-SETUP.md).
These coordinate forms are not interchangeable. If you initialized a
different `--issue-root`, use that configured root for the record path below.
The installed help and owner diagnostics explain this syntax. On
`issue_ref_invalid`, stop and inspect the exact diagnostic; do not guess or retry.

## Prerequisites and example outcome

Retain `AWARE` as the absolute command from your single installation and
`aware_repo_root` as your explicitly initialized absolute repository path.
Use your actual supported harness execution, not an evaluator fixture or a
borrowed actor. The example assumes a customer-approved **draft-only** JSON
checker specification: no application implementation or approval. Choose your
own reference, task text and exact scope before running it. The sample scope
admits the Issue record, Protocol manifest and `docs/specs/json-checker`
descendants; it is not permission to overwrite foreign work or reserve paths.

## Snapshot then guarded scope and progress

Run this block once for a new reference in the initialized repository. It saves
full receipts in a fresh private directory outside the repository. Python only
decodes the public JSON read projection; it does not write authority or import
SDK/provider internals. Each mutation uses the digest from its explicit preceding
read. No loop refreshes a guard or retries a refused mutation.

```bash
set -eu
: "${AWARE:?Use the absolute command from your installation}"
: "${aware_repo_root:?Set your explicitly initialized absolute repository path}"
if test -n "${CODEX_THREAD_ID-}" && test -z "${CLAUDE_CODE_SESSION_ID-}"; then
  first_issue_actor="codex-$CODEX_THREAD_ID"
elif test -n "${CLAUDE_CODE_SESSION_ID-}" && test -z "${CODEX_THREAD_ID-}"; then
  first_issue_actor="claude_code-$CLAUDE_CODE_SESSION_ID"
else
  echo 'Missing or ambiguous genuine harness identity; remain read-only.' >&2
  exit 2
fi
printf 'Execution: %s\n' "$first_issue_actor"
first_issue_actor_evidence="harness:$first_issue_actor"
first_issue_ref='fb/2026-10-11/json-checker-draft'
first_issue_record='docs/issues/2026/10/11/fb-2026-10-11-json-checker-draft.md'
first_issue_evidence="$(mktemp -d "${TMPDIR:-/tmp}/aware-first-issue.XXXXXXXX")"
first_issue_intent_prefix="$(basename "$first_issue_evidence")"
printf 'Retain full receipts at %s\n' "$first_issue_evidence"

"$AWARE" issue ensure-snapshot --repository-root "$aware_repo_root" \
  --issue-ref "$first_issue_ref" --title 'Draft a JSON checker specification' \
  --priority P1 --owner-ref "$first_issue_actor" \
  --source-description 'Customer-approved draft-only example' \
  --problem 'Agents need a shared description of a read-only JSON checker.' \
  --objective 'Create and observe a draft; do not implement or approve it.' \
  --acceptance 'The draft requires that checking never modifies its input.' \
  --client-intent-id "$first_issue_intent_prefix-create" \
  --actor-ref "$first_issue_actor" --actor-evidence-ref "$first_issue_actor_evidence" \
  --format json > "$first_issue_evidence/create.json"

first_issue_read_guard() {
  /usr/bin/python3.12 - "$1" "$first_issue_actor" <<'PY'
import json, re, sys
with open(sys.argv[1], encoding="utf-8") as source:
    result = json.load(source)
if result.get("outcome") != "found":
    raise SystemExit("Issue read did not find the record; retain its full receipt.")
projection = result["projection"]
if projection["identity"]["owner_ref"] != sys.argv[2]:
    raise SystemExit("Issue owner differs from this execution; do not mutate.")
digest = projection["source"]["digest"]
if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
    raise SystemExit("Issue read did not supply an exact source digest.")
print(digest)
PY
}

"$AWARE" issue resolve-read-projection --repository-root "$aware_repo_root" \
  --issue-ref "$first_issue_ref" --format json > "$first_issue_evidence/scope-read.json"
first_issue_scope_guard="$(first_issue_read_guard "$first_issue_evidence/scope-read.json")"
"$AWARE" issue bind-scope --repository-root "$aware_repo_root" \
  --issue-ref "$first_issue_ref" --expected-source-sha256 "$first_issue_scope_guard" \
  --scope-path "$first_issue_record" --scope-path aware.protocol.toml \
  --scope-path docs/specs/json-checker \
  --client-intent-id "$first_issue_intent_prefix-scope" \
  --actor-ref "$first_issue_actor" --actor-evidence-ref "$first_issue_actor_evidence" \
  --format json > "$first_issue_evidence/scope.json"

"$AWARE" issue resolve-read-projection --repository-root "$aware_repo_root" \
  --issue-ref "$first_issue_ref" --format json > "$first_issue_evidence/progress-read.json"
first_issue_progress_guard="$(first_issue_read_guard "$first_issue_evidence/progress-read.json")"
"$AWARE" issue start-progress --repository-root "$aware_repo_root" \
  --issue-ref "$first_issue_ref" --expected-source-sha256 "$first_issue_progress_guard" \
  --client-intent-id "$first_issue_intent_prefix-progress" \
  --actor-ref "$first_issue_actor" --actor-evidence-ref "$first_issue_actor_evidence" \
  --format json > "$first_issue_evidence/progress.json"
"$AWARE" issue resolve-read-projection --repository-root "$aware_repo_root" \
  --issue-ref "$first_issue_ref" --format json > "$first_issue_evidence/admitted-read.json"
printf 'Inspect admitted-read.json for owner, in_progress status and exact scope.\n'
```

## Inspect the outcome before continuing

The final read should be `outcome=found`, with this execution as owner,
`status=in_progress` and the three chosen scope paths. Preserve the separate
create/scope/progress receipts and actual source digests. Declared
`harness:<execution>` evidence is not cryptographic authentication. Read
projections and this decoding helper do not themselves authorize effects.

On any nonzero exit, stop and retain the receipt and stderr. Do not repeat the
whole block, invent success, reuse another execution or assume earlier effects
were rolled back. An invalid reference refuses before creating the Issue;
other failures may follow already-applied snapshot or scope effects.

This block admits work only. It does not configure SPEC, create a draft, approve
anything, stage or commit files, close the Issue or perform recovery. Continue
through [SPEC setup/draft guidance](../WORKFLOW.md#paired-publication-and-closeout) and
[governed publication](../repository/README.md) under the admitted scope. Keep
the installed operation help and full effect/cleanup receipts available.

## Implementation branch for a tested JSON checker

Choose this branch **instead of** the draft branch for the explicitly selected
[JSON checker task](../tasks/JSON-CHECKER.md). It needs no SPEC, Workspace setup,
Project/Goal or Agent a12. Use a fresh task reference in an explicitly initialized
new customer target. Existing repositories require compatibility review; never
replace their instructions just to run this example. The customer must approve
the outcome, the six paths below and local publication/closeout. Other tasks need
their own approved paths and acceptance; this example grants none by itself.

Use Bash and keep the same shell for the four blocks below. Set `AWARE` to your
absolute installed command and `aware_repo_root` to the absolute customer target.
Set `task_python` to the actual absolute interpreter chosen for the task tests,
and `useful_author_name` / `useful_author_email` to the approved local Git author.
Change `useful_issue_ref` below before invocation if selecting another fresh
reference. Full receipts stay in a new private directory outside the repository.
On any nonzero result, stop and retain stdout/stderr; do not rerun a whole block
or refresh a guard automatically. Earlier effects may already have happened.

### Admit the implementation scope

```bash
set -euo pipefail
: "${AWARE:?Set the absolute installed command}"
: "${aware_repo_root:?Set the absolute initialized customer repository}"
: "${task_python:?Set the actual absolute task-test interpreter}"
: "${useful_author_name:?Set the approved local author name}"
: "${useful_author_email:?Set the approved local author email}"
test -x "$AWARE" && test -x "$task_python"
if test -n "${CODEX_THREAD_ID-}" && test -z "${CLAUDE_CODE_SESSION_ID-}"; then
  useful_actor="codex-$CODEX_THREAD_ID"
elif test -n "${CLAUDE_CODE_SESSION_ID-}" && test -z "${CODEX_THREAD_ID-}"; then
  useful_actor="claude_code-$CLAUDE_CODE_SESSION_ID"
else
  echo 'Missing or ambiguous genuine harness identity; remain read-only.' >&2
  exit 2
fi
useful_issue_ref='fb/2026-10-18/implement-json-checker'
useful_receipts="$(mktemp -d "${TMPDIR:-/tmp}/aware-implementation.XXXXXXXX")"
useful_intent="$(basename "$useful_receipts")"
printf 'Execution %s; retain receipts at %s\n' "$useful_actor" "$useful_receipts"
useful_coordinates=(--repository-root "$aware_repo_root" --issue-ref "$useful_issue_ref")
useful_actor_args=(--actor-ref "$useful_actor" --actor-evidence-ref "harness:$useful_actor")
"$AWARE" issue ensure-snapshot "${useful_coordinates[@]}" \
  --title 'Implement and test a read-only JSON checker' --priority P1 \
  --owner-ref "$useful_actor" --source-description 'Customer-approved implementation task' \
  --problem 'Check whether a file contains JSON without modifying the input.' \
  --objective 'Deliver working source, tests, usage documentation and local closeout.' \
  --acceptance 'Approved JSON-checker cases pass; input and unrelated bytes/modes survive.' \
  --client-intent-id "$useful_intent-create" "${useful_actor_args[@]}" \
  --format json > "$useful_receipts/create.json" 2> "$useful_receipts/create.stderr"

useful_read_guard() {
  "$task_python" - "$1" "$useful_actor" <<'PY'
import json, re, sys
from pathlib import PurePosixPath
with open(sys.argv[1], encoding="utf-8") as stream:
    result = json.load(stream)
if result.get("outcome") != "found":
    raise SystemExit("Issue not found; retain the original receipt.")
p = result["projection"]
if p["identity"]["owner_ref"] != sys.argv[2]:
    raise SystemExit("This execution does not own the Issue; stop.")
digest, path = p["source"]["digest"], p["source"]["path"]
if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
    raise SystemExit("No exact original Issue guard; stop.")
if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
    raise SystemExit("Issue record is not repository-relative; stop.")
print(digest)
PY
}
"$AWARE" issue resolve-read-projection "${useful_coordinates[@]}" --format json \
  > "$useful_receipts/scope-read.json" 2> "$useful_receipts/scope-read.stderr"
useful_scope_guard="$(useful_read_guard "$useful_receipts/scope-read.json")"
useful_issue_record="$("$task_python" -c 'import json,sys; print(json.load(open(sys.argv[1]))["projection"]["source"]["path"])' "$useful_receipts/scope-read.json")"
useful_paths=("$useful_issue_record" AGENTS.md aware.protocol.toml README.md src/jsoncheck.py tests/test_jsoncheck.py)
useful_scope_args=()
for useful_path in "${useful_paths[@]}"; do useful_scope_args+=(--scope-path "$useful_path"); done
"$AWARE" issue bind-scope "${useful_coordinates[@]}" \
  --expected-source-sha256 "$useful_scope_guard" "${useful_scope_args[@]}" \
  --client-intent-id "$useful_intent-scope" "${useful_actor_args[@]}" \
  --format json > "$useful_receipts/scope.json" 2> "$useful_receipts/scope.stderr"
"$AWARE" issue resolve-read-projection "${useful_coordinates[@]}" --format json \
  > "$useful_receipts/progress-read.json" 2> "$useful_receipts/progress-read.stderr"
useful_progress_guard="$(useful_read_guard "$useful_receipts/progress-read.json")"
"$AWARE" issue start-progress "${useful_coordinates[@]}" \
  --expected-source-sha256 "$useful_progress_guard" \
  --client-intent-id "$useful_intent-progress" "${useful_actor_args[@]}" \
  --format json > "$useful_receipts/progress.json" 2> "$useful_receipts/progress.stderr"
"$AWARE" issue resolve-read-projection "${useful_coordinates[@]}" --format json \
  > "$useful_receipts/admitted-read.json" 2> "$useful_receipts/admitted-read.stderr"
```

Stop and inspect `admitted-read.json`: require your owner, `in_progress` and the
six approved paths. The Issue identifier and observed Markdown path are different
coordinates. Read projections and the decoder grant no new authority or
authentication. Scope includes selected scaffold for first publication, not
permission to modify it; preserve `AGENTS.md`, `aware.protocol.toml`, the
init-created `docs/issues/PROTOCOL.md` and any unrelated note with their modes.
The last two may remain untracked outside publication; do not claim a clean tree.

### Implement and verify before publication

Use approved engineering tools to implement `src/jsoncheck.py`, meaningful
`tests/test_jsoncheck.py` and usage in `README.md`. Check the selected task's
ordinary and error cases, scalar values and input preservation. Document actual
limits, including interpreter nesting limits; a closed Issue does not prove
application correctness. Provider-native edits are not Workspace CAS receipts.

Record the actual interpreter and run this task's tests; a failure stops before
publication. Read both test streams and inspect the source changes and preserved
files before continuing. Do not infer the test interpreter from Aware's install.

```bash
"$task_python" -c 'import sys; print(sys.executable); print(sys.version)' \
  > "$useful_receipts/test-interpreter.txt" 2> "$useful_receipts/test-interpreter.stderr"
"$task_python" -B -m unittest discover -s "$aware_repo_root/tests" -v \
  > "$useful_receipts/task-tests.stdout" 2> "$useful_receipts/task-tests.stderr"
```

### Preview exact publication and review it

Local publication/closeout must be authorized. The next block only previews it.
Use the approved author, not a borrowed evaluation author. Keep the original read
guard and exact request unchanged between this preview and the next decision.

```bash
export GIT_AUTHOR_NAME="$useful_author_name" GIT_COMMITTER_NAME="$useful_author_name"
export GIT_AUTHOR_EMAIL="$useful_author_email" GIT_COMMITTER_EMAIL="$useful_author_email"
"$AWARE" issue resolve-read-projection "${useful_coordinates[@]}" --format json \
  > "$useful_receipts/publication-read.json" 2> "$useful_receipts/publication-read.stderr"
useful_publication_guard="$(useful_read_guard "$useful_receipts/publication-read.json")"
useful_publish=("$AWARE" issue publish-close "${useful_coordinates[@]}"
  --expected-issue-source-sha256 "$useful_publication_guard"
  --message 'Deliver the tested read-only JSON checker'
  --resolution 'Approved implementation and verification reviewed; local closeout selected.'
  --verified-by "$useful_receipts/task-tests.stdout"
  --verified-by "$useful_receipts/task-tests.stderr"
  --client-intent-id "$useful_intent-publication" "${useful_actor_args[@]}" --format json)
for useful_path in "${useful_paths[@]}"; do useful_publish+=(--path "$useful_path"); done
"${useful_publish[@]}" --dry-run \
  > "$useful_receipts/publication-preview.json" 2> "$useful_receipts/publication-preview.stderr"
```

**Review stop:** inspect preview, source/test results, actual selected files and
unrelated bytes/modes. The dry-run neither commits nor closes; it does not pin
earlier HEAD/work-file bytes for apply. If reviewed inputs change, stop and make
a new explicit decision—do not update the saved request or refresh its guard
silently. Do not run apply merely because the previous block exited zero.

### Explicitly apply the reviewed request

Only after that review, run this block in the same shell with the same array.
It invokes the original paired operation once, not two independently replayable
capabilities. Capture both streams before inspecting the result.

```bash
"${useful_publish[@]}" \
  > "$useful_receipts/publication-apply.json" 2> "$useful_receipts/publication-apply.stderr"
"$AWARE" issue resolve-read-projection "${useful_coordinates[@]}" --format json \
  > "$useful_receipts/closed-read.json" 2> "$useful_receipts/closed-read.stderr"
```

Inspect both original receipts and the final Issue projection. Implementation
and closeout are separate non-atomic effects: retain commit identities, CAS/index
and cleanup results, partial effects and unknowns. A failure may follow a known
commit; it does not imply rollback. Standalone close cannot recover spent live
authority from saved Git JSON. Never republish, refresh guards or retry a mutation
to recover a receipt. Stop and request a supported recovery disposition instead.
Keep known untracked scaffold/foreign files; remote push remains a separate
authorization. Human inspection, not this script, decides task acceptance.
