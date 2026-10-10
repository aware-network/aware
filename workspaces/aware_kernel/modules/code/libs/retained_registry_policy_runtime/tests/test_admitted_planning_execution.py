"""Real Workspace source join and selected execution; fixture application parent."""

import os
from dataclasses import replace

import pytest
import test_operation_context as fixtures
from aware_code_retained_registry_policy_runtime import direct_epoch_tracking as hooks
from aware_code_retained_registry_policy_runtime import direct_host as direct
from aware_code_retained_registry_policy_runtime import epoch_participation as epochs
from aware_code_retained_registry_policy_runtime import operation_context as contexts
from aware_code_retained_registry_policy_runtime import planning_execution as execution
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
    CatalogPublicationExpectation,
    DirectInvocationExpectation,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticBodyCodecBinding,
    TypedEmptyCoordinate,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticDependencyPlanningInput,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DependencyPlanningInputCodec,
)
from aware_workspace_runtime import SourceObservationUnavailable
from test_contracts import invocation
from test_direct_epoch_tracking import clearance
from test_planning_epoch_lifetime import Owner
from test_planning_execution import Codec, Provider
from test_retained_input_admission import assembled

pytestmark = pytest.mark.asyncio


def configure_epoch(owner, host):
    original = DirectInvocationExpectation(
        owner.expected.invocation_identity, owner.expected.epoch_identity, os.getpid()
    )
    digest = ContentDigest.of_bytes(b"fixture membership")
    owner.epoch = CatalogPairEpochExpectation(
        original, object(), direct._HOSTS[host].catalog_digest, digest, digest
    )
    owner.successor = CatalogPublicationExpectation(
        object(),
        owner.epoch,
        replace(owner.epoch, publication_identity=object()),
        digest,
    )
    guard = owner.acquire_catalog_epoch_exclusion(owner.parent, expected=original)
    try:
        owner.tracker = epochs._assemble_code_epoch_participation(
            owner=owner,
            parent=owner.parent,
            invocation=original,
            epoch_owner=owner,
            guard=guard,
        )
        hooks._bind_direct_policy_epoch(
            host, owner.tracker, owner.current, expected=owner.epoch, guard=guard
        )
    finally:
        owner.release_catalog_epoch_exclusion(guard)


def configure_provider(monkeypatch):
    original_profile = fixtures.planning_profile
    original_binding = fixtures.CodeSemanticMaterializationProfileBinding

    def profile():
        value = original_profile()
        provider = value.providers[0]
        provider = replace(
            provider,
            result_role=replace(
                provider.result_role, contract=DependencyPlanningInputCodec.contract
            ),
        )
        return replace(value, providers=(provider,))

    class Binding:
        @staticmethod
        def create(**values):
            profile = values["profile_declaration"]
            values["result_product_contracts"] = tuple(
                type(product).create(
                    role=product.role,
                    contract=profile.providers[0].result_role.contract,
                )
                if product.role == profile.terminal_result_role
                else product
                for product in values["result_product_contracts"]
            )
            return original_binding.create(**values)

    monkeypatch.setattr(fixtures, "planning_profile", profile)
    monkeypatch.setattr(fixtures, "CodeSemanticMaterializationProfileBinding", Binding)
    monkeypatch.setattr(fixtures, "_SelectedProvider", Provider)
    monkeypatch.setattr(fixtures, "JsonBodyCodec", Codec)


def closure_for(owner, context):
    record = contexts._CONTEXTS[context]
    runtime = owner.expected.runtime
    bodies = tuple(
        sorted(contexts._bodies(record.retained), key=lambda b: b.coordinate.role)
    )
    call = replace(
        invocation(),
        profile_ref=runtime.profile.profile_ref,
        profile_digest=runtime.profile.digest,
        target_package=record.expected.package,
        predecessor=TypedEmptyCoordinate(
            runtime.profile.providers[0].result_role.contract
        ),
        requested_output_roles=(),
        inputs=tuple(b.coordinate for b in bodies),
        provider_bindings=(fixtures._BINDING,),
        body_codec_bindings=tuple(
            SemanticBodyCodecBinding(c, i)
            for c, i in sorted(
                runtime._codec_implementations.items(), key=lambda x: x[0].key
            )
        ),
    )
    return selected.SelectedProviderInvocationClosure(call, bodies)


async def test_real_join_survives_running_and_returned_validation(
    tmp_path, monkeypatch
):
    configure_provider(monkeypatch)
    async with assembled(tmp_path, owner_type=Owner, before_policy=configure_epoch) as (
        _,
        owner,
        host,
        issuer,
        admission_origin,
        context,
        expected,
        package,
        inventory,
    ):
        record = contexts._CONTEXTS[context]
        runtime = owner.expected.runtime
        provider = selected._registration_state(record.registration).provider
        provider.result = SemanticDependencyPlanningInput(
            expected.package, expected.source_identity_digest, ()
        )
        origin = execution.bind_planning_execution_origin(host, record.registration)
        registry = admission_origin.issue_registry_package_admission(context, package)
        joined = admission_origin.join(context, registry, package, inventory)

        def check_running():
            issuer.validate_package_context_admission(package, expected=expected)
            issuer.validate_declaration_inventory_admission(
                inventory, expected=expected
            )
            admission_origin.validate(joined)
            with pytest.raises(ContractViolation, match="active"):
                clearance(owner, owner.tracker)

        provider.hook = check_running
        admitted = selected.issue_selected_provider_execution(
            runtime,
            record.registration,
            closure_for(owner, context),
            operation_context=context,
        )
        with pytest.raises(ContractViolation, match="replay"):
            selected.issue_selected_provider_execution(
                runtime,
                record.registration,
                closure_for(owner, context),
                operation_context=context,
            )
        selected.execute_selected_provider(runtime, admitted)
        check_running()
        assert execution._ORIGINS[origin][2][context].status == "returned"
        assert provider.calls == 1 and provider.closure_calls == 1


async def test_missing_join_refuses_before_provider_closure(tmp_path, monkeypatch):
    configure_provider(monkeypatch)
    async with assembled(tmp_path, owner_type=Owner, before_policy=configure_epoch) as (
        _,
        owner,
        host,
        _,
        _,
        context,
        _,
        _,
        _,
    ):
        record = contexts._CONTEXTS[context]
        execution.bind_planning_execution_origin(host, record.registration)
        provider = selected._registration_state(record.registration).provider
        with pytest.raises(ContractViolation, match="join required"):
            selected.issue_selected_provider_execution(
                owner.expected.runtime,
                record.registration,
                closure_for(owner, context),
                operation_context=context,
            )
        assert provider.calls == 0 and provider.closure_calls == 0


async def test_changed_source_after_adoption_prevents_execution(tmp_path, monkeypatch):
    configure_provider(monkeypatch)
    async with assembled(tmp_path, owner_type=Owner, before_policy=configure_epoch) as (
        root,
        owner,
        host,
        _,
        admission_origin,
        context,
        _,
        package,
        inventory,
    ):
        record = contexts._CONTEXTS[context]
        origin = execution.bind_planning_execution_origin(host, record.registration)
        registry = admission_origin.issue_registry_package_admission(context, package)
        admission_origin.join(context, registry, package, inventory)
        admitted = selected.issue_selected_provider_execution(
            owner.expected.runtime,
            record.registration,
            closure_for(owner, context),
            operation_context=context,
        )
        (root / "demo/home/aware.demo.toml").write_bytes(b"changed")
        with pytest.raises((ContractViolation, SourceObservationUnavailable)):
            selected.execute_selected_provider(owner.expected.runtime, admitted)
        assert selected._registration_state(record.registration).provider.calls == 0
        assert execution._ORIGINS[origin][2][context].status == "uncertain"
        with pytest.raises(ContractViolation, match="active"):
            clearance(owner, owner.tracker)


async def test_running_ticket_without_original_stage_is_not_context_authority(
    monkeypatch,
):
    from test_planning_epoch_lifetime import setup as epoch_setup

    values, tracker = epoch_setup(monkeypatch)
    owner, host, _, _, _, _ = values
    try:
        context = fixtures.begin(values)
        expected = contexts.source_planning_expectation(host, context)
        reservation = contexts._CONTEXTS[context].reservation
        with hooks._guard(reservation.binding) as guard:
            tracker._start_epoch_use(guard, reservation.use)
        with pytest.raises(ContractViolation, match="lifecycle unavailable"):
            contexts.source_planning_context_validator(
                host
            ).validate_retained_semantic_operation_context(context, expected=expected)
        with pytest.raises(ContractViolation, match="active"):
            clearance(owner, tracker)
    finally:
        direct.close_direct_validation_host(host)
