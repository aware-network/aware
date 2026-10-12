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
