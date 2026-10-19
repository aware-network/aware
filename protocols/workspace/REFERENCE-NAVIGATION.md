# Workspace reference navigation

Agent **0.2.0a14** software was published at `08a598fdeb8f960bf30fb8e85229e820286e67be`.
Acquire that exact revision and retain its complete source/notice envelope.
This alignment changes current wording and pins, not software or operation authority.
Both reviews and original guards remain required.

Use the [workflow](../WORKFLOW.md) and
keep both explicit decisions. Contributor governance and Issue guards remain separate.

## Carry an original result explicitly through stdin

Workspace review now accepts `--reference-from-stdin` instead of `--reference`.
Supply exactly one complete UTF-8 JSON result captured from the original Agent
command, with `contract=aware.agent.workspace-review.v1` and its original
top-level `/reference`. The client delegates reference decoding and all live-use
checks to the original SDK. A nested reference, diagnostic string or a filename
inside JSON is not an alternative selector. The two flags are mutually exclusive.
Legacy inline `--reference` behavior is unchanged.

An input frame's `status`, apparent completion or human prose grants no authority.
The frame must reach EOF. Input is bounded to 2 MiB, 64 container levels and
65,536 nodes; malformed UTF-8/JSON, duplicate keys, non-finite values, interactive
or unavailable stdin and missing top-level references refuse. If the producer
does not close its stream, no automatic timeout or mutation retry is promised;
interrupt deliberately and retain the partial-input evidence. Exit 130 preserves
interruption and does not mean the SDK acquired or dispatched an operation.

Capture each original JSON result during its original invocation into a newly
chosen private file. Do not repeat a mutating command to recover its output.
Select all repository/evidence/result paths explicitly; never point this flow at
the acquired public contributor checkout. Historical inspection can focus a
complete selected list without copying a long reference:

```bash
: "${aware_customer_repo:?Set the customer repository}"
: "${aware_evidence_root:?Set the existing private disjoint evidence root}"
: "${aware_first_result:?Set the complete original prepare-result JSON file}"
"$AWARE" workspace review show --repository-root "$aware_customer_repo" --evidence-root "$aware_evidence_root" --reference-from-stdin --focus scope < "$aware_first_result"
```

`show --focus overview|scope|files|guards` is historical review only, with **no
current-use authority**. It preserves original release uncertainty and client
cleanup. A guard shown here is stored evidence, not a freshly observed guard.
Focus cannot be combined with `--json`; omitted focus preserves prior output.
For full JSON, use `show --json`; for original captured bytes, use `evidence`.
Neither reader replays the original operation or restores spent admission.

Stop after that first inspection. Only after explicitly accepting the physical
scope, choose a distinct scope intent and absent second-result file:

```bash
: "${aware_scope_intent:?Choose a new explicit scope decision intent}"
: "${aware_second_result:?Choose an absent private second-result JSON file}"
test ! -e "$aware_second_result"
test ! -L "$aware_second_result"
set -C
"$AWARE" workspace review scope --repository-root "$aware_customer_repo" --evidence-root "$aware_evidence_root" --reference-from-stdin --client-intent-id "$aware_scope_intent" --accept-reviewed-effect-scope --json < "$aware_first_result" > "$aware_second_result"
```

Stop again and inspect this second result and its complete evidence. Inspect its
final files with `show --focus files`, consuming **that second result**, not the
first. Scope acceptance does not authorize apply. Only after a separate final-file
decision invoke apply with its own intent:

```bash
: "${aware_apply_intent:?Choose a new explicit apply decision intent}"
"$AWARE" workspace review apply --repository-root "$aware_customer_repo" --evidence-root "$aware_evidence_root" --reference-from-stdin --client-intent-id "$aware_apply_intent" --accept-reviewed-final-files --json < "$aware_second_result"
```

Do not pipe prepare directly into scope/apply as an unattended sequence. Do not
blindly run these blocks in sequence. Fresh owner currentness checks still use
the original reviewed guards unchanged. Staleness requires a new explicit prepare
and review decision, never automatic refresh. Spent reuse remains refused and
may report genuine exit-3 retention/cleanup incompleteness. Workspace reference
transport does not automate Issue guard extraction, publication or closeout.

