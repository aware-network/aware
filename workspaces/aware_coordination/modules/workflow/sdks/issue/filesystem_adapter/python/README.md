# Aware Issue filesystem adapter

Filesystem authority provider for canonical Issue SDK operations.

## Issue references

Supply `fb/YYYY-MM-DD/<slug>`, for example
`fb/2026-10-11/json-checker-draft`. A slug contains lowercase letters or digits,
with single hyphens between segments. A reference is not a Markdown path:
the provider resolves it under the Issue root admitted by `aware.protocol.toml`
using `YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md`.

Malformed references return the existing `issue_ref_invalid` diagnostic followed
by the expected syntax and an example. This guidance comes from this owner and
survives SDK and CLI JSON/summary presentation unchanged. Invalid syntax refuses
before manifest admission or target access; it does not select a corrected
reference, broaden authority or authorize a retry.

## Bounded identity lookup

Bounded reads and mutations still check every admitted `fb-*.md` candidate under
the original Issue root for duplicate identity. The original Issue runtime's
`read_issue_source_header` reuses the same Markdown parser, including case-folded
field names, first-Tag selection, value normalization and indented continuations.
Headers permanently end at the first section in that grammar; a completed
header can therefore establish identity without loading an oversized body.

The existing source-byte ceiling also bounds each candidate's identity lookup.
Reads use chunks of at most 4 KiB, with at most one extra byte to detect overflow.
EOF completes a small sectionless header. If neither EOF nor the header boundary
is established within the ceiling, or the header cannot be read/decoded, the
original `issue_duplicate_candidate_unavailable` refusal remains. No overflow
candidate is silently skipped. Known duplicate headers still refuse before
mutation, including when their bodies are oversized or invalid UTF-8.

This identity check does not validate or expose another candidate's body.
Selected Issue source, manifest and planned-result limits remain unchanged;
large selected records still require the supported full-source profile. Ordinary
unbounded defaults retain their existing behavior. Sequential filesystem lookup
is not atomic root isolation, a lease or an Evaluation observation capability.

## Genuine single-use source-change admission

`FilesystemIssueOperationProvider.admit_source_change()` freshly resolves the
original Issue authority and verifies exact bytes, invoking harness execution,
owner, In Progress lifecycle and the shared exact-or-prefix scope policy.
The request contains no claimed actor. Exactly one supported nonblank harness
session is observed; ambiguity and missing identity refuse. This is
`filesystem_harness_observed_v1`, not authenticated resident Actor authority.

The owner-issued, process-local admission retains the original provider,
Issue file/parent identities, immutable intent and the qualified FileSystem
physical handle. `validate_source_change()` rejects structural or foreign
provider permits. The admission exposes only fixed bound physical operations,
not an arbitrary callback guard. It rechecks Issue and physical currentness
before/after each operation and at completion, accepts only the actual
owner-created manifest replacement, consumes once and irreversibly retires
on refusal/interruption/release. Known/unknown effects remain without rollback.

Completion includes the physical owner's read-only consumed-identity check
after the final Issue read. This is a bounded sequential cooperative read
horizon, not atomic cross-owner isolation, a source lease or continuous
confinement. Matching digests cannot revive a retired admission. SDK requests,
receipts and effects cannot mint it.

Protocol must still supply candidate semantics and its concrete supported
writer/composition, then prove a fresh SPEC read. The source proofs here use
explicit supplier roots because this adapter is not installed in the selected
environment. No aggregate projection/locks, installation, public command,
service activation, repository publication capability, Goal/Issue lifecycle
admission, build, release or push is implied.

The adapter admits an explicit `aware.protocol.toml`, resolves the declared
Issue authority record beneath the repository, delegates Markdown meaning to
`aware-issue-runtime`, applies transitions through
`aware-issue-operational-runtime`, and writes with source-digest CAS. It does
not select work or use the compatibility local-state cache.

Repository publication delegates to `aware-workspace-operator`; this adapter
does not stage files, compose commits, or mutate refs itself.

Close verifies the supplied implementation-publication Git receipt through the
Workspace owner, writes the Closed projection under source CAS, and delegates
the Issue-only closeout commit under the admitted pre-close authority snapshot.
If publication fails, the adapter restores the exact pre-close source under a
second digest guard. The returned closeout receipt is distinct from the prior
implementation receipt recorded in the Issue.

Durable replacement uses the canonical block, set-owner, and resume operations.
Only the authored current owner may transfer a non-Closed Issue, and every step
requires the latest source digest. The provider records the new owner and
handoff activity in the Issue authority record; it does not infer ownership
from a CLI process or local cache. Unassignment is not exposed by this first
filesystem interface.

## Optional Specification pairing read

The explicit `aware_issue_fs_adapter.specification_iteration` composition uses
the `specification` extra. Ordinary Issue operations do not load SPEC and keep
their existing dependency closure. This source entrance is not an installed
consumer capability or a CLI command.

`FilesystemSpecificationIterationBindingProvider` requires a live, genuine
SPEC iteration admission plus the explicitly selected repository/manifest.
It freshly consumes the original owner port, admits the real Protocol bytes,
maps source-base/namespace coordinates, compares every selected closure member
to committed regular-file bytes and reads the Issue through the existing owner.
Manifest, source, Issue and HEAD are revalidated before returning. New Issues
may be uncommitted; SPEC must have a committed epoch. Unborn Git cannot supply
that epoch, without disabling ordinary unbound Issue use.

Uniqueness is scoped to the explicit SPEC closure assembled by its owner. The
`<spec-key>` template slot identifies a location, not a guessed semantic key.
Other packages are not discovered by following dependency refs. The result
reports this explicit selection and a bounded sequential read horizon, not
atomic cross-owner isolation or permanent currentness over later changes.

Every result is non-authorizing: no durable binding/cardinality slot, approval,
Issue claim, WorkContext, dispatch or publication. Closed, unassigned and
foreign-owned Issues remain observable. Actual SPEC retirement is authoritative;
caller-built DTOs, closures, raw paths and matching digests cannot replace it.
The genuine SPEC provider and pairing context must remain alive and be closed
by their respective owners. No fallback to Service/API or legacy SPEC parsing.
