"""Original selected-product eligibility for one existing Workspace catalog entry."""

from contextlib import contextmanager
from dataclasses import fields, replace
from types import SimpleNamespace

import pytest

from aware_code_retained_registry_policy_runtime import selected_catalog_eligibility as eligibility
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.registry_policy import (
    RegistryPolicy,
    RegistryPolicyGrant,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticMaterializationProfileBinding,
)

from test_calculation import _binding, _digest


def _selected(monkeypatch):
    authority = _binding(provider_key="authority", profile_ref="owner.authority")
    product = _binding(provider_key="graph", profile_ref="owner.graph")
    registration = object()
    declaration = {
        "semantic_contract": {"provider_key": "authority", "role": "sdk"},
        "semantic_package_family": "public",
        "semantic_package_kind": "sdk",
        "declared_package_kinds": ["sdk"],
    }
    policy = RegistryPolicy(
        _digest("closure"),
        (
            RegistryPolicyGrant(
                _digest("source"),
                ContentDigest.of_bytes(canonical_json_bytes(declaration)),
                "sdk", "sdk", "fixture", ("root",),
            ),
        ),
    )
    selected = SimpleNamespace(
        scope_key="scope", module_id="module", package_id="pkg",
        source_identity_digest=_digest("source"),
    )
    state = SimpleNamespace()
    calls = []

    class Stages:
        stages = (("authority_derivation", object(), object()),)
        entries = ((
            "authority", authority.profile_declaration,
            authority.profile_declaration.providers[0],
            authority.provider_execution_bindings[0], authority.binding_digest,
        ),)
        resolver = SimpleNamespace(read_profile_binding=lambda **_kwargs: authority)

        def validate_declared_profiles(self, _declaration):
            calls.append("declared")

        def validate(self):
            calls.append("stages")

    class Products:
        products = ((SimpleNamespace(profile=product.profile_declaration), registration),)
        entries = ((
            "graph", product.profile_declaration,
            product.profile_declaration.providers[0],
            product.provider_execution_bindings[0], product.binding_digest,
        ),)
        resolver = SimpleNamespace(read_profile_binding=lambda **_kwargs: product)

        def validate(self):
            calls.append("products")
            if not state.live:
                raise ContractViolation("original product revoked")

    state.stage_retention = Stages()
    state.product_retention = Products()
    state.live = True

    @contextmanager
    def source(_host, admitted):
        if not state.live or admitted is not policy:
            raise ContractViolation("original selected policy unavailable")
        calls.append("before")
        yield state, object(), policy, SimpleNamespace(expectation=selected)
        if not state.live:
            raise ContractViolation("selected source revoked")
        calls.append("after")

    monkeypatch.setattr(eligibility, "_selected_policy_source", source)
    monkeypatch.setattr(eligibility, "_selected_policy_view", lambda *_: object())
    monkeypatch.setattr(
        eligibility, "selected_qualified_occurrence",
        lambda _closure, _view, key: (key, object(), object(), declaration),
    )
    return policy, registration, product, state, calls


def test_selected_eligibility_exposes_exact_product_profile_and_roles(monkeypatch):
    policy, registration, product, _state, calls = _selected(monkeypatch)
    handle = eligibility.issue_selected_product_catalog_eligibility(
        object(), policy, registration
    )
    view = eligibility.read_selected_product_catalog_eligibility(handle)
    assert view.profile_ref == product.profile_declaration.profile_ref
    assert view.semantic_provider_key == "graph"
    assert view.terminal_roles == ("python_sdk", "result")
    assert (view.scope_key, view.module_id, view.package_id) == (
        "scope", "module", "pkg"
    )
    assert view.source_identity_digest == _digest("source")
    eligibility.validate_selected_product_catalog_eligibility(handle, expected=view)
    assert calls.count("before") == calls.count("after") == 3


def test_eligibility_rejects_substitution_revocation_and_reconstruction(monkeypatch):
    policy, registration, _product, state, _calls = _selected(monkeypatch)
    host = object()
    handle = eligibility.issue_selected_product_catalog_eligibility(
        host, policy, registration
    )
    view = eligibility.read_selected_product_catalog_eligibility(handle)
    with pytest.raises(ContractViolation, match="view substituted"):
        eligibility.validate_selected_product_catalog_eligibility(
            handle, expected=replace(view, profile_ref="foreign")
        )
    with pytest.raises(ContractViolation, match="registration unavailable"):
        eligibility.issue_selected_product_catalog_eligibility(
            host, policy, object()
        )
    with pytest.raises(TypeError, match="Code-issued"):
        eligibility.SelectedProductCatalogEligibility()
    with pytest.raises(ContractViolation, match="unavailable"):
        eligibility.read_selected_product_catalog_eligibility(
            object.__new__(eligibility.SelectedProductCatalogEligibility)
        )
    state.live = False
    with pytest.raises(ContractViolation, match="unavailable"):
        eligibility.validate_selected_product_catalog_eligibility(
            handle, expected=view
        )


def test_eligibility_rejects_inapplicable_live_product_profile(monkeypatch):
    policy, registration, product, state, _calls = _selected(monkeypatch)
    foreign = CodeSemanticMaterializationProfileBinding.create(**{
        **{
            field.name: getattr(product, field.name)
            for field in fields(product)
            if field.name != "binding_digest"
        },
        "semantic_owner_key": "foreign",
    })
    state.product_retention.resolver.read_profile_binding = lambda **_kwargs: foreign
    with pytest.raises(ContractViolation, match="inapplicable"):
        eligibility.issue_selected_product_catalog_eligibility(
            object(), policy, registration
        )


def test_guarded_publication_check_uses_original_identity_without_source_read(
    monkeypatch,
):
    from aware_code_retained_registry_policy_runtime import declaration_host
    from aware_code_retained_registry_policy_runtime import direct_epoch_tracking
    from aware_code_retained_registry_policy_runtime import direct_host

    policy, registration, _product, _state, _calls = _selected(monkeypatch)
    host = object()
    handle = eligibility.issue_selected_product_catalog_eligibility(
        host, policy, registration
    )
    original = object()
    catalog = object()
    guard = object()
    checks = []

    def check_guard(value):
        if value is not guard:
            raise ContractViolation("foreign guard")
        checks.append("guard")

    products = SimpleNamespace(
        products=((object(), registration),),
        current_catalog=None,
        catalog_digest="catalog-digest",
        resolver=SimpleNamespace(
            _admission=catalog,
            _validate_retained_catalog_coordinate=lambda: (
                None, None, "catalog-digest"
            ),
        ),
        check_identities=lambda: checks.append("product identities"),
    )
    state = SimpleNamespace(
        closed=False,
        declaration_binding=original,
        product_retention=products,
        expected=SimpleNamespace(catalog=catalog),
        methods={"selected_locked": SimpleNamespace(
            call=lambda *args, **kwargs: checks.append("selected locked")
        )},
    )
    epoch = SimpleNamespace(tracker=SimpleNamespace(guard=check_guard))
    monkeypatch.setattr(direct_host, "_HOSTS", {host: state})
    monkeypatch.setattr(
        direct_host, "_POLICIES",
        {policy: (host, object(), "source-digest", policy, object(), original, epoch)},
    )
    monkeypatch.setattr(direct_epoch_tracking, "_BINDINGS", {host: epoch})
    monkeypatch.setattr(
        declaration_host, "_check_declaration_source_locked",
        lambda _host, _guard: checks.append("declaration locked"),
    )
    eligibility.check_selected_product_catalog_eligibility_locked(
        handle, guard=guard
    )
    assert checks == [
        "guard", "declaration locked", "selected locked", "product identities"
    ]
    with pytest.raises(ContractViolation, match="foreign guard"):
        eligibility.check_selected_product_catalog_eligibility_locked(
            handle, guard=object()
        )
