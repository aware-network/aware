# Aware Code Semantic Contract Runtime

This package is the zero-production-dependency execution boundary for Code
semantic-contract providers and profiles.

It owns strict portable coordinates, provider declarations, acyclic profile
resolution, invocation/result envelopes, canonical codecs, async provider
execution and nonserializable execution completion. Exact invocation codec
bindings admit canonical body bytes into runtime-local live values; providers
cannot receive detached objects or return coordinate-only results. Domain
packages retain their transition/prepared-effect body meaning and codecs.
Workspace retains source/session/publication authority. Meta/OIG remains an
optional canonical adapter that independently re-executes admitted intent.

The package imports no Workspace, FileSystem, API, SDK, Ontology, Meta, ORM,
OCG/OIG, generated, service, registry or materialization package.

## Portable semantic-package authority

The package exposes the Code-neutral
`CodePortableSemanticPackageAuthority` value and its strict v1 codec. Create
authority with `create_portable_semantic_package_authority(...)`, serialize it
only through `to_wire()` or `canonical_bytes()`, and reconstruct it only through
`from_wire(...)` or `from_canonical_bytes(...)`. The Code-owned content
coordinate is issued by
`code_portable_semantic_package_authority_body_ref(...)`.

There are no module-level encode/decode aliases and no compatibility-DTO or
mapping fallback. The value is not yet integrated into a production consumer;
that migration requires its own complete atomic inventory.

Run focused proofs:

```bash
uv run --isolated --extra test pytest -q
```

Canonical contract:
`../../../docs/specs/semantic-contract-runtime/SPEC.md`.


## Portable package authority as a semantic body

`package_authority_body_codec` adds an explicit `PackageAuthorityBodyCodec` and
`package_authority_body` factory over the existing portable authority v1. The
body bytes are exactly `CodePortableSemanticPackageAuthority.canonical_bytes()`;
decoding delegates to its strict owner decoder. No envelope or new authority
value is introduced, and no codec/profile is globally registered.

The logical role is `package_authority`. Its Code contract ref uses the existing
portable authority schema and codec identity. Its value ref/full-body digest/size
come from `code_portable_semantic_package_authority_body_ref`; the internal
domain-separated authority digest is never substituted for the full-body SHA.
The optional invocation check binds package ref only. Owner-specific kind,
manifest-source digest and convergence laws remain in the selected semantic
contract; host admission remains external. Tests cover multiple owner kinds.

## Portable grammar source groups

`grammar_source_group` adds four immutable V1 records and the
`CodeGrammarSourceGroupCodec` over the existing Code selection/origin codecs.
`decode_grammar_source_group`, `encode_grammar_source_group` and
`grammar_source_group_body` are also exported from the package root.

The codec preserves occurrence-qualified members even when package labels,
paths and source bytes are equal. It checks complete selection/origin/source
correspondence, canonical JSON, closed fields, exact types, collection and byte
bounds, ordered unique members/edges and root connectivity. It does not sort,
normalize source text, merge members or impose Language's separate contribution
graph rules. Package self-edges and cycles can be valid portable connectivity.

```python
from aware_code_semantic_contract_runtime import (
    CodeGrammarSourceGroupCodec,
    grammar_source_group_body,
)

codec = CodeGrammarSourceGroupCodec()
group = codec.decode(received_canonical_bytes)
retained_body = grammar_source_group_body(group)
assert codec.encode(group) == received_canonical_bytes
```

Successful decoding establishes portable correspondence only. It cannot
authenticate original Workspace selections, dependency admissions or borrowed
resource lifetimes. `grammar_source_group_body` creates the original
`SemanticBody` representation; it does not admit an invocation or grant an
additional context budget. The original context validator still charges all
body bytes and serialized coordinates together.

This source slice keeps the existing dependency-free package metadata. Original
input/contribution correspondence, canonical generated SDK exposure, successor
version/projection qualification and installation are separate deliveries.

## Grammar group input correspondence

`validate_grammar_source_group_input(group, input=owner_input)` is exported from
the package root and implemented in `grammar_profile_join.py`. It freshly
checks the complete original `SemanticInputProductionInput` digest and context
budget, one exact group body/coordinate, the root package and every root source
path, complete coordinate and byte body in original order.

Call this helper inside the original registered producer. It performs no source
or context-owner call and retains no validation cache. The registered executor
must still authenticate the original source/context before and after owner
execution. A coherent manufactured detached pair can pass correspondence;
that does not grant original admission, revive a consumed use or supply
Workspace lifetime evidence. Package names and source-identity continuity
remain checks of the original issuer.

The bounded source proof uses synthetic owner fixtures through the real Code
executor. Genuine Workspace grouped-source joining, Language contribution
production/correspondence and canonical SDK composition remain separate.

## Retained declaration context schema

The original `retained_declaration_scope_codec` submodule exports immutable
`RETAINED_DECLARATION_SCOPE_V3_DESCRIPTOR` bytes and
`RETAINED_DECLARATION_SCOPE_V3_REF`. The descriptor is exactly 2,544 canonical
bytes; its schema SHA-256 is
`34ca57cb747ded8a3d9a55127b6ba39257c5852dae297b7ba5a218a00222c0e9`.
The reference retains key `aware.code.retained-dependency-scope-closure.v3`
and version `3`. Existing V3 payload encoders/decoders and their wires are unchanged.

Use that exact reference in the existing Code receiving declaration:

```python
from aware_code_semantic_contract_runtime.retained_declaration_scope_codec import (
    RETAINED_DECLARATION_SCOPE_V3_REF,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputContextContract,
)

declaration_context = SemanticInputContextContract(
    "declaration_scope", RETAINED_DECLARATION_SCOPE_V3_REF,
)
```

This publishes a schema identity, not an original declaration projection,
registration or admission. Workspace must supply the original scope/member
correlation through its existing issuer. The full context-body hash, original
closure digest and descriptor schema digest remain distinct. Declaration and
grouped contexts share the existing aggregate 8 MiB budget; no standalone codec
limit widens that budget. Source constants do not qualify an installation,
public grammar operation, native parser or generated SDK.

## Receiving original declaration and grouped contexts

`read_grammar_declaration_context(owner_input)` is exported from the package
root. Call it inside the original registered producer; it returns the original
`CodeGrammarSourceGroupV1` and complete `CodeRetainedDependencyScopeClosureV3`.
It freshly validates the input graph/digest and shared context budget, exact
context roles/references, ordered root sources and each member's qualified
scope/module/package occurrence against the supplied original declaration.
Manifest paths, body references, digest, size and package kind must correspond;
equal package labels, paths or bytes cannot substitute another occurrence.

This synchronous primitive performs no source reads, TOML interpretation,
Language reconstruction, registration, caching or cleanup. A coherent
manufactured input can pass portable correspondence. Original registered
execution must still authenticate nominal origin, currentness and borrowed
lifetimes before and after production; this helper grants no admission.

Source tests now consume Workspace's committed correlated-declaration issuer
through the original registered executor. They prove success and refusal after
an original module changes; restoring bytes does not revive the retired use.
The supplier's planning comparison remains an explicit upstream fixture. These
are source proofs, not installed planning, generated SDK or public materialization
readiness. Authored interpretation and genuine Language contribution production
remain the next receiving stage.

## Portable grammar payload and failure codecs

The neutral package now supplies the Python owner payload surface for the
accepted grammar receiving contract:

- `CodeGrammarSyntaxBindingV2` and its complete provider, declaration,
  contribution and anchor models, with `CodeGrammarSyntaxBindingCodec` and
  `encode_grammar_syntax_binding` / `decode_grammar_syntax_binding`.
- `CodeGrammarProfileSelectionCodec`, reusing the original full profile model
  and codec under an 8 MiB body bound. `grammar_profile_selection_body` and
  `grammar_syntax_binding_body` produce exact portable body coordinates; the
  full-body digest is distinct from the original profile's domain digest.
- `CodeGrammarSourceRoleSelectionV1` with a strict standalone data codec;
  `CodeGrammarReadTransitionV1` and `CodeGrammarReadEffectV1` as detached values.
  Transition/effect output codecs still require the later original contextual
  production join; this package supplies no context-free output decoder.
- `CodeGrammarRoleCleanupReceiptV1` and `CodeGrammarRoleFailureEvidenceV1`,
  with closed canonical codecs. Nullable fields require explicit null. Known
  results, uncertain work/epoch states and per-resource disposal statuses remain
  distinct; inconsistent verified-completion claims refuse.

All ports are exported at the package root. Syntax decoding preserves occurrence
identity, authored provider order and field-path segment order, and validates
unique canonical inventories and contribution-coordinate correspondence.
It does not repair, reorder, merge equal-labelled occurrences or select another
schema/version. Imported profile/provider/coordinate owners are unchanged.

```python
from aware_code_semantic_contract_runtime import CodeGrammarSyntaxBindingCodec

codec = CodeGrammarSyntaxBindingCodec()
payload = codec.decode(received_canonical_bytes)
assert codec.encode(payload) == received_canonical_bytes
```

These are **portable data**, not original source/result admission, factory
registration, execution completion or cleanup authority. An internally
consistent decoded `verified` receipt is still an untrusted observation until
its original owner authenticates it. No cleanup ticket, raw return, exception
or live reader is serialized or issued by these ports. Root/profile association,
namespace/dependency/currentness checks and contextual transition/effect
admission remain original registered execution responsibilities.

This is a bounded source successor, not an installed release or public grammar
operation. The canonical installer migration below advances the authored version
to 0.2.0; production dependencies remain empty. No SDK payload alias, Dart
payload decoder, parser, Language, Workspace, Service or Object dependency is
introduced.

## Canonical installed factory intake

`installed_provider_factory` owns the installed-entry-point lookup, lock and
cache previously held by Dev. Import its two functions from this submodule:

```python
from aware_code_semantic_contract_runtime.installed_provider_factory import (
    admit_installed_semantic_stage_factory,
    admit_installed_semantic_product_factory,
)
```

Root intake preserves the existing key-only behavior. Fixed-product intake
additionally checks the unique entry point, exact target and normalized
distribution before loading or returning a cached admission. Its exact UTF-8
tokens are bounded to 512 bytes for key/distribution and 4,096 bytes for target;
targets must be `module:function`, without extras. The loaded function must
match that module and qualified name and pass the original zero-argument
factory admission. Both entrances share the same admission and cache.

The qualified application supplies fixed product metadata; request TOML does
not select a load target. Product intake refuses after fork before touching the
inherited lock. Neither entrance executes the admitted factory. Loading can
import code and have effects; failures preserve the original exception without
alternate loading or automatic retry.

This binds a live factory, not original source, catalog, epoch, execution or
installed-byte authority. The Dev compatibility module directly reexports the
same root function. Source parity does not qualify package resolution, genuine
grammar execution or a consumer installation.

## Grammar operational declarations

`grammar_operational_profile(stage)` constructs a fresh complete original
`SemanticContractProfileDeclaration` for exactly `profile_selection` or
`syntax_binding`. It uses the accepted provider/schema references, required
input roles and terminal result/effect roles, and the original graph validator.
Both profiles apply only to `code`, `ontology` and `sdk` roots for
`resolve_grammar_profile`.

```python
from aware_code_semantic_contract_runtime import (
    grammar_operational_contracts,
    grammar_operational_profile,
)

profile = grammar_operational_profile("syntax_binding")
required_body_contracts = grammar_operational_contracts("syntax_binding")
assert len(required_body_contracts) == 7
```

The canonical contract inventory contains each input/transition/result/effect
reference once: six for profile selection, seven for syntax binding. Syntax
requires `code.profile_selection` as a consumed input; it does not reuse that
body as its generic state predecessor. Its own state remains typed-empty.

These operational declarations are not the customer's authored interpretation
profile. They issue no provider, catalog, runtime, host or source admission.
The inventory names the required contracts; it does not itself supply concrete
codecs or admit their execution. The contextual output codecs below, genuine
factories/catalog products and original host attachment must be qualified before grammar execution. No automatic graph
target, file write, parser build or Object dependency follows from these values.

## Contextual grammar output codecs

`CodeGrammarReadTransitionCodec` and `CodeGrammarReadEffectCodec` implement the
existing Code runtime's contextual codec protocol. Context-free `encode` and
`decode` always refuse. The runtime supplies and registers the original body
validation context; clients must not manufacture a context or epoch.

Both codecs verify the exact registered body and codec coordinate, purpose,
operational profile/provider, complete input roles, typed-empty state, source
input digest, input-closure digest and candidate result. Syntax additionally
matches its candidate to the consumed full-profile body and selection. An effect
requires its already admitted transition and emits the literal physical effect
`none` only for successful read-only derivation.

Copied/unregistered contexts, epoch or codec substitution, mismatched bodies and
result-coordinate changes refuse. Original result failures and interruptions
propagate without retry. These ports introduce no new registry and do not upgrade
failure/cleanup uncertainty to success. Existing portable models and wire
references remain unchanged.

This qualifies source-level correlation through original Code runtime contexts
with fixture providers. It does not authenticate Workspace source provenance,
factory enrollment or host attachment. Genuine grammar execution, complete input
codec assembly, generated SDK parity and installed qualification remain separate.

## Grammar input and context codecs

`CodeRetainedDeclarationScopeCodec` exposes the original complete V3
declaration codec as a runtime body adapter. Its new implementation coordinate
is `RETAINED_DECLARATION_SCOPE_V3_CODEC_IMPLEMENTATION`; the earlier schema
publication did not supply this adapter identity. Original V3 functions,
descriptor, bytes, ordering and bounds remain unchanged.

`CodeGrammarSourceRoleSelectionCodec` delegates the accepted selection V1 wire
to its original owner functions. `grammar_input_body_codecs()` returns a fresh
three-entry table for `declaration_scope`, `grammar_selection` and
`grammar_source_group`, reusing the existing group codec. It is not a complete
six/seven-contract product, a registry or a source-admitted factory. Syntax's
retained profile input and source-bound result adapters remain explicit additions.

```python
from aware_code_semantic_contract_runtime import (
    grammar_input_body_codecs,
    validate_grammar_source_role_selection,
)

input_codecs = grammar_input_body_codecs()
validate_grammar_source_role_selection(selection, input=original_owner_input)
```

Inside original registered production, call the selection check before and
after interpretation. It reuses the existing complete input/context receiver,
preserving the aggregate budget and digest. It matches operation, stage, root
occurrence, original consumer scope and the exact selected profile publication.
Imported profiles also require the original consumer's declaration association;
scope membership, equal paths or equal bytes alone cannot select a profile.

These are fresh portable correspondence checks. Decoding or passing the check
does not authenticate Workspace provenance, admit a provider/host, establish
currentness, or revive a retired use. Original owners must retain and revalidate
those lifetimes. No source reader, validation cache, alternate generator,
Object dependency or mandatory Service is added. Genuine factories/catalog
attachment, canonical SDK composition and installed qualification remain separate.
