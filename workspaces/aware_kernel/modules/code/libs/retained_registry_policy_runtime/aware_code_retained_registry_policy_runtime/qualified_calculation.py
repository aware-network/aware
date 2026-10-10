"""Fixed qualified source policy over v2 closure; never nominal admission."""

from __future__ import annotations

from dataclasses import dataclass

from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV2,
    AwareModuleSpecV3,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_v2 import (
    CodeRetainedDependencyScopeClosureV2,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalog,
)
from aware_code_semantic_contract_runtime.registry_policy import (
    RegistryPolicy,
    RegistryPolicyGrant,
)

from .calculation import (
    _catalog_correspondence,
    _plain,
    _scope_declarations,
    _validate_declared_package_kind,
)
from .profile_membership import resolve_profile_memberships

QUALIFIED_POLICY_PROFILE = "aware.code.retained-registry-policy.v4"


@dataclass(frozen=True, slots=True)
class QualifiedExecutionProviderSelection:
    """Portable proposal for one selected package, never factory authority."""

    source_identity_digest: ContentDigest
    provider_key: str
    registration_declaration_digest: ContentDigest


@dataclass(frozen=True, slots=True)
class QualifiedDeclaredProviderCandidate:
    """One declared key and all occurrences; no installation or execution."""

    provider_key: str
    source_identity_digests: tuple[ContentDigest, ...]
    registration_declaration_digests: tuple[ContentDigest, ...]


def propose_qualified_declared_provider_candidates(
    closure: CodeRetainedDependencyScopeClosureV2,
) -> tuple[QualifiedDeclaredProviderCandidate, ...]:
    """Index complete retained participants without consulting ambient factories.

    The original Workspace closure and installed provider inventory must be
    authenticated separately. Source-only targets may appear in this value;
    their presence imposes no executable catalog or factory requirement.
    """
    if type(closure) is not CodeRetainedDependencyScopeClosureV2:
        raise TypeError("exact qualified closure required")
    # The same complete relationship-policy laws used by the live host must
    # reject namespace/root conflicts before any installed factory is called.
    rows = tuple(_qualified_occurrences(closure))
    _calculate_qualified_source_policy(closure, rows)
    grouped: dict[str, list[tuple[ContentDigest, ContentDigest]]] = {}
    seen_sources: set[ContentDigest] = set()
    for _, package, _, declaration in rows:
        source = package.source_identity_digest
        if source in seen_sources:
            raise ContractViolation("duplicate qualified source occurrence")
        seen_sources.add(source)
        meaning = _plain(declaration)
        key = meaning["semantic_contract"]["provider_key"]
        digest = ContentDigest.of_bytes(canonical_json_bytes(meaning))
        grouped.setdefault(key, []).append((source, digest))
    result = []
    for key in sorted(grouped, key=str.encode):
        occurrences = sorted(grouped[key], key=lambda row: row[0].value.encode())
        if len({declaration for _, declaration in occurrences}) != 1:
            raise ContractViolation(
                "qualified provider key has incompatible registration declarations"
            )
        result.append(
            QualifiedDeclaredProviderCandidate(
                key,
                tuple(row[0] for row in occurrences),
                tuple(row[1] for row in occurrences),
            )
        )
    return tuple(result)


def propose_qualified_execution_providers(
    closure: CodeRetainedDependencyScopeClosureV2,
    selected_source_identity_digests: tuple[ContentDigest, ...],
) -> tuple[QualifiedExecutionProviderSelection, ...]:
    """Interpret exact selected nodes without promoting source-only targets.

    Workspace must authenticate the selected graph nodes and original closure,
    then revalidate both around factory acquisition. A proposed provider key is
    data: it cannot select a factory or establish live registration authority.
    """
    if type(closure) is not CodeRetainedDependencyScopeClosureV2:
        raise TypeError("exact qualified closure required")
    if (
        type(selected_source_identity_digests) is not tuple
        or not 0 < len(selected_source_identity_digests) <= 256
        or any(type(item) is not ContentDigest for item in selected_source_identity_digests)
    ):
        raise ContractViolation("bounded exact selected source identities required")
    for item in selected_source_identity_digests:
        item.__post_init__()
    if len(set(selected_source_identity_digests)) != len(selected_source_identity_digests):
        raise ContractViolation("duplicate selected source identity")

    # The exact qualified traversal validates the retained relationship topology
    # and imported profile associations. This step precedes factory acquisition,
    # so an executable catalog cannot be a prerequisite here.
    by_source = {}
    for _, package, _, declaration in _qualified_occurrences(closure):
        by_source.setdefault(package.source_identity_digest, []).append(
            (package, declaration)
        )
    result = []
    for source in selected_source_identity_digests:
        matches = by_source.get(source, ())
        if len(matches) != 1:
            raise ContractViolation("unique selected qualified package required")
        package, declaration = matches[0]
        registration = _plain(declaration)
        declaration_digest = ContentDigest.of_bytes(
            canonical_json_bytes(registration)
        )
        result.append(
            QualifiedExecutionProviderSelection(
                source,
                registration["semantic_contract"]["provider_key"],
                declaration_digest,
            )
        )
    return tuple(result)


def validate_qualified_execution_provider_catalog(
    closure: CodeRetainedDependencyScopeClosureV2,
    catalog: CodeSemanticContractCatalog,
    selection: tuple[QualifiedExecutionProviderSelection, ...],
) -> None:
    """Check the later live catalog against the original source proposal.

    The caller still must validate the original Workspace closure and selected
    nodes before and after factory acquisition, and bind nominal registrations.
    """
    if type(catalog) is not CodeSemanticContractCatalog:
        raise TypeError("exact Code catalog required")
    catalog.__post_init__()
    if type(selection) is not tuple or not selection or any(
        type(item) is not QualifiedExecutionProviderSelection for item in selection
    ):
        raise ContractViolation("exact execution provider proposal required")
    current = propose_qualified_execution_providers(
        closure, tuple(item.source_identity_digest for item in selection)
    )
    if current != selection:
        raise ContractViolation("selected provider proposal changed")
    # Full relationship policy remains distinct from executable selection.
    calculate_qualified_registry_policy(closure, catalog)
    for item in selection:
        package, _, declaration = qualified_occurrence(
            closure, item.source_identity_digest
        )
        _catalog_correspondence(
            _plain(declaration), catalog, package_kind=package.package_kind
        )


def _address_scope(closure, declaring_scope, model, address):
    if type(model) is AwareModuleSpecV2:
        return declaring_scope
    scope = address["scope"]
    if scope["kind"] == "local":
        return declaring_scope
    matches = [
        s.scope_key
        for s in closure.scopes
        if s.workspace_handle == scope["workspace_handle"]
    ]
    if len(matches) != 1:
        raise ContractViolation("qualified target Workspace unavailable")
    target = matches[0]
    if not any(
        e.declaring_scope_key == declaring_scope and e.target_scope_key == target
        for e in closure.edges
    ):
        raise ContractViolation("qualified target requires direct declared edge")
    return target


def _qualified_occurrences(closure):
    """Sole qualified correspondence traversal shared by grants and stage checks."""
    selections = resolve_profile_memberships(closure)
    scopes = {}
    participants = {}
    for scope in closure.scopes:
        models, packages, declarations, occurrences = _scope_declarations(
            scope.projection, versions=(AwareModuleSpecV2, AwareModuleSpecV3)
        )
        scopes[scope.scope_key] = (models, packages, declarations)
        participants.update(
            {(scope.scope_key, *key): value for key, value in occurrences.items()}
        )
    for key, occurrence in participants.items():
        scope_key, module_id, package_id = key
        models, packages, _ = scopes[scope_key]
        model = models[module_id]
        address = _plain(occurrence.registration.value)
        target_scope = _address_scope(closure, scope_key, model, address)
        owner_key = (address["module_id"], address["package_id"])
        target = scopes[target_scope][2].get(owner_key)
        if target is None:
            raise ContractViolation("qualified registration package unavailable")
        matches = [
            r
            for r in target.registrations
            if _plain(r)["key"] == address["registration_key"]
        ]
        if len(matches) != 1:
            raise ContractViolation("exact qualified registration unavailable")
        declaration = matches[0]
        if target_scope != scope_key:
            eligible = [
                (selection, member)
                for selection in selections
                if selection.edge.declaring_scope_key == scope_key
                and selection.edge.target_scope_key == target_scope
                for member in selection.members
                if (member.package.module_id, member.package.package_id) == owner_key
                and member.registration == declaration
            ]
            if not eligible:
                raise ContractViolation(
                    "registration not entitled by direct selected profile"
                )
            # All occurrences remain covered by the closure; never flatten their
            # restrictions into an ambient provider-key registry or pick a winner.
        registration = _plain(declaration)
        package = packages[(module_id, package_id)]
        _validate_declared_package_kind(registration, package.package_kind)
        if package.manifest_relative_path != registration["manifest_filename"]:
            raise ContractViolation("registration manifest filename differs")
        for mapping in _plain(occurrence.dependency_targets.value):
            for target in mapping["targets"]:
                dependency_scope = _address_scope(closure, scope_key, model, target)
                if (
                    dependency_scope,
                    target["module_id"],
                    target["package_id"],
                ) not in participants:
                    raise ContractViolation(
                        "qualified direct dependency occurrence unavailable"
                    )
        yield key, package, occurrence, declaration


def qualified_occurrence(closure, source_identity_digest):
    matches = [
        (package, occurrence, declaration)
        for _, package, occurrence, declaration in _qualified_occurrences(closure)
        if package.source_identity_digest == source_identity_digest
    ]
    if len(matches) != 1:
        raise ContractViolation("unique qualified source occurrence required")
    return matches[0]


def calculate_qualified_registry_policy(
    closure: CodeRetainedDependencyScopeClosureV2,
    catalog: CodeSemanticContractCatalog,
) -> RegistryPolicy:
    """Fixed grants over owner declarations; original admission remains required."""
    if type(catalog) is not CodeSemanticContractCatalog:
        raise ContractViolation("exact Code catalog required")
    catalog.__post_init__()
    return _calculate_qualified_source_policy(closure)


def _calculate_qualified_source_policy(
    closure: CodeRetainedDependencyScopeClosureV2,
    rows=None,
) -> RegistryPolicy:
    """Shared source-only policy meaning; no executable catalog dependency."""
    if rows is None:
        rows = tuple(_qualified_occurrences(closure))
    grants = [
        RegistryPolicyGrant(
            package.source_identity_digest,
            ContentDigest.of_bytes(canonical_json_bytes(_plain(declaration))),
            package.package_kind,
            _plain(declaration)["semantic_package_kind"],
            occurrence.namespace.value,
            occurrence.owned_roots.value,
        )
        for _, package, occurrence, declaration in rows
    ]
    return RegistryPolicy(
        closure.closure_digest,
        tuple(
            sorted(
                grants,
                key=lambda g: (
                    g.source_identity_digest.value,
                    g.registration_declaration_digest.value,
                ),
            )
        ),
    )
