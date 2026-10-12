# Aware SDK Contract Runtime

Materialization-independent, language-neutral SDK operation contracts. A
manifest binds public SDK methods to operation request/result/error Type Schema
slices, injected provider operations, and every declared product-language
target under one canonical digest.

`SdkDefinitionState` joins that selected manifest with the complete SDK
operation/method inventory. The join is necessary because a legacy or merely
eligible operation can change renderer-visible SDK meaning without changing
the selected manifest. `SdkDefinitionTransition` derives a complete tagged
movement catalog against typed-empty or one exact predecessor, and
`SdkPreparedDefinitionEffect` carries the complete result state required by a
renderer. Their public codecs are contextual and compare exact canonical bytes
with a fresh derivation.

Source paths are deliberately absent from definition identity, transitions,
and prepared effects. A source adapter may retain them as separate provenance,
but no path can change SDK semantic bytes or acquire publication authority.

The package depends only on `aware-meta-type-schema`. It does not import API,
Ontology, OIG, ORM, Workspace, a service implementation, or generated code.

## Public distribution boundary

The complete `aware-sdk-contract-runtime` library is prepared for distribution
with its original Meta type-schema dependency, not a copied type evaluator.
Version 0.1.1 requires `aware-meta-type-schema>=0.1.1,<0.2.0`; both suppliers
carry their complete Apache-2.0 license and scoped attribution in `LICENSE`
and `NOTICE`. This packaging successor preserves executable implementation
and semantic identities.

Library distribution does not select the separately packaged source adapter,
provider, renderer, compiler or materializer. It does not grant source,
publication or Service authority. The installed consumer composition and its
public envelope remain separate qualification and delivery decisions.

`manifest` holds the one bytes-only `aware.sdk.toml` grammar and its strict
portable meaning codec. The legacy filesystem loader delegates one read to
that grammar. The selected SDK provider applies its operation-specific target
and dependency admission rules to the same parsed model; neither parser nor
codec issues source or package authority.

The original manifest reader retains optional, strictly bounded
`generation_profiles` declarations as `AwareSdkTomlGenerationProfileSpec`
values. Each carries exactly the accepted renderer, operations and three output
directories; public-rail escape, conflicting artifact paths and overlapping
operation partitions refuse. These are authored generation declarations, not
selected SDK definitions or authority to render. Complete declaration coverage
and type ownership remain checks of the original source/profile materializer.
Workspace compilation and registered metadata discovery consume the same reader
without selecting or running a profile.

Unprofiled manifests preserve `aware.sdk.manifest.meaning.v1` bytes exactly.
Profiled meaning uses `aware.sdk.manifest.meaning.profiled.v1`, retaining every
profile in canonical name order. Neither codec admits publication or source
currentness; neither imports a renderer or source compiler.
