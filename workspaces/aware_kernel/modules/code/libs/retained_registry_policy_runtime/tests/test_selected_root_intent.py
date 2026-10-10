"""Neutral root-role rules and the original v3 selected-source boundary."""

from contextlib import contextmanager
from dataclasses import fields, replace
from types import SimpleNamespace

import pytest

from aware_code_retained_registry_policy_runtime import direct_host
from aware_code_retained_registry_policy_runtime import selected_root_intent as roots
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticMaterializationProfileBinding,
)
from aware_code_semantic_contract_runtime.registry_policy import (
    RegistryPolicy,
    RegistryPolicyGrant,
)

from test_calculation import _binding, _digest
from test_declaration_host import registered_epoch


def _entry(*, singleton):
    original = _binding(provider_key="fixture", profile_ref="fixture.authority")
    profile = replace(
        original.profile_declaration,
        terminal_output_roles=() if singleton else ("python_sdk",),
    )
    values = {
        field.name: getattr(original, field.name)
        for field in fields(original)
        if field.name != "binding_digest"
    }
    values["profile_declaration"] = profile
    values["result_product_contracts"] = tuple(
        product
        for product in original.result_product_contracts
        if not singleton or product.role != "python_sdk"
    )
    return CodeSemanticMaterializationProfileBinding.create(**values)


def _neutral_selected(
    monkeypatch,
    *,
    singleton=True,
    owned_roots=("alpha", "beta"),
    family="public",
    semantic_kind="sdk",
    declared_kind="sdk",
    product_entries=(),
    product_registrations=(),
):
    entry = _entry(singleton=singleton)
    declaration = {
        "semantic_contract": {"provider_key": "fixture", "role": "sdk"},
        "semantic_package_family": family,
        "semantic_package_kind": semantic_kind,
        "declared_package_kinds": [declared_kind],
    }
    grant = RegistryPolicyGrant(
        _digest("source"),
        ContentDigest.of_bytes(canonical_json_bytes(declaration)),
        declared_kind,
        semantic_kind,
        "fixture",
        owned_roots,
    )
    policy = RegistryPolicy(_digest("scope"), (grant,))
    selected = SimpleNamespace(
        scope_key="scope", module_id="module", package_id="pkg"
    )
    source = SimpleNamespace(expectation=selected)
    calls = []

    class RetainedStages:
        stages = (("authority_derivation", object(), object()),)
        entries = ((
            "fixture", entry.profile_declaration, object(), object(),
            entry.binding_digest,
        ),)
        resolver = SimpleNamespace(read_profile_binding=lambda **_kwargs: entry)

        def validate_declared_profiles(self, declaration):
            calls.append(("declaration", declaration))

        def validate(self):
            calls.append(("registration", None))

    if product_registrations and len(product_registrations) != len(product_entries):
        raise AssertionError("test product registrations must align")
    registrations = product_registrations or tuple(object() for _ in product_entries)

    class RetainedProducts:
        products = tuple(
            (SimpleNamespace(profile=item.profile_declaration), original)
            for item, original in zip(product_entries, registrations, strict=True)
        )
        entries = tuple(
            (
                item.semantic_provider_key, item.profile_declaration,
                object(), object(), item.binding_digest,
            )
            for item in product_entries
        )
        resolver = SimpleNamespace(
            read_profile_binding=lambda **kwargs: next(
                item for item in product_entries
                if item.semantic_provider_key == kwargs["semantic_provider_key"]
            )
        )

        def validate(self):
            calls.append(("product", None))

    state = SimpleNamespace(
        stage_retention=RetainedStages(),
        product_retention=RetainedProducts() if product_entries else None,
    )

    @contextmanager
    def original(_host, _policy):
        calls.append(("before", None))
        yield state, object(), policy, source
        calls.append(("after", None))

    monkeypatch.setattr(roots, "_selected_policy_source", original)
    monkeypatch.setattr(roots, "_selected_policy_view", lambda *_: object())
    monkeypatch.setattr(
        roots, "selected_qualified_occurrence",
        lambda _closure, _view, _key: (_key, object(), object(), declaration),
    )
    return policy, entry, calls


def test_singleton_root_uses_complete_grant_and_exact_catalog_contract(monkeypatch):
    policy, entry, calls = _neutral_selected(monkeypatch)
    intent, requirement = roots.derive_selected_root_intent(object(), policy)
    assert intent.operation_kind == "materialize"
    assert intent.requested_semantic_root_refs == ("alpha", "beta")
    assert intent.requested_terminal_output_roles == ("result",)
    assert intent.semantic_configuration_coordinate is None
    assert requirement == next(
        product for product in entry.result_product_contracts
        if product.role == "result"
    )
    assert [kind for kind, _ in calls] == [
        "before",
        "declaration",
        "registration",
        "after",
    ]


def test_distinct_semantic_kind_uses_declared_executable_kind(monkeypatch):
    policy, _, _ = _neutral_selected(
        monkeypatch, semantic_kind="fixture_semantic_package"
    )
    intent, requirement = roots.derive_selected_root_intent(object(), policy)
    assert intent.requested_semantic_root_refs == ("alpha", "beta")
    assert requirement.role == "result"


def test_wrong_declared_executable_kind_refuses(monkeypatch):
    policy, _, _ = _neutral_selected(monkeypatch, declared_kind="foreign")
    with pytest.raises(ContractViolation, match="catalog package correspondence"):
        roots.derive_selected_root_intent(object(), policy)


def test_package_only_root_refuses_ambiguous_owner_products(monkeypatch):
    policy, _, _ = _neutral_selected(monkeypatch, singleton=False)
    with pytest.raises(ContractViolation, match="ambiguous"):
        roots.derive_selected_root_intent(object(), policy)


def test_explicit_role_uses_original_matching_product_profile(monkeypatch):
    graph = _binding(provider_key="fixture_graph", profile_ref="fixture.product")
    original = object()
    policy, _, calls = _neutral_selected(
        monkeypatch, singleton=False, product_entries=(graph,),
        product_registrations=(original,)
    )
    intent, requirement, provider_key = roots.derive_selected_product_root_intent(
        object(), policy, requested_role="python_sdk",
        selected_product_registration=original,
    )
    assert provider_key == "fixture_graph"
    assert intent.requested_terminal_output_roles == ("python_sdk",)
    assert requirement == next(
        item for item in graph.result_product_contracts
        if item.role == "python_sdk"
    )
    assert [kind for kind, _ in calls].count("product") == 2


def test_explicit_role_rejects_effect_unknown_and_foreign_owner(monkeypatch):
    graph = _binding(provider_key="fixture_graph", profile_ref="fixture.product")
    foreign = CodeSemanticMaterializationProfileBinding.create(**{
        **{
            field.name: getattr(graph, field.name)
            for field in fields(graph)
            if field.name != "binding_digest"
        },
        "semantic_owner_key": "foreign",
    })
    original = object()
    policy, _, _ = _neutral_selected(
        monkeypatch, product_entries=(foreign,), product_registrations=(original,)
    )
    with pytest.raises(ContractViolation, match="another package owner"):
        roots.derive_selected_product_root_intent(
            object(), policy, requested_role="python_sdk",
            selected_product_registration=original,
        )
    with pytest.raises(ContractViolation, match="original product required"):
        roots.derive_selected_product_root_intent(
            object(), policy, requested_role="python_sdk",
            selected_product_registration=None,
        )


def test_explicit_role_uses_exact_selected_profile_amid_duplicate_roles(monkeypatch):
    first = _binding(provider_key="fixture_graph_a", profile_ref="fixture.product.a")
    second = _binding(provider_key="fixture_graph_b", profile_ref="fixture.product.b")
    first_registration, second_registration = object(), object()
    policy, _, _ = _neutral_selected(
        monkeypatch, product_entries=(first, second),
        product_registrations=(first_registration, second_registration),
    )
    _, requirement, provider_key = roots.derive_selected_product_root_intent(
        object(), policy, requested_role="python_sdk",
        selected_product_registration=first_registration,
    )
    assert provider_key == "fixture_graph_a"
    assert requirement == next(
        item for item in first.result_product_contracts
        if item.role == "python_sdk"
    )
    with pytest.raises(ContractViolation, match="registration unavailable"):
        roots.derive_selected_product_root_intent(
            object(), policy, requested_role="python_sdk",
            selected_product_registration=object(),
        )
    with pytest.raises(ContractViolation, match="not selected product output"):
        roots.derive_selected_product_root_intent(
            object(), policy, requested_role="effect",
            selected_product_registration=second_registration,
        )


def test_selected_root_refuses_missing_roots(monkeypatch):
    policy, _, _ = _neutral_selected(monkeypatch, owned_roots=())
    with pytest.raises(ContractViolation, match="no semantic roots"):
        roots.derive_selected_root_intent(object(), policy)


def test_selected_root_refuses_catalog_package_mismatch(monkeypatch):
    policy, _, _ = _neutral_selected(monkeypatch, family="foreign")
    with pytest.raises(ContractViolation, match="registration catalog package"):
        roots.derive_selected_root_intent(object(), policy)


def test_original_host_refuses_foreign_policy_and_revoked_source():
    owner, host = registered_epoch()
    _other_owner, other = registered_epoch()
    try:
        policy = direct_host.produce_registry_policy(host, owner.selected)
        with pytest.raises(ContractViolation, match="original v3 policy"):
            roots.derive_selected_root_intent(other, policy)
        owner.selected_live = False
        with pytest.raises(ContractViolation, match="selected source unavailable"):
            roots.derive_selected_root_intent(host, policy)
    finally:
        direct_host.close_direct_validation_host(host)
        direct_host.close_direct_validation_host(other)
