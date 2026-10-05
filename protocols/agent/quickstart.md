# One bounded customer task

Commands below use Bash. Setup installs the versioned root contract and modules;
inspect its preserved-file/integration report before continuing.

Read [the contract](AGENTS.md). Install as described in [README](README.md).
Use an existing customer Git repository with committed HEAD and configured Git
author. The customer approves the objective and exact source paths; examples
below use `src/result.py`, not a license to edit an arbitrary repository.

## Establish the inputs

For Codex, require the actual harness variable. For another provider use its
corresponding stable identity; do not copy a Codex identifier.

```sh
test -n "$CODEX_THREAD_ID" || exit 1
execution_id="codex-$CODEX_THREAD_ID"
aware_cmd=/tmp/aware-agent-env/bin/aware
aware_python=/tmp/aware-agent-env/bin/python
customer_repo=/absolute/customer-repo
issue_ref=fb/2026-10-05/customer-task
issue_path=docs/issues/2026/10/05/fb-2026-10-05-customer-task.md
```

Select your actual date/slug and exact repository. In a fresh profile:

```sh
"$aware_cmd" init --repository-root "$customer_repo"
bootstrap_paths=(aware.protocol.toml AGENTS.md .aware/agent-protocol.md
  .aware/agent-bootstrap.json docs/agents/README.md docs/agents/operational-work.md
  docs/agents/repository-change.md docs/agents/verification-and-handoff.md
  docs/issues/PROTOCOL.md docs/alignment/README.md docs/alignment/PROTOCOL.md
  docs/alignment/CURRENT.md)
scope_args=()
for owned_path in "${bootstrap_paths[@]}"; do
  scope_args+=(--scope-path "$owned_path")
done
"$aware_cmd" issue open --repository-root "$customer_repo" \
  --issue-ref "$issue_ref" --title "Customer-approved bounded outcome" \
  --scope-path src/result.py "${scope_args[@]}" \
  --client-intent-id "$execution_id:open:customer-task" \
  --actor-ref "$execution_id" --actor-evidence-ref "harness:$execution_id"
```

`open` delegates snapshot creation, exact scope binding and start-progress to
three existing SDK operations. The Issue path is included automatically; retain
each receipt. If it reports `incomplete`, inspect those operations rather than
assuming rollback. An existing Issue is not overwritten. Setup paths are scoped
above because this first task will commit them too.
For existing customer docs, review the report and include only paths explicitly
approved for publication; do not absorb unrelated work. An optional
`--link-existing-agents` setup is an explicit customer preparation decision.

Define a helper that observes the latest digest through the installed operation:

```sh
issue_digest() {
  "$aware_cmd" issue resolve-read-projection \
    --repository-root "$customer_repo" --issue-ref "$issue_ref" |
    "$aware_python" -c 'import json,sys; print(json.load(sys.stdin)["projection"]["source"]["digest"])'
}
```

Record the **real** approved objective and acceptance, replacing the example:

```sh
"$aware_cmd" issue append-update --repository-root "$customer_repo" \
  --issue-ref "$issue_ref" --expected-source-sha256 "$(issue_digest)" \
  --client-intent-id "$execution_id:objective:customer-task" \
  --actor-ref "$execution_id" --actor-evidence-ref "harness:$execution_id" \
  --message "Customer objective: <actual request>. Acceptance: <actual checks>."
```

## Implement, verify, publish

Perform only the approved source changes. Run the real checks; do not turn the
example below into a fabricated test pass. Record their result:

```sh
"$aware_cmd" issue append-update --repository-root "$customer_repo" \
  --issue-ref "$issue_ref" --expected-source-sha256 "$(issue_digest)" \
  --client-intent-id "$execution_id:verification:customer-task" \
  --actor-ref "$execution_id" --actor-evidence-ref "harness:$execution_id" \
  --message "Verification: <actual command, result and evidence>."

commit_digest="$(issue_digest)"
publication_paths=(src/result.py "$issue_path" "${bootstrap_paths[@]}")
publication_args=()
for owned_path in "${publication_paths[@]}"; do
  publication_args+=(--path "$owned_path")
done
"$aware_cmd" repository commit --repository-root "$customer_repo" \
  --issue-ref "$issue_ref" --expected-issue-source-sha256 "$commit_digest" \
  "${publication_args[@]}" --message "Deliver customer-approved outcome" \
  --actor-ref "$execution_id" --actor-evidence-ref "harness:$execution_id" --dry-run
```

Inspect the plan. If it matches the approved work, invoke the **identical** command
without `--dry-run`, retaining its JSON output. No raw `git add`/`git commit`.
An out-of-scope path or wrong owner must be refused; preserve that evidence.
Unrelated staged and unstaged work must remain untouched.

Extract the **actual** `publication_receipt_ref` from that apply result. Use it
below, not a placeholder or a guessed hash:

```sh
publication_receipt='git:<actual commit from the successful apply result>'
"$aware_cmd" issue close --repository-root "$customer_repo" \
  --issue-ref "$issue_ref" --expected-source-sha256 "$(issue_digest)" \
  --client-intent-id "$execution_id:close:customer-task" \
  --actor-ref "$execution_id" --actor-evidence-ref "harness:$execution_id" \
  --resolution "<actual bounded outcome>" --verified-by "<actual verification>" \
  --publication-receipt-ref "$publication_receipt"
```

Close validates the implementation receipt and publishes a separate Issue-only
closeout. Neither operation pushes a remote, approves a Goal, or dispatches work.
Git publication here is local; a remote push requires the customer's separate approval.

## Replace an execution

The current owner records remaining work and evidence, then uses `issue block`
and `issue set-owner --new-owner-ref <actual replacement execution>` with the
usual repository, Issue, current digest, actor/evidence and unique intent flags.
Each command needs a **fresh** digest. The replacement reads the projection,
checks its owner and scope, and calls `issue resume` as itself. Consult each
command's `--help` for exact flags. The former owner cannot resume after transfer.

No manual Issue edits. No automatic authority inferred from a chat handoff.
