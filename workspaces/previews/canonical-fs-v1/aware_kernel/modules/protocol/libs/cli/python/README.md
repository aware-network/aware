# aware-protocol-cli

Thin command-line projection of `protocol_sdk.admit_target` and optional
`protocol_sdk.setup_specification`.

The executable selects the filesystem provider explicitly, constructs the
typed SDK request, invokes `ProtocolSdkClient`, and renders the returned
receipt. It contains no TOML parser, profile evaluator, filesystem containment
logic, service discovery, Goal/Issue behavior, or authority fallback.

The CLI preserves the explicit `--repository-root` text as the SDK
`target_ref`. Path interpretation, resolution, and typed filesystem refusals
belong to the selected provider and its owning adapter after authority
selection; the CLI does not expand or normalize the target.

## Optional governed SPEC setup command (unreleased source checkpoint)

The source `aware-protocol setup-specification` command projects the accepted
optional composition. Preview is the default (`--dry-run` may be explicit);
`--apply` requests effects and cannot be combined with `--dry-run`. Both modes
require an explicit repository, Issue reference, exact manifest and Issue byte
digests (`sha256:<hex>`), SPEC root and client intent. Repeat `--directory-path`
in the required effect order for every admitted missing ancestor and the root;
the command does not discover or insert ancestors. An existing root can require
no directory effects, but the Issue still must admit the manifest replacement.
No actor or capability JSON may be supplied as authorization.

The public Python module `aware_protocol_cli.specification_setup` supplies
`IssueGovernedSpecificationSetupProvider` for the neutral SDK setup port.
The optional `specification-setup` extra declares Issue SDK >=0.10.1,<0.11.0 and
Issue FS adapter >=0.9.1,<0.10.0; those imports occur only at invocation. Missing
integration refuses without fallback. Neutral Protocol runtime, public SDK and
manifest candidate mechanics have no reverse Issue dependency. This composition
is above the owners, not another parser, scope matcher or physical writer.

Preview freshly obtains and validates a genuine Issue admission, then releases
it without effects. Apply freshly prepares the candidate, obtains the same
owning admission interface, and consumes explicit directories → exact manifest
replacement → Issue completion. It preserves actual none/applied/unknown
evidence, original mode and unrelated work; a post-effect refusal is not success
or automatic rollback. Harness-observed FS ownership is not authenticated
actor-action issuance. Cooperative descriptor confinement is not a continuous
filesystem sandbox or a transaction with arbitrary concurrent writers.

Setup creates no SPEC documents, approved iterations, bootstrap, Issue lifecycle
transition, staging or commit. A fresh, separately admitted SPEC reader must
observe independently qualified documents afterward. This optional composition
does not itself supply a complete SPEC consumer installation.

Results preserve the SDK's preimage/postimage digests, ordered paths, per-path
effects, mode/durability/identity evidence and actual authority grade. Typed
refusal returns exit 2 and none/applied/unknown effects, including residual
scratch paths. Unexpected invocation failure returns exit 1 with unknown
effects; it cannot establish that no source changed. Usage errors return exit 2
before invocation. Receipts are JSON on stdout, never transferable admissions.

The cooperative profile checks exact bytes, retained identities and observed
metadata. It does not detect every intervening equal-byte write or provide
continuous confinement. A post-effect refusal remains a refusal with actual
effects; inspect before any retry. Preview is not authorization for later apply.

Historical 0.2.0 and 0.3.1 installation receipts retain their exact supplier
versions. CLI **0.3.2** qualifies unchanged command implementations against the
physically separated Issue SDK/FS successors and Protocol FS
`>=0.6.2,<0.7.0`, including the F-004 diagnostic repair. The canonical producer
profile selects setup explicitly; default CLI dependencies remain Issue-free.
Source qualification does not select this successor in a public archive or
replace a6. A pinned consumer installation, operation proof and source/notice
review remain required. Do not run a development checkout as a customer install.

## Neutral command-runtime pilot

Only `admit` registers and dispatches through `aware-command-runtime`. The
registration labels the existing `protocol_sdk.admit_target` operation; the
handler still constructs its original typed request and selects the same FS
provider. The registry grants no authority and introduces no SDK evaluator.
Setup/version stay on their original command branches; setup remains lazily
imported. A duplicate `admit` registration refuses instead of replacing an
existing owner. No registrar discovery or developer `.env`/root lookup occurs.

The supplier constraint is `>=0.1.1,<0.2.0`; the pilot installation must select
the reviewed 0.1.1 wheel by its exact hash. This version range is not evidence
for another supplier version. The CLI carries package-local legal files and
requires a new candidate with installed request/result, stream, exit-code and
sibling-command parity before consumer adoption. The declared CLI version
changed to 0.3.1 for that historical pilot; the 0.3.2 metadata qualification
does not change domain results, command registration or refusal semantics.
