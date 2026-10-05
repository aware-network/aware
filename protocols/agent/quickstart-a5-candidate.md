# a5 candidate: durable work through the installed owner

This is a preparation guide, not the selected public release. a4 remains the
published installation. This candidate targets Linux x86-64 / Python 3.12.
Use only the exact reviewed archive and separately pinned candidate manifest.
Install into a fresh environment with networking disabled; keep its source and
legal attachments. Do not overwrite an existing installation or bootstrap.

Obtain explicit approval for the repository, problem, objective, acceptance and
exact paths. Publish the genuine harness execution identity and set `actor` to
that exact identity; no model alias or inherited owner. Use the selected
installed `aware` executable, not a source checkout.

```sh
"$aware_command" --version
"$aware_command" contract
"$aware_command" init --repository-root "$customer_repository" --create-repository
"$aware_command" issue open \
  --repository-root "$customer_repository" \
  --issue-ref fb/2026-10-05/customer-result \
  --title 'Deliver the approved customer result' \
  --problem 'The approved request needs a durable work record.' \
  --objective 'Deliver the customer-approved bounded result.' \
  --acceptance 'Run the approved checks and preserve unrelated work.' \
  --scope-path src/result.py \
  --client-intent-id "$intent" \
  --actor-ref "$actor" --actor-evidence-ref "$actor_evidence" \
  --format summary
```

Creation intent is only for an approved new empty target; omit it for an
existing Git repository. Configure the customer's Git author explicitly; Aware
does not invent author identity, a remote or a seed commit. Scaffold files must
be separately approved and included in scope if they belong in the first commit.
The Issue path is included by the open composition.

Problem, objective and acceptance are repeatable plain single-line inputs.
New `open` requires them, but the shared SDK retains omitted-content legacy
compatibility. Criteria start unchecked. Narrative updates retain progress;
they do not rewrite authored content or automatically establish acceptance.
Open is non-atomic: inspect all partial receipts before recovery.

Observe through `issue resolve-read-projection` before every write. With default
JSON, retain `projection.source.digest`. Summary observations retain the same
digest under `source.digest`. Supply it to the next command, using
`--expected-issue-source-sha256` for repository commit and
`--expected-source-sha256` for other mutations. Never manufacture a digest.

`aware repository commit` accepts exact repeated `--path` arguments, current
Issue digest, actor/evidence and message. Inspect its dry-run before the
identical apply. Retain the actual `publication_receipt_ref` and verification
when closing through `aware issue close`. Both commands accept
`--format summary`; the default remains full SDK JSON.

Summaries preserve publication `operator_ref`, `transaction_mode` and
`reference_update`, plus diagnostics and receipts. Index fields describe that
operation only. Applied publication with pending reconciliation is not a clean
index. Unknown is absent evidence, never success. Closeout leaves authored
criteria unchecked and does not grant Goal acceptance, approval or dispatch.

Do not manually edit Issue records or repair staging to turn a refusal into a
pass. Keep foreign work and locks intact. For handoff, record remaining work,
block, set the replacement's real execution identity, and have that execution
observe and resume. Customer recovery is durable-record consumption, not
transcript authority. No Service/API, generated ontology, authentication,
hostile-process isolation, automatic bootstrap upgrade or remote push is implied.
