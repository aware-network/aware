"""Graph product retention is original, catalog-bound and epoch-bound."""

import os
from dataclasses import fields, replace
from uuid import uuid4

import pytest
from aware_code_retained_registry_policy_runtime import direct_host
from aware_code_retained_registry_policy_runtime.calculation import (
    calculate_registry_policy,
)
from aware_code_retained_registry_policy_runtime.product_runtime_retention import (
    _capture_product_runtime_retention,
)
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    RetainedSemanticProductRuntimeExpectation,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticContractCatalogResolver,
    CodeSemanticMaterializationProfileBinding,
    _issue_code_semantic_contract_catalog,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime
from test_calculation import _binding, _catalog
from test_direct_host import Owner
from test_direct_origin_interfaces import context
from test_materialization_catalog import _execution_closure
from test_operation_context import (
    _ARTIFACT,
    _BINDING,
    _CONFIGURATION,
    _SelectedProvider,
)
from test_profile_runtime import JsonBodyCodec


def _case(*, foreign_executable=False):
    key = "graph_product_" + uuid4().hex
    original = _binding(provider_key=key, profile_ref="graph_product")
    provider = _SelectedProvider()
    provider._declaration = original.profile_declaration.providers[0]
    profile = original.profile_declaration
    declaration = provider.declaration
    contracts = {item.contract for item in profile.inputs} | {
        declaration.result_role.contract,
        declaration.transition_contract,
        declaration.effect_contract,
        *(item.contract for item in declaration.output_roles),
    }
    runtime = SemanticContractRuntime(
        profile, {key: provider}, {item: JsonBodyCodec(item) for item in contracts}
    )
    binding = replace(_BINDING, provider_key=key)

    def factory():
        return selected._SelectedProviderFactoryProduct(
            runtime,
            provider,
            binding,
            provider.execute,
            provider.input_closure,
            _ARTIFACT,
            _CONFIGURATION,
        )

    admission = selected._admit_selected_provider_factory(
        factory_ref=key, provider_key=key, selection_factory=factory
    )
    root = selected._issue_selected_provider_selection_root(admission)
    registration = selected.register_selected_provider(runtime, root)
    values = {
        field.name: getattr(original, field.name)
        for field in fields(original)
        if field.name != "binding_digest"
    }
    values["provider_execution_bindings"] = (binding,)
    entry = CodeSemanticMaterializationProfileBinding.create(**values)
    catalog = _catalog(entry)
    executables, planners = _execution_closure(catalog)
    executables = tuple(
        (implementation, configuration, object() if foreign_executable else provider)
        if implementation == binding.implementation
        and configuration == binding.configuration
        else (implementation, configuration, executable)
        for implementation, configuration, executable in executables
    )
    live = [True]
    admitted = _issue_code_semantic_contract_catalog(
        catalog=catalog,
        provider_executable_bindings=executables,
        dependency_planner_bindings=planners,
        host_liveness=lambda: live[0],
    )
    base = context()
    resources = tuple(
        replace(
            item,
            resource=runtime if item.role == "code_runtime" else admitted,
        )
        if item.role in {"code_runtime", "catalog"}
        else item
        for item in base.resources
    )
    expected = replace(
        base,
        process_id=os.getpid(),
        runtime=runtime,
        catalog=admitted,
        resources=resources,
        product_runtime_bindings=(
            RetainedSemanticProductRuntimeExpectation(runtime, registration),
        ),
    )
    retained = _capture_product_runtime_retention(expected)
    return expected, retained, provider, live


def test_original_product_catalog_and_registration_are_retained():
    expected, retained, provider, live = _case()
    retained.validate()
    assert retained.products[0] == (
        expected.runtime,
        expected.product_runtime_bindings[0].registration,
    )
    assert provider.calls == 0
    live[0] = False
    with pytest.raises(ContractViolation):
        retained.validate()


def test_product_identity_substitution_rejects():
    expected, retained, _, _ = _case()
    product = expected.product_runtime_bindings[0]
    original = product.registration
    object.__setattr__(product, "registration", object())
    try:
        with pytest.raises((ContractViolation, TypeError)):
            retained.check_identities()
    finally:
        object.__setattr__(product, "registration", original)
    retained.validate()


def test_catalog_executable_must_be_original_provider():
    with pytest.raises(ContractViolation, match="executable absent"):
        _case(foreign_executable=True)


def test_successor_requires_same_original_product_entry():
    expected, retained, _, _ = _case()
    resolver = CodeSemanticContractCatalogResolver(expected.catalog)
    successor = retained.successor(resolver, expected.catalog)
    assert successor.products == retained.products
    successor.validate()
    original = expected.epoch_identity
    object.__setattr__(expected, "epoch_identity", object())
    try:
        with pytest.raises(ContractViolation):
            successor.validate()
    finally:
        object.__setattr__(expected, "epoch_identity", original)

    other = _catalog(
        _binding(
            provider_key="other_" + uuid4().hex,
            profile_ref="other_product",
        )
    )
    executables, planners = _execution_closure(other)
    other_admission = _issue_code_semantic_contract_catalog(
        catalog=other,
        provider_executable_bindings=executables,
        dependency_planner_bindings=planners,
        host_liveness=lambda: True,
    )
    with pytest.raises(ContractViolation):
        retained.successor(
            CodeSemanticContractCatalogResolver(other_admission), other_admission
        )


def test_fixed_host_retains_product_under_original_command_parent():
    base, _, _, _ = _case()
    owner = Owner(None)
    resources = tuple(
        replace(
            item,
            resource=(
                owner if item.role in {
                    "composition_factory", "lifetime_runtime", "scope_adapter"
                } else calculate_registry_policy
                if item.role == "policy_producer" else item.resource
            ),
        )
        for item in base.resources
    )
    expected = replace(base, resources=resources)
    owner.expected = expected
    bootstrap = direct_host._assemble_direct_command_bootstrap(
        lifetime=owner.lifetime, expected=expected
    )
    host = direct_host.register_direct_workspace_origin(
        bootstrap, owner.lifetime
    )
    try:
        state = direct_host._HOSTS[host]
        assert state.product_retention is not None
        state.product_retention.validate()
        owner.live = False
        with pytest.raises(ContractViolation):
            state.check(read_catalog=False)
    finally:
        direct_host.close_direct_validation_host(host)
