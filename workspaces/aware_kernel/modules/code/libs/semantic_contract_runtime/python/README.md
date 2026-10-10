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
