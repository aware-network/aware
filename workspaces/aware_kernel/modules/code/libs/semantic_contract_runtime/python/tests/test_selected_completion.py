"""Selected completion mechanics; lifecycle fixture is not trusted host admission."""

import asyncio
from dataclasses import dataclass, replace

import pytest
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.contracts import ContractViolation
from aware_code_semantic_contract_runtime.runtime import (
    ExecutionCompletion,
    ProviderDerivation,
)
from test_contracts import (  # pyright: ignore[reportMissingImports]
    delta_bodies,
    delta_result,
)
from test_selected_provider import (  # pyright: ignore[reportMissingImports]
    _call,
    _selected,
    _SelectedProvider,
)


@dataclass(frozen=True, slots=True)
class _HostSelectedUse:
    node_identity: object


@dataclass(frozen=True, slots=True)
class _HostOperationContext:
    use: _HostSelectedUse
    node_identity: object


@dataclass(frozen=True, slots=True)
class _HostSelectedInput:
    call: object
    bodies: object
    use: _HostSelectedUse
    node_identity: object


class _GraphNodeOrigin:
    """Host-owned use retained across one generic selected execution."""

    def __init__(self, context, selected_input):
        self.context = context
        self.selected_input = selected_input
        self.status = "fresh"
        self.current = True
        self.validations = 0
        self.host_checks = 0
        self.completion = None
        self.failed = False

    def adopt(self, context):
        if context is not self.context or self.status != "fresh":
            raise ContractViolation("original fresh graph operation context required")
        if (
            context.use is not self.selected_input.use
            or context.node_identity is not self.selected_input.node_identity
        ):
            raise ContractViolation("selected input differs from graph operation")
        self.status = "running"
        return context.use

    def validate(self, use, closure):
        if (
            use is not self.context.use
            or self.status != "running"
            or closure.invocation is not self.selected_input.call
            or closure.input_bodies is not self.selected_input.bodies
        ):
            raise ContractViolation("original running selected use required")
        if not self.current:
            raise ContractViolation("graph operation currentness changed")
        self.validations += 1

    def validate_host_use(self, use, node_identity):
        if (
            use is not self.context.use
            or node_identity is not self.context.node_identity
            or self.status != "running"
        ):
            raise ContractViolation("original running selected use required")
        if not self.current:
            raise ContractViolation("graph operation currentness changed")
        self.host_checks += 1

    def complete(self, use, result):
        self.validate_host_use(use, self.context.node_identity)
        self.completion = result
        self.status = "completed"

    def fail(self, use):
        if use is not self.context.use:
            raise ContractViolation("foreign selected use failed")
        self.failed = True
        self.status = "failed"


class Origin:
    def __init__(self):
        self.result = None
        self.failed = False
        self.reject_complete = False

    def adopt(self, context):
        return context

    def validate(self, use, closure):
        assert use is not None and closure is not None

    def complete(self, use, result):
        self.result = result
        if self.reject_complete:
            raise ContractViolation("final guard failed")

    def fail(self, use):
        self.failed = True


def assembly(monkeypatch, *, mode="runtime_completion", transform=None):
    calls = []

    def execute(self, step, semantic_input):
        calls.append(step)
        result = delta_result(step.invocation, step.input_closure_digest)
        derivation = ProviderDerivation(result, delta_bodies(result))
        return derivation if transform is None else transform(derivation)

    monkeypatch.setattr(_SelectedProvider, "execute", execute)
    runtime, _, _, registration = _selected()
    origin = Origin()
    selected._bind_selected_execution_lifecycle(
        runtime, registration, origin, terminal_mode=mode
    )
    call, bodies = _call(runtime)
    admission = selected.issue_selected_provider_execution(
        runtime, registration, (call, bodies), operation_context=object()
    )
    return runtime, registration, origin, admission, calls


def test_same_selected_call_returns_original_runtime_completion(monkeypatch):
    runtime, _, origin, admission, calls = assembly(monkeypatch)
    completion = selected.execute_selected_provider(runtime, admission)
    assert type(completion) is ExecutionCompletion
    assert runtime.owns_completion(completion)
    assert origin.result is completion
    assert len(calls) == 1
    assert runtime.snapshot_completion(completion).result.outputs
    with pytest.raises(ContractViolation):
        selected.execute_selected_provider(runtime, admission)
    with pytest.raises(ContractViolation):
        runtime._complete_selected_derivation(admission, None)


def test_owner_value_mode_is_not_payload_inferred(monkeypatch):
    runtime, _, origin, admission, calls = assembly(monkeypatch, mode="owner_value")
    result = selected.execute_selected_provider(runtime, admission)
    assert type(result) is ProviderDerivation
    assert origin.result is result
    assert len(calls) == 1


@pytest.mark.parametrize("mode", ["missing", "extra", "wrong_return"])
def test_invalid_return_or_body_closure_rejects(monkeypatch, mode):
    def transform(derivation):
        if mode == "wrong_return":
            return object()
        if mode == "missing":
            return replace(derivation, bodies=derivation.bodies[:-1])
        return replace(derivation, result=replace(derivation.result, outputs=()))

    runtime, _, origin, admission, calls = assembly(monkeypatch, transform=transform)
    with pytest.raises((TypeError, ContractViolation)):
        selected.execute_selected_provider(runtime, admission)
    assert origin.failed
    assert len(calls) == 1
    assert origin.result is None


def test_final_lifecycle_rejection_revokes_provisional_completion(monkeypatch):
    runtime, _, origin, admission, _ = assembly(monkeypatch)
    origin.reject_complete = True
    with pytest.raises(ContractViolation, match="final guard"):
        selected.execute_selected_provider(runtime, admission)
    assert type(origin.result) is ExecutionCompletion
    assert not runtime.owns_completion(origin.result)
    assert origin.failed


def test_premature_finalizer_and_raw_execution_reject(monkeypatch):
    runtime, _, _, admission, _ = assembly(monkeypatch)
    with pytest.raises(ContractViolation, match="unavailable"):
        runtime._complete_selected_derivation(admission, None)
    call, bodies = _call(runtime)
    with pytest.raises(ContractViolation, match="tracked"):
        asyncio.run(runtime.execute(call, bodies))
    assert runtime.owns_completion(
        selected.execute_selected_provider(runtime, admission)
    )


def test_digest_validation_preserves_canonical_output_tuple(monkeypatch):
    runtime, _, _, _, _ = assembly(monkeypatch)
    call, _ = _call(runtime)
    original = call.requested_output_roles
    digest = call.digest
    assert call.digest == digest
    call.to_wire()
    assert call.requested_output_roles is original


def test_terminalizing_registration_cannot_close(monkeypatch):
    runtime, registration, _, admission, _ = assembly(monkeypatch)
    original = runtime._accept_provider_derivation
    attempts = []

    def validate(*args):
        with pytest.raises(ContractViolation, match="active execution"):
            selected.close_selected_provider_registration(runtime, registration)
        attempts.append(True)
        return original(*args)

    monkeypatch.setattr(runtime, "_accept_provider_derivation", validate)
    assert runtime.owns_completion(
        selected.execute_selected_provider(runtime, admission)
    )
    assert attempts == [True]


def test_bad_terminal_mode_rejects_before_execution(monkeypatch):
    with pytest.raises(ContractViolation, match="terminal mode"):
        assembly(monkeypatch, mode="auto")


def test_terminal_handoff_binds_original_return_and_thread(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    runtime, _, _, admission, _ = assembly(monkeypatch)
    original = runtime._complete_selected_derivation

    def finalize(admitted, derivation):
        with pytest.raises(ContractViolation, match="unavailable"):
            original(admitted, replace(derivation))
        with (
            ThreadPoolExecutor(max_workers=1) as pool,
            pytest.raises(ContractViolation, match="unavailable"),
        ):
            pool.submit(original, admitted, derivation).result()
        return original(admitted, derivation)

    monkeypatch.setattr(runtime, "_complete_selected_derivation", finalize)
    assert runtime.owns_completion(selected.execute_selected_provider(runtime, admission))


def _graph_selected_assembly(
    monkeypatch,
    *,
    invalidate_during_execution=False,
    substitute_input_use=False,
):
    retained = {}
    original_input_closure = _SelectedProvider.input_closure

    def input_closure(self, value):
        if type(value) is not _HostSelectedInput:
            raise TypeError("exact host-selected input required")
        return original_input_closure(self, (value.call, value.bodies))

    def execute(self, step, semantic_input):
        del self
        if semantic_input is not retained["selected_input"]:
            raise ContractViolation("original host-selected input required")
        origin = retained["origin"]
        origin.validate_host_use(semantic_input.use, semantic_input.node_identity)
        if invalidate_during_execution:
            origin.current = False
        origin.validate_host_use(semantic_input.use, semantic_input.node_identity)
        result = delta_result(step.invocation, step.input_closure_digest)
        return ProviderDerivation(result, delta_bodies(result))

    monkeypatch.setattr(_SelectedProvider, "input_closure", input_closure)
    monkeypatch.setattr(_SelectedProvider, "execute", execute)
    runtime, _, _, registration = _selected()
    call, bodies = _call(runtime)
    node_identity = object()
    use = _HostSelectedUse(node_identity)
    context = _HostOperationContext(use, node_identity)
    input_use = _HostSelectedUse(node_identity) if substitute_input_use else use
    selected_input = _HostSelectedInput(call, bodies, input_use, node_identity)
    origin = _GraphNodeOrigin(context, selected_input)
    retained.update(selected_input=selected_input, origin=origin)
    selected._bind_selected_execution_lifecycle(
        runtime,
        registration,
        origin,
        terminal_mode="runtime_completion",
    )
    admission = selected.issue_selected_provider_execution(
        runtime,
        registration,
        selected_input,
        operation_context=context,
    )
    return runtime, registration, origin, context, admission


def test_graph_node_rejects_selected_input_use_substitution(monkeypatch):
    with pytest.raises(ContractViolation, match="selected input differs"):
        _graph_selected_assembly(monkeypatch, substitute_input_use=True)


def test_graph_node_use_spans_selected_execution_and_runtime_completion(monkeypatch):
    runtime, registration, origin, context, admission = _graph_selected_assembly(
        monkeypatch
    )

    completion = selected.execute_selected_provider(runtime, admission)

    assert type(completion) is ExecutionCompletion
    assert runtime.owns_completion(completion)
    assert origin.completion is completion
    assert origin.status == "completed"
    assert origin.validations == 3
    assert origin.host_checks == 3
    with pytest.raises(ContractViolation, match="original running selected use"):
        origin.validate_host_use(context.use, context.node_identity)
    with pytest.raises(ContractViolation, match="fresh graph operation context"):
        selected.issue_selected_provider_execution(
            runtime,
            registration,
            origin.selected_input,
            operation_context=context,
        )
    with pytest.raises(ContractViolation, match="fresh graph operation context"):
        selected.issue_selected_provider_execution(
            runtime,
            registration,
            origin.selected_input,
            operation_context=replace(context),
        )


def test_graph_node_currentness_change_revokes_selected_execution(monkeypatch):
    runtime, _, origin, context, admission = _graph_selected_assembly(
        monkeypatch,
        invalidate_during_execution=True,
    )

    with pytest.raises(ContractViolation, match="currentness changed"):
        selected.execute_selected_provider(runtime, admission)

    assert origin.failed
    assert origin.status == "failed"
    assert origin.completion is None
    with pytest.raises(ContractViolation, match="original running selected use"):
        origin.validate_host_use(context.use, context.node_identity)
    with pytest.raises(ContractViolation, match="not active"):
        selected.execute_selected_provider(runtime, admission)
