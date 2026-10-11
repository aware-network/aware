# Aware Issue CLI

Thin command-line projection of canonical Issue SDK operations.

## Issue reference inputs

Every target command takes `--issue-ref fb/YYYY-MM-DD/<slug>`, not an Issue
Markdown path. For example, use `--issue-ref fb/2026-10-11/json-checker-draft`.
The slug uses lowercase letters or digits separated by single hyphens. The FS
provider resolves the reference through the admitted Protocol Issue binding;
with root `docs/issues`, this example selects
`docs/issues/2026/10/11/fb-2026-10-11-json-checker-draft.md`.

The same argument help is available through the standalone registrar and
`aware issue <command> --help`. Invalid references preserve the original
`issue_ref_invalid` code and the provider's syntax/example diagnostics in both
JSON and summary output. The CLI neither guesses a reference from a path nor
implements another grammar or repairs authority.

CLI 0.8.3 retains FS adapter `>=0.9.4,<0.10.0` so the help and owner diagnostics
ship together. These source successors require a newly pinned installed
candidate; they do not alter the currently published installation.

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

## Publish implementation and close together

`publish-close` performs implementation publication, then separately admits and
publishes closeout through the same genuine owner lifetime. It is **not atomic**.
The returned receipts retain the original owner evidence if closeout fails. Unknown
CAS, unavailable unlock, pending index projection or consumer-return refusal
stops the sequence; there is no publication retry or source rollback.

Before publication, finish the Issue's admitted lifecycle and scope changes.
Observe the current source through the selected installation:

```text
aware issue resolve-read-projection \
  --repository-root /absolute/approved/repository \
  --issue-ref fb/2026-10-11/approved-task \
  --format json
```

Require `outcome="found"`. Use the returned `projection.source.digest` unchanged
as `--expected-issue-source-sha256`. It is `sha256:<hex>` over the **exact Issue
Markdown bytes**, not HEAD, a Protocol's normalized semantic digest, a SPEC
draft digest or implementation-file bytes. Any intervening Issue edit makes
that observation stale; do not automatically fetch a replacement guard and retry.

After reviewing the admitted paths, source and verification evidence, use the
paired command from that same selected installation. Substitute the observed
guard and your genuine execution/evidence coordinates below:

```text
aware issue publish-close \
  --repository-root /absolute/approved/repository \
  --issue-ref fb/2026-10-11/approved-task \
  --expected-issue-source-sha256 <reviewed-projection.source.digest> \
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
Save the complete JSON output in an approved evidence location outside the
implementation paths, including on exit `2`. An implementation commit can exist
even when the paired command refuses later closeout; inspect every receipt,
not only the final outcome.

`--dry-run` only plans implementation; it neither publishes nor closes. A later
apply **prepares afresh**: it does not execute a retained dry-run plan or bind
itself to the preview's HEAD and implementation bytes. Review intervening
changes before deciding to invoke apply. Transaction-time owner validation is
separate; preview does not grant publication or retry authority.

The fresh standalone `close` command cannot reconstruct original completion
authority from `--publication-receipt-ref git:<commit>`. It refuses with
`issue_closeout_original_implementation_required`. If implementation is already
published, retain that receipt and request supported original-owner recovery;
the shipped CLI provides no durable completion reconstruction. **Do not
republish implementation just to regain close authority.**

## Handle publication refusals

Keep the exact owner code and full failure/publication/cleanup evidence. Stop
the attempted sequence; absence of diagnostics does not mean no effects.

| Owner code | Next action |
| --- | --- |
| `issue_publication_source_stale` | Observe the current Issue and review the change against the prior guard. Any new request needs explicit review and fresh admission; never silently refresh the guard until apply succeeds. |
| `issue_source_out_of_scope` | Compare rejected paths with admitted scope. Remove paths that do not belong, or explicitly admit the required scope through the Issue owner before a separately reviewed request. |
| `issue_closeout_original_implementation_required` | Preserve the implementation receipt and request supported owner recovery. Saved Git evidence is not completion authority; do not republish to regain it. |

Known publication stays known even if cleanup, closeout or consumer return
fails. Unknown publication or cleanup stays unknown; do not infer rollback,
successful unlock, permission to retry or completed closeout from Git reachability.
For a non-publication failure such as missing Git author identity, preserve the
original diagnostic and correct the input through its owner before evaluating
any separately admitted request. This does not promise zero preparatory effects.

`aware issue present-receipt --receipt-path /absolute/path/full-result.json`
shows saved evidence without replaying the operation. Its wrapper records
`operation_invoked=false`, `authority_restored=false` and
`currentness=not_revalidated`. Exit `0` means presentation succeeded, not that
the recorded operation succeeded. It neither recovers close authority nor
refreshes the Issue-source guard.

Each `aware.issue.repository-operation.v2` receipt contains the full Workspace
result, Issue observation and original cleanup observations. JSON and summary
both preserve current-operation failure/publication evidence, including all 32
writer fields. These are presentation carriers, not the ordinary v1 result or
a new native semantic binding. `present-receipt` also reads saved full compound
output without restoring authority. Save full JSON before presenting summaries.

This guidance follows the independently accepted nine-case shipped-install
audit. CLI 0.8.3's help is a source successor, not a changed public installation.
Successor dependency/profile
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
