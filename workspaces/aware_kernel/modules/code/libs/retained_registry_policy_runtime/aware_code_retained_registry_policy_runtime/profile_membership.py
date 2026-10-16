"""Derive declared profile members from portable retained bytes, never grants.

Original Workspace validators must authenticate selections, status and membership.
Code's later live registration join must authenticate executable correspondence.
"""

from __future__ import annotations

from dataclasses import dataclass

from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV2,
    AwareModuleSpecV3,
    DeclarationTable,
)
from aware_code_module_manifest_contract_runtime.profile_models import (
    CodeSemanticContractProfileManifestSpec,
    CodeSemanticContractProfileProviderSpec,
    CodeSemanticContractProfileProviderSpecV2,
)
from aware_code_module_manifest_contract_runtime.profile_parser import (
    parse_profile_manifest,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure import (
    DependencyScopeEdge,
)
from aware_code_semantic_contract_runtime.dependency_scope_closure_v2 import (
    CodeRetainedDependencyScopeClosureV2,
    DependencyScopeProfileAssociation,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeRetainedDeclarationPackage,
    CodeRetainedDependencyScopeClosureV3,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopePackage,
)

from .calculation import _plain, _scope_declarations
from .qualified_scope import (
    validate_selected_scope_graph_v2,
    validate_selected_scope_graph_v3,
)


@dataclass(frozen=True, slots=True)
class ProfileMemberDeclaration:
    """Portable correspondence only; every registration remains declared meaning."""

    member: CodeSemanticContractProfileProviderSpec
    package: CodeRetainedScopePackage | CodeRetainedDeclarationPackage
    registration: DeclarationTable


@dataclass(frozen=True, slots=True)
class ProfileMembershipSelection:
    """One original edge occurrence's interpreted evidence, not an admission."""

    closure_digest: ContentDigest
    edge: DependencyScopeEdge
    association: DependencyScopeProfileAssociation
    meaning: CodeSemanticContractProfileManifestSpec
    members: tuple[ProfileMemberDeclaration, ...]


def _module_declarations(scope):
    models, packages, declarations, _ = _scope_declarations(
        scope.projection, versions=(AwareModuleSpecV2, AwareModuleSpecV3)
    )
    return models, packages, declarations


def _profile_registration_matches(member, module, package_id, registration):
    """Match only the exposure authored in this retained profile occurrence."""
    value = _plain(registration)
    if value["semantic_contract"]["provider_key"] != member.provider_key:
        return False
    if type(member) is CodeSemanticContractProfileProviderSpecV2:
        if member.package_id != package_id or member.registration_key != value["key"]:
            return False
        stages = [row["stage"] for row in value["profiles"]]
        if member.exposure == "graph_product":
            return type(module) is AwareModuleSpecV3 and stages == ["graph_product"]
        return member.exposure == "stage_pair" and stages == ["authority_derivation", "source_planning"]
    return type(member) is CodeSemanticContractProfileProviderSpec


def resolve_profile_memberships(
    closure: CodeRetainedDependencyScopeClosureV2 | CodeRetainedDependencyScopeClosureV3,
) -> tuple[ProfileMembershipSelection, ...]:
    """Interpret requested members without filesystem access or runtime imports.

    All matching registrations remain separately bound to their package; this does
    not choose an operation's registration, equate provider keys to live keys or
    require result capabilities. Consumer status is checked by original Workspace.
    """
    if type(closure) is CodeRetainedDependencyScopeClosureV2:
        validate_selected_scope_graph_v2(closure)
    elif type(closure) is CodeRetainedDependencyScopeClosureV3:
        validate_selected_scope_graph_v3(closure)
    else:
        raise TypeError("exact qualified dependency closure required")
    digest = closure.closure_digest
    scopes = {s.scope_key: s for s in closure.scopes}
    target_declarations = {}
    selections = []
    for edge, association in zip(
        closure.edges, closure.profile_associations, strict=True
    ):
        meaning = parse_profile_manifest(
            association.manifest.body, source_label=association.manifest.relative_path
        )
        if (
            type(meaning.aware_semantic_contract_profile) is not int
            or meaning.aware_semantic_contract_profile not in (1, 2)
            or meaning.profile.key != edge.profile_key.value
            or meaning.profile.status != "active"
        ):
            raise ContractViolation("selected profile version/key/status differs")
        if edge.target_scope_key not in target_declarations:
            target_declarations[edge.target_scope_key] = _module_declarations(
                scopes[edge.target_scope_key]
            )
        modules, packages, declarations = target_declarations[edge.target_scope_key]
        requested_keys = edge.semantic_contract_provider_keys.value
        if not isinstance(requested_keys, tuple):
            raise ContractViolation("exact provider restriction tuple required")
        requested = set(requested_keys)
        members = []
        found = set()
        for member in meaning.providers:
            if member.provider_key not in requested:
                continue
            if member.status != "active" or member.module_id not in modules:
                raise ContractViolation(
                    "requested profile member inactive or module missing"
                )
            matches = []
            for key, declaration in declarations.items():
                if key[0] != member.module_id:
                    continue
                for registration in declaration.registrations:
                    if _profile_registration_matches(
                        member, modules[member.module_id], key[1], registration
                    ):
                        matches.append(
                            ProfileMemberDeclaration(
                                member, packages[key], registration
                            )
                        )
            if not matches:
                raise ContractViolation("requested member has no retained registration")
            members.extend(matches)
            found.add(member.provider_key)
        if found != requested:
            raise ContractViolation("requested provider absent from selected profile")
        selections.append(
            ProfileMembershipSelection(
                digest, edge, association, meaning, tuple(members)
            )
        )
    return tuple(selections)
