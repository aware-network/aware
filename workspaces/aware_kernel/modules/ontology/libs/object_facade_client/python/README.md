# Ontology Object facade client: detached wire and ABI data

## Private native preparation and topology guards

The optional `_preparation_scan` extension implements the preparation guard's
complete field and identity scans for the exact CPython runtime declared in
`../native/preparation_scan_build_lock_v0.json`. It retains the existing rows
and checks them afresh on every entrance, return and unwind. It does not cache
validation or grant host authority.

The same extension also scans the original topology checker's complete rows.
`bind_topology_installer` binds its one authored sentinel before installation;
the nested installer/checker bytecode and closure layouts are unchanged.
`scan_topology` receives the original checker and its bound CodeObject, never
caller-supplied rows or a successful-check token. Weak layout records retain
only immutable code-field positions. Mutable function/default/closure,
namespace, class/MRO and container state is read afresh at every existing
entry/return/unwind boundary. It does not issue Meta, Code or Workspace evidence.

The topology diagnostic observer records native read addresses in raw storage
and creates Python trace objects only after the scan. It performs another full
fresh scan after serialization. Its optional exact Boolean GC-stress argument
forces collection at that diagnostic boundary and restores the original GC
enabled state; production guard calls never request forced collection. Trace
data and an accepted diagnostic are not publication or currentness authority.

Installation binds the native entry into the checker's immutable code constants
before creating protected wrappers. The original checker bytecode and closure
layout remain intact. The portable profile runs the existing Python scans when
the extension is absent. A present extension's loader error or native refusal
propagates; neither selects portable recovery.
Both bootstrap entrances confirm that a spec is genuinely absent before
selecting portable installation. A present loader raising `ModuleNotFoundError`
with the extension's own name is still a terminal load error.

The build requires the lock's exact compiler, headers, source digest and runtime
ABI. `hatch_build.py` can compile an isolated artifact and emit a receipt without
installing it. Pass the C source, lock and an existing temporary output directory
as its three positional arguments. Its receipt records the compiler command,
actual dependencies and output digest. Keep generated binaries outside authored
source paths.

The wheel hook is disabled by default, retaining the portable wheel. Set
`HATCH_BUILD_HOOK_ENABLE_CUSTOM=1` for a native wheel build from this source
checkout with the exact admitted runtime and toolchain. The build reads the
sibling native lock and includes one ABI-specific extension in a platform wheel.
Native builds from a source distribution and other runtime profiles remain
unqualified. Wheel conformance and joined operational qualification are separate.

This authored package implements the detached framing portion of the accepted
[facade v1 contract](../../../../../../../docs/reports/ontology-facade-command-result-durability-contract-20261002.md).
It exports data types, strict codecs, data digest helpers, a delivery Protocol
and detached read exchange. It depends only on the Meta TypeSchema foundation.
The codecs perform no I/O; the read client calls the explicitly supplied transport.

`encode_request` / `decode_request` and `encode_result` / `decode_result` check
closed schemas, canonical UTF-8 JSON, members/tags/nulls, integer versus Boolean
rules, inclusive limits, digest domains and fixed facade-wrapper contracts.
They preserve complete lower Body bytes and check their size/hash. JSON-framed
bodies contribute cumulatively to structural depth/member ceilings; opaque
non-JSON bytes still require the owning codec. No lower semantic codec is copied.
`match_result` checks the declared request/result correlations and result reserve.
`WireError.code` is a local data refusal, never an authentic host outcome.

All outcomes bind one acyclic `outcome_preimage`; replay retains the complete
non-replay original Result, its witnesses and fresh active/historical association.
Witnesses obey closed required-role structure, direct/value-field rules, ordering
and observation correlation. `required_witness_roles` reports unconditional
structure. Claim requirements selected by an authentic owner profile, combined
owner reread bodies, lower-body membership, source observations and every nominal
issuer/peer/currentness check remain owner/host responsibilities. A structurally
valid result is **untrusted data**, including an `ok` or `replay.active` result.

Neither a matching digest nor `FacadeTransport.exchange` authenticates a peer.
Body contract identifiers never select an import, verifier, route or callback.
The package issues no witness, claim, fence, grant, session or completion evidence.
It does not implement retry, duplicate-outcome storage, journal recovery or an
alternate Service/Ontology runtime.

Message-local limits are enforced here. Operation-wide limits (64 commands,
16 Actions, 32 acquired Objects, original business/argument budgets), host
retention/capacity, one-use challenges and the monotonic deadline require the
later admitted original-owner/host lifecycle. Static ordinal/update ceilings do
not establish those lifecycle proofs. Existing owned RuntimeValue/Object-target
data and ActionArgument sequences are transported without semantic validation;
the admitted owning codec and ABI must validate them before any use.

The bounded scalar successor adds a public `OntologyObjectFacade` base and
`ScalarObjectContext` for generated async methods. Infrastructure supplies an
already caller-bound client, immutable ABI descriptions, receiver and business
key. Ontology owns runtime/provider/Meta composition; consumers never import it.
Host execution, bridge migration, renderer installation and materialization are
separate gates. This package changes no root manifest, lock or generated output.

## Generated scalar Objects

Normal application code receives its bound generated Object:

```python
async def application(object):
    return await object.read_scalar()
```

Infrastructure uses `ScalarObjectContext.for_local_scalar(...)` to retain the
accepted `LocalScalarClient`, receiver, original `OntologyObjectClassBinding` and
exact generated fragment-closure digest, then calls
`context.bind(GeneratedClass, action_ref=..., invocation_key=...)` for injection.
Those binding checks establish consistency, not host authentication or admission.
Caller authority and the original deadline remain in the supplied host transport.

Context descriptions are reusable. Each bound scalar facade permits one selected
Action once; it consumes that right before awaiting transport. Read
`object.invocation_receipt` after completion when infrastructure needs the
existing receipt. Refusal/cancellation propagates and leaves no reusable call
right. `close()` closes an unused binding. No retry, journal or global receipt
cache is added. A fresh binding cannot bypass the backend's durable replay check.

The accepted no-argument adapter refuses arguments locally. The fixed
`ScalarActionInvoker` successor boundary takes ordered exact parameter-ref/value
pairs; supplying it does not qualify an argument-bearing backend. Fields,
constructors, relationships and multi-method transactions are unavailable in
this profile. This does not change full facade preparation or its qualification.

See the [client/backend handoff](../../../../../../../docs/reports/ontology-generated-client-backend-handoff-20261010.md).

Run the data and import proofs from the repository root without installing:

```sh
.venv/bin/pytest -q -c workspaces/aware_kernel/modules/ontology/libs/object_facade_client/python/pyproject.toml workspaces/aware_kernel/modules/ontology/libs/object_facade_client/python/tests
.venv/bin/basedpyright --pythonpath .venv/bin/python -p workspaces/aware_kernel/modules/ontology/libs/object_facade_client/python/pyproject.toml
```

These are framing/dependency proofs, not authentic host, issuer, VM, store,
materialization or remote conformance tests.

## A1 shared portable definitions

`owner_values` is the sole owning implementation of `FrozenJson`, `ValueKind`,
`RuntimeValue`, the three descriptive Action target forms and tagged
`ActionArgument` values. Ontology's internal encoding/model imports reference
these same class/function objects. Public consumers import this package only.
The portable construction/serialization methods validate native data and retain
existing tags, decimal strings, homogeneous repeated scalars, canonical bytes
and digest domains. They supply no schema, ABI, target/currentness or grant proof.

A1 adds no Object, activation, preparation, host adapter or transport implementation.
Host codec guards retain the owner helper/method closure internally; no verifier,
provider or nominal capability is exported. Root package registration, installed
wheel conformance and refreshed child source/launch acceptance remain separate.
The source import proof loads five public modules and fifteen TypeSchema modules
from their declared source roots. The sixteen-file TypeSchema census also includes
`type_schema_operation.py`, which this import does not load.


### A2: declared ABI data

The public owner also supplies class/member ABI descriptions, roles, cardinality,
traversal and residence enums. Host imports are exact aliases of these definitions.
Meta TypeSchema remains the sole owner of ValueShape, ShapeKind and ScalarKind;
the narrow foundation dependency loads its package initializer, including its
nominal definitions. The facade exports only shape data, and never admits or
mints those nominal authorities. Complete ABI derivation/decoding, topology joins
and contextual verification remain host-local. Native tuple/list inputs are
supported; arbitrary iterables and foreign records refuse before dispatch.
There is no client activation, renderer, bound Object or executable entrance.

### A3: portable record prerequisites

The same public owner supplies `MutationScope`, `CoverageGrade`, `FieldValue`,
`ObjectInstance`, `RelationshipInstance`, `ProjectionCoverage`,
`SchemaActionParameterDefinition` and `SchemaActionDefinition`. Host model/schema
imports retain exact class identity. These are detached records and descriptions;
an Object instance ref or mutation-scope field grants no branch or execution access.

Native preflight protects constructors, serialization and nested shape/value
returns. RelationshipInstance keeps its historical class source with checked
native method wrappers; host contextual capture retains both wrapper and original
implementation code. Canonical bytes, tags, defaults and ordering retain their
existing laws. Fields and parameters do not add new uniqueness or topology rules.

Complete ABI/snapshot derivation, external endpoint admission, contextual codec
authority, prepared operation and durable settlement remain host-local. Preparation,
client binding/activation, bridge migration and materialization are later units.


## Complete portable Object ABI

The package owns OntologyObjectActionRoleDeclaration, OntologyObjectActionRoleManifest
and OntologyObjectAbi, with one object_abi_codec implementation. Ontology host
imports are exact aliases. encode_object_abi/decode_object_abi preserve canonical
UTF-8 bytes, contract identifiers and digests. Expected digests are caller-supplied
consistency assertions; decoding creates no nominal admission or execution authority.

Bundle/slice/topology factories remain in Ontology's host as explicit
create_object_action_role_manifest and derive_object_abi functions. Public
manifest.create and ABI.derive do not exist. Consumers do not import these host
factories, providers, stores or runtime machinery. Services will consume the same
bounded client rail and materialized typed Object facade after those later units.

Direct portable construction admits native owning data only. The current decoder
profile additionally requires every relationship peer class inside its class closure,
including external-dependency peers; construction's declared external omission is
not a decoder roundtrip guarantee. Unsupported complete-body facade profiles remain
unavailable until separately qualified. F0.2 Body/aggregate/depth limits remain
cumulative at future facade admission; no bulk or alternate codec rail is introduced.

This is detached data and codec conformance only. It does not install or activate
Objects, migrate the Service bridge, render materialized output or run the VM.
Historical preparer/child source pins require independently reviewed successors
before evaluator experiments under the changed source.

## A5: complete Object values, endpoint claims and snapshot data

`owner_values` owns complete `OntologyObjectValue` records, resident relationship
slices and edges, both external endpoint reference variants, their coordinates,
profiles and evidence claims, and source observation claims. Host imports retain
exact class/function identity. `object_value_codec` supplies the one structural
value/endpoint grammar; Ontology's host codec helpers and metrics context are
exact aliases. The topology-dependent relationship-slice factory remains an
explicit host function. Public relationship slices have no attached host factory.

`OntologyObjectSnapshotData` and `OntologyObjectSnapshotAuthorityData` carry the
complete snapshot payload. Their provider component is
`OntologyObjectProviderAuthorityClaim`: six primitive fields with `preview`,
`local_operational` or `canonical_replica` grade. Both canonical branch/commit
coordinates are required for `canonical_replica`; both are null otherwise.
These grades are distinct from external endpoint evidence profiles. Every claim
remains data, including names inherited from historical evidence contracts.

`encode_object_value` / `decode_object_value` and
`encode_object_snapshot_data` / `decode_object_snapshot_data` preserve existing
canonical bytes, digest domains, ordering, nullable fields and complete payloads.
They recursively admit exact operands before nested lookup or enum conversion.
Construction and encoding share non-mutating semantic validation of source,
authority and snapshot digests, nested values and value-authority correspondence.
Valid detached copies require no provenance marker. Genuine guards and original
executable helpers remain retained across mutable dispatch and helper returns. Native-only JSON traversal
retains the C string primitives and invokes no mutable JSON encoder/decoder
callbacks. The standalone structural codecs retain legacy body sizes; the future
facade's 16,384-byte Body, depth and cumulative member limits still apply at that
outer entrance. There is no bulk route or relaxed facade profile.

Ontology alone owns `AuthorityEvidence`, operational snapshot classes, provider
admission and view resolution. Its checked `snapshot_data_from_host_snapshot`
adapter projects host snapshots to detached data. There is no public inverse
projection that installs a provider or creates operational authority. Consumers
continue to import this public package; runtime composition, activation and
provider machinery remain behind Ontology. Typed materialized Objects and common
Service binding infrastructure are later units.

At the A5 checkpoint, a normal public import loaded eight public modules and
fifteen TypeSchema modules. Its explicit source-read import added two framing
modules. The C successor census below includes later accepted portable preparation,
subject framing and the new client; both retain the same dependency boundary.

This source cut does not install, activate, execute, materialize or deploy Objects.
The three-package wheel proof has been adapted but requires its separate installed
conformance gate. Changed owner/host bytes and the two new codec members require
separate source-pin successor and complete-child/no-VM launch acceptance.

## C: detached generic read exchange

`exchange_read(transport, request_bytes)` accepts one prepared canonical generic
read Request and the existing `FacadeTransport`. Common Service infrastructure
owns preparation, original caller permission and the installed transport. The
client decodes the exact Request and admits its minimum result budget before
calling `transport.exchange` once with the unchanged bytes.

```python
from aware_ontology_object_facade_client import exchange_read

response = await exchange_read(installed_transport, prepared_request_bytes)
```

The return is detached `source_read_wire.Result | source_read_wire.Rejection`
data. A Result must satisfy the owning grammar, witnesses, complete correlation,
selection/revision joins and final byte budget. A Rejection has its separately
bounded grammar and asserts no verified association. Invalid frames and local
budget failures raise `WireError`; malformed requests fail before dispatch.
Transport errors and cancellation propagate unchanged. No timeout extension,
fallback, automatic retry, result truncation or second journal is introduced.
Explicit repeated calls remain separate exchanges; the original infrastructure
owns duplicate handling, fresh admission, cancellation settlement and cleanup.

This API uses the existing canonical implementation. It creates no permission,
issuer, model, provider, binding, activated operation or working Object. Even a
well-framed `ok` result and matching witnesses remain data requiring original
owner verification. Consumers receive this client boundary; they do not compose
Ontology runtime, Meta, stores or source providers. The future materialized typed
facade and Service/View ergonomics extend the same rail through later scopes.

The complete public source inventory has nineteen modules. A normal import loads
eighteen of them plus sixteen Meta TypeSchema modules; explicit subject framing
loads the nineteenth. Exact source and loaded-origin proofs forbid ambient Aware,
Service, Ontology host, provider and execution-package imports. O's actual
recipient and S's positive nominal lifecycle remain separate implementation gates.
# Supported local scalar consumer (trusted-runtime v0)

An application receives a caller-bound `LocalScalarClient` from its configured
host. Its only import is this public package:

```python
from aware_ontology_object_facade_client import LocalScalarClient

async def read(ontology: LocalScalarClient):
    result = await ontology.invoke_scalar(
        object_ref="object:root",
        action_ref="scalar.read_scalar",
        invocation_key="demo/001",
    )
    return result.value, result.receipt
```

The host owns caller authorization, Action/Function configuration, source pins,
the two operational journals and the isolated stock-Python worker. Applications
cannot supply executable bodies, a provider, a permit or an alternative runtime.
Invocation keys are scoped to caller and configured Object/Action/store; they
are not Meta permits. Exact duplicates, concurrent duplicates and retries after
a lost response are refused durably. There is no automatic retry.

Success means scalar validation, both journal settlements and worker cleanup
have completed. `ScalarInvocationError.recovery_ref` preserves the original
attempt coordinate for failures; cancellation propagates after child cleanup.
The implementation does not claim remote facade witness/peer authentication or
hostile in-process mutation resistance. Broader Object operations remain out of
this local profile. Infrastructure/hosting packages are not imported by this
public API. The older detached read and framing contracts are unchanged.

After a lost response, use the same bound client and business key without
executing again:

```python
status = await ontology.invocation_status(
    object_ref="object:root", action_ref="scalar.read_scalar",
    invocation_key="demo/001", recovery_ref=original_attempt_ref,
)
```

`recovery_ref` is optional and checks the key's original attempt, never a global
lookup. States are `not_found`, `pending`, `unavailable`, `recovery_required`
and `backend_settled`. The response includes the original journal revision and
references, and a `backend_receipt` only after both original journal joins.
It does not return a scalar value or assert worker cleanup/host success. Status
cannot issue a permit, contact the provider, change the journal or retry.
Admitted keys stay spent, even when their status is unavailable or uncertain.

Host infrastructure can restore a status-only reader without admitting an
executable runtime; that client refuses `invoke_scalar`. The host package's
README documents a test-free team starter and its explicit init/invoke/status
commands. Caller authorization and configuration remain host-owned.

## Constructor client successor (source candidate)

`ObjectConstructorContext` binds an infrastructure-owned `invoke_constructor`
port, exact original class binding, complete fragment digest and expected
provider/generation. The explicit constructor renderer emits a subclass of
`OntologyObjectConstructor` with typed, required scalar arguments. Business
application code receives that bound operation:

```python
blob = await storage_blob.create(sha=uploaded_sha, mime_type="text/plain", size_bytes=byte_count)
receipt = blob.invocation_receipt
```

There is one constructor Action per binding. Optional/null, relationship
construction and instance Actions refuse in this profile. Arguments retain
their original parameter refs/order; the client does not normalize SHA, choose
identity, upload bytes, write metadata or select a FunctionImpl. Infrastructure
and the original backend own those admissions and effects.

The backend port returns `ObjectCreationResult` only after commit/reconciliation,
positive persistent reread, both journal settlements and worker cleanup. The
client checks exact response kinds, all original request/binding labels,
provider joins and a receipt with the original durable revision and local
operational evidence. `canonical_commit_ref` is optional and stays `None` when
the backend has no canonical commit; the client must not invent one. Receipt
data and Boolean completion markers are consistency checks, not nominal
authority or an independent persistence proof.

Success returns a distinct object of the generated class carrying an original
`OntologyRuntimeActionInstanceRefTarget` and `ObjectCreationReceipt`. It is an
inert created-object handle: no field snapshot, implicit lookup, relationship
traversal or further operation right. Neither it nor the original constructor
can invoke again after operation entry. Python signature arity errors precede
entry and backend contact. Completed/failed/closed operations and created handles drop
their infrastructure context reference. A new operation requires explicit
infrastructure binding; same-key replay remains the backend's durable refusal.

Failures preserve the backend's original exception/recovery coordinate and
cancellation. There is no automatic retry or compensation. This trusted-local
profile does not claim hostile in-process mutation resistance, qualified
remote transport or a working persistent Storage backend. See the
[client/backend handoff](../../../../../../../docs/reports/storage-generated-client-backend-handoff-20261010.md)
for the pending integration and effect gates.

## Explicit state acquisition

`await GeneratedState.get(reference, using=reads)` is the primary public read
API. The inherited class method delegates to
`reads.bind(GeneratedState, reference).acquire(...)`; that mechanism remains
available for reusable selections. Binding alone performs no I/O. `get()` asks
the explicitly injected infrastructure reader for freshly admitted state,
forwarding optional `expected_revision_ref`. There is no global backend or
ambient caller. A declared field named `get` refuses explicitly at state-class
creation or context admission rather than being overwritten. The resulting
`ObjectObservation` contains immutable typed fields, the original detached
snapshot, coverage and owner-projected configuration/history correspondence.
Getters perform no I/O and convey no Action permission.

`expected_revision_ref` constrains the newly observed head in the configured
branch/lane; it never selects historical state as a fallback. Context closure
prevents new acquisition and suppresses a response returned during closure.
Already delivered observations remain historical data. The initial profile
supports declared Boolean, integer and text fields with their null semantics;
relationships, enum state and Action activation remain separate profiles.

The supplied invoker retains caller, deadline and original backend admission.
Constructing these detached records or supplying another local invoker does not
produce an authentic host observation. The Storage adapter is an explicit
trusted-local, provisional snapshot profile, not canonical OIG replay or an
Actor/Grant issuer. Source and installed qualification remain separately reported.

The combined Object-interaction profile can retain declared external relationship
metadata through `decode_object_abi(..., allow_external_dependency_bindings=True)`.
Infrastructure selects this option explicitly. The default decoder retains its
closed class-closure profile. The option admits neither a missing resident peer
nor a foreign relationship owner; it supplies no external Object state, read
authorization or navigation capability. Enum-aware reads still require the
original schema and exact generated schema digest.
