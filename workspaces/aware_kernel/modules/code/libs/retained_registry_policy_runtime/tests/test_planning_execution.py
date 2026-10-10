"""Original Code planning adapter and selected executor; fixture application root."""

import asyncio
from dataclasses import replace

import pytest
import test_operation_context as fixtures
from aware_code_retained_registry_policy_runtime import direct_host as host
from aware_code_retained_registry_policy_runtime import planning_execution as execution
from aware_code_retained_registry_policy_runtime import (
    retained_input_admission as admissions,
)
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import (
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
from test_contracts import invocation
from test_direct_epoch_tracking import clearance
from test_planning_epoch_lifetime import setup as epoch_setup


class Codec(fixtures.JsonBodyCodec):
    def decode(self, body):
        if self.contract == fixtures.SOURCE:
            return body.decode()
        return super().decode(body)

    def encode(self, value):
        if self.contract == fixtures.SOURCE:
            return value.encode()
        return super().encode(value)


class Provider(fixtures._SelectedProvider):
    def __init__(self):
        self.calls = 0
        self.closure_calls = 0
        self.hook = None
        self.fail_execution = False
        self.result = None

    def input_closure(self, value):
        self.closure_calls += 1
        if self.hook:
            self.hook()
        return value

    def execute(self, step, value):
        self.calls += 1
        if self.hook:
            self.hook()
        if self.fail_execution:
            raise ValueError("provider failed")
        return self.result


class FixtureIssuer:
    """Unit-test owner only. Real Workspace integration is tested separately."""

    def __init__(self, resources):
        self.observation_runtime = resources["observation_runtime"]
        self.membership_runtime = resources["membership_runtime"]
        self.package = object()
        self.inventory = object()
        self.expected = None

    def validate_package_context_admission(self, handle, *, expected):
        assert handle is self.package
        fixtures.op._equal(expected, self.expected)

    def validate_declaration_inventory_admission(self, handle, *, expected):
        assert handle is self.inventory
        fixtures.op._equal(expected, self.expected)

    def validate_occurrence_assignments(
        self, handle, *, expected, namespace, owned_roots
    ):
        self.validate_package_context_admission(handle, expected=expected)
        assert namespace == "home" and owned_roots == ("home",)


def setup(monkeypatch, *, declare_result=True):
    original_binding = fixtures.CodeSemanticMaterializationProfileBinding

    class BindingFactory:
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

    original_profile = fixtures.planning_profile

    def planning_profile():
        profile = original_profile()
        if not declare_result:
            return profile
        provider = profile.providers[0]
        provider = replace(
            provider,
            result_role=replace(
                provider.result_role, contract=DependencyPlanningInputCodec.contract
            ),
        )
        return replace(profile, providers=(provider,))

    original_bootstrap = host._assemble_direct_command_bootstrap
    issuer_holder = []

    def bootstrap(*, lifetime, expected):
        resources = {r.role: r.resource for r in expected.resources}
        issuer = FixtureIssuer(resources)
        issuer_holder.append(issuer)
        expected = replace(
            expected,
            resources=tuple(
                replace(r, resource=issuer) if r.role == "semantic_issuer" else r
                for r in expected.resources
            ),
        )
        resources["lifetime_runtime"].expected = expected
        return original_bootstrap(lifetime=lifetime, expected=expected)

    with monkeypatch.context() as patch:
        patch.setattr(host, "_assemble_direct_command_bootstrap", bootstrap)
        patch.setattr(fixtures, "planning_profile", planning_profile)
        patch.setattr(
            fixtures, "CodeSemanticMaterializationProfileBinding", BindingFactory
        )
        patch.setattr(fixtures, "_SelectedProvider", Provider)
        patch.setattr(fixtures, "JsonBodyCodec", Codec)
        values, tracker = epoch_setup(patch)
    owner, direct, _, _provider, registration, request = values
    origin = execution.bind_planning_execution_origin(direct, registration)
    context = fixtures.begin(values)
    expected = fixtures.op.source_planning_expectation(direct, context)
    issuer = issuer_holder[0]
    issuer.expected = expected
    owner.admission_origin = admissions.assemble_retained_input_admission_origin(direct)
    registry = owner.admission_origin.issue_registry_package_admission(
        context, issuer.package
    )
    owner.admission_origin.join(context, registry, issuer.package, issuer.inventory)
    values[3].result = SemanticDependencyPlanningInput(
        expected.package, expected.source_identity_digest, ()
    )
    runtime = owner.expected.runtime
    bodies = tuple(
        sorted(fixtures.op._bodies(request), key=lambda b: b.coordinate.role)
    )
    call = replace(
        invocation(),
        profile_ref=runtime.profile.profile_ref,
        profile_digest=runtime.profile.digest,
        target_package=expected.package,
        predecessor=TypedEmptyCoordinate(
            runtime.profile.providers[0].result_role.contract
        ),
        requested_output_roles=(),
        inputs=tuple(b.coordinate for b in bodies),
        provider_bindings=(fixtures._BINDING,),
        body_codec_bindings=tuple(
            SemanticBodyCodecBinding(contract, impl)
            for contract, impl in sorted(
                runtime._codec_implementations.items(), key=lambda x: x[0].key
            )
        ),
    )
    closure = selected.SelectedProviderInvocationClosure(call, bodies)
    return values, tracker, origin, context, closure


def test_original_reservation_adopted_before_closure_and_through_execution(monkeypatch):
    values, tracker, origin, context, closure = setup(monkeypatch)
    owner, direct, _, provider, registration, _ = values

    def blocked():
        with pytest.raises(ContractViolation, match="active"):
            clearance(owner, tracker)

    provider.hook = blocked
    admission = selected.issue_selected_provider_execution(
        owner.expected.runtime, registration, closure, operation_context=context
    )
    assert provider.closure_calls == 1 and provider.calls == 0
    result = selected.execute_selected_provider(owner.expected.runtime, admission)
    assert provider.calls == 1
    stage = execution._ORIGINS[origin][2][context]
    assert stage.result is result and stage.status == "returned"
    blocked()
    with pytest.raises(ContractViolation):
        selected.execute_selected_provider(owner.expected.runtime, admission)
    host.close_direct_validation_host(direct)


def test_context_required_before_input_closure(monkeypatch):
    values, _, _, _, closure = setup(monkeypatch)
    with pytest.raises(ContractViolation, match="context required"):
        selected.issue_selected_provider_execution(
            values[0].expected.runtime, values[4], closure
        )
    assert values[3].closure_calls == 0
    host.close_direct_validation_host(values[1])


def test_replay_does_not_invalidate_first_admission(monkeypatch):
    values, _, _, context, closure = setup(monkeypatch)
    runtime = values[0].expected.runtime
    admission = selected.issue_selected_provider_execution(
        runtime, values[4], closure, operation_context=context
    )
    with pytest.raises(ContractViolation, match="replay"):
        selected.issue_selected_provider_execution(
            runtime, values[4], closure, operation_context=context
        )
    selected.execute_selected_provider(runtime, admission)
    assert values[3].calls == 1
    host.close_direct_validation_host(values[1])


def test_raw_runtime_execution_refuses(monkeypatch):
    values, _, _, _, closure = setup(monkeypatch)
    with pytest.raises(ContractViolation, match="tracked selected"):
        asyncio.run(
            values[0].expected.runtime.execute(closure.invocation, closure.input_bodies)
        )
    assert values[3].calls == 0
    host.close_direct_validation_host(values[1])


def test_foreign_closure_rejects_before_provider(monkeypatch):
    values, tracker, origin, context, closure = setup(monkeypatch)
    bad = replace(
        closure, invocation=replace(closure.invocation, profile_ref="foreign")
    )
    with pytest.raises(ContractViolation, match="closure differs"):
        selected.issue_selected_provider_execution(
            values[0].expected.runtime, values[4], bad, operation_context=context
        )
    assert values[3].calls == 0
    assert execution._ORIGINS[origin][2][context].status == "uncertain"
    with pytest.raises(ContractViolation, match="active"):
        clearance(values[0], tracker)
    host.close_direct_validation_host(values[1])


def test_provider_failure_remains_uncertain(monkeypatch):
    values, tracker, origin, context, closure = setup(monkeypatch)
    values[3].fail_execution = True
    runtime = values[0].expected.runtime
    admission = selected.issue_selected_provider_execution(
        runtime, values[4], closure, operation_context=context
    )
    with pytest.raises(ValueError, match="provider failed"):
        selected.execute_selected_provider(runtime, admission)
    assert execution._ORIGINS[origin][2][context].status == "uncertain"
    with pytest.raises(ContractViolation, match="active"):
        clearance(values[0], tracker)
    host.close_direct_validation_host(values[1])


def test_original_origin_method_substitution_refuses_before_closure(monkeypatch):
    values, _, origin, context, closure = setup(monkeypatch)
    origin.adopt = lambda value: object()
    with pytest.raises(ContractViolation, match="entrance substituted"):
        selected.issue_selected_provider_execution(
            values[0].expected.runtime, values[4], closure, operation_context=context
        )
    assert values[3].closure_calls == 0
    host.close_direct_validation_host(values[1])


def test_lifecycle_binding_is_single_use(monkeypatch):
    values, _, _, _, _ = setup(monkeypatch)
    with pytest.raises(ContractViolation, match="late or replayed"):
        execution.bind_planning_execution_origin(values[1], values[4])
    host.close_direct_validation_host(values[1])


def test_close_does_not_reopen_raw_runtime(monkeypatch):
    values, _, _, _, closure = setup(monkeypatch)
    runtime = values[0].expected.runtime
    selected.close_selected_provider_registration(runtime, values[4])
    with pytest.raises(ContractViolation, match="tracked selected"):
        asyncio.run(runtime.execute(closure.invocation, closure.input_bodies))
    host.close_direct_validation_host(values[1])


def test_fork_refuses_and_parent_execution_remains_valid(monkeypatch):
    import os

    values, _, _, context, closure = setup(monkeypatch)
    runtime = values[0].expected.runtime
    admission = selected.issue_selected_provider_execution(
        runtime, values[4], closure, operation_context=context
    )
    pid = os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(os, "getpid", lambda: pid + 1)
        with pytest.raises(ContractViolation):
            selected.execute_selected_provider(runtime, admission)
        with pytest.raises(ContractViolation):
            asyncio.run(runtime.execute(closure.invocation, closure.input_bodies))
    selected.execute_selected_provider(runtime, admission)
    host.close_direct_validation_host(values[1])


def test_raw_execution_exposure_prevents_late_binding(monkeypatch):
    values, _tracker = epoch_setup(monkeypatch)
    runtime = values[0].expected.runtime
    with pytest.raises(TypeError):
        asyncio.run(runtime.execute(object(), ()))
    with pytest.raises(ContractViolation, match="late or replayed"):
        execution.bind_planning_execution_origin(values[1], values[4])
    host.close_direct_validation_host(values[1])
