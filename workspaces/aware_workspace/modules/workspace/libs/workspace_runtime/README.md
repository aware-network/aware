# Aware Workspace Runtime

## Repository preparation neutral lifecycle

`repository_preparation` orchestrates original plans, single-use admissions and
lossless result/error evidence for `repository_sdk.prepare_repository` through
the fixed owning FS port. It performs no path reads, Git invocation or directory
creation. The FS adapter retains physical identities and effects. Provider-native
harness correlation is not authenticated actor-action issuance or Issue authority.

Runtime/SDK 0.2.1 and FS adapter 0.1.1 are the source successors. Apply spends the
original capability before freshness/effects; mismatch, interruption or refusal
retires it. Failed return validation never recreates write authority. Source
tests do not establish an installed `aware init` or whole-package neutrality.

## Manifest-derived package source checkout

`aware-cli workspace checkout` is a direct, materialization-independent operation
on this runtime. It reuses `LocalCheckoutWorkspaceCompositionProvider` and Code's
module parser to walk repository → Workspace → module → package declarations,
including direct `repo.codes` and `workspace.codes` memberships. It selects
canonical Python distribution names with PEP 508 requirements and extras; an
ambiguous name refuses rather than selecting an arbitrary occurrence.

```bash
aware-cli workspace checkout --repo-root . \
  --package aware-specification-cli --plan --json
aware-cli workspace checkout --repo-root . \
  --package aware-specification-cli --destination /tmp/spec-source-checkout --json
aware-cli workspace checkout --verify /tmp/spec-source-checkout --json
```

The destination must be new and outside the repository. Source is the complete
Git-tracked physical package root, copied without dependency, export or version
rewrites. Untracked nonignored files, symlinks, ambiguous membership, unavailable
static metadata, conflicting local versions, unknown extras, forbidden required
edges and stale sources refuse. `--forbid-package` supplies repeatable exact
distribution names; it never silently removes required dependencies.

The generated `checkout-inventory.json` binds explicit selection, the complete
marker environment, declaration/leaf-manifest hashes, local dependency edges,
build metadata, source files/modes and the Git revision basis. Actual working
tree bytes are hashed, so the revision basis is not a clean-release claim.
`registry_requirements` preserves original activated requirements and markers;
`registry_resolver_requests` gives their effective constraints for that fixed
target. Registry artifact locking and wheel verification belong to the qualified
packaging resolver. They are not implemented by this source checkout.

Native target markers are recorded by default. A cross-target `--marker NAME=VALUE`
request must supply every field of the PEP 508 environment. Build requirements
remain distinct in each package's original `build_system` metadata; consumers
do not acquire build/test dependencies as runtime dependencies.

Python callers use `PackageSourceCheckout` from
`aware_workspace_runtime.package_checkout` as a context manager, then
`resolve(...)`, `write(...)` and `verify_package_checkout(...)`. No Service,
Platform, selected semantic provider or materialization admission is needed.
Before/after descriptor-confined rereads detect source drift; they do not create
an external-writer fence. Inventory verification proves byte/coverage integrity,
not supplier authority, OSS disclosure permission, installation or publication.

## Named and composed checkout profiles

Repository `[[checkout_profile_sets]]` version 2 selects exact declared Python
Code leaves. A module member uses `workspace`, `module` and `package` IDs. A
direct Workspace Code member uses `workspace` and its Workspace-relative
`code_manifest`; a direct repository member uses `repo_code_manifest`.
Paths must match the corresponding original `codes` declaration. A matching
filename or distribution name does not establish profile membership.

```toml
[[checkout_profile_sets]]
key = "portable_protocol"
version = 2
package_selections = [
  { workspace = "aware_kernel", module = "protocol", package = "protocol_runtime" },
  { workspace = "aware_kernel", module = "protocol", package = "protocol_sdk_python" },
  { workspace = "aware_kernel", module = "protocol", package = "protocol_fs_adapter" },
]

[[checkout_profile_sets]]
key = "portable_protocols"
version = 2
include_profiles = ["portable_protocol", "portable_specification"]
```

Selections may declare `extras = ["group"]`; required dependencies, constraints
and extras are resolved by the same package closure as `--package`. Composition
forms a deduplicated union, supports transitive includes, and refuses unknown
members, cycles, unsupported leaves and conflicts. `--profile` and `--package`
are repeatable and can be combined. Profiles never change package features,
exports, versions or dependency declarations.

```bash
aware-cli workspace checkout --profile portable_protocols --plan --json
aware-cli workspace checkout --profile portable_protocols \
  --overlay agent_coordination_surface \
  --destination /tmp/portable-protocols-checkout --json
aware-cli workspace checkout --verify /tmp/portable-protocols-checkout --json
```

Profile checkouts include every base `repository_files` entry. A profile's
`overlays` or explicit `--overlay` selects additional declared entries, copying
original bytes from `source_path` to `target_path`. Unknown overlays, missing or
untracked files, links and collisions with package files or the generated
inventory refuse. V2 inventory records expanded profiles, exact manifest
members, extras, overlay mappings and source hashes. The reader captures and
rechecks these bytes under the same lifetime; independent verification checks
the complete written set. Explicit package-only inventories retain v1.

The existing unversioned `public_kernel` and `agentic_public_workspace` profiles
retain v1 broad Workspace/revision meaning, including generated and non-Python
members. Source checkout refuses them instead of returning an incomplete
Python subset. Their revision-based loader remains available; it delegates the
shared profile grammar, refuses v2 selection through that legacy route, and
keeps its projected repository manifest limited to v1 profiles. The new named
profiles are source/software selection, separate from
`semantic_contract_profile_sets`, which select semantic execution providers.
Registry locking, packaging, disclosure approval and release publication remain
separate; a profile inventory grants none of them.

## Failed mutation effect evidence

Failed mutation receipts retain optional neutral `physical_effect` evidence:
`none`, known `applied`, or `unknown`, with exact known before/after target
digests and independently reported durability. Failure remains failure; this
does not grant a success coordinate, converged change evidence, or safe retry.
The receipt codec emits version 2 only when this evidence is present. Legacy
version 1 receipts remain readable and byte-shape compatible, with no invented
physical effect evidence. Persistence and idempotent replay retain the failure.
Retained setup identity, explicit directory admissions and Issue consumption
are separate supplier capabilities. No installation is implied by this source.

## Neutral revision preparation

The runtime exposes strict portable Workspace revision-state values and one
zero-write preparation entrance. A successful materialization graph execution
may be joined to process-local execution provenance through
`admit_completed_workspace_materialization_graph_execution()`. Preparation
then consumes that capability together with separately admitted predecessor,
source-closure, membership, and selection context and returns exactly one of:

- a predecessor-bound `WorkspaceRevisionCandidate`;
- exact unchanged-state evidence; or
- deterministic refusal evidence retaining only the verified authority prefix.

This boundary performs no provider execution, source read, repository write,
Ontology call, Meta/OIG call, publication, branch-head mutation, or authority
grade elevation. Decoded portable values remain structural evidence. OIG
commit bindings and Ontology-Object publication remain separate downstream
contracts.

`aware-workspace-runtime` is the generated-free local operational substrate for
Workspace. It owns repository observation lifecycle, ordered local batches,
bounded replay, explicit gaps, current snapshots, health, and independent
consumer checkpoints over FileSystem primitives.

It does not own canonical Repository identity, `WorkspaceRevision`, graph/OIG
commits, Reactivity Events, actor attribution, ServiceHost activation,
module semantic resolution, or Development composition.

## Neutral semantic materialization publication

`semantic_materialization_publication.py` is the provider-neutral Workspace
authority boundary over the Code semantic-contract runtime. It joins an exact
source/operation admission to one runtime-owned publication snapshot, stages
and rereads the terminal canonical bodies, then advances one direct package
result head by expected-revision CAS and exact reread.

Workspace does not decode SDK/API/Ontology values, re-enter provider codecs,
apply a `CodePackageDelta`, activate generated products, create a
`WorkspaceRevision`, or claim canonical OIG authority. The direct package head
is the O(1) write path; any workspace-wide result catalog is a derived read
projection rather than a publication prerequisite.

## Recoverable generated-output mirror

`generated_output_apply.py` consumes only one exact staged
`aware.code.package-delta.v1` selected by an admitted materialization head. The
Workspace operation authority resolves the checkout root; a portable request
cannot nominate a filesystem path. A host-owned cross-process lease serializes
the package effect window before preflight.

Each path must already equal its exact prior state or its exact desired state.
The latter is typed interruption recovery. Pending changes use FileSystem's
descriptor-confined CAS primitive. Workspace then rereads every retained path
and every cumulative deletion tombstone, stages the compact output-state body,
performs one expected-revision output-head CAS, and rereads the stored head.
Partial file effects, lease loss and head-CAS loss issue no head receipt.

The checkout remains a recoverable operational mirror. The output head claims
neither generated-product activation, `WorkspaceRevision`, canonical replica,
OCG nor OIG authority. Those effects remain separate adapters over the exact
head rather than availability requirements for neutral materialization.

## Durable materialization session journal

`materialization_session.py` turns an exact reread-backed package result into
ordered WorkspaceSession evidence. A runtime-issued, nonserializable admission
binds the operation, session, participant, baseline, package set and explicit
`local_operational | workspace_authorized_shared` grade. Append stages one
immutable canonical event by its digest, advances one compact session head by
expected-revision CAS, rereads both records and only then issues a fanout
receipt.

Replay follows a bounded predecessor-digest chain and returns contiguous
events or an explicit epoch, cursor or retention reset. Snapshots resolve only
one admitted, bounded package page through direct package-head reads; append
never scans packages or session history and never synchronously compacts it.
The event and head are collaboration evidence, not checkout application,
`WorkspaceRevision`, canonical graph history or OIG authority.

## One neutral materialize operation

`materialization_operation.py` is the single Workspace-owned execution facade
above the Code runtime, package-result publisher and session journal. A client
submits one strict portable proposal. The Workspace authority issues one
nonserializable admission; a host-injected resolver produces the exact neutral
Code invocation and canonical body closure. The operation executes the fixed
runtime and constructs publication and fanout child admissions internally.

The resolver's implementation/profile coordinates are fixed at composition
and checked on every call. Workspace imports no SDK/API/Ontology provider and
does not let the client submit a provider, runtime, execution completion or
child admission. Results preserve exact plan, execution, publication, fanout
and total timings plus both subordinate counter sets. Named stage failures
issue no complete operation result and leave already-completed lower effects
explicitly recoverable through their own exact retry laws.

## Operational validation contracts

`operational_validation.py` defines dependency-clean source package, profile,
plan, suite receipt, aggregate receipt, effect, and currentness values. These
values bind an exact neutral repository observation and never claim
`WorkspaceRevision`, canonical `CodePackage`, ORM/Ontology admission, release,
or publication authority. Development may schedule disposable workers over the
contract; later Object/Ontology ABI adapters may preserve its receipts without
reinterpreting their execution status or currentness.

The package is deliberately below the public Workspace SDK and future Local
Service / Service API adapters. Those boundaries translate its neutral values;
they do not fork its execution core.

## Semantic-package composition input authority

`semantic_package_composition.py` defines the dependency-clean, input-only R1
wire value. Strict v2 decoding yields `portable_input`, never Workspace
admission.
The owning Workspace operation runtime joins that value to the exact operation
body/ref, ingress capture and authenticated package-manifest dependency
authority before issuing `workspace_authorized`. Reachable package closure is
body-free and independent from source movements. One package-scoped prior is
required for every reachable package. Only the target may use authenticated
typed-empty authority; retained dependencies require positive membership in
the operation-bound accepted-result catalog and exact package/schema/Object-ABI
coordinates, plus the optional artifact coordinate when present. Only changed create/update
`.aware` after-bodies enter the parse batch, while deletes remain path/before-
digest tombstones. Typed-empty genesis alone requires complete create bodies,
while `source_current` claims only that no changed `.aware` body requires
source-semantic work. It never claims command-wide `exact_current`: Workspace
must later join parent operation/currentness, provider/execution authority,
package/dependency and requested-root authority, prior schema/ABI/artifact
authority, renderer configuration and exact target-output currentness. The portable value
contains no independent operation identity, source authority, schema/Meaning/
Object-ABI result, renderer output, CodePackageDelta, graph effect, or
publication claim.
Its sole active contract is documented under
`contracts/semantic_package_composition/v2/`; v1 has no decoder or compatibility
surface.

## Portable semantic bundle manifest

The inert R5-A manifest contract is owned by the zero-runtime-dependency
`aware-workspace-semantic-bundle-contract` wheel. This operational runtime does
not re-export, wrap, decode, or otherwise retain a compatibility surface for
that portable contract. Workspace admission remains separately owned here,
and local immutable caching begins in R5-C.

`FileSystemIndexObservationProvider` remains the default Python reference
provider. `FileSystemBackendObservationProvider` is the explicit injection
boundary for a neutral FileSystem `ObservationBackend`. It accepts a factory so
Workspace can close maintained resources on session stop and recreate them for
a new epoch. Backend snapshots/deltas are root-checked and translated into
Workspace entries/changes; Workspace recomputes its own snapshot digest and
retains cursor/journal authority. Selecting `rust_shadow` requires a prebuilt
binary and explicit factory construction—there is no runtime build, `auto`
selection, silent fallback, or default-route change.

`WorkspaceRepositoryLocalServiceParticipant` is the module-owned Local Service
adapter over one injected maintained observation session. It exposes strict
snapshot, confined source-read, health, poll, checkpoint, and `source_changes`
replay contracts while preserving Workspace epochs, cursors, snapshot digests,
typed gaps, and `local_uncommitted` authority. Source reads require the exact
current snapshot coordinates and indexed path, open every component relative to
the admitted repository with symlink following disabled, enforce participant
and caller byte budgets, and verify indexed metadata before and after the read.
It does not create a provider, scan, watcher, index, journal, semantic resolver,
graph mutation, or materialization rail.

Workspace explicitly opts only `snapshot_page` and `read_source` into Agent or
automation discovery. Their module-authored Draft 2020-12 schemas use narrower
page/read budgets than the host ceilings and carry canonical digests. Full
snapshot, health, poll, composition, chunk continuation, and acknowledgement
remain ordinary Local Service calls—not tools. Workspace imports no Agent or
provider package; an Agent boundary may translate the exact catalog later.

## Repository change evidence values

`change_evidence.py` defines the immutable, generated-free values shared by
later repository evidence resolvers and transports. The vocabulary keeps seven
authority postures distinct: provider report, Workspace observation, bounded
provider correlation, Workspace-authorized mutation, committed revision,
ambiguity, and evidence gap. External Agent/provider and Issue context remains
opaque reference data; it cannot upgrade correlation into authorship or
Workspace authorization.

`change_evidence_codec.py` is the strict versioned JSON-compatible boundary for
external evidence, resolved change evidence, CAS mutation receipts, lazy diff
requests/pages, and consumer checkpoints. It rejects missing or unknown fields,
unsupported versions, invalid types, inconsistent provenance, and tampered
deterministic identities. Phase 04 also defines a strict operation envelope for
mutation request bytes and authorized receipt/evidence results; body bytes use
canonical base64 and the nested evidence values retain the same contract.

`WorkspaceRepositoryChangeEvidenceResolver` is the Phase 02 derived projection
over one injected, already-maintained observation session. It consumes only the
session replay contract; it never constructs or polls a provider and does not
retain a second raw observation journal. Each consumer owns an independent
monotonic checkpoint and a bounded persistence-neutral evidence snapshot.
External reports correlate only when an explicit time interval and reported
change shape select one non-coalesced observed batch. Multiple candidates and
coalescing remain ambiguous; epoch or retention loss becomes a typed gap with
explicit reset acceptance. Correlation never becomes actor attribution or
`workspace_authorized` evidence.

## Authorized mutation and operational diff

`WorkspaceRepositoryMutationCoordinator` admits one expected observation
coordinate plus exact target existence/content digest, then uses the
observation session's serialized-effect gate so no background poll can split
admission from convergence. File bytes are changed only through FileSystem's
descriptor-confined CAS primitive. Only an applied effect with an exact target
change in the resulting observer batch receives a deterministic mutation
receipt and `workspace_authorized` evidence. Stale, conflict, denied, failed,
no-op, retention, and convergence failures carry no authorized evidence.

`WorkspaceRepositoryOperationalBodyStore` retains bounded volatile pre/post
bodies only for those authorized operations. The lazy operational diff
provider reads that registry—not the current filesystem—and emits exact,
budgeted text hunks or explicit partial, binary, stale, unavailable, and
cancelled states. Eviction and missing preimages fail closed. Direct external
writes continue through ordinary observer evidence and cannot mint receipts,
retained bodies, or authorization.

When a mutation coordinator and its operational diff provider are explicitly
injected, `WorkspaceRepositoryLocalServiceParticipant` exposes
`repository_mutate` and `repository_diff`. The participant only decodes the
strict neutral envelope, delegates to the owning Workspace runtime, and encodes
the canonical result. Conflict/stale/denied/failed receipts and
partial/binary/stale/unavailable diff pages remain successful typed values;
malformed envelopes and absent runtime capabilities are Local Service failures.
The operations are not Agent-discoverable tools. No transport client receives
filesystem access or authority to mint evidence.

When an evidence resolver over that same maintained observation session is
injected, the participant also exposes `repository_correlate_external`. It
accepts only the Workspace-owned strict external-evidence envelope and returns
canonical provider-reported, provider-correlated, ambiguous, or gap evidence.
It imports no Agent/provider contract, does not create another observer, and
never upgrades path/time overlap into actor authorship. Development owns the
peer translation from Agent edit observations and retains only the resulting
cross-domain references.
