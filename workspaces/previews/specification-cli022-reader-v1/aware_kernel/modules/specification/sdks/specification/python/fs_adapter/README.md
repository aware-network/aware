# Specification FS SDK adapter

Explicit Linux source-base descriptor and ordered root selection. Reads reuse
the existing strict Specification adapter; no second parser or readiness
evaluator. The packaged schema is an exact copy of the canonical V1 schema,
and the existing installer verifies its hash. No checkout-relative fallback.

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
new admission/read/provider descriptors. Prior rejected inputs remain caller
owned except for terminal failure cleanup performed by their original issuers.
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
