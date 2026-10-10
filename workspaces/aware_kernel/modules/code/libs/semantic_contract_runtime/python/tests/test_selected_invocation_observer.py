"""Original Code factory/admission/lifecycle proofs; no owner-store authority."""
from __future__ import annotations

import copy
import gc
import pickle
import weakref
from dataclasses import replace
from threading import Thread
from uuid import uuid4

import pytest
from aware_code_semantic_contract_runtime import (
    ContractViolation,
    ProviderDerivation,
    ProviderStepInvocation,
    SemanticContractRuntime,
)
from aware_code_semantic_contract_runtime import selected_provider as selected
from test_contracts import delta_bodies, delta_result
from test_profile_runtime import profile
from test_selected_provider import (
    _ARTIFACT,
    _BINDING,
    _CONFIGURATION,
    _call,
    _codecs,
    _SelectedProvider,
)


@pytest.fixture
def observed():
    faults = {}
    key = "observer_" + uuid4().hex
    binding = replace(_BINDING, provider_key=key)
    created = []

    class Provider(_SelectedProvider):
        def __init__(self):
            super().__init__()
            self.events: list[str] = []
            self.uses: list[selected.SelectedInvocationUse] = []
            self.evidence: list[selected.SelectedInvocationEvidence] = []

        def observe(self, event, use):
            self.events.append(event)
            if event == "associated":
                self.uses.append(use)
            evidence = selected.require_selected_invocation(use, self)
            self.evidence.append(evidence)
            callback = faults.get(event)
            if callback is not None:
                callback(evidence)
            return faults.get("return_" + event)

        def execute(self, step, semantic_input) -> ProviderDerivation:  # pyright: ignore[reportIncompatibleMethodOverride]
            assert type(step) is ProviderStepInvocation
            self.calls += 1
            evidence = selected.require_selected_invocation(self.uses[-1], self)
            assert evidence.step_invocation is step
            assert evidence.semantic_input is semantic_input
            if faults.get("execute"):
                faults["execute"]()
            result = delta_result(step.invocation, step.input_closure_digest)
            assert result.transition is not None and result.effect is not None
            transition = replace(result.transition, provider_key=key)
            effect = replace(result.effect, provider_key=key, transition_digest=transition.digest)
            result = replace(result, transition=transition, effect=effect, outputs=tuple(
                replace(item, provider_key=key, prepared_effect_digest=effect.digest) for item in result.outputs
            ))
            return ProviderDerivation(result, delta_bodies(result))

    def factory():
        provider = Provider()
        provider._declaration = replace(provider.declaration, provider_key=key)
        base = profile()
        declared = replace(base, profile_ref=key, providers=(provider.declaration,),
                           steps=(replace(base.steps[0], provider_key=key),))
        runtime = SemanticContractRuntime(declared, {key: provider}, _codecs())
        created.append((runtime, provider))
        return selected._SelectedProviderFactoryProduct(
            runtime, provider, binding, provider.execute, provider.input_closure,
            _ARTIFACT, _CONFIGURATION, selected_invocation_observer=provider.observe,
        )

    original_factory = selected._admit_selected_provider_factory(
        factory_ref=key, provider_key=key, selection_factory=factory)
    root = selected._issue_selected_provider_selection_root(original_factory)
    runtime, provider = created[0]
    registration = selected.register_selected_provider(runtime, root)
    context = object()

    class Lifecycle:
        def adopt(self, value):
            assert value is context
            return value

        def validate(self, value, closure):
            assert value is context

        def complete(self, value, completion):
            assert value is context and runtime.owns_completion(completion)
            if faults.get("terminal"):
                faults["terminal"]()

        def fail(self, value):
            assert value is context
            provider.events.append("lifecycle_failed")

    original = Lifecycle()
    selected._bind_selected_execution_lifecycle(runtime, registration, original,
                                               terminal_mode="runtime_completion")
    call, bodies = _call(runtime)
    call = replace(call, profile_ref=key, provider_bindings=(binding,))
    semantic_input = (call, bodies)
    yield runtime, provider, registration, semantic_input, context, faults
    # Tests deliberately leave pre-dispatch admissions active in some cases.
    for admission, execution in tuple(selected._EXECUTIONS.values()):
        if execution.registration is registration and execution.lifecycle == "active":
            selected._abort_selected_provider_execution(runtime, admission)
    if not selected._REGISTRATIONS[id(registration)][1].closed:
        selected.close_selected_provider_registration(runtime, registration)


def admit(observed):
    runtime, _, registration, value, context, _ = observed
    return selected.issue_selected_provider_execution(runtime, registration, value, operation_context=context)


def run(observed):
    return selected.execute_selected_provider(observed[0], admit(observed))


def test_original_attribution_and_provisional_then_terminal_success(observed):
    runtime, provider, registration, value, _, _ = observed
    completion = run(observed)
    assert provider.events == ["associated", "dispatch", "complete"]
    assert provider.calls == 1
    assert [e.phase for e in provider.evidence] == provider.events
    assert all(e.runtime is runtime and e.registration is registration and e.provider is provider
               and e.semantic_input is value for e in provider.evidence)
    assert all(not e.terminal_success for e in provider.evidence)
    assert provider.evidence[0].completion is None
    assert provider.evidence[-1].completion is completion
    final = selected.require_selected_invocation(provider.uses[0], provider)
    assert final.terminal_success and final.completion is completion
    assert final.closure is provider.evidence[0].closure
    assert final.step_invocation is provider.evidence[0].step_invocation


def test_equal_inputs_produce_distinct_admission_and_completion_attribution(observed):
    provider = observed[1]
    first = run(observed)
    use = provider.uses[0]
    second = run(observed)
    a = selected.require_selected_invocation(use, provider)
    b = selected.require_selected_invocation(provider.uses[1], provider)
    assert a.admission is not b.admission and a.sequence + 1 == b.sequence
    assert a.completion is first and b.completion is second and first is not second
    assert a.step_invocation.invocation.digest == b.step_invocation.invocation.digest
    detached = replace(a, completion=second)
    with pytest.raises(ContractViolation):
        selected.require_selected_invocation(detached, provider)  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize("phase", ["associated", "dispatch", "complete", "terminal", "execute"])
def test_each_failure_retires_use_and_withdraws_provisional_completion(observed, phase):
    runtime, provider, _, _, _, faults = observed
    def refuse(*args):
        raise RuntimeError("original refusal")
    faults[phase] = refuse
    with pytest.raises(RuntimeError, match="original refusal"):
        run(observed)
    assert "failed" in provider.events
    assert provider.events[-1] == "lifecycle_failed"
    assert provider.calls == (phase in {"execute", "complete", "terminal"})
    for use in provider.uses:
        with pytest.raises(ContractViolation):
            selected.require_selected_invocation(use, provider)
    for evidence in provider.evidence:
        if evidence.completion is not None:
            assert not runtime.owns_completion(evidence.completion)
    faults.clear()
    assert runtime.owns_completion(run(observed))


def test_pre_dispatch_abort_notifies_and_retires_original_use(observed):
    runtime, provider, _, _, _, _ = observed
    admission = admit(observed)
    selected._abort_selected_provider_execution(runtime, admission)
    assert provider.calls == 0
    assert provider.events == ["associated", "failed", "lifecycle_failed"]
    with pytest.raises(ContractViolation):
        selected.require_selected_invocation(provider.uses[0], provider)


@pytest.mark.parametrize("phase", ["associated", "dispatch", "complete"])
def test_observer_return_must_be_exact_none(observed, phase):
    observed[-1]["return_" + phase] = False
    with pytest.raises(ContractViolation, match="return None"):
        run(observed)
    with pytest.raises(ContractViolation):
        selected.require_selected_invocation(observed[1].uses[0], observed[1])


def test_duplicate_or_reentrant_active_association_refuses(observed):
    first = admit(observed)
    with pytest.raises(ContractViolation, match="active invocation"):
        admit(observed)
    assert observed[1].calls == 0
    selected._abort_selected_provider_execution(observed[0], first)


def test_copy_serialization_reconstruction_and_foreign_provider_refuse(observed):
    admit(observed)
    provider = observed[1]
    use = provider.uses[0]
    for copier in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            copier(use)
    with pytest.raises(TypeError):
        selected.SelectedInvocationUse()
    for wrong in (object.__new__(selected.SelectedInvocationUse), object()):
        with pytest.raises(ContractViolation):
            selected.require_selected_invocation(wrong, provider)  # pyright: ignore[reportArgumentType]
    with pytest.raises(ContractViolation):
        selected.require_selected_invocation(use, object())


def test_successful_use_is_weakly_retained_and_closure_revokes_it(observed):
    run(observed)
    provider = observed[1]
    use = provider.uses[0]
    reference = weakref.ref(use)
    provider.uses.clear()
    del use
    gc.collect()
    assert reference() is None
    run(observed)
    selected.close_selected_provider_registration(observed[0], observed[2])
    with pytest.raises(ContractViolation):
        selected.require_selected_invocation(provider.uses[0], provider)


def test_foreign_thread_and_recycled_thread_identifier_refuse(observed):
    admit(observed)
    provider = observed[1]
    errors = []
    def foreign():
        try:
            selected.require_selected_invocation(provider.uses[0], provider)
        except ContractViolation:
            errors.append("refused")
    thread = Thread(target=foreign)
    thread.start()
    thread.join()
    assert errors == ["refused"]


def test_changed_input_refuses_before_dispatch(observed):
    admission = admit(observed)
    evidence = observed[1].evidence[0]
    evidence.closure.input_values[0]["changed"] = True
    with pytest.raises(ContractViolation):
        selected.execute_selected_provider(observed[0], admission)
    assert observed[1].calls == 0
    assert "failed" in observed[1].events


def test_substituted_observer_descriptor_runs_zero_foreign_behavior(observed, monkeypatch):
    admission = admit(observed)
    provider = observed[1]
    calls = []
    class Hostile:
        def __get__(self, *args):
            calls.append("foreign")
            raise AssertionError("foreign observer descriptor")
    monkeypatch.setattr(type(provider), "observe", Hostile())
    with pytest.raises(ContractViolation):
        selected.execute_selected_provider(observed[0], admission)
    assert calls == []
    assert provider.calls == 0
    with pytest.raises(ContractViolation):
        selected.require_selected_invocation(provider.uses[0], provider)


def test_substituted_invocation_verifier_runs_zero_foreign_behavior(observed, monkeypatch):
    admission = admit(observed)
    provider = observed[1]
    calls = []
    def hostile(*args):
        calls.append("foreign")
        raise AssertionError("foreign verifier")
    monkeypatch.setattr(selected, "require_selected_invocation", hostile)
    with pytest.raises(ContractViolation):
        selected.execute_selected_provider(observed[0], admission)
    assert calls == []
    assert provider.calls == 0


@pytest.mark.parametrize("field", ["semantic_input", "closure", "step_invocation", "sequence"])
def test_coherent_execution_field_substitution_cannot_change_original_attribution(observed, field):
    admission = admit(observed)
    runtime, provider = observed[:2]
    execution, _ = selected._execution_state(runtime, admission)
    original = getattr(execution, field)
    if field == "closure":
        replacement = replace(original)
    elif field == "step_invocation":
        replacement = copy.copy(original)
    elif field == "sequence":
        replacement = original + 1
    else:
        replacement = tuple(list(original))  # noqa: C414 - deliberately copy tuple identity.
    setattr(execution, field, replacement)
    with pytest.raises(ContractViolation):
        selected.require_selected_invocation(provider.uses[0], provider)
    setattr(execution, field, original)
    with pytest.raises(ContractViolation, match="revoked"):
        selected.require_selected_invocation(provider.uses[0], provider)
    with pytest.raises(ContractViolation):
        selected.execute_selected_provider(runtime, admission)
    assert provider.calls == 0


@pytest.mark.parametrize("name", ["_fresh_step_invocation", "_observer_intact", "SelectedInvocationEvidence", "type"])
def test_original_verifier_poison_is_behavior_free_and_restoration_cannot_revive(observed, monkeypatch, name):
    admission = admit(observed)
    provider = observed[1]
    use = provider.uses[0]
    calls = []
    def foreign(*args):
        calls.append("foreign")
        raise AssertionError("foreign behavior")
    with monkeypatch.context() as change:
        change.setattr(selected, name, foreign, raising=False)
        with pytest.raises(ContractViolation):
            selected.require_selected_invocation(use, provider)
    assert calls == []
    with pytest.raises(ContractViolation):
        selected.execute_selected_provider(observed[0], admission)
    with pytest.raises(ContractViolation):
        selected.require_selected_invocation(use, provider)


def test_poisoned_evidence_descriptor_is_never_invoked(observed, monkeypatch):
    admission = admit(observed)
    provider = observed[1]
    calls = []
    class ForeignDescriptor:
        def __get__(self, *args):
            calls.append("foreign")
            raise AssertionError("foreign descriptor")
    with monkeypatch.context() as change:
        change.setattr(selected.SelectedInvocationEvidence, "provider", ForeignDescriptor())
        with pytest.raises(ContractViolation):
            selected.require_selected_invocation(provider.uses[0], provider)
    assert calls == []
    with pytest.raises(ContractViolation):
        selected.execute_selected_provider(observed[0], admission)


def test_process_change_rejects_without_acquiring_inherited_lock(observed, monkeypatch):
    admission = admit(observed)
    provider = observed[1]
    record = selected._require_observed_invocation(provider.uses[0], provider)
    actual = record.pid
    record.pid = actual + 1
    with pytest.raises(ContractViolation, match="process/thread"):
        selected.require_selected_invocation(provider.uses[0], provider)
    record.pid = actual
    with pytest.raises(ContractViolation):
        selected.execute_selected_provider(observed[0], admission)


def test_dead_original_thread_is_not_replaced_by_same_numeric_identifier(observed):
    admission = admit(observed)
    provider = observed[1]
    record = selected._require_observed_invocation(provider.uses[0], provider)
    original = record.thread
    dead = Thread(target=lambda: None)
    dead.start()
    dead.join()
    record.thread = dead
    with pytest.raises(ContractViolation, match="process/thread"):
        selected.require_selected_invocation(provider.uses[0], provider)
    record.thread = original
    with pytest.raises(ContractViolation):
        selected.execute_selected_provider(observed[0], admission)


def test_cancellation_is_terminal_and_original_failure_survives_cleanup_failure(observed):
    runtime, provider, _, _, _, faults = observed
    def cancel(*args):
        raise KeyboardInterrupt("cancelled")
    def cleanup(*args):
        raise RuntimeError("observer cleanup failed")
    faults["dispatch"] = cancel
    faults["failed"] = cleanup
    with pytest.raises(KeyboardInterrupt, match="cancelled"):
        run(observed)
    assert provider.calls == 0
    assert provider.events[-1] == "lifecycle_failed"
    with pytest.raises(ContractViolation):
        selected.require_selected_invocation(provider.uses[0], provider)
    faults.clear()
    assert runtime.owns_completion(run(observed))


def test_retained_exception_does_not_retain_codes_failed_execution_graph(observed):
    _, provider, _, _, _, faults = observed
    retained = []
    def refuse(*args):
        raise RuntimeError("retained failure")
    faults["terminal"] = refuse
    try:
        run(observed)
    except RuntimeError as error:
        retained.append(error)
    assert len(retained) == 1
    traceback = retained[0].__traceback__
    checked_active = False
    while traceback is not None:
        frame = traceback.tb_frame
        if frame.f_code.co_name == "execute_selected_provider":
            checked_active = True
            state = frame.f_locals["execution"]
            assert state.semantic_input is None
            assert state.closure is None
            assert state.step_invocation is None
            assert state.primitive_snapshot is None
            assert state.terminal_derivation is None
            assert frame.f_locals["fresh"] is None
            assert frame.f_locals["result"] is None
            assert frame.f_locals["completion"] is None
        traceback = traceback.tb_next
    assert checked_active
    with pytest.raises(ContractViolation):
        selected.require_selected_invocation(provider.uses[0], provider)


def test_nested_step_tuple_is_strongly_retained_and_compared_with_is(observed):
    admission = admit(observed)
    provider = observed[1]
    record = selected._require_observed_invocation(provider.uses[0], provider)
    step = record.execution.step_invocation
    original = step.inputs
    assert record.step_nodes[1] is original
    object.__setattr__(step, "inputs", tuple(list(original)))  # noqa: C414 - copied tuple poison.
    assert step.inputs is not original
    assert record.step_nodes[1] is original
    with pytest.raises(ContractViolation, match="step node"):
        selected.require_selected_invocation(provider.uses[0], provider)
    object.__setattr__(step, "inputs", original)
    with pytest.raises(ContractViolation):
        selected.execute_selected_provider(observed[0], admission)


@pytest.mark.parametrize("kind", ["unbound", "other_provider", "optional", "varargs"])
def test_factory_observer_rejects_structural_or_wrong_provider_entrances(kind):
    key = "observer_invalid_" + uuid4().hex
    class Provider(_SelectedProvider):
        def valid(self, event, use):
            return None
        def optional(self, event, use=None):
            return None
        def varargs(self, *args):
            return None
    def factory():
        provider = Provider()
        provider._declaration = replace(provider.declaration, provider_key=key)
        base = profile()
        declared = replace(base, profile_ref=key, providers=(provider.declaration,),
                           steps=(replace(base.steps[0], provider_key=key),))
        runtime = SemanticContractRuntime(declared, {key: provider}, _codecs())
        callback = {"unbound": Provider.valid, "other_provider": Provider().valid,
                    "optional": provider.optional, "varargs": provider.varargs}[kind]
        return selected._SelectedProviderFactoryProduct(
            runtime, provider, replace(_BINDING, provider_key=key), provider.execute, provider.input_closure,
            _ARTIFACT, _CONFIGURATION, selected_invocation_observer=callback,  # pyright: ignore[reportArgumentType]
        )
    admitted = selected._admit_selected_provider_factory(factory_ref=key, provider_key=key,
                                                         selection_factory=factory)
    with pytest.raises((TypeError, ContractViolation)):
        selected._issue_selected_provider_selection_root(admitted)


def test_observer_cannot_bypass_original_tracked_completion_lifecycle(observed):
    runtime, provider, registration, value, _, _ = observed
    with pytest.raises(ContractViolation, match="original tracked"):
        selected.issue_selected_provider_execution(runtime, registration, value)
    assert provider.events == [] and provider.calls == 0


def test_existing_observed_invocation_cannot_appoint_an_input_verifier(observed):
    from aware_code_semantic_contract_runtime.selected_input_verification import (
        release_selected_invocation_input_verification,
        validate_selected_invocation_inputs,
    )
    run(observed)
    provider = observed[1]
    use = provider.uses[0]
    with pytest.raises(ContractViolation, match="not bound"):
        validate_selected_invocation_inputs(use, provider)
    with pytest.raises(ContractViolation, match="not bound"):
        release_selected_invocation_input_verification(use, provider)
    with pytest.raises(ContractViolation):
        validate_selected_invocation_inputs(object(), provider)
    with pytest.raises(ContractViolation):
        validate_selected_invocation_inputs(use, object())
    assert provider.calls == 1


def test_original_lifecycle_copy_cannot_create_input_authority(observed):
    from aware_code_semantic_contract_runtime.selected_input_verification import (
        validate_selected_invocation_inputs,
    )
    run(observed)
    state = selected._registration_state(observed[2])
    original = state.execution_lifecycle
    state.execution_lifecycle = copy.copy(original)
    try:
        with pytest.raises(ContractViolation, match="lifecycle changed"):
            validate_selected_invocation_inputs(observed[1].uses[0], observed[1])
    finally:
        state.execution_lifecycle = original


def test_original_lifecycle_entrance_map_cannot_add_a_noop_verifier(observed):
    from aware_code_semantic_contract_runtime.selected_input_verification import (
        validate_selected_invocation_inputs,
    )
    run(observed)
    state = selected._registration_state(observed[2])
    original = state.execution_lifecycle
    called = []
    original.entrances["verify_inputs"] = (None, lambda *args: called.append(True), None, None)
    try:
        with pytest.raises(ContractViolation, match="entrance record changed"):
            validate_selected_invocation_inputs(observed[1].uses[0], observed[1])
    finally:
        original.entrances.pop("verify_inputs")
    assert called == []
