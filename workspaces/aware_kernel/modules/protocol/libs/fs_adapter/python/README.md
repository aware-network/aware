# aware-protocol-fs-adapter

Strict admission and lowering for repository-authored
`aware.protocol.toml` manifests.

## Retained initial profile bootstrap source checkpoint

Adapter **0.6.4**, SDK `>=0.3.1,<0.4.0`, exposes the explicit original bootstrap
provider and requires Runtime `>=0.1.1,<0.2.0`. Optional `bootstrap` requires
FileSystem `>=0.3.3,<0.4.0`; default dependencies remain free of that optional
supplier, Workspace and Service.
The existing `draft` range and reader semantics are unchanged.

The provider renders the canonical `aware.collaboration.fs_v1` manifest using
the existing manifest content validator. Only Issue records have authority;
Goal, Feed, Specification and Evidence remain unavailable. Versioned guidance
uses the installed `aware`, not producer checkout commands. Setting
`install_agent_contract=false` requests only the manifest and explicitly reports
that onboarding files were not installed.

Planning requires an independently checked concrete Git root, explicit ordered
missing Issue-root ancestors and absent file targets. The original FileSystem
retained creator supplies no-replace publication, permissions and per-path
effects; Protocol does not copy a writer. Existing files refuse even when their
bytes match. Existing directories retain modes; new directories are private.
No Git creation, seed commit, staging, remote or Issue lifecycle mutation occurs.

Apply spends the original runtime's claim before freshness checks and effects.
After confirmed physical disposal, return-time checks reobserve exact manifest
and guidance bytes, regular-file identities, modes, target directories and Git
root. Effects and original cleanup uncertainty survive failures, including
post-publication refusals. Later release cannot upgrade an uncertain cleanup.
Published bytes are never deleted as rollback and refusal never permits retry.

These checks qualify cooperative descriptor traversal and observed currentness,
not continuous confinement or every-write detection. Source integration does
not establish a shipped `aware init`, fresh consumer installation or release.

## Correlated admission return (0.6.3 source checkpoint)

The existing `FilesystemProtocolSdkProvider` now returns the original exact
SDK request with every successful or refused admission. SDK 0.3 requires this
correlation value and result wire v2; the dependency is `>=0.3.0,<0.4.0`.
Provider identity, path interpretation, manifest rules, diagnostics, retained
capabilities and optional draft mechanics are unchanged. No source refusal
becomes a fallback or a write permit. SDK 0.2 and this provider are not a
qualified mixed generation. Installed compatibility and candidate pinning
remain separate proofs; existing wheels/public previews stay unchanged.

## Original draft admission diagnostics in 0.6.2

Draft admission preserves the original `SpecificationSelectionError.diagnostics`
alongside `specification_draft_admission_failed`, the source exception class and
cleanup notes. A manifest-byte mismatch therefore retains
`specification_selection_manifest_changed`; callers do not need to infer the
reason from paths or independently repeat admission. The original exception
remains the chained cause. Unknown exceptions do not supply arbitrary diagnostic
attributes or raw messages, and process interruptions retain their original form.

This patch changes diagnostic carriage only. SDK signatures, ownership checks,
cleanup behavior, dependency ranges and authority are unchanged. A refusal before
SDK draft invocation is admission evidence, not proof that `create_draft` ran.
The 0.6.2 source checkpoint does not replace any accepted wheel or public preview;
a freshly pinned installed candidate remains a separate qualification.

## Original cleanup-completion evidence (0.6.1 source checkpoint)

The original target retains the same owner's resource ledger independently of
selection-registry removal. Each original selection cleanup attempts its owned
correlated reader and repository descriptor at most once, recording attempted
disposal, component failures and completion. A raised/ambiguous close is never
retried; a reused numeric descriptor is not an owned recovery target.

`observe_specification_draft_input` and `release_specification_draft_input` now
project that original history through their existing fields:
`owner_cleanup_attempted=false`, `owner_cleanup_outcome="not_attempted"` before
disposal, and `true`/`"completed"` only after the original component ledger
confirms disposal. Interrupted/failed completion remains `"incomplete"`;
missing original completion remains `"unknown"`. Neither a release returning
normally, a terminal phase, equal source bytes nor descriptor-count restoration
can supply this evidence. Snapshots remain detached history, not cleanup grants.

Target retirement and subsequent custody release preserve the first cleanup
outcome. A later normal return cannot upgrade an earlier failure, including after
test-only/manual disposal. Protocol completion describes only Protocol's owned
base resources: it does not certify Issue's independently transferred physical
claim, scratch removal, publication durability or consumer-owned readers. Those
outcomes and lifetimes remain independent; published bytes are never removed.

Protocol FS **0.6.1** changes no default dependencies, optional ranges, public
call shapes or record semantics. This is source evidence only. SPEC's existing
top-level cleanup contract still requires unknown Protocol completion and must
be separately adopted before verified customer authoring. The accepted 0.6.0
wheel/archive and their exit-2 qualification remain unchanged. Independent
review, a freshly pinned installed successor and exact public-content review
remain separate gates; no automatic retry of known publication is admitted.

## Draft input custody (0.6.0 source checkpoint)

Protocol 0.6 adds cleanup-only original custody before freshness validation.
`reserve_specification_draft_input(target, physical_plan=..., attempt_ref=...,
client_intent_id=...)` reserves the target under its owner lock, then reserves
the genuine FileSystem plan. Conflicts refuse before freshness or touching the
first owner. Coordinates come from retained historical issuance, including after
stale/terminal source; they are not fresh observations or authoring permits.

The opaque reservation lends its original `physical_reservation` to the Issue
coordinator. Issue authenticates its own disabled preparing admission; the lower
owners verify resource handoff only. Transfer FileSystem first, then call
`transfer_specification_draft_input` with that original physical claim and the
same opaque receiver identity. Issue keeps claims private and revalidates through
them before activation. Protocol does not authenticate an Issue or copy policy.

Reserved originals reject raw validation/bind/spend/read/finish/release entrances
before freshness or retirement. Transferred originals require their original
`input_claim`; bind additionally takes `physical_input_claim`. Nested physical
checks and reader acquisition forward the exact original physical claim.
Genuinely unreserved standalone entrances preserve their previous call shapes.
All successor Issue admissions must enroll, including legacy-shaped calls; old
Issue-only invisible claims and source-mixed generations are not qualified.

`observe_specification_draft_input` returns frozen historical evidence, not a
release grant. `release_specification_draft_input` disposes only owned originals
once and preserves independent outcomes/diagnostics. A joint reservation owns
its physical child until that child transfers; a Protocol claim never disposes
Issue's separately transferred physical claim. Collected reservations cannot
clean transferred claims. Foreign-process inputs refuse without cleanup.
Protocol cleanup completion stays unknown; a normal return is not proof of it.
Published packages and separately owned correlated readers survive writer cleanup.

The four custody ports and original types/refusal are exported from the public
facade without importing optional owners. Default runtime/SDK/schema dependencies
are unchanged; the `draft` extra now requires
`aware-file-system>=0.3.0,<0.4.0`. Missing custody exports refuse, without fallback.
No generated catalog/lock, wheel, installation or public preview changes follow
from this source checkpoint. The actual CLI leak and Issue/SPEC composition remain
separate. See the bounded source report at
`docs/reports/protocol-specification-draft-input-custody-20261007.md`.

## Governed SPEC draft ports (historical 0.5.0 source qualification)

`admit_specification_draft_target` retains one absent package target from a fresh
filesystem v1 manifest selection with an exact `sha256:<hex>` byte guard. The
parent must exist; existing targets (including dangling links) refuse. Original
capabilities cannot be constructed, copied, serialized or used from a fork.

The original target's guarded `manifest_locator: str` exposes the retained,
canonical repository-relative **Protocol** manifest coordinate, including nested
locations. It is not `selected_manifest_path`, which names the SPEC document.
Obtain it before exact Issue-request construction; it revalidates the original
target and rejects forged, foreign-process, stale or terminal holders. Detached
text may survive cleanup, but is never admission or write authority. Issue must
join this original coordinate to its request/provider selection as well as the
existing manifest-byte digest; equal bytes at different paths are not equivalent.
This source port does not by itself implement or accept that Issue-owned join.

Issue's genuine draft admission binds the original FileSystem plan, spends the
Protocol publication transition and finishes the exact correlated selection.
Protocol neither authorizes Issue effects nor stages, parses or publishes a
package. SPEC remains responsible for real staged parser/lowerer validation.
Caller DTOs, setup permits, callbacks, equal-body plans, unknown publication and
ordinary source observations cannot replace original owner evidence.

`admit_specification_draft_published_read` returns the existing
`SpecificationSourceSelection` with private original-postimage correlation.
FileSystem's fixed optional exports load lazily; ordinary import/reading remains
FileSystem-, Issue- and SPEC-independent. Independent readers survive writer
release; provider close does not release a consumer-owned selection. Consumed
target checks are read-only through that exact reader, never renewed write use.
Release each original holder under its own lifetime; target release never deletes
packages, removes scratch or releases another owner's physical plan/reader.
Original target cleanup is idempotent but currentness and transitions refuse after
release. Interrupted or stale checks terminally retire the relevant authority.

SPEC's separately accepted governed composition adds real staged parser/lowerer
validation and lossless effect/cleanup evidence above these original ports.
That is source evidence, not installed customer authoring, approval, iterations
or repository publication. Default read behavior is unchanged.

Protocol FS **0.5.0** versions these additive ports. Its optional `draft` extra
declares **`aware-file-system>=0.2.0,<0.3.0`**. Default dependencies are unchanged;
ordinary imports and uncorrelated reads do not load FileSystem, Issue or SPEC.
The extra supplies physical integration, not Issue authorization or a SPEC
writer. Missing or incompatible fixed owner exports refuse with
`specification_draft_integration_unavailable`; there is no fallback writer.

FileSystem 0.2.0 remains an owner-qualified release target: the current supplier
source metadata is still 0.1.5 and is not an admitted substitute. This source
checkpoint does not claim an installable draft dependency closure. Supplier
versioning, neutral projection, generated catalogs/locks, wheel construction and
fresh installed composition are separate gates. The retained Protocol 0.4.0
reader wheel and selected previews remain unchanged. SPEC must independently
prove reader parity before widening its existing `<0.5.0` reader bound; a writer
uses its separate governed dependency selection.

Qualification remains observed-state, cooperative confinement: not every-write
detection, continuous confinement, durability or hostile-code isolation.

## SPEC setup candidate preparation (source checkpoint)

`aware_protocol_fs_adapter.specification_setup.prepare_specification_setup`
prepares bytes only; `SpecificationSetupCandidate` is data, not authority.
It freshly admits an existing, regular, non-aliased `aware.protocol.toml` and
requires the exact byte preimage, filesystem authority and collaboration fs_v1
semantic version 1. It supports only unavailable SPEC → authority, with
`specification_fs_v1`, an explicit canonical relative root and the fixed
`<spec-key>/aware.spec.toml` template; an identical binding is byte-preserving.
Different active bindings, profile upgrades and authority handover refuse.

The editor supports an explicit `[records.specification]` table and a single
quoted `role = "unavailable"` or single-quoted equivalent. It preserves other
source spans, comments and LF/CRLF. Inline/dotted or multiline forms refuse;
even triple-quote markers in comments conservatively refuse this finite editor.
The before/after semantic delta and candidate bytes are checked through existing
canonical admission, not a second profile evaluator. Ordered directory intent
is limited to the selected root and its explicit ancestors.

This package performs no mutation, Issue evaluation or publication. Actual
directory preparation, mode-preserving replacement, identity revalidation and
single-use consumption belong to the genuine Issue/physical owner in the
optional client composition. FS adapter 0.4.0 requires SDK >=0.2.0,<0.3.0;
no lock projection, wheel build or installed closure is claimed here.

This package also implements the filesystem provider for the canonical
`protocol_sdk.admit_target` operation. The provider delegates to the existing
admission implementation; it does not copy profile or containment rules, probe
for a service, or fall back from `service_api` to filesystem authority.

The adapter validates structural shape, supported collaboration record
profiles, filesystem path containment, and the filesystem authority mode. It
returns neutral `aware-protocol-runtime` values. It does not select an SDK
implementation, inspect installed CLI capabilities, discover a service, or
allow filesystem fallback from Service/API authority.

The admitted filesystem profile retains repository roots and templates beside
the neutral Protocol manifest. Those locations do not enter the canonical
record profile/role binding, so a later Service/API adapter is not forced to
model filesystem paths.

Successful filesystem admission always requires an existing repository root.
The bytes entrance is useful for retained fixtures, but it requires the same
repository context and performs the same containment checks as the on-disk
entrance. A refusal made before source bytes are read reports no source digest.

Containment walks each declared POSIX path from the resolved repository root.
Every prefix observed to exist is resolved strictly; a symlink loop, broken
symlink, file-as-parent, or other resolution failure is refused. The untouched
tail after the first genuinely missing component remains permitted so a fresh
repository need not pre-create every declared record directory. Refusals use a
stable Protocol reason plus a separate exception-class detail.

Manifest admission proves the observed bootstrap and record roots were
contained at that moment. Every owning filesystem operation must still resolve
and validate its concrete target at use time; templates and mutable filesystem
topology are not permanent authorization.

## Native Goal source capability (source implementation)

Strict admission now recognizes these separate combinations:

- `aware.collaboration.fs_v1`, semantic version 1, with the unchanged legacy
  `aware.goal.markdown.v1` record profile.
- `aware.collaboration.fs_v2`, semantic version 2, with
  `aware.goal.phase.markdown.v1`. Goal and Issue records must have authority
  roles. Other record families retain their independently declared profiles.
- `aware.collaboration.fs_v3`, semantic version 3, preserves the fs_v2 native
  Goal and Issue profiles and requires an authoritative
  `aware.project.context.toml.v1` record with the finite
  `project-<slug>.toml` location template.

The v1 manifest envelope and `canonical_v1` admission outcome are unchanged;
the outcome names the admission contract, not collaboration-profile version.
Admission is not a Goal carrier decoder, an eligibility decision or installed
operation proof. The Goal owner reads exact V2/V3 and refuses native V1 or
legacy substitution. No Goal writer is introduced.

`admit_native_goal_resolver(repository_root=..., manifest_path=...)` is the
on-disk capability issuer. Its result contains the actual admission and either
a `NativeGoalResolverCapability` or no capability for a refused admission.
Requesting issuance from a valid legacy profile raises
`NativeGoalResolverError("native_goal_profile_required")`, never falls back.
The same native Goal issuer accepts fs_v3 because it retains the exact same
native Goal record profile and authority role there; it returns the same
`NativeGoalResolverCapability` type, not a renamed Project token or fs_v2
fallback. The Goal owner still proves actual committed Goal readings.

The native Goal provider must call `require_native_goal_resolver(value)` at its
entrance and derive its repository from the returned capability. A caller-built
`FilesystemRecordBinding`, decoded result, digest or raw root is not accepted.
Public capability construction, subclassing, copying and pickling are refused;
even an unregistered nominal object fails the issuer-membership check. This is
a process-local caller-data boundary, not a sandbox against hostile Python
code with access to private module internals. Another process must freshly
admit the manifest through the selected composition; fork-inherited capability
objects refuse because their issuer process identity differs.

The capability retains the repository path and device/inode identity, exact
manifest coordinate and byte digest, complete admitted profile, and Goal
root/template. `revalidate()` checks current repository identity, readmits the
same on-disk manifest, and compares its bytes, profile and source coordinate.
Properties expose immutable retained metadata, not fresh observations; the
provider must revalidate at invocation and again before returning success.

The initial native template grammar is deliberately finite:

- `YYYY/MM/DD/goal-YYYY-MM-DD-<slug>.md`
- `goal-YYYY-MM-DD-<slug>.md`

Dates must be real calendar dates, repeated directory/file dates must agree,
and slugs are lowercase ASCII kebab tokens. Other templates refuse native
admission; no glob, regex or inferred layout is used. `match_goal_path(path)`
revalidates and returns location date/slug or `None` for a path outside the
declared grammar. `resolve_goal_path(path)` additionally checks current
containment beneath both repository and resolved Goal root, returning a frozen
`NativeGoalLocation`. Neither method reads Goal content or authenticates its
identity. Missing targets remain possible: Goal must prove committed source
availability, regular-file identity, unique Goal identity, V2/V3 carriage,
Gate, prerequisites and Git epoch itself. All prerequisites use the same
capability; no fixed `docs/goals` discovery is required.

`NativeGoalResolverError` carries a stable `code` and `diagnostics` tuple for
pre-source refusals. Do not turn it into an invented Goal observation digest.
No Protocol dependency is added to neutral Goal runtime, and the existing
public Protocol SDK transport remains unchanged. These are source capabilities;
this fs_v3 change alone proves neither an installed fs_v3 Goal operation nor a
new customer distribution.

## Project location capability (source implementation)

`admit_project_resolver(repository_root=..., manifest_path=...)` issues only
from fresh, on-disk fs_v3 admission. The opaque `ProjectResolverCapability`
retains the real native Goal capability from that same issuer invocation and
the admitted Project root/template. `goal_capability` exposes that genuine
token to the existing Goal provider after revalidation; a constructed binding,
digest, decoded result, raw root, copied token or fork-inherited token cannot
replace either capability. The Project token revalidates repository identity,
manifest bytes, source coordinate and complete profile through the retained
Goal issuer before use. Manifest/profile changes revoke both tokens.

`match_project_path` accepts only a flat `project-<slug>.toml` location beneath
the admitted customer root. `resolve_project_path` additionally checks current
repository and Project-root containment. The returned slug is location
metadata, not `project_key` or committed source proof. A missing target may be
a valid location; the Project provider must verify committed regular-file
identity, bounded complete discovery, content-owned key uniqueness, source
publication/currentness, participating Goal readings and terminal containment
and HEAD checks. Neither capability creates an FO1 namespace, Object/branch,
caller admission, Service result, or installed customer capability.

## SPEC source selection (0.3.0 source implementation)

The separate read-only SPEC composition uses `admit_specification_selection`:
explicit `repository_root`, `manifest_path`, ordered unique
`selected_manifest_paths` and optional exact `expected_manifest_sha256`.
Only `aware.collaboration.fs_v1 / semantic_version=1` with authoritative
`specification_fs_v1` and `<spec-key>/aware.spec.toml` is admitted initially.
The slot is one location segment, not the semantic Specification key. Selected
paths are repository-relative; all required roots are supplied explicitly.
There is no SPEC scan, parser, dependency-root discovery or fixed `docs/specs`.

`SpecificationSelectionAdmission` contains the actual canonical admission and
an opaque `SpecificationSourceSelection`, or no selection for semantic
admission refusal. Source/selection failures raise `SpecificationSelectionError`
with stable `code`/`diagnostics`. The issuer reads at most 1 MiB of manifest
bytes through no-follow regular-file descriptors and delegates those owner-read
bytes to existing canonical admission. It accepts no caller bytes/decoded
bindings. Wrong/outside manifest locations and nonregular/symlink manifests
refuse before content reads. This more restrictive source entrance does not
rewrite the existing compatibility manifest admission contract.

The issuer retains its repository descriptor, device/inode/mount and namespace
identity, manifest file/parent identity, exact manifest-byte digest, admitted
profile and selected package roots. `require_specification_selection` and the
selection's `revalidate()` check actual issuance/process/lifetime, freshness and
no-follow path topology. Missing tails remain possible; the SPEC owner proves
availability. Prefix identities become retained when first observed, so later
same-content directory replacement still refuses. Copying, serialization,
nominal forgery and fork-inherited use refuse. This is Linux source support,
not hostile-code isolation or a permanently authorized filesystem topology.

`consume_specification_selection(selection, receiver)` is the trusted factory
bridge. `receiver(borrowed_fd, roots, guard)` receives a **fresh duplicate** and
returns a consumer with `close()`. It must duplicate the borrowed descriptor
into its provider, never close the borrow itself or reopen an unchecked path.
The borrow closes on all exits; receiver exceptions must clean their own partial
construction. The bridge revalidates before returning. On final validation
failure it calls the returned consumer's `close()` to retire that provider's
descriptors/admissions; cleanup failures are secondary exception notes, never
success or a replacement refusal. No result is exported as JSON authority.

Provider close must not call `release_specification_selection`: selection
lifetime belongs to the composition and can be shared across providers.
Explicit release closes the issuer descriptor and makes further guarded use
refuse; garbage collection also closes an unused issuer descriptor. Each
provider's duplicate remains its own cleanup responsibility.

SPEC must implement its **read-only** `from_protocol_selection` factory and
pre/post observation/admission/source-evidence guards using this actual issuer.
Its `create_draft` must refuse before effects through that entrance until a
separate Issue-governed writer is accepted. Protocol cannot enforce that claim
against arbitrary callbacks with filesystem access. Receiver lifecycle probes
are not SPEC factory integration or installed-capability evidence.

The agreed dependency boundary is the optional `protocol` extra in
`aware-specification-fs-sdk-adapter`, selecting
`aware-protocol-fs-adapter>=0.3.0,<0.4.0` through lazy integration imports.
The supported consumer CLI must explicitly require that extra; missing
integration refuses without raw-root fallback. The SPEC owner implements those
dependencies; neutral SPEC runtime, source values and public SDK remain independent.
Package-manager projection/lock synchronization, public source projection,
build/installation, setup and public delivery remain separate cuts. No dependency
or evaluator is duplicated here, and no supported a6 interface changes.
