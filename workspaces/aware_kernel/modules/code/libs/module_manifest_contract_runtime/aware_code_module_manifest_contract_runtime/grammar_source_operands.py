"""Derive grammar operands from original supplied data, never admission.

The explicit request key is a selector, not authority. Original registered
execution must authenticate input/catalog/currentness before and after this
helper. It issues no provider, result-retention or execution capability.
"""

from __future__ import annotations

from dataclasses import dataclass

from aware_code_semantic_contract_runtime.contracts import (
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.grammar_product_contracts import (
    CodeGrammarSourceRoleSelectionV1,
)
from aware_code_semantic_contract_runtime.grammar_profile_contract import (
    CodeGrammarDeclarationSourceV1,
)
from aware_code_semantic_contract_runtime.grammar_profile_join import (
    read_grammar_declaration_context,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalogResolver,
)
from aware_code_semantic_contract_runtime.profile import (
    SemanticContractProfileDeclaration,
)
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputProductionInput,
)
from aware_code_semantic_contract_runtime.source_origin import decode_source_origin

from .grammar_profile_composition import _produce_profile_selection
from .grammar_profile_source import (
    GrammarProfileSourceError,
    _read_grammar_v2_product_nomination,
    _selector,
    parse_grammar_provider_module,
    parse_registered_grammar_profile,
)
from .parser import parse_module_manifest
from .profile_models import (
    CodeSemanticContractProfileManifestSpecV2,
    CodeSemanticContractProfileProviderSpecV2,
)
from .v3_models import AwareModuleSpecV3


@dataclass(frozen=True, slots=True)
class GrammarSourceOperands:
    """Detached complete operands; neither registration nor authority evidence."""

    selection: CodeGrammarSourceRoleSelectionV1
    profile: SemanticContractProfileDeclaration
    provider_occurrences: tuple[str, ...]


def derive_grammar_source_operands(
    input: SemanticInputProductionInput,
    *,
    profile_key: str,
    catalog: CodeSemanticContractCatalogResolver,
) -> GrammarSourceOperands:
    """Resolve one explicit authored table without caller-supplied operands.

    Refuse ambiguous scopes, qualified occurrences or full registered profiles.
    Availability/priority, first matching labels or equal bytes never choose a
    winner. This source-data step does not authenticate original source owners.
    """
    if type(input) is not SemanticInputProductionInput:
        raise TypeError("exact grammar production input required")
    if type(catalog) is not CodeSemanticContractCatalogResolver:
        raise TypeError("original Code catalog resolver required")
    key = _selector(profile_key)
    group, closure = read_grammar_declaration_context(input)
    if input.stage not in ("profile_selection", "syntax_binding") or (
        input.package_identity.package.package_kind not in ("code", "ontology", "sdk")
    ):
        raise ContractViolation("grammar source role/package differs")

    publications = tuple(
        row
        for row in closure.local_profiles
        if row.profile_key == key
        and (
            row.owning_scope_key == closure.consumer_scope_key
            or any(
                association.declaring_scope_key == closure.consumer_scope_key
                and association.target_scope_key == row.owning_scope_key
                and association.manifest == row.manifest
                for association in closure.profile_associations
            )
        )
    )
    if len(publications) != 1:
        raise ContractViolation("explicit grammar profile scope is absent or ambiguous")
    publication = publications[0]
    authored = parse_registered_grammar_profile(
        publication.manifest.body, profile_key=key
    )
    selection = CodeGrammarSourceRoleSelectionV1(
        input.operation_ref,
        input.stage,
        input.input_digest,
        group.root_occurrence_ref,
        key,
        CodeGrammarDeclarationSourceV1(
            closure.repository_binding_ref,
            publication.owning_scope_key,
            "profile",
            publication.manifest.relative_path,
            publication.manifest.body_ref,
            publication.manifest.content_digest,
            len(publication.manifest.body),
        ),
    )

    occurrences = []
    nomination = None
    is_v2 = type(authored) is CodeSemanticContractProfileManifestSpecV2
    scopes = {row.scope_key: row for row in closure.scopes}
    scope = scopes[publication.owning_scope_key]
    for declared in authored.providers:
        if is_v2 and type(declared) is not CodeSemanticContractProfileProviderSpecV2:
            raise ContractViolation("exact authored V2 product row required")
        modules = tuple(
            row
            for row in scope.projection.modules
            if row.module_id == declared.module_id
        )
        if len(modules) != 1:
            raise ContractViolation("authored grammar provider module unavailable")
        module = parse_module_manifest(modules[0].manifest.body)
        packages = tuple(
            package
            for package in module.packages
            if (
                package.id == declared.package_id
                if type(declared) is CodeSemanticContractProfileProviderSpecV2
                else package.semantic_contract is not None
                and package.semantic_contract.provider_key == declared.provider_key
            )
        )
        if len(packages) != 1:
            if is_v2:
                raise GrammarProfileSourceError(
                    "authored V2 grammar provider package is absent or ambiguous",
                    reason="syntax_provider_declaration_mismatch",
                )
            raise ContractViolation(
                "authored grammar provider package is absent or ambiguous"
            )
        module, package = parse_grammar_provider_module(
            modules[0].manifest.body,
            package_id=packages[0].id,
            provider_key=declared.provider_key,
        )
        if is_v2:
            if (
                type(module) is not AwareModuleSpecV3
                or type(declared) is not CodeSemanticContractProfileProviderSpecV2
            ):
                raise GrammarProfileSourceError(
                    "exact V3 product declaration required",
                    reason="syntax_provider_declaration_mismatch",
                )
            nomination = _read_grammar_v2_product_nomination(module, declared=declared)
        retained = tuple(
            row
            for row in scope.projection.packages
            if row.module_id == declared.module_id and row.package_id == package.id
        )
        if len(retained) != 1:
            raise ContractViolation("original grammar package occurrence unavailable")
        matching = []
        for member in group.members:
            origin = decode_source_origin(bytes.fromhex(member.origin_body_hex))
            occurrence = origin.occurrence
            if (
                occurrence.scope_key == publication.owning_scope_key
                and occurrence.module_id == declared.module_id
                and occurrence.package_id == package.id
                and (
                    not is_v2
                    or (
                        occurrence.repository_binding_ref
                        == closure.repository_binding_ref
                        and occurrence.package_root
                        == (
                            ""
                            if retained[0].package_root == "."
                            else retained[0].package_root
                        )
                        and occurrence.outer_manifest_path
                        == retained[0].manifest_relative_path
                    )
                )
            ):
                matching.append(member.occurrence_ref)
        if len(matching) != 1:
            raise ContractViolation(
                "qualified grammar provider occurrence is absent or ambiguous"
            )
        occurrences.append(matching[0])

    keys = tuple(row.provider_key for row in authored.providers)
    if len(keys) != len(set(keys)):
        raise ContractViolation("authored grammar provider keys are duplicate")
    if is_v2:
        catalog.validate_catalog()
    profiles = {}
    products = []
    for entry in catalog.catalog.entries:
        profile = entry.profile_declaration
        if is_v2:
            if (
                entry.semantic_provider_key == keys[0]
                and (profile.profile_ref, profile.version, profile.digest.value)
                == nomination
                and len(profile.providers) == 1
                and profile.providers[0].provider_key == keys[0]
            ):
                products.append(profile)
            continue
        if len(profile.providers) == len(keys) and {
            row.provider_key for row in profile.providers
        } == set(keys):
            profiles[canonical_json_bytes(profile.to_wire())] = profile
    if is_v2:
        catalog.validate_catalog()
    if (len(products) if is_v2 else len(profiles)) != 1:
        raise ContractViolation(
            "complete original grammar profile is absent or ambiguous"
        )
    profile = products[0] if is_v2 else next(iter(profiles.values()))
    qualified = tuple(occurrences)
    # Reuse the original full correspondence and catalog before/after checks.
    # No reduced profile or second interpretation/validation algorithm is emitted.
    _produce_profile_selection(
        input,
        selection=selection,
        profile=profile,
        catalog=catalog,
        provider_occurrences=qualified,
        stage=input.stage,
    )
    return GrammarSourceOperands(selection, profile, qualified)
