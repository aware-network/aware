# aware-protocol-sdk

Typed SDK interface for `protocol_sdk.admit_target`.

The caller injects one already selected authority provider. The SDK does not
probe for a filesystem or service, fall back between authority modes, parse
`aware.protocol.toml`, or own Goal, Issue, Specification, or publication
semantics. The filesystem implementation is supplied by
`aware-protocol-fs-adapter`; a later Service/API provider must implement the
same operation meaning and return the same neutral admission contract.

## Admission return boundary (0.3.0 source checkpoint)

SDK 0.3.0 requires `ProtocolTargetAdmissionResult.request`: an exact detached
`ProtocolTargetAdmissionRequest`. Result wire contract is
`aware.protocol.target-admission-result.v2`; the authored SDK semantic version
is 2. Operation/provider identities and request wire v1 are unchanged.
Providers must return the original request, not an inferred path or digest;
SDK 0.2 providers cannot be mixed into this generation. The FS provider in
adapter 0.6.3 implements this return shape. There is no v1 fallback or inferred
correlation.

The client revalidates a detached request before invocation and reconstructs
returned values through their original neutral owners. It checks exact request
correlation and admitted manifest target kind/authority. It neither reruns
filesystem admission nor treats a transport value as a retained capability.
Provider and caller originals are not normalized or modified by this check.

`ProtocolTargetAdmissionError` implements the genuine authored error carrier.
Invalid requests refuse before invocation (`effect=none`); invalid/uncorrelated
returns refuse after one invocation (`effect=unknown`). Provider exceptions
retain their existing form; no automatic retry occurs. Error reports retain
known fields as detached, explicitly **unvalidated provider reports**, not
accepted admission or proven source effects. Text/items/depth/node limits and
unsupported-value omissions are explicit in `report_diagnostics`. No arbitrary
provider serializer, iterator or representation is executed. Opaque admission
and report `Json` declarations do not replace Python owner validation.

This is source contract qualification, not an installed SDK/public selection.

## Governed SPEC setup (source checkpoint)

`protocol_sdk.setup_specification` uses the neutral
`ProtocolSpecificationSetupRequest`, result/effect/error values and
`ProtocolSpecificationSetupClient` provider port. These values are not permits.
The request separately binds exact manifest and Issue byte `sha256:<hex>`
digests, explicit root/directories, Issue reference and caller intent. No actor
string, decoded binding or preview can replace the selected owner's admission.

The optional existing-client composition obtains fresh Issue authority for
preview and apply. Planned results have no consumption evidence; completed
results carry the actual owner's effect, execution and authority-grade evidence.
Refusals retain applied/unknown effects and require fresh observation, not
automatic rollback. Source setup and repository publication are separate.

SDK 0.3.0 is an authored source version, not an installed release receipt.
No service selection, Issue policy, physical writer, SPEC parser or approval
implementation is added to this neutral package.
