# Specification FS SDK adapter

## Issue storage successors — source qualification 0.4.2

The optional `governed` extra now selects Issue SDK `>=0.10.1,<0.11.0`,
Issue FS adapter `>=0.9.1,<0.10.0` and FileSystem `>=0.3.1,<0.4.0`.
The SDK's compatibility JSON cache delegates storage to FileSystem; it remains
filesystem I/O, not a pure data-only SDK. No retired Runtime storage shim,
private Service import or alternate writer is introduced.

Genuine retained custody, draft success/refusal, correlated reading and cleanup
are source-qualified against these accepted suppliers. Mandatory dependencies,
Protocol reader bounds and governed Protocol floor remain unchanged. Existing
provider and SDK implementation bytes are unchanged. CLI 0.4.2 already admits
this adapter successor; its implementation and selection are not changed here.

Protocol/Bundle must extend the canonical consumer profile and projection and
prove the exact SDK-to-FS closure in a fresh offline, checkout-hidden install.
Source qualification does not accept that installation, candidate notices,
public selection, release or new iteration capabilities. Historical entries
below describe their original generations, not the current dependency floor.

## Original Protocol completion — source successor 0.4.1 / SDK 0.3.1

With genuine Issue-issued input custody, SPEC carries Protocol0.6.1's original
attempt/context-correlated owner observations: `false/not_attempted`,
`true/completed`, `true/incomplete` or `true/unknown`. No release return, phase,
physical outcome, descriptor scan or caller-built snapshot supplies authority.
Known original outcomes remain terminal; later disposal cannot upgrade them.
Observer faults retain the last valid history with diagnostics.

Historical `None/unknown` receipts remain readable and byte-meaning unchanged;
snapshotting does not recompute them from nested data. Without original custody,
the compatibility context still reports unknown. Public carriers check structural
correlation and lossless history only; they cannot issue or restore live authority.

Protocol completion covers only its original selection/root descriptor. Physical
package cleanup and independently borrowed consumer readers remain separate.
Their failures still refuse with primary error/publication history and uncertainty;
`completed` alone is not whole-operation success.

Mandatory SDK floor is `>=0.3.1,<0.4.0`; the optional governed Protocol floor is
`[draft]>=0.6.1,<0.7.0`. Other edges and reader range `>=0.3.0,<0.7.0` are unchanged.
These are source declarations, not installed/public qualification. CLI0.4.0's
custody restoration is independently accepted, but it still reports Protocol
completion as unknown and requires its own success/evidence adoption. Bundle
must refresh its neutral projection and prove the exact installed successor.

## Historical draft input custody — source successor 0.4.0 / SDK 0.3.0

Pass the original Issue-issued `input_custody` to
`open_governed_specification_draft(...)`. The factory claims an execution- and
context-correlated association before rendering or currentness checks. A failed
constructor, context entry or operation disposes only through that original
Issue context/admission. A rejected competing context cannot dispose the first
context's resources. If no handle returns, qualified correlated failure evidence
can still describe the owner's disposal; the snapshot itself cannot authorize
another release. Missing or malformed evidence stays unknown, never caller-owned.

Reserved-resource operations use Issue's delegation: staged lenses, publication,
correlated reads, completion and once-only disposal. SPEC never extracts a lower
claim or retries cleanup on raw holders. Successful writer disposal leaves the
independent read alive until the context closes it through its original owner.

The neutral SDK carries every `input_custody` field, nested resource observation
and physical ledger, with immutable snapshots and non-regression checks. SDK
refusals preserve the primary error, known publication and effect uncertainty;
foreign attempt/request/execution evidence is rejected. Protocol target cleanup
completion remains unknown even when an owner invocation returns. Historical
Issue disposal fields now include `protocol_cleanup_owner="issue"`; that statement
is historical evidence, not a permit or a claim of Protocol completion.

The optional `governed` extra selects Protocol `[draft]>=0.6.0,<0.7.0`,
Issue SDK `>=0.9.0,<0.10.0`, Issue FS `>=0.8.0,<0.9.0` and
FileSystem `>=0.3.0,<0.4.0`. The mandatory SDK edge is `>=0.3.0,<0.4.0`;
runtime/strict adapter dependencies stay unchanged. The optional reader range
retains Protocol 0.3–0.5 and adds the source-qualified 0.6 reader. Imports stay
lazy; reader use does not require Issue, FileSystem or service packages.

Omitting custody retains a compatibility constructor with unknown pre-issuance
responsibility. Any later successor Issue admission still enters owner arbitration;
there is no reserved raw-resource fallback. This compatibility shape does not fix
the pre-issuance CLI leak. The authoring CLI must separately adopt original custody
before calling the factory; its descriptor-restoration and installed neutral
candidate proofs remain held. No published preview, CLI bounds or bundle changes
follow from this source cut.

## Historical pre-issuance cleanup boundary — source successor 0.3.3

Original-holder identity does not establish untransferred cleanup ownership.
Another genuine context may already have Issue admission for the same holders.
Before Issue invocation, both cleanup responsibilities therefore remain `unknown`,
including an initial Protocol currentness refusal. The existing Issue observer's
unavailable lookup cannot prove the absence of a claim. No phase, identity,
error code, missing disposition or unattempted physical cleanup resolves this.
The original plan/target checks remain mandatory currentness/identity checks,
never caller cleanup grants. The initial 0.3.3 identity-based caller proposal
was rejected in review and is superseded by this conservative correction.

Immediately before invoking Issue, both responsibilities become `unknown`.
A failure without qualified original Issue disposition remains unknown even if
physical observation says `attempted=false`. A genuine unclaimed, caller-owned,
unattempted Issue disposition can resolve physical responsibility to `caller`;
An unclaimed original Issue disposition must also carry `protocol_cleanup_owner`
as `caller` to resolve the target. A claimed disposition cannot make a context
that received no admission the target's caller owner. A returned admission
transfers both to `context`. Known claimed/attempted cleanup must never be
retried based on an earlier snapshot. Observation never disposes resources.

SDK0.2.1 carrier shapes and all dependency bounds remain unchanged. CLI must
separately adopt the carrier's pre-issuance boundary without guessing from absent
Issue evidence. Protocol completion remains unknown; this source successor is
not an installed authoring candidate or public selection. The CLI three-descriptor
leak remains held: Issue/FileSystem must supply positive untransferred-input
evidence/custody at the original cleanup/transfer boundary, including concurrent
claims and target/plan correlation. A detached snapshot must not become durable
release permission. SPEC then maps that evidence; CLI consumes it separately.

Explicit Linux source-base descriptor and ordered root selection. Reads reuse
the existing strict Specification adapter; no second parser or readiness
evaluator. The packaged schema is an exact copy of the canonical V1 schema,
and the existing installer verifies its hash. No checkout-relative fallback.

## Pure renderer facade — source successor 0.3.1

The following paragraph records the accepted renderer-only generation;
the cleanup propagation successor is described below.

`render_specification_draft(request)` accepts the original
`SpecificationDraftRequest` and returns sorted immutable `(relative_path,
exact_bytes)` member pairs. It delegates to the existing renderer without
changing its parser, meaning, canonical bytes or size limits. Malformed typed
inputs return `SpecificationOperationError` with `effect="none"`.

This helper performs no filesystem access, staging, publication, Issue
admission, Protocol setup or cleanup. Its output is preparation data, not a
permit or proof that a SPEC exists. Historical stage/rename/cleanup helpers
are not exposed by the package facade. Rendering creates no approval,
iteration, durable Issue association or Git effect.

Mandatory and optional dependencies are unchanged from 0.3.0. The published
reader preview remains pinned; source metadata 0.3.1 does not select or install
it. Cleanup-disposition propagation and its composition successor remain
separate work; this patch does not claim verified governed cleanup.

## Protocol-selected read-only entrance (source version 0.3.0)

`SpecificationFsSdkProvider.from_protocol_selection(selection)` consumes only
the live `SpecificationSourceSelection` issued by the real Protocol adapter.
Protocol lends a fresh repository-descriptor duplicate, ordered package roots
and its original freshness guard. The existing provider duplicates that
descriptor and reuses its strict observer, schema, lowerer and iteration owner.
It does not reopen an unchecked repository path or infer roots from dependencies.

Observation, iteration admission and original-provider source-evidence reads
check Protocol before source access and again through their successful-return
horizon. A selection refusal retires retained iteration admissions. Invalid,
released, cross-process or stale selections are typed errors, never raw-root
fallback. The Protocol prefix preserves the original owner's refusal code;
SPEC parsing/identity errors remain SPEC-owned. This is sequential revalidation,
not an atomic filesystem transaction or immutable state after return.

This provider is read-only: `create_draft` returns
`SpecificationOperationError("protocol_selected_writer_unavailable", effect="none")`
before rendering or staging. The selection is neither approval, Issue scope nor
committed-Git authority. Original iteration capabilities remain process-local;
JSON observations cannot restore them.

Construction or final-admission failure closes newly constructed provider
resources and retires its admissions. Borrowed-descriptor cleanup belongs to
Protocol. `provider.close()` never releases a selection shared by another
provider; the original selection owner separately invokes Protocol release.

Integration is the optional `protocol` extra:
`aware-protocol-fs-adapter>=0.3.0,<0.6.0`. Imports are lazy: ordinary adapter,
runtime, source-value and public SDK imports do not require Protocol. A missing
extra or issuer API returns `protocol_integration_unavailable`. Consumer CLI
0.2.1 explicitly requires this extra and uses only the guarded entrance.

The 0.2.1 metadata amendment retains 0.3 support and admits the source-qualified
0.4 reader. It adds no setup writer or new SDK semantics. Protocol setup's
Issue/physical supplier closure and installed qualification remain separate.

The historical 0.2.2 source metadata adopted `aware-specification-sdk>=0.2.0,<0.3.0`
after accepted real read-composition qualification. Reader behavior and the
optional Protocol range stayed unchanged; it excluded Protocol 0.5. The
accepted CLI 0.2.1 registrar selects adapter `[protocol]>=0.2.2,<0.3.0` and
the neutral command runtime. These source declarations do not establish an
installed dependency closure, consumer selection or governed draft authoring.

The original `SpecificationFsSdkProvider(fd, roots)` remains compatibility/
internal, with its existing ungoverned draft primitive described below. It is
not a substitute when consumer admission fails. No supported governed writer
or installed distribution follows from this source change.

## Compatibility draft primitive

Draft creation supports one absent package with complete explicit contract
meaning and no iterations. The existing parent directory must already exist.
It validates a private same-parent staged package, then uses Linux
`renameat2(RENAME_NOREPLACE)` to publish the directory without overwriting a
competing target. Lack of that facility refuses. This is atomic visibility of
one directory, not power-loss durability, Issue authorization, Git publication
or a multi-owner transaction. Failures after publication report the effect as
`published`; do not blindly retry. Iteration-approval writers are unavailable.

`admit_iteration` issues an installation-local retained read capability over
an existing plan. `revalidate_specification_iteration_admission` consumes that
capability through its issuing provider and freshly reobserves all declared
roots. Serialized SDK evidence, another provider, copied/restamped values and
retired capabilities cannot replace it. It does not prove maintainer approval,
committed Git identity, HEAD currentness, Issue scope or Work admission. Those
are separate Workflow/repository integration obligations.

`revalidate_specification_iteration_source_evidence(capability)` returns
`SpecificationIterationSourceEvidence` from the original provider's fresh,
consume-once adaptation. It carries the same observation and iteration identity,
all selected source closures and their exact member bytes/digests, the retained
source-base `(device, inode, mount)` identity, and mount-namespace identity.
No second parser, scan or independently authored member list is used.

The source base is not automatically a repository. Workflow must compare that
identity with its independently admitted repository base and verify committed
member bytes, unique identities, Git epoch, Issue and Protocol state. Matching
digests in another directory do not establish that mapping. These are local
Linux observation coordinates, not portable repository identifiers.

Evidence is immutable data, not a transferable capability. Reconstructing,
copying or decoding it cannot replace the original retained admission; consumers
must invoke fresh revalidation, not accept supplied evidence as proof. Returned
snapshots remain readable after retirement but cannot authenticate later use.
This guards public caller-data entrances, not hostile Python with access to
module internals. Source-base/namespace identity is checked before and after
the owned read. This is not a global filesystem transaction or a guarantee of
unchanged files after return. At-use/publication guards remain separately owned.
The correlated evidence port adds no Git, approval or binding authority.

Author and intent refs are recorded declarations, not authenticated actors or
scope grants. The consumer workflow must compose its governance before writes.
This source package is not yet admitted in any consumer bundle. Notice/metadata
and the exact installed integration proof remain release-owner work.

## Governed draft composition — source checkpoint, not an installed entrance

`open_governed_specification_draft(...)` yields the existing SDK client in a
context. It requires a genuine Issue provider, an original absent Protocol draft
target and a planned FileSystem package containing exactly the existing renderer's
bytes. There is no free repository-root/manifest-path, caller verifier or setup
permit fallback. The factory obtains the manifest coordinate from the guarded
target and execution/request evidence from original Issue admission.

The context entry validates/binds but creates no directories/documents. Invocation
stages through Issue, validates the actual staged package through SPEC's existing
strict parser/lowerer and FileSystem's exact-entry checks, and publishes once
through Issue. It then observes the original Protocol-correlated read, lets Issue
finish and release, and checks the independent reader after writer cleanup.
It does not stage Git, commit, accept a Gate or author approved iterations.

After successful admission this context owns the supplied target/plan and its
new admission/read/provider descriptors. Rejection does not establish caller
ownership: original holders may already belong to another admitted context.
Only qualified original-owner disposition can resolve that uncertainty; absence
of evidence must not authorize release of supplied inputs.
Every exit attempts owned cleanup; published bytes are never deleted. Complete
context exit is required before reporting success. Escaped clients cannot renew
authority. Immutable evidence remains readable and retains temporal history,
unknown submission, known publication, residual paths and cleanup diagnostics;
`package_outcome=none` does not imply no scratch effects.

Source tests use real owners, including nested Protocol manifests; fault probes
wrap owner methods. This is cooperative, sequential at-use/return checking, not
an atomic cross-owner transaction, authenticated actor identity, hostile-Python
confinement or continuous currentness. Issue's last check is during its successful
release; later independent SPEC/Protocol reads do not renew Issue authority.

The installed reader candidate still selects its accepted historical bytes.
**Do not build/publish this advancing tree as adapter 0.2.2.** Source metadata
now versions the accepted composition as adapter 0.3.0. The reader extra admits
Protocol `>=0.3.0,<0.6.0` after independently accepted source compatibility;
`from_protocol_selection` still refuses draft writes even with governed installed.

The separate optional `governed` extra selects Protocol FS
`[draft]>=0.5.0,<0.6.0`, Issue SDK `>=0.8.0,<0.9.0`, Issue FS
`>=0.7.0,<0.8.0` and FileSystem `>=0.2.0,<0.3.0`. Mandatory neutral
requirements remain unchanged. These dependencies select original owners;
installing an extra never supplies Issue authorization or currentness evidence.

For a neutral consumer, Bundle must explicitly select the accepted 41-input
draft profile at `5c3acc1405c7`, rooted in producer revision `b510b2117d73`.
Its separate `+draft.1` identities preserve owner implementation bytes while
narrowing metadata/export surfaces. The full internal Issue packages remain
service-coupled and are not this consumer closure. Source/profile acceptance
is not installed dependency or notice/public-content clearance.

CLI 0.2.1 retains its historical adapter `[protocol]>=0.2.2,<0.3.0` bound:
it cannot select this 0.3 source package. Its versioned successor requires a
separate Issue; the pinned reader candidate retains original 0.2.2/Protocol 0.4
bytes. No writer CLI, installed-authoring capability, consumer selection,
legacy physical delegation, aggregate lock/environment update or release is
claimed by this metadata adoption.

## Lossless cleanup propagation — source successor 0.3.2

The original context returned by `open_governed_specification_draft(...)`
supports `observe_draft_cleanup()` before invocation and after failed entry or
closure. Early failures without a usable context carry the same detached
knowledge through `SpecificationOperationError.cleanup_evidence`. Neither
lookup stages, releases, reopens resources nor renews write authority.

The adapter maps original Issue disposition and FileSystem observations into
the SDK's six neutral values without changing their fields. Failed issuance
may already have claimed/released physical inputs: a missing returned admission
does not mean caller-owned untouched inputs. The recorded invocation boundary
is separate from each supplier's historical ownership and attempted/outcome
observations. Unknown knowledge stays unknown. Original cause-chain diagnostics
survive wrapped owner refusals.

Once successful admission returns, SPEC owns context cleanup. It observes the
original Issue disposition before release; an already attempted or unobservable
attempt is never blindly retried. SPEC records each own invocation before the
call. Known publication, ordered effects, earlier faults and attempt knowledge
cannot regress; residue may shrink during legitimate cleanup. Invalid or lost
lookups preserve the last valid original snapshot and add explicit diagnostics,
not rewritten supplier fields or a claim of new completion.

Protocol target retirement can attempt cleanup before a later release call.
SPEC separately records that later invocation/return/fault; Protocol-owner
attempted/outcome remain `None` / `unknown`, including a retirement failure
followed by a normal release return. **This is not fully verified consumer
cleanup.** Consumers must not infer cleanup from phase, Issue's historical
`protocol_cleanup_owner="caller"`, or a successful release return.

Source metadata now requires neutral SDK `>=0.2.1,<0.3.0`. The optional governed
extra retains Protocol FS `[draft]>=0.5.0,<0.6.0` and raises producer floors to
Issue SDK `>=0.8.1,<0.9.0`, Issue FS `>=0.7.2,<0.8.0`, and FileSystem
`>=0.2.1,<0.3.0`. The reader Protocol range and all pure-renderer/reader function
bodies remain unchanged. Bundle must refresh and explicitly select the neutral
producer profile; internal Issue packages are still not a consumer closure.
CLI 0.3.0 must separately qualify adapter `[governed]>=0.3.2,<0.4.0`.
No aggregate lock, installed candidate, reader selection or publication follows
from this source successor.
