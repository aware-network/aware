"""Project one unambiguous graph root from the original selected Code owner.

The result is detached intent, not Workspace source or participation authority.
The selected-policy enclosure retains the original v3 source and epoch through
the final guarded check; this module never interprets an owner manifest.
"""

from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.materialization_planning import (
    CodeSemanticMaterializationIntent,
    CodeSemanticRequiredResultProduct,
)

from .calculation import _execution_entry_correspondence, _plain
from .declaration_host import _selected_policy_source, _selected_policy_view
from .selected_participant_calculation import selected_qualified_occurrence


def _explicit_root_product(
    state, authority_entry, registration, package_kind, role, selected_registration
):
    """Validate a role against the one original selected product registration."""
    family = registration["semantic_package_family"]
    package_role = registration["semantic_contract"]["role"]
    products = state.product_retention
    if products is None:
        raise ContractViolation("original selected product registration unavailable")
    products.validate()
    matches = [
        (runtime, retained)
        for (runtime, original), retained in zip(
            products.products, products.entries, strict=True
        )
        if original is selected_registration
    ]
    if len(matches) != 1:
        raise ContractViolation("original selected product registration unavailable")
    runtime, retained = matches[0]
    provider_key, profile, _declaration, _binding, digest = retained
    entry = products.resolver.read_profile_binding(
        profile=profile, semantic_provider_key=provider_key
    )
    if entry.binding_digest != digest or runtime.profile != profile:
        raise ContractViolation("original root product binding changed")
    if (
        entry.semantic_owner_key != authority_entry.semantic_owner_key
        or family not in entry.package_families
        or package_role not in entry.package_roles
        or package_kind not in profile.package_kinds
        or "materialize" not in profile.operation_kinds
        or not (
            set(entry.manifest_contracts)
            & set(authority_entry.manifest_contracts)
        )
    ):
        raise ContractViolation("selected product belongs to another package owner")
    if role not in (profile.terminal_result_role, *profile.terminal_output_roles):
        raise ContractViolation("requested role is not selected product output")
    matches = [item for item in entry.result_product_contracts if item.role == role]
    if len(matches) != 1:
        raise ContractViolation("selected root product contract unavailable")
    products.validate()
    return matches[0], provider_key


def _derive_selected_root_intent(
    host, policy, *, requested_role=None, selected_product_registration=None
):
    """Return the existing neutral intent and one required product for a v3 root.

    A package-only command has no role or semantic configuration field, so its
    authority profile must expose one non-effect product. An explicit role is
    input intent paired with the original selected product registration: Code
    checks both against the owner policy and retained live profile.
    """
    with _selected_policy_source(host, policy) as (state, closure, admitted, source):
        if len(admitted.grants) != 1:
            raise ContractViolation("one selected package grant required")
        grant = admitted.grants[0]
        if not grant.owned_roots:
            raise ContractViolation("selected package has no semantic roots")
        selected = source.expectation
        _, _, _, declaration = selected_qualified_occurrence(
            closure, _selected_policy_view(host, policy),
            (selected.scope_key, selected.module_id, selected.package_id),
        )
        stages = state.stage_retention
        if stages is None:
            raise ContractViolation("original selected stage pair unavailable")
        stages.validate_declared_profiles(declaration)
        stages.validate()

        registration = _plain(declaration)
        if (
            ContentDigest.of_bytes(canonical_json_bytes(registration))
            != grant.registration_declaration_digest
            or registration["semantic_package_kind"] != grant.semantic_package_kind
        ):
            raise ContractViolation("selected root registration differs")
        provider_key = registration["semantic_contract"]["provider_key"]
        authority = [
            retained
            for (stage, _runtime, _registration), retained in zip(
                stages.stages, stages.entries, strict=True
            )
            if stage == "authority_derivation" and retained[0] == provider_key
        ]
        if len(authority) != 1:
            raise ContractViolation("unique original authority profile required")
        _, profile, _, _, digest = authority[0]
        entry = stages.resolver.read_profile_binding(
            profile=profile, semantic_provider_key=provider_key
        )
        if entry.binding_digest != digest:
            raise ContractViolation("selected authority binding changed")
        _execution_entry_correspondence(
            registration, entry, package_kind=grant.declared_package_kind
        )
        if (
            grant.declared_package_kind not in profile.package_kinds
            or "materialize" not in profile.operation_kinds
        ):
            raise ContractViolation("selected authority profile inapplicable")
        if requested_role is None:
            if selected_product_registration is not None:
                raise ContractViolation("package-only root cannot select a product")
            roles = (profile.terminal_result_role, *profile.terminal_output_roles)
            if len(roles) != len(set(roles)) or len(roles) != 1:
                raise ContractViolation("package-only root product role ambiguous")
            role = roles[0]
            if role == profile.terminal_effect_role:
                raise ContractViolation("effect cannot be a root product")
            products = [
                item for item in entry.result_product_contracts
                if item.role == role
            ]
            if len(products) != 1:
                raise ContractViolation("selected root product contract unavailable")
            selected_product = products[0]
        else:
            if type(requested_role) is not str or not requested_role:
                raise TypeError("explicit root role must be an exact nonempty string")
            if selected_product_registration is None:
                raise ContractViolation(
                    "explicit role requires original selected product"
                )
            role = requested_role
            selected_product, selected_provider_key = _explicit_root_product(
                state,
                entry,
                registration,
                grant.declared_package_kind,
                role,
                selected_product_registration,
            )
        product = CodeSemanticRequiredResultProduct.create(
            role=role, contract=selected_product.contract
        )
        intent = CodeSemanticMaterializationIntent.create(
            operation_kind="materialize",
            requested_semantic_root_refs=grant.owned_roots,
            requested_terminal_output_roles=(role,),
            semantic_configuration_coordinate=None,
        )
        return intent, product, (
            selected_provider_key if requested_role is not None else None
        )


def derive_selected_root_intent(host, policy):
    """Preserve the package-only singleton rule and existing return shape."""
    intent, product, _provider = _derive_selected_root_intent(host, policy)
    return intent, product


def derive_selected_product_root_intent(
    host, policy, *, requested_role, selected_product_registration
):
    """Return explicit role, contract and selected provider-key constraint."""
    if requested_role is None or selected_product_registration is None:
        raise ContractViolation("explicit role and original product required")
    return _derive_selected_root_intent(
        host,
        policy,
        requested_role=requested_role,
        selected_product_registration=selected_product_registration,
    )


__all__ = ["derive_selected_root_intent", "derive_selected_product_root_intent"]
