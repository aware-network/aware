"""Catalog-entry eligibility from one original selected graph-product registration.

The detached view is input to Workspace's existing membership catalog. Only the
original Code handle can revalidate that view before paired publication.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from weakref import WeakKeyDictionary

from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)

from .calculation import _execution_entry_correspondence, _plain
from .declaration_host import _selected_policy_source, _selected_policy_view
from .selected_participant_calculation import selected_qualified_occurrence


@dataclass(frozen=True, slots=True)
class SelectedProductCatalogEligibilityView:
    """Detached, non-authorizing package/profile/role correspondence."""

    scope_key: str
    module_id: str
    package_id: str
    source_identity_digest: ContentDigest
    profile_ref: str
    semantic_provider_key: str
    terminal_roles: tuple[str, ...]


class SelectedProductCatalogEligibility:
    """Original Code-issued revalidation handle; not a catalog admission."""

    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("selected product eligibility is Code-issued")

    def __reduce__(self):
        raise TypeError("selected product eligibility cannot be serialized")


_ELIGIBILITIES: WeakKeyDictionary[SelectedProductCatalogEligibility, tuple] = (
    WeakKeyDictionary()
)


def _derive(host, policy, registration):
    with _selected_policy_source(host, policy) as (state, closure, admitted, source):
        if len(admitted.grants) != 1:
            raise ContractViolation("one selected package grant required")
        grant = admitted.grants[0]
        selected = source.expectation
        keys = (selected.scope_key, selected.module_id, selected.package_id)
        _, _, _, declaration = selected_qualified_occurrence(
            closure, _selected_policy_view(host, policy), keys
        )
        stages = state.stage_retention
        products = state.product_retention
        if stages is None or products is None:
            raise ContractViolation("original selected stage and product unavailable")
        stages.validate_declared_profiles(declaration)
        stages.validate()
        products.validate()
        owner = _plain(declaration)
        if (
            ContentDigest.of_bytes(canonical_json_bytes(owner))
            != grant.registration_declaration_digest
            or owner["semantic_package_kind"] != grant.semantic_package_kind
        ):
            raise ContractViolation("selected product owner declaration changed")
        authority_key = owner["semantic_contract"]["provider_key"]
        authority = [
            retained
            for (stage, _runtime, _original), retained in zip(
                stages.stages, stages.entries, strict=True
            )
            if stage == "authority_derivation" and retained[0] == authority_key
        ]
        if len(authority) != 1:
            raise ContractViolation("unique original authority profile required")
        _, authority_profile, _, _, authority_digest = authority[0]
        authority_entry = stages.resolver.read_profile_binding(
            profile=authority_profile, semantic_provider_key=authority_key
        )
        if authority_entry.binding_digest != authority_digest:
            raise ContractViolation("selected authority catalog binding changed")
        _execution_entry_correspondence(
            owner, authority_entry, package_kind=grant.declared_package_kind
        )
        if (
            grant.declared_package_kind not in authority_profile.package_kinds
            or "materialize" not in authority_profile.operation_kinds
        ):
            raise ContractViolation("selected authority profile inapplicable")

        matches = [
            retained
            for (_runtime, original), retained in zip(
                products.products, products.entries, strict=True
            )
            if original is registration
        ]
        if len(matches) != 1:
            raise ContractViolation("original selected product registration unavailable")
        provider_key, profile, provider, binding, digest = matches[0]
        entry = products.resolver.read_profile_binding(
            profile=profile, semantic_provider_key=provider_key
        )
        if (
            entry.binding_digest != digest
            or entry.semantic_owner_key != authority_entry.semantic_owner_key
            or owner["semantic_package_family"] not in entry.package_families
            or owner["semantic_contract"]["role"] not in entry.package_roles
            or grant.declared_package_kind not in profile.package_kinds
            or grant.declared_package_kind not in provider.package_kinds
            or "materialize" not in profile.operation_kinds
            or "materialize" not in provider.operation_kinds
            or not set(entry.manifest_contracts).intersection(
                authority_entry.manifest_contracts
            )
            or provider not in profile.providers
            or binding not in entry.provider_execution_bindings
        ):
            raise ContractViolation("selected product profile inapplicable")
        roles = (profile.terminal_result_role, *profile.terminal_output_roles)
        if (
            len(roles) != len(set(roles))
            or profile.terminal_effect_role in roles
            or any(
                len([item for item in entry.result_product_contracts if item.role == role])
                != 1
                for role in roles
            )
        ):
            raise ContractViolation("selected product terminal roles unavailable")
        result = SelectedProductCatalogEligibilityView(
            selected.scope_key,
            selected.module_id,
            selected.package_id,
            selected.source_identity_digest,
            profile.profile_ref,
            provider_key,
            tuple(sorted(roles, key=str.encode)),
        )
        products.validate()
        return result


def issue_selected_product_catalog_eligibility(
    host, policy, registration
) -> SelectedProductCatalogEligibility:
    """Retain one selected product's exact live catalog eligibility."""
    view = _derive(host, policy, registration)
    handle = object.__new__(SelectedProductCatalogEligibility)
    _ELIGIBILITIES[handle] = (host, policy, registration, view, os.getpid())
    return handle


def read_selected_product_catalog_eligibility(
    handle: SelectedProductCatalogEligibility,
) -> SelectedProductCatalogEligibilityView:
    """Revalidate the original host, source, policy, registration and catalog."""
    if type(handle) is not SelectedProductCatalogEligibility:
        raise TypeError("original selected product eligibility required")
    retained = _ELIGIBILITIES.get(handle)
    if retained is None or retained[4] != os.getpid():
        raise ContractViolation("selected product eligibility unavailable")
    host, policy, registration, view, _pid = retained
    if _derive(host, policy, registration) != view:
        raise ContractViolation("selected product eligibility changed")
    return view


def validate_selected_product_catalog_eligibility(
    handle: SelectedProductCatalogEligibility,
    *,
    expected: SelectedProductCatalogEligibilityView,
) -> None:
    """Publication precheck; a copied view does not validate itself."""
    if type(expected) is not SelectedProductCatalogEligibilityView:
        raise TypeError("exact selected product eligibility view required")
    if read_selected_product_catalog_eligibility(handle) != expected:
        raise ContractViolation("selected product eligibility view substituted")


def check_selected_product_catalog_eligibility_locked(
    handle: SelectedProductCatalogEligibility, *, guard: object
) -> None:
    """Final original-identity check under the already-held parent exclusion.

    Call full validation immediately before acquiring that exclusion. This
    method reads no source bodies and never acquires the parent guard itself.
    """
    from . import direct_host as direct
    from .declaration_host import _check_declaration_source_locked
    from .direct_epoch_tracking import _BINDINGS

    if type(handle) is not SelectedProductCatalogEligibility:
        raise TypeError("original selected product eligibility required")
    retained = _ELIGIBILITIES.get(handle)
    if retained is None or retained[4] != os.getpid():
        raise ContractViolation("selected product eligibility unavailable")
    host, policy, registration, _view, _pid = retained
    state = direct._HOSTS.get(host)
    binding = _BINDINGS.get(host)
    record = direct._POLICIES.get(policy)
    if (
        state is None or state.closed or binding is None
        or record is None or len(record) != 7
        or record[0] is not host or record[6] is not binding
        or state.declaration_binding is not record[5]
    ):
        raise ContractViolation("original selected product epoch unavailable")
    binding.tracker.guard(guard)
    _check_declaration_source_locked(host, guard)
    state.methods["selected_locked"].call(
        record[1], expectation=record[4], binding_digest=record[2],
        guard=guard,
    )
    products = state.product_retention
    if products is None or not any(
        original is registration for _runtime, original in products.products
    ):
        raise ContractViolation("original selected product registration unavailable")
    products.check_identities()
    if (
        products.resolver._admission is not (
            products.current_catalog
            if products.current_catalog is not None
            else state.expected.catalog
        )
        or products.resolver._validate_retained_catalog_coordinate()[2]
        != products.catalog_digest
    ):
        raise ContractViolation("selected product catalog changed")


__all__ = [
    "SelectedProductCatalogEligibility",
    "SelectedProductCatalogEligibilityView",
    "issue_selected_product_catalog_eligibility",
    "read_selected_product_catalog_eligibility",
    "validate_selected_product_catalog_eligibility",
    "check_selected_product_catalog_eligibility_locked",
]
