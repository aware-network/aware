"""Pre-host product correspondence; portable input, never execution authority.

This breaks no publication lifetime: Workspace authenticates the original
declarations/source and admits participation alongside the original Code leg.
The subsequent live Code host still issues policy and execution admissions.
"""

from __future__ import annotations

from dataclasses import dataclass

from aware_code_semantic_contract_runtime import ContractViolation, SemanticContractRef
from aware_code_semantic_contract_runtime.portable_semantic_package_authority import (
    CodePortableSemanticContract,
)
from aware_code_semantic_contract_runtime.product_contribution import (
    SelectedProviderProductContribution,
    read_selected_provider_product_catalog_contribution,
    read_selected_provider_product_contribution,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeRetainedDependencyScopeClosureV3,
)
from aware_code_semantic_contract_runtime.retained_input_projections import (
    CodeSemanticRegistryPackageInput,
)
from aware_code_semantic_contract_runtime.selected_participant_scope import (
    CodeSelectedParticipantViewV1,
)

from .calculation import _execution_entry_correspondence, _plain
from .declaration_eligibility import (
    DeclaredPackageEligibility,
    calculate_declaration_eligibility,
)
from .selected_participant_calculation import selected_qualified_occurrence


@dataclass(frozen=True, slots=True)
class DeclaredProductProjection:
    package: DeclaredPackageEligibility
    registry: CodeSemanticRegistryPackageInput
    manifest_contracts: tuple[SemanticContractRef, ...]
    terminal_roles: tuple[str, ...]


def project_declared_product(
    closure: CodeRetainedDependencyScopeClosureV3,
    view: CodeSelectedParticipantViewV1,
    contribution: SelectedProviderProductContribution,
) -> DeclaredProductProjection:
    """Compare complete declared participation with one original owner product.

    This neither calls the factory/catalog producer nor admits a package. The
    owner catalog must already have been produced by the original composition.
    Manifest contracts describe matcher eligibility, not raw manifest bytes.
    """
    if type(view) is not CodeSelectedParticipantViewV1:
        raise TypeError("exact selected participant view required")
    eligibility = calculate_declaration_eligibility(closure, selected_view=view)
    key = (view.root.scope_key, view.root.module_id, view.root.package_id)
    rows = [row for row in eligibility.packages if row.occurrence_key == key]
    if len(rows) != 1:
        raise ContractViolation("one selected declaration required")
    _, package, _, declaration = selected_qualified_occurrence(closure, view, key)
    meaning = _plain(declaration)
    original = read_selected_provider_product_contribution(contribution)
    catalog = read_selected_provider_product_catalog_contribution(contribution)
    if len(catalog.entries) != 1:
        raise ContractViolation("one original product catalog entry required")
    entry = catalog.entries[0]
    profile = original.profile
    expected = {
        "stage": "graph_product",
        "profile_ref": profile.profile_ref,
        "profile_version": profile.version,
        "profile_digest": profile.digest.to_wire(),
    }
    if (
        meaning["profiles"] != [expected]
        or meaning["semantic_contract"]["provider_key"] != original.binding.provider_key
        or package.manifest.relative_path.rsplit("/", 1)[-1]
        != meaning["manifest_filename"]
        or "materialize" not in profile.operation_kinds
    ):
        raise ContractViolation("exact declared original graph product required")
    _execution_entry_correspondence(meaning, entry, package_kind=package.package_kind)
    roles = (profile.terminal_result_role, *profile.terminal_output_roles)
    if (
        len(roles) != len(set(roles))
        or profile.terminal_effect_role in roles
        or any(sum(result.role == role for result in entry.result_product_contracts) != 1
               for role in roles)
    ):
        raise ContractViolation("complete non-effect product roles required")
    registry = CodeSemanticRegistryPackageInput(
        meaning["manifest_contract_kind"], meaning["manifest_filename"],
        rows[0].provider_key, meaning["semantic_package_family"],
        rows[0].semantic_package_kind,
        CodePortableSemanticContract(**meaning["semantic_contract"]),
        tuple(meaning["supported_languages"]), meaning["code_package_surface"].get("value"),
        rows[0].namespace, rows[0].owned_roots, profile.profile_ref, profile.version,
        profile.digest, original.binding,
    )
    result = DeclaredProductProjection(
        rows[0], registry, entry.manifest_contracts, tuple(sorted(roles, key=str.encode))
    )
    read_selected_provider_product_contribution(contribution)
    read_selected_provider_product_catalog_contribution(contribution)
    return result


def project_declared_inspect_product(
    closure: CodeRetainedDependencyScopeClosureV3,
    view: CodeSelectedParticipantViewV1,
    contribution: SelectedProviderProductContribution,
) -> DeclaredProductProjection:
    """Compare one inspect-only original product with its declared participation.

    This neither calls the factory/catalog producer nor admits a package. The
    owner catalog must already have been produced by the original composition.
    Manifest contracts describe matcher eligibility, not raw manifest bytes.
    """
    if type(view) is not CodeSelectedParticipantViewV1:
        raise TypeError("exact selected participant view required")
    eligibility = calculate_declaration_eligibility(closure, selected_view=view)
    key = (view.root.scope_key, view.root.module_id, view.root.package_id)
    rows = [row for row in eligibility.packages if row.occurrence_key == key]
    if len(rows) != 1:
        raise ContractViolation("one selected declaration required")
    _, package, _, declaration = selected_qualified_occurrence(closure, view, key)
    meaning = _plain(declaration)
    original = read_selected_provider_product_contribution(contribution)
    catalog = read_selected_provider_product_catalog_contribution(contribution)
    if len(catalog.entries) != 1:
        raise ContractViolation("one original product catalog entry required")
    entry = catalog.entries[0]
    profile = original.profile
    expected = {
        "stage": "graph_product",
        "profile_ref": profile.profile_ref,
        "profile_version": profile.version,
        "profile_digest": profile.digest.to_wire(),
    }
    if (
        meaning["profiles"] != [expected]
        or meaning["semantic_contract"]["provider_key"] != original.binding.provider_key
        or package.manifest.relative_path.rsplit("/", 1)[-1]
        != meaning["manifest_filename"]
        or profile.operation_kinds != ("inspect",)
    ):
        raise ContractViolation("exact declared original inspect-only graph product required")
    _execution_entry_correspondence(meaning, entry, package_kind=package.package_kind)
    roles = (profile.terminal_result_role, *profile.terminal_output_roles)
    if (
        len(roles) != len(set(roles))
        or profile.terminal_effect_role in roles
        or any(sum(result.role == role for result in entry.result_product_contracts) != 1
               for role in roles)
    ):
        raise ContractViolation("complete non-effect product roles required")
    registry = CodeSemanticRegistryPackageInput(
        meaning["manifest_contract_kind"], meaning["manifest_filename"],
        rows[0].provider_key, meaning["semantic_package_family"],
        rows[0].semantic_package_kind,
        CodePortableSemanticContract(**meaning["semantic_contract"]),
        tuple(meaning["supported_languages"]), meaning["code_package_surface"].get("value"),
        rows[0].namespace, rows[0].owned_roots, profile.profile_ref, profile.version,
        profile.digest, original.binding,
    )
    result = DeclaredProductProjection(
        rows[0], registry, entry.manifest_contracts, tuple(sorted(roles, key=str.encode))
    )
    read_selected_provider_product_contribution(contribution)
    read_selected_provider_product_catalog_contribution(contribution)
    return result


def check_declared_product_origin(
    contribution: SelectedProviderProductContribution,
    expected: DeclaredProductProjection,
) -> None:
    """No owner dispatch or source I/O under Workspace's held parent guard.

    Full projection validation must immediately precede the guard. Code owns
    these original registration/catalog records; portable expected fields alone
    cannot create a contribution or restore a closed original registration.
    """
    from aware_code_semantic_contract_runtime import product_contribution as owner
    from aware_code_semantic_contract_runtime import selected_provider as selected

    if type(expected) is not DeclaredProductProjection:
        raise TypeError("exact declared product projection required")
    with selected._LOCK:
        state = owner._state(contribution)
        catalog = owner._CATALOG_PRODUCTS.get(contribution)
        if type(catalog) is not owner._CatalogProductState:
            raise ContractViolation("original product catalog retired")
        entry = catalog.entries[0]
        if (
            state.product.runtime.profile.digest != expected.registry.profile_digest
            or state.product.binding != expected.registry.binding
            or entry.profile_declaration.profile_ref != expected.registry.profile_ref
            or entry.semantic_provider_key != expected.registry.semantic_provider_key
        ):
            raise ContractViolation("declared original product changed")
