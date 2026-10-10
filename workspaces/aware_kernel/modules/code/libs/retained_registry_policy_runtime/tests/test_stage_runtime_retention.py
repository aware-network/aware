"""Real Code registrations/catalog; fixture assembly is not parent authority."""

import os
from dataclasses import fields, replace
from itertools import cycle

import pytest
from aware_code_retained_registry_policy_runtime.stage_runtime_retention import (
    _capture_stage_runtime_retention,
)
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    DirectCommandResourceBinding,
    RetainedSemanticStageRuntimeExpectation,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    CodeSemanticMaterializationProfileBinding,
    _issue_code_semantic_contract_catalog,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime
from test_calculation import _binding, _catalog
from test_direct_origin_interfaces import context
from test_materialization_catalog import _execution_closure
from test_operation_context import (
    _ARTIFACT,
    _BINDING,
    _CONFIGURATION,
    _SelectedProvider,
)
from test_profile_runtime import JsonBodyCodec

# One original zero-argument fixture factory. Its fixed two-product schedule
# is not a production contribution/assembly proof.
_STAGES = cycle(("planning", "authority"))
_BINDING = replace(_BINDING, provider_key="stage_retention_test")


def stage_factory():
    profile = _binding(
        provider_key="stage_retention_test", profile_ref=next(_STAGES)
    ).profile_declaration
    provider = _SelectedProvider()
    provider._declaration = profile.providers[0]
    declaration = provider.declaration
    contracts = {i.contract for i in profile.inputs} | {
        declaration.result_role.contract,
        declaration.transition_contract,
        declaration.effect_contract,
        *(r.contract for r in declaration.output_roles),
    }
    runtime = SemanticContractRuntime(
        profile,
        {"stage_retention_test": provider},
        {c: JsonBodyCodec(c) for c in contracts},
    )
    return selected._SelectedProviderFactoryProduct(
        runtime,
        provider,
        _BINDING,
        provider.execute,
        provider.input_closure,
        _ARTIFACT,
        _CONFIGURATION,
    )


FACTORY = selected._admit_selected_provider_factory(
    factory_ref="aware.test.stage-retention",
    provider_key="stage_retention_test",
    selection_factory=stage_factory,
)


@pytest.fixture(scope="module")
def case():
    stages = []
    entries = []
    providers = []
    for stage, factory in (
        ("source_planning", FACTORY),
        ("authority_derivation", FACTORY),
    ):
        root = selected._issue_selected_provider_selection_root(factory)
        state = selected._selection_root_state(root)
        runtime = state.runtime
        registration = selected.register_selected_provider(runtime, root)
        stages.append(
            RetainedSemanticStageRuntimeExpectation(stage, runtime, registration)
        )
        providers.append(state.provider)
        base = _binding(
            provider_key="stage_retention_test", profile_ref=runtime.profile.profile_ref
        )
        values = {
            f.name: getattr(base, f.name)
            for f in fields(base)
            if f.name != "binding_digest"
        }
        values.update(
            profile_declaration=runtime.profile, provider_execution_bindings=(_BINDING,)
        )
        entries.append(CodeSemanticMaterializationProfileBinding.create(**values))
    catalog = _catalog(*entries)
    executables, planners = _execution_closure(catalog)
    live = [True]
    admitted = _issue_code_semantic_contract_catalog(
        catalog=catalog,
        provider_executable_bindings=executables,
        dependency_planner_bindings=planners,
        host_liveness=lambda: live[0],
    )
    original = context()
    resources = tuple(
        replace(
            b, resource=(stages[0].runtime if b.role == "code_runtime" else admitted)
        )
        if b.role in ("catalog", "code_runtime")
        else b
        for b in original.resources
    )
    expected = replace(
        original,
        process_id=os.getpid(),
        runtime=stages[0].runtime,
        catalog=admitted,
        stage_runtime_bindings=tuple(stages),
        resources=(
            DirectCommandResourceBinding(
                "authority_code_runtime", stages[1].runtime, "borrowed"
            ),
            *resources,
        ),
    )
    retained = _capture_stage_runtime_retention(expected)
    return expected, retained, providers, live


def test_original_live_stages_revalidate_without_execution(case):
    expected, retained, providers, _ = case
    retained.validate()
    retained.validate()
    assert retained.stages[0][1] is expected.runtime
    assert retained.stages[1][2] is expected.stage_runtime_bindings[1].registration
    assert all(p.calls == 0 for p in providers)


@pytest.mark.parametrize("field", ["epoch_identity", "invocation_identity", "catalog"])
def test_parent_or_catalog_substitution_rejects(case, field):
    expected, retained, _, _ = case
    original = getattr(expected, field)
    object.__setattr__(expected, field, object())
    try:
        with pytest.raises(ContractViolation):
            retained.validate()
    finally:
        object.__setattr__(expected, field, original)


def test_stage_registration_replacement_rejects(case):
    expected, retained, _, _ = case
    value = expected.stage_runtime_bindings[1]
    original = value.registration
    object.__setattr__(value, "registration", object())
    try:
        with pytest.raises(ContractViolation, match="registration changed"):
            retained.validate()
    finally:
        object.__setattr__(value, "registration", original)


def test_cleanup_disposition_change_rejects(case):
    expected, retained, _, _ = case
    resource = expected.resources[0]
    object.__setattr__(resource, "disposition", "owned")
    try:
        with pytest.raises(ContractViolation, match="resource changed"):
            retained.validate()
    finally:
        object.__setattr__(resource, "disposition", "borrowed")


def test_declaration_stage_correspondence_is_separate_from_nominal_registration(case):
    _, retained, _, _ = case
    declaration = {
        "semantic_contract": {"provider_key": "stage_retention_test"},
        "profiles": [
            {
                "stage": stage,
                "profile_ref": entry[1].profile_ref,
                "profile_version": entry[1].version,
                "profile_digest": entry[1].digest.to_wire(),
            }
            for (stage, _, _), entry in zip(
                retained.stages, retained.entries, strict=True
            )
        ],
    }
    assert type(retained.validate_declared_profiles(declaration)) is bytes
    declaration["profiles"][1]["profile_ref"] = "planning"
    with pytest.raises(ContractViolation, match="declared stage profile"):
        retained.validate_declared_profiles(declaration)


def test_fork_rejects_before_inherited_registration_locks(case, monkeypatch):
    _, retained, _, _ = case
    pid = os.getpid()
    monkeypatch.setattr(os, "getpid", lambda: pid + 1)
    with pytest.raises(ContractViolation, match="another process"):
        retained.validate()


def test_catalog_revocation_invalidates_both_stages(case):
    _, retained, _, live = case
    live[0] = False
    try:
        with pytest.raises(ContractViolation):
            retained.validate()
    finally:
        live[0] = True


def test_foreign_runtime_registration_pair_rejects_capture(case):
    expected, _, _, _ = case
    planning, authority = expected.stage_runtime_bindings
    changed = replace(
        expected,
        stage_runtime_bindings=(
            replace(planning, registration=authority.registration),
            replace(authority, registration=planning.registration),
        ),
    )
    with pytest.raises(ContractViolation, match="original stage registration runtime changed"):
        _capture_stage_runtime_retention(changed)


def test_original_provider_method_substitution_rejects(case, monkeypatch):
    from types import MethodType

    _, retained, providers, _ = case
    provider = providers[1]
    calls = []

    def substitute(self, value):
        calls.append(value)

    with monkeypatch.context() as patch:
        patch.setattr(provider, "input_closure", MethodType(substitute, provider))
        with pytest.raises(ContractViolation):
            retained.validate()
    del provider.__dict__["input_closure"]
    assert calls == []


def test_two_distinct_selected_owners_share_one_retained_host_context():
    """A single-pair SDK fixture cannot establish complete provider fanout."""

    stages = []
    entries = []
    registrations = []
    for provider_key in ("alpha_selected", "beta_selected"):
        binding = replace(_BINDING, provider_key=provider_key)
        profiles = iter(("planning", "authority"))

        def factory():
            profile = _binding(
                provider_key=provider_key, profile_ref=next(profiles)
            ).profile_declaration
            provider = _SelectedProvider()
            provider._declaration = profile.providers[0]
            contracts = {item.contract for item in profile.inputs} | {
                provider.declaration.result_role.contract,
                provider.declaration.transition_contract,
                provider.declaration.effect_contract,
                *(role.contract for role in provider.declaration.output_roles),
            }
            runtime = SemanticContractRuntime(
                profile,
                {provider_key: provider},
                {contract: JsonBodyCodec(contract) for contract in contracts},
            )
            return selected._SelectedProviderFactoryProduct(
                runtime,
                provider,
                binding,
                provider.execute,
                provider.input_closure,
                _ARTIFACT,
                _CONFIGURATION,
            )

        admitted_factory = selected._admit_selected_provider_factory(
            factory_ref=f"aware.test.{provider_key}",
            provider_key=provider_key,
            selection_factory=factory,
        )
        for stage in ("source_planning", "authority_derivation"):
            root = selected._issue_selected_provider_selection_root(admitted_factory)
            original = selected._selection_root_state(root)
            registration = selected.register_selected_provider(original.runtime, root)
            registrations.append(registration)
            stages.append(
                RetainedSemanticStageRuntimeExpectation(
                    stage, original.runtime, registration
                )
            )
            base = _binding(
                provider_key=provider_key,
                profile_ref=original.runtime.profile.profile_ref,
            )
            values = {
                field.name: getattr(base, field.name)
                for field in fields(base)
                if field.name != "binding_digest"
            }
            values.update(
                profile_declaration=original.runtime.profile,
                provider_execution_bindings=(binding,),
            )
            entries.append(CodeSemanticMaterializationProfileBinding.create(**values))
    catalog = _catalog(*entries)
    executables, planners = _execution_closure(catalog)
    admitted = _issue_code_semantic_contract_catalog(
        catalog=catalog,
        provider_executable_bindings=executables,
        dependency_planner_bindings=planners,
        host_liveness=lambda: True,
    )
    original = context()
    resources = (
        DirectCommandResourceBinding(
            "authority_code_runtime", stages[1].runtime, "borrowed"
        ),
        *(
            replace(
                resource,
                resource=(
                    stages[0].runtime
                    if resource.role == "code_runtime"
                    else admitted
                ),
            )
            if resource.role in ("catalog", "code_runtime")
            else resource
            for resource in original.resources
        ),
    )
    expected = replace(
        original,
        process_id=os.getpid(),
        runtime=stages[0].runtime,
        catalog=admitted,
        resources=resources,
        stage_runtime_bindings=tuple(stages),
    )
    retained = _capture_stage_runtime_retention(expected)
    retained.validate()
    assert len(retained.stages) == 4
    assert retained.stages[2][2] is registrations[2]
    authority_runtime, authority_registration, _ = retained.authority_stage_for(
        registrations[2]
    )
    assert authority_runtime is stages[3].runtime
    assert authority_registration is registrations[3]
    with pytest.raises(ContractViolation, match="planning stage pair unavailable"):
        retained.authority_stage_for(registrations[3])
    for key, offset in (("alpha_selected", 0), ("beta_selected", 2)):
        declaration = {
            "semantic_contract": {"provider_key": key},
            "profiles": [
                {
                    "stage": stages[index].stage,
                    "profile_ref": stages[index].runtime.profile.profile_ref,
                    "profile_version": stages[index].runtime.profile.version,
                    "profile_digest": stages[index].runtime.profile.digest.to_wire(),
                }
                for index in (offset, offset + 1)
            ],
        }
        assert type(retained.validate_declared_profiles(declaration)) is bytes
    with pytest.raises(ContractViolation, match="stage pair"):
        _capture_stage_runtime_retention(
            replace(
                expected,
                resources=(
                    replace(resources[0], resource=stages[3].runtime),
                    *resources[1:],
                ),
                stage_runtime_bindings=(stages[0], stages[3], stages[2], stages[1]),
            )
        )
    with pytest.raises(ContractViolation, match="duplicate original stage registration"):
        _capture_stage_runtime_retention(
            replace(
                expected,
                stage_runtime_bindings=(
                    stages[0],
                    stages[1],
                    replace(stages[2], registration=registrations[0]),
                    stages[3],
                ),
            )
        )


def test_closed_registration_invalidates_retention(case):
    _, retained, _, _ = case
    runtime, registration = retained.stages[1][1:]
    selected.close_selected_provider_registration(runtime, registration)
    with pytest.raises(ContractViolation, match="closed"):
        retained.validate()
