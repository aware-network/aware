# Aware Meta Type Schema

Zero-dependency immutable values and portable codecs for Meta-owned semantic
type meaning. This package sits beneath OCG/ClassConfig admission and beneath
Ontology and API consumers. It imports no graph runtime, ORM, service,
provider, generated package, or materialization code.

## Public distribution boundary

The complete `aware-meta-type-schema` library is prepared for distribution as
shared neutral infrastructure, including the pure composition, migration and
local read-model modules described below. It is not a Meta/Object product
release and does not select an Object provider, Service, graph store or
materializer. Distribution of these modules does not admit their use as
operational authority or qualify a consumer integration.

Aware-authored files use Apache-2.0; the complete license and scoped attribution
are carried in this package's `LICENSE` and `NOTICE`. Separately distributed
dependencies retain their own terms. Version 0.1.1 changes packaging and
documentation only; semantic contracts and executable implementation are
unchanged. Public delivery remains governed by the exact consumer envelope.

Contracts:

- `aware.meta.semantic-type-schema.v1`
- `aware.meta.semantic-type-schema-slice.v1`

Phase 02 adds pure bounded diagnostics for schema and typed values, directional
structural compatibility, and explicit migration plans bound to exact source
and target schema digests. Migration is schema-directed and returns a new
portable value; it never mutates input, admits a catalog, or calls a provider.

## Cross-package persistent composition

R2 adds an inert, provider-neutral composition kernel without relaxing the v1
bundle or slice contracts:

```text
TypeDefinition
  -> content-addressed definition fragment

package/path admission
  -> exact source-attribution fragment

typed-empty | exact prior package/catalog roots
  + exact binding movements
  -> fixed-depth persistent root patches + immutable CAS-ready bodies

catalog + request-scoped positive reader + requested type roots
  -> exact cross-package composed slice
```

The persistent index is a 64-level SHA-256 radix trie. Every body coordinate
uses the exact `cas://aware-meta-type-schema/<lowercase-sha256>` address and one
closed schema/ref-field role. Transitions read only
changed key paths, return bodies without writing them, and never enumerate a
package or catalog complement. Each read authenticates canonical bytes against
the expected ref, digest, size, schema, node depth, and key path.

Package transitions expose exact definition create/update/delete lifecycle
evidence and embed the complete typed-empty or exact prior package authority.
They also expose structured source-attribution lifecycle. Catalog admission
decodes exact lifecycle bodies, binds fragment types to index keys, and requires
definition and attribution lifecycle maps to match before patching.
The match is the exact prior-to-successor binding-value delta, permitting
document-only changes and source-path moves to retain byte-identical definition
indexes while still authenticating the new document/path attribution.
Catalog transitions positively join that evidence to package and
owner indexes: the target remains present, moved packages are target-reachable,
every owner package contains the definition, package deletion removes all
owners, and missing or extra owner movements fail before patching.

Composed slices carry the exact catalog root, bounded target/dependency
package-root evidence, and a deduplicated immutable fixed-depth proof bundle
for catalog-package, catalog-owner, and package-definition membership.
Direct construction and strict decode re-derive each package, owner, and
definition body coordinate from its exact semantic value, then validate the
dependency closure. Coherent restamping cannot make one coordinate impersonate
another role.

Reader callbacks, caches, timings, byte/read counters, and lookup observations
are ephemeral and excluded from semantic identity. A plain mapping or reader
with a mutation surface cannot be used as prior authority.

This checkpoint has no production source consumer. It does not import the
Aware parser, Workspace, Ontology, graph, ORM, provider, renderer, service, or
materialization packages, and it issues no Workspace, canonical, publication,
commit, or materialization authority.


## Local pure-read model appointment

`aware_meta_type_schema.local_read_model` provides an explicit private composition
appointment for `aware.meta.local-single-graph-scalar-read-model.v1`. It consumes
the existing complete canonical TypeSchema bundle and exactly derived slice,
the declared root/identity/projection coordinates, and complete original topology
bytes. The admitted subset has one graph root, required non-null string, integer
or boolean fields, and empty constraints, aliases and defaults. Unsupported
features and unknown keys are rejected. This does not admit Code factories or
replace the existing broader TypeSchema APIs.

An original local composition creates the owner through
`create_local_model_owner`, then appoints the complete model before a read. The
constructor-issued owner and opaque model handles have original weak identity
membership. Portable DTOs, content hashes, reference labels, subclasses and copied
values cannot recreate that membership. Consumers retain the original module
ports `validate_local_model_owner` and `verify_local_model`; they authenticate
actual owner/handle identity without reading a method on a caller-supplied owner.
Ontology remains responsible for topology and Object/branch/projection laws.
The provider remains responsible for actual namespace appointment, source inputs,
full typed-state derivation and currentness.

Read-time verification is fresh and decoder-free. It rechecks the appointed
original owner/model association, source dispatch relations, process/thread and
unextended deadline, returning the complete original immutable model evidence.
The lifetime ceiling is 30,000 ms. Source/context failure, revision conflict,
expiry, retirement, release and close have terminal membership behavior; restoring
source bindings cannot revive a retired admission. Cleanup touches only the
original owner registry. It requires no Action, Service journal, provider store
write, external callback or publication.

The owner bank bounds original owners to 64, known live-or-retired model identities
to 64 per owner, handle records to 64 per owner, and aggregate retained full model
bytes plus admission bodies to 8 MiB. Released admission buffers and collected
weak handles are reclaimed without removing live terminal membership.

Source/refusal proofs and original TypeSchema equivalence tests qualify this
bounded profile separately. It establishes no general multi-model GOH acceptance,
provider freshness, end-to-end latency or operational integration by itself.
