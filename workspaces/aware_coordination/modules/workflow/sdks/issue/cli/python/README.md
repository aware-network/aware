# Aware Issue CLI

Thin command-line projection of canonical Issue SDK operations.

The read and lifecycle commands select the filesystem provider and render its
typed result. The CLI does not parse Issue Markdown, implement transition
rules, select work, or treat local compatibility state as authority.

`commit-workspace` explicitly composes Issue SDK → Issue runtime → supplying
Workspace SDK, using the original FS writer. The FS adapter performs its own
IO only and no longer dispatches foreign publication or rollback orchestration.

`close` composes the canonical close operation; its JSON result distinguishes
the supplied implementation receipt from the closeout publication receipt
created by the selected authority. A fresh standalone invocation cannot recover
original completion authority from a Git receipt and therefore refuses.

## Explicit publication and closeout loop source checkpoint

`publish-close` performs implementation publication, then separately admits and
publishes closeout through the same genuine owner lifetime. It is **not atomic**.
Both complete original owner receipts remain visible if closeout fails. Unknown
CAS, unavailable unlock, pending index projection or consumer-return refusal
stops the sequence; there is no publication retry or source rollback.

```text
<explicitly selected Issue CLI> publish-close \
  --repository-root /absolute/approved/repository \
  --issue-ref fb/YYYY-MM-DD/approved-task \
  --expected-issue-source-sha256 sha256:<exact-Issue-bytes> \
  --path exact/implementation/path \
  --message "Publish approved change" \
  --actor-ref <genuine-provider-execution> \
  --actor-evidence-ref <approved-evidence> \
  --client-intent-id <close-intent> \
  --resolution "Completed bounded work" \
  --verified-by <verification-evidence> \
  --format json
```

The Issue must be In Progress, owned by the genuine harness execution, and
scope both the implementation and its exact Issue document. The supplied Issue
digest is also the closeout source guard: it is not automatically refreshed
after publication. A concurrent Issue edit refuses closeout and stays intact.
`--dry-run` only plans implementation; it neither publishes nor closes.

Each `aware.issue.repository-operation.v2` receipt contains the full Workspace
result, Issue observation and original cleanup observations. JSON and summary
both preserve current-operation failure/publication evidence, including all 32
writer fields. These are presentation carriers, not the ordinary v1 result or
a new native semantic binding. `present-receipt` also reads saved full compound
output without restoring authority. Save full JSON before presenting summaries.

This proves source-level CLI composition only. Successor dependency/profile
qualification and checkout-hidden neutral installation remain separate; neither
the selected aware-dev host command nor public artifacts are changed.

`block`, `set-owner`, and `resume` expose durable filesystem handoff. They are
separate commands because a failed transfer must leave the blocked state
visible instead of reporting an atomic handoff that did not occur.

## Reusable family registrar (0.8.0 source checkpoint)

`aware_issue_cli.main.register_issue_commands(registry)` registers the existing
eleven SDK projections, saved-result presentation and the explicit compound
projection in Kernel's public
`AwareCommandRegistry`. The standalone main consumes exactly that registrar and
dispatches through `aware-command-runtime>=0.1.1,<0.2.0`. Registration performs
no provider construction, admission, operation execution or filesystem effects.
A colliding leaf name refuses before any command from this family is added;
foreign registrations are never replaced.

The registrar's operation labels identify existing SDK contracts, not a new
operation or package-selection catalog. `present-receipt` has no SDK operation
label: it is presentation only and never restores authority. The existing flags,
JSON/summary defaults and typed requests remain unchanged for ordinary reads
and mutations. Publication/closeout consumer binding and evidence use the
explicit lossless successor above. Registry help includes leaf
descriptions; this is a presentation difference, not a new capability.

A composing client mounts the returned command specifications, preserves their
leaf names, parser configuration and `_aware_command_name` dispatch marker, and
uses Kernel's actual dispatch. The handler uses the selected leaf specification,
not a parent family's `args.command`. Invocation context is not Issue authority.
No permanent subprocess wrapper or copied handler is required. This module is
not eagerly imported by the package facade.

This is a supplier source checkpoint only. Workspace's canonical
`portable_protocols` profile still determines the consumer package closure.
Compatible installed composition, public selection and aware-dev operational
bootstrap replacement are separate gates.

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
