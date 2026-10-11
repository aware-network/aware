# Admit your first filesystem Issue

After [installation and explicit initialization](../WORKFLOW.md), use the same
installed `aware` command to create a snapshot, bind approved paths and start
progress. These are three separate SDK operations, not one transaction. Init
does not admit an Issue, and this example does not grant task authorization.

## Reference versus record path

For this filesystem profile, `--issue-ref` is an identifier:

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

The reference is used by `--issue-ref`; the repository-relative record path is
used by `--scope-path`. They are not interchangeable. If you initialized a
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
