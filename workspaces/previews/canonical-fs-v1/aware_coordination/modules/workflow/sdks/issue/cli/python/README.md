# Aware Issue CLI

Thin command-line projection of canonical Issue SDK operations.

The read and lifecycle commands select the filesystem provider and render its
typed result. The CLI does not parse Issue Markdown, implement transition
rules, select work, or treat local compatibility state as authority.

`commit-workspace` is the command-line entrance to the canonical checked
publication operation. It delegates all owner/status/scope and Git effects to
the filesystem provider and Workspace operator.

`close` composes the canonical close operation; its JSON result distinguishes
the supplied implementation receipt from the closeout publication receipt
created by the selected authority.

`block`, `set-owner`, and `resume` expose durable filesystem handoff. They are
separate commands because a failed transfer must leave the blocked state
visible instead of reporting an atomic handoff that did not occur.

## Full results and concise presentation (CLI 0.6.0)

The operational default remains `--format json`: the complete canonical SDK
result. Exit codes, requests, owner checks and domain effects are unchanged.
`--format summary` selects presentation `aware.issue.cli-summary.v2`. It preserves
current-operation diagnostics/evidence, exact operation/Issue/provider/operator
refs, commit/publication refs, reference-update/transaction/index results, and
explicit effect/cleanup fields. Missing currentness or outcome evidence remains
null/unknown, not a success inferred from Issue status.

Only `projection.evidence` (historical recorded evidence) is replaced with an
explicit omission descriptor: count, deterministic presentation digest, encoded
byte size and original Issue source coordinates. The digest binds that collection
using sorted compact ASCII JSON in UTF-8, **not** Issue source bytes, Protocol
manifest bytes, SPEC closure or a live owner admission. Current-operation evidence
is not truncated, so unusually large current receipts can still be large.
This is not a universal output-size guarantee.

The renderer stores nothing. For an exact historical full result, retain the
original JSON response in your consumer's evidence capture before presenting it:

```text
<explicitly selected aware-issue-cli> resolve-read-projection ... --format json
<explicitly selected aware-issue-cli> present-receipt --receipt-path /absolute/path/full-result.json
```

`present-receipt` reads an existing regular JSON file (maximum 16 MiB), rejects
duplicate keys/nonfinite numbers/summary inputs, and never constructs a provider,
replays a domain operation, refreshes guards, writes files or restores capabilities.
Optional `--expected-receipt-sha256 sha256:<hex>` guards exact saved file bytes;
it is distinct from the historical-collection digest in the summary. Paths are
relative to the invoking process working directory unless absolute. Symlinks and
nonregular leaf inputs refuse.

Its output wraps the unchanged result or its summary with presentation evidence:
original receipt path/digest, `operation_invoked=false`,
`currentness=not_revalidated`, `authority_restored=false`. Exit 0 means presentation
succeeded, **not** that the recorded operation succeeded. Recorded refusal,
partial-publication, pending-reconciliation and unknown cleanup remain visible.
`--format json` on this command returns the original full result inside the wrapper.

Durable recovery still starts with original Issue/source records and fresh admission
for the new execution. A later `resolve-read-projection --format json` observes
current source; it is not retrieval of an unchanged historical result unless the
source digest still matches. Saved output is evidence, never authorization to retry.
Inspect recorded publication and reconciliation evidence before any retry;
reobserve/review stale sources rather than silently refreshing until apply succeeds.

This successor source is not an installed release or a new selected entrance.
Protocol/Bundle must pin and qualify its neutral closure; Repository reviews
publication/failure presentation parity. No change to aware-dev bootstrap selection
is implied.
