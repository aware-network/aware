# aware-protocol-sdk

Typed SDK interface for `protocol_sdk.admit_target`.

## Narrow profile bootstrap source checkpoint

SDK **0.3.1** adds the genuinely authored `protocol_sdk.initialize_profile`
contract. `ProtocolBootstrapClient.filesystem` explicitly selects the original
Protocol FS provider; no service probing or fallback is performed. Its seven
public request/input/observation/result/error value roots are the original
neutral-runtime **0.1.1** values (`>=0.1.1,<0.2.0`), with strict detached codecs.
Decoding a value never constructs a live plan or admission.

`prepare_bootstrap_request` and `render_bootstrap_input` prepare explicit inputs
without effects or authority. Prospective rendering supports an absent root;
live planning independently requires a concrete Git repository. Preview is the
request default. Apply requires a fresh, original single-use admission from
`plan_initialization` followed by `admit_initialization`. Closing the plan
releases only its own resources.

The operation creates only the initial Issue-authority manifest and optionally
versioned onboarding guidance. It does not create an Issue, initialize Git,
stage, commit, configure a remote or start a service. Repository preparation is
a separate Workspace SDK operation. The FS adapter's `bootstrap` extra admits
FileSystem `>=0.3.3,<0.4.0`; this SDK has no dependency on Workspace or Service.

Return validation retains the original dispatch request, attempt, per-path
effects and cleanup even when externally exposed values are mutated or malformed.
Rejected reports remain explicitly unvalidated. Refusals never imply rollback
or retry permission; cleanup uncertainty cannot become success through later
release. Harness correlation is not authenticated actor-action issuance.

This is a source checkpoint, not a shipped `aware init` command, selected
consumer environment or installed onboarding proof.

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
