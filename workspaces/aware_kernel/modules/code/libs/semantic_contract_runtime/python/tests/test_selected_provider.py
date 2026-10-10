from __future__ import annotations

import copy
import json
import os
from collections.abc import Callable
from dataclasses import replace
from uuid import uuid4

import pytest
from test_contracts import (  # pyright: ignore[reportMissingImports]
    declaration,
    input_bodies,
    invocation,
)
from test_profile_runtime import (  # pyright: ignore[reportMissingImports]
    JsonBodyCodec,
    profile,
)

import aware_code_semantic_contract_runtime.selected_provider as _selected_provider
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    ContractViolation,
    ProviderDerivation,
    ProviderExecutionBinding,
    SelectedProviderInvocationClosure,
    SemanticBody,
    SemanticBodyCodec,
    SemanticConfigurationCoordinate,
    SemanticContractInvocation,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    SemanticContractRuntime,
    SemanticImplementationCoordinate,
    canonical_json_bytes,
    canonical_json_text,
    close_selected_provider_registration,
    execute_selected_provider,
    issue_selected_provider_execution,
    register_selected_provider,
    selected_provider_probe,
)

_ARTIFACT = canonical_json_bytes({"artifact": "selected-sdk-provider"})
_CONFIGURATION = canonical_json_bytes({"configuration": "selected-sdk-default"})
_BINDING = ProviderExecutionBinding(
    "sdk",
    SemanticImplementationCoordinate(
        "selected-sdk-provider", ContentDigest.of_bytes(_ARTIFACT)
    ),
    SemanticConfigurationCoordinate(
        "selected-sdk-default", ContentDigest.of_bytes(_CONFIGURATION)
    ),
)


def _codecs() -> dict[SemanticContractRef, SemanticBodyCodec]:
    runtime_profile = profile()
    contracts = {item.contract for item in runtime_profile.inputs} | {
        runtime_profile.providers[0].result_role.contract,
        runtime_profile.providers[0].transition_contract,
        runtime_profile.providers[0].effect_contract,
        *(item.contract for item in runtime_profile.providers[0].output_roles),
    }
    return {contract: JsonBodyCodec(contract) for contract in contracts}


class _SelectedProvider:
    def __init__(self) -> None:
        self._declaration = declaration()
        self.calls = 0
        self.last_input_value: dict[str, object] | None = None
        self.execution_hook: Callable[[], None] | None = None

    @property
    def declaration(self) -> SemanticContractProviderDeclaration:
        return self._declaration

    async def derive(self, invocation: object) -> ProviderDerivation:
        del invocation
        raise AssertionError("ordinary derive is not used by this focused proof")

    def input_closure(self, value: object) -> SelectedProviderInvocationClosure:
        if type(value) is not tuple or len(value) != 2:
            raise TypeError("test semantic input must be exact pair")
        call, bodies = value
        if type(call) is not SemanticContractInvocation or type(bodies) is not tuple:
            raise TypeError("test semantic input values must be exact")
        input_value = json.loads(bodies[0].canonical_body)
        if type(input_value) is not dict:
            raise TypeError("test input body must decode to an exact object")
        self.last_input_value = input_value
        return SelectedProviderInvocationClosure(
            call,
            bodies,
            input_values=(input_value,),
        )

    def execute(self, step: object, semantic_input: object) -> ContentDigest:
        from aware_code_semantic_contract_runtime import ProviderStepInvocation

        if type(step) is not ProviderStepInvocation:
            raise TypeError("selected step must be exact")
        self.calls += 1
        if self.execution_hook is not None:
            self.execution_hook()
        assert semantic_input is not None
        return step.input_closure_digest


def _runtime() -> tuple[SemanticContractRuntime, _SelectedProvider]:
    provider = _SelectedProvider()
    runtime_profile = profile()
    runtime = SemanticContractRuntime(
        runtime_profile,
        {"sdk": provider},
        _codecs(),
    )
    return runtime, provider


def _construct_selected_provider() -> (
    _selected_provider._SelectedProviderFactoryProduct
):  # pyright: ignore[reportPrivateUsage]
    runtime, provider = _runtime()
    return _selected_provider._SelectedProviderFactoryProduct(  # pyright: ignore[reportPrivateUsage]
        runtime=runtime,
        provider=provider,
        binding=_BINDING,
        executable_entrance=provider.execute,
        input_closure_entrance=provider.input_closure,
        semantic_implementation_contract_body=_ARTIFACT,
        configuration_body=_CONFIGURATION,
    )


_TEST_FACTORY = _selected_provider._admit_selected_provider_factory(  # pyright: ignore[reportPrivateUsage]
    factory_ref="aware.test.selected-sdk-provider.factory.v1",
    provider_key="sdk",
    selection_factory=_construct_selected_provider,
)


def _selected() -> tuple[
    SemanticContractRuntime,
    _SelectedProvider,
    _selected_provider.AdmittedSemanticProviderSelectionRoot,
    _selected_provider.AdmittedSemanticProviderRegistration,
]:
    root = _selected_provider._issue_selected_provider_selection_root(  # pyright: ignore[reportPrivateUsage]
        _TEST_FACTORY
    )
    state = _selected_provider._selection_root_state(root)  # pyright: ignore[reportPrivateUsage]
    runtime = state.runtime
    provider = state.provider
    assert type(provider) is _SelectedProvider
    registration = register_selected_provider(runtime, root)
    return runtime, provider, root, registration


def _call(
    runtime: SemanticContractRuntime,
) -> tuple[SemanticContractInvocation, tuple[SemanticBody, ...]]:
    value = replace(
        invocation(profile_digest=runtime.profile.digest),
        provider_bindings=(_BINDING,),
    )
    return value, input_bodies(value)


def test_selected_provider_derives_input_closure_and_invokes_exact_live_provider() -> (
    None
):
    runtime, provider, _, registration = _selected()
    probe = selected_provider_probe(runtime, registration)
    call, bodies = _call(runtime)
    observed = probe((call, bodies))  # type: ignore[operator]
    assert type(observed) is ContentDigest
    assert provider.calls == 1

    close_selected_provider_registration(runtime, registration)
    with pytest.raises(ContractViolation, match="closed"):
        probe((call, bodies))  # type: ignore[operator]


def test_selected_provider_probe_retains_exact_factory_authority() -> None:
    runtime, _, _, registration = _selected()
    probe = selected_provider_probe(runtime, registration)
    _selected_provider._require_selected_provider_probe_factory(  # pyright: ignore[reportPrivateUsage]
        probe,
        factory_ref="aware.test.selected-sdk-provider.factory.v1",
    )
    with pytest.raises(ContractViolation, match="factory differs"):
        _selected_provider._require_selected_provider_probe_factory(  # pyright: ignore[reportPrivateUsage]
            probe,
            factory_ref="aware.test.substitute.factory.v1",
        )


def test_selected_provider_rejects_substitution_replay_and_foreign_entrance() -> None:
    runtime, _, _, registration = _selected()
    with pytest.raises(TypeError, match="factory admission must be exact"):
        _selected_provider._issue_selected_provider_selection_root(  # pyright: ignore[reportPrivateUsage]
            object()  # pyright: ignore[reportArgumentType]
        )

    call, bodies = _call(runtime)
    admission = issue_selected_provider_execution(runtime, registration, (call, bodies))
    with pytest.raises(TypeError, match="cannot be copied"):
        copy.copy(admission)
    _ = execute_selected_provider(runtime, admission)
    with pytest.raises(ContractViolation, match="not active"):
        _ = execute_selected_provider(runtime, admission)


def test_tracked_selected_admission_aborts_before_provider_dispatch() -> None:
    class Origin:
        def __init__(self) -> None:
            self.use = object()
            self.failures = 0
            self.completions = 0

        def adopt(self, context: object) -> object:
            assert context is self.use
            return context

        def validate(self, stage: object, closure: object) -> None:
            assert stage is self.use
            assert type(closure) is SelectedProviderInvocationClosure

        def complete(self, stage: object, result: object) -> None:
            del stage, result
            self.completions += 1

        def fail(self, stage: object) -> None:
            assert stage is self.use
            self.failures += 1

    runtime, provider, _, registration = _selected()
    origin = Origin()
    _selected_provider._bind_selected_execution_lifecycle(  # pyright: ignore[reportPrivateUsage]
        runtime, registration, origin, terminal_mode="runtime_completion"
    )
    call, bodies = _call(runtime)
    admission = issue_selected_provider_execution(
        runtime, registration, (call, bodies), operation_context=origin.use
    )
    foreign_runtime, _, _, _ = _selected()
    with pytest.raises(ContractViolation, match="another runtime/process"):
        _selected_provider._abort_selected_provider_execution(  # pyright: ignore[reportPrivateUsage]
            foreign_runtime, admission
        )
    assert origin.failures == 0

    _selected_provider._abort_selected_provider_execution(  # pyright: ignore[reportPrivateUsage]
        runtime, admission
    )
    assert origin.failures == 1
    assert origin.completions == 0
    assert provider.calls == 0
    with pytest.raises(ContractViolation, match="not active"):
        execute_selected_provider(runtime, admission)
    with pytest.raises(ContractViolation, match="not active"):
        _selected_provider._abort_selected_provider_execution(  # pyright: ignore[reportPrivateUsage]
            runtime, admission
        )
    assert origin.failures == 1


def test_tracked_abort_stays_terminal_when_owner_cleanup_raises() -> None:
    class FailingOrigin:
        def adopt(self, context: object) -> object:
            return context

        def validate(self, stage: object, closure: object) -> None:
            del stage, closure

        def complete(self, stage: object, result: object) -> None:
            raise AssertionError("provider must not run")

        def fail(self, stage: object) -> None:
            del stage
            raise RuntimeError("owner cleanup failed")

    runtime, provider, _, registration = _selected()
    _selected_provider._bind_selected_execution_lifecycle(  # pyright: ignore[reportPrivateUsage]
        runtime, registration, FailingOrigin(), terminal_mode="runtime_completion"
    )
    call, bodies = _call(runtime)
    admission = issue_selected_provider_execution(
        runtime, registration, (call, bodies), operation_context=object()
    )
    with pytest.raises(RuntimeError, match="owner cleanup failed"):
        _selected_provider._abort_selected_provider_execution(  # pyright: ignore[reportPrivateUsage]
            runtime, admission
        )
    with pytest.raises(ContractViolation, match="not active"):
        execute_selected_provider(runtime, admission)
    assert provider.calls == 0


def test_selected_provider_rejects_canonical_closure_restamping() -> None:
    runtime, _, _, registration = _selected()
    call, bodies = _call(runtime)
    admission = issue_selected_provider_execution(runtime, registration, (call, bodies))
    object.__setattr__(
        call,
        "invocation_ref",
        "restamped-invocation",
    )
    with pytest.raises(
        ContractViolation,
        match="(closure changed|admitted input coordinates differ)",
    ):
        _ = execute_selected_provider(runtime, admission)


def test_selected_provider_rejects_cross_runtime_copy_and_fork_replay() -> None:
    runtime, _, _, registration = _selected()
    with pytest.raises(TypeError, match="cannot be copied"):
        copy.copy(registration)
    other_runtime, _ = _runtime()
    with pytest.raises(ContractViolation, match="another runtime"):
        selected_provider_probe(other_runtime, registration)

    call, bodies = _call(runtime)
    probe = selected_provider_probe(runtime, registration)
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:  # pragma: no cover - asserted by parent pipe evidence
        os.close(read_fd)
        try:
            probe((call, bodies))
        except ContractViolation as error:
            os.write(write_fd, str(error).encode("utf-8"))
        finally:
            os.close(write_fd)
        os._exit(0)
    os.close(write_fd)
    evidence = os.read(read_fd, 4096)
    os.close(read_fd)
    _, status = os.waitpid(child, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    assert b"another process" in evidence


def test_selected_provider_rejects_live_substitution_and_sequence_overflow() -> None:
    runtime, _, _, registration = _selected()
    call, bodies = _call(runtime)
    admission = issue_selected_provider_execution(runtime, registration, (call, bodies))
    runtime._providers["sdk"] = _SelectedProvider()  # pyright: ignore[reportPrivateUsage]
    with pytest.raises(ContractViolation, match="selected live provider changed"):
        _ = execute_selected_provider(runtime, admission)

    other_runtime, _, _, other_registration = _selected()
    retained = _selected_provider._REGISTRATIONS[id(other_registration)][  # pyright: ignore[reportPrivateUsage]
        1
    ]
    retained.sequence = (1 << 64) - 1
    overflow_probe = selected_provider_probe(other_runtime, other_registration)
    with pytest.raises(ContractViolation, match="sequence exhausted"):
        overflow_probe(_call(other_runtime))


def test_selected_provider_rejects_body_and_binding_substitution_after_admission() -> (
    None
):
    runtime, _, _, registration = _selected()
    call, bodies = _call(runtime)
    admission = issue_selected_provider_execution(runtime, registration, (call, bodies))
    replacement_body = b'{"source":"replacement"}'
    replacement_coordinate = replace(
        bodies[0].coordinate,
        digest=ContentDigest.of_bytes(replacement_body),
        size_bytes=len(replacement_body),
    )
    object.__setattr__(bodies[0], "coordinate", replacement_coordinate)
    object.__setattr__(bodies[0], "canonical_body", replacement_body)
    object.__setattr__(call, "inputs", (replacement_coordinate,))
    with pytest.raises(
        ContractViolation,
        match="(closure changed|admitted input coordinates differ)",
    ):
        _ = execute_selected_provider(runtime, admission)


def test_selected_provider_rejects_live_input_value_restamping() -> None:
    runtime, provider, _, registration = _selected()
    call, bodies = _call(runtime)
    admission = issue_selected_provider_execution(runtime, registration, (call, bodies))
    input_value = provider.last_input_value
    assert input_value is not None
    input_value["source"] = "restamped"
    with pytest.raises(ContractViolation, match="changed after admission"):
        _ = execute_selected_provider(runtime, admission)


def test_selected_provider_verification_primitive_is_protected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def hostile_descriptor_get(*args: object) -> object:
        del args
        calls.append("called")
        raise AssertionError("foreign descriptor getter executed")

    runtime, provider, _, registration = _selected()
    call, bodies = _call(runtime)
    with monkeypatch.context() as initial:
        initial.setattr(
            _selected_provider, "_MEMBER_DESCRIPTOR_GET", hostile_descriptor_get
        )
        with pytest.raises(TypeError, match="verification primitive changed"):
            issue_selected_provider_execution(runtime, registration, (call, bodies))
    assert calls == []

    admission = issue_selected_provider_execution(runtime, registration, (call, bodies))
    with monkeypatch.context() as preinvoke:
        preinvoke.setattr(
            _selected_provider, "_MEMBER_DESCRIPTOR_GET", hostile_descriptor_get
        )
        with pytest.raises(ContractViolation, match="closure changed"):
            execute_selected_provider(runtime, admission)
    assert calls == []
    with pytest.raises(ContractViolation, match="not active"):
        execute_selected_provider(runtime, admission)

    def hostile_type(value: object) -> type[object]:
        calls.append("type")
        return type(value)

    admission = issue_selected_provider_execution(runtime, registration, (call, bodies))
    provider.execution_hook = lambda: monkeypatch.setattr(
        _selected_provider, "type", hostile_type, raising=False
    )
    try:
        with pytest.raises(ContractViolation, match="closure changed"):
            execute_selected_provider(runtime, admission)
    finally:
        monkeypatch.delattr(_selected_provider, "type")
        provider.execution_hook = None
    assert calls == []
    with pytest.raises(ContractViolation, match="not active"):
        execute_selected_provider(runtime, admission)

    admission = issue_selected_provider_execution(runtime, registration, (call, bodies))
    provider.execution_hook = lambda: monkeypatch.setattr(
        _selected_provider, "_MEMBER_DESCRIPTOR_GET", hostile_descriptor_get
    )
    try:
        with pytest.raises(ContractViolation, match="closure changed"):
            execute_selected_provider(runtime, admission)
    finally:
        monkeypatch.setattr(
            _selected_provider,
            "_MEMBER_DESCRIPTOR_GET",
            _selected_provider._RETAINED_MEMBER_DESCRIPTOR_GET,  # pyright: ignore[reportPrivateUsage]
        )
        provider.execution_hook = None
    assert calls == []
    with pytest.raises(ContractViolation, match="not active"):
        execute_selected_provider(runtime, admission)


def test_selected_provider_verifier_closes_builtin_and_helper_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    snapshot = _selected_provider._capture_primitive_snapshot(  # pyright: ignore[reportPrivateUsage]
        ("value", 1)
    )

    def hostile(*args: object) -> object:
        del args
        calls.append("called")
        return object()

    for name in ("type", "object", "list", "len"):
        with monkeypatch.context() as changed:
            changed.setattr(_selected_provider, name, hostile, raising=False)
            with pytest.raises(TypeError, match="verification primitive changed"):
                _selected_provider._primitive_snapshot_matches(  # pyright: ignore[reportPrivateUsage]
                    ("value", 1), snapshot
                )
        assert calls == []

    with monkeypatch.context() as changed:
        changed.setattr(_selected_provider, "_encode_primitive_graph", hostile)
        with pytest.raises(TypeError, match="verification primitive changed"):
            _selected_provider._primitive_snapshot_matches(  # pyright: ignore[reportPrivateUsage]
                ("value", 1), snapshot
            )
    assert calls == []

    with monkeypatch.context() as changed:
        changed.setattr(_selected_provider, "_MEMBER_DESCRIPTOR_GET", hostile)
        changed.setattr(
            _selected_provider, "_RETAINED_MEMBER_DESCRIPTOR_GET", hostile
        )
        with pytest.raises(TypeError, match="verification primitive changed"):
            _selected_provider._capture_primitive_snapshot(  # pyright: ignore[reportPrivateUsage]
                ("value", 1)
            )
    assert calls == []

    for name in ("_RETAINED_DICT_CONTAINS", "_RETAINED_DICT_GETITEM"):
        with monkeypatch.context() as changed:
            changed.setattr(_selected_provider, name, hostile)
            with pytest.raises(TypeError, match="verification primitive changed"):
                _selected_provider._capture_primitive_snapshot(  # pyright: ignore[reportPrivateUsage]
                    ("value", 1)
                )
        assert calls == []


def test_selected_provider_requires_exact_canonical_artifact_bodies() -> None:
    with pytest.raises(ContractViolation, match="canonical JSON"):
        _selected_provider._canonical_body(  # pyright: ignore[reportPrivateUsage]
            b'{"z":1,"a":2}', "semantic implementation contract closure"
        )
    assert (
        canonical_json_text({"artifact": "selected-sdk-provider"}).encode() == _ARTIFACT
    )


def test_selected_provider_selection_root_and_qualification_are_single_use() -> None:
    runtime, _, root, registration = _selected()
    with pytest.raises(TypeError, match="cannot be copied"):
        copy.copy(root)
    with pytest.raises(ContractViolation, match="already consumed"):
        register_selected_provider(runtime, root)
    probe = selected_provider_probe(runtime, registration)
    session = _selected_provider._open_selected_provider_qualification_session(  # pyright: ignore[reportPrivateUsage]
        probe
    )
    bindings = []
    for phase in ("bootstrap", "operational_current", "operational_delta"):
        binding = _selected_provider._begin_selected_provider_qualification_phase(  # pyright: ignore[reportPrivateUsage]
            session, phase, expected_operation_count=1
        )
        probe(_call(runtime))
        bindings.append(
            _selected_provider._finish_selected_provider_qualification_phase(  # pyright: ignore[reportPrivateUsage]
                binding
            )
        )
        witnesses = _selected_provider._selected_provider_phase_witnesses(  # pyright: ignore[reportPrivateUsage]
            binding
        )
        assert len(witnesses) == 1
        assert witnesses[0][0] == len(bindings)
    _selected_provider._consume_selected_provider_qualification_session(  # pyright: ignore[reportPrivateUsage]
        tuple(bindings)
    )
    with pytest.raises(ContractViolation, match="closed"):
        probe(_call(runtime))


def test_selected_provider_qualification_rejects_interleaving_and_wrong_count() -> None:
    runtime, _, _, registration = _selected()
    probe = selected_provider_probe(runtime, registration)
    session = _selected_provider._open_selected_provider_qualification_session(  # pyright: ignore[reportPrivateUsage]
        probe
    )
    binding = _selected_provider._begin_selected_provider_qualification_phase(  # pyright: ignore[reportPrivateUsage]
        session, "bootstrap", expected_operation_count=2
    )
    probe(_call(runtime))
    with pytest.raises(ContractViolation, match="operation count differs"):
        _selected_provider._finish_selected_provider_qualification_phase(  # pyright: ignore[reportPrivateUsage]
            binding
        )


def test_selected_provider_probe_requires_nominal_issuance() -> None:
    runtime, _, _, registration = _selected()
    forged = object.__new__(_selected_provider.SelectedSemanticProviderProbe)
    object.__setattr__(forged, "_token", _selected_provider._PROBE_TOKEN)  # pyright: ignore[reportPrivateUsage]
    object.__setattr__(forged, "_runtime", runtime)
    object.__setattr__(forged, "_registration", registration)
    object.__setattr__(forged, "_last_timings_ns", ())
    with pytest.raises(ContractViolation, match="not nominally admitted"):
        forged(_call(runtime))


def test_selected_provider_qualification_failure_closes_registration() -> None:
    runtime, _, _, registration = _selected()
    probe = selected_provider_probe(runtime, registration)
    session = _selected_provider._open_selected_provider_qualification_session(  # pyright: ignore[reportPrivateUsage]
        probe
    )
    bindings = []
    for phase in ("bootstrap", "operational_current", "operational_delta"):
        binding = _selected_provider._begin_selected_provider_qualification_phase(  # pyright: ignore[reportPrivateUsage]
            session, phase, expected_operation_count=1
        )
        probe(_call(runtime))
        bindings.append(
            _selected_provider._finish_selected_provider_qualification_phase(  # pyright: ignore[reportPrivateUsage]
                binding
            )
        )
    with pytest.raises(ContractViolation, match="bindings differ"):
        _selected_provider._consume_selected_provider_qualification_session(  # pyright: ignore[reportPrivateUsage]
            (bindings[1], bindings[0], bindings[2])
        )
    with pytest.raises(ContractViolation, match="closed"):
        probe(_call(runtime))


def test_private_predecessor_port_retains_original_provider_method() -> None:
    key = "private_port_" + uuid4().hex
    calls = []
    created = []

    class PortProvider(_SelectedProvider):
        def predecessor_view(self, approval):
            calls.append(approval)
            return object()

    def factory():
        provider = PortProvider()
        provider._declaration = replace(provider.declaration, provider_key=key)
        base = profile()
        selected_profile = replace(
            base,
            profile_ref="private." + key,
            providers=(provider.declaration,),
            steps=(replace(base.steps[0], provider_key=key),),
        )
        runtime = SemanticContractRuntime(
            selected_profile, {key: provider}, _codecs()
        )
        created.append((runtime, provider))
        return _selected_provider._SelectedProviderFactoryProduct(
            runtime, provider, replace(_BINDING, provider_key=key),
            provider.execute, provider.input_closure, _ARTIFACT,
            _CONFIGURATION,
            private_stage_predecessor_port=provider.predecessor_view,
        )

    factory_admission = _selected_provider._admit_selected_provider_factory(
        factory_ref=key, provider_key=key, selection_factory=factory
    )
    root = _selected_provider._issue_selected_provider_selection_root(
        factory_admission
    )
    runtime, provider = created[0]
    registration = register_selected_provider(runtime, root)
    try:
        _selected_provider._validate_selected_private_stage_predecessor_port(
            registration
        )
        assert calls == []
        state = _selected_provider._registration_state(registration)
        original = state.private_stage_predecessor_port
        state.private_stage_predecessor_port = PortProvider().predecessor_view
        with pytest.raises(ContractViolation, match="original predecessor port"):
            _selected_provider._validate_selected_private_stage_predecessor_port(
                registration
            )
        state.private_stage_predecessor_port = original
        provider.predecessor_view = lambda approval: approval
        with pytest.raises((ContractViolation, TypeError)):
            _selected_provider._validate_selected_private_stage_predecessor_port(
                registration
            )
        assert calls == []
    finally:
        close_selected_provider_registration(runtime, registration)


def test_private_predecessor_port_absence_does_not_gain_authority() -> None:
    runtime, _, _, registration = _selected()
    with pytest.raises(ContractViolation, match="unavailable"):
        _selected_provider._validate_selected_private_stage_predecessor_port(
            registration
        )
    close_selected_provider_registration(runtime, registration)


@pytest.mark.parametrize("fault", [None, "role", "contract", "no_port", "foreign_type"])
def test_private_predecessor_input_is_original_declared_profile_binding(fault) -> None:
    from aware_code_semantic_contract_runtime.private_stage_contract import PrivateStageRoleContract

    key = "bound_port_" + uuid4().hex
    created = []

    class Provider(_SelectedProvider):
        def predecessor(self, role, body, grant):
            raise AssertionError("registration never invokes the port")

    def factory():
        provider = Provider()
        provider._declaration = replace(provider.declaration, provider_key=key)
        base = profile()
        declared = replace(base, providers=(provider.declaration,),
                           steps=(replace(base.steps[0], provider_key=key),))
        runtime = SemanticContractRuntime(declared, {key: provider}, _codecs())
        binding = PrivateStageRoleContract(declared.inputs[0].role, declared.inputs[0].contract)
        if fault == "role":
            binding = replace(binding, role="unlisted")
        elif fault == "contract":
            binding = replace(binding, contract=provider.declaration.result_role.contract)
        elif fault == "foreign_type":
            binding = object()
        created.append((runtime, provider))
        return _selected_provider._SelectedProviderFactoryProduct(
            runtime, provider, replace(_BINDING, provider_key=key), provider.execute,
            provider.input_closure, _ARTIFACT, _CONFIGURATION,
            private_stage_predecessor_port=None if fault == "no_port" else provider.predecessor,
            private_stage_predecessor_input=binding,
        )

    admitted = _selected_provider._admit_selected_provider_factory(
        factory_ref=key, provider_key=key, selection_factory=factory
    )
    if fault is not None:
        with pytest.raises((ContractViolation, TypeError)):
            _selected_provider._issue_selected_provider_selection_root(admitted)
        return
    root = _selected_provider._issue_selected_provider_selection_root(admitted)
    runtime, _provider = created[0]
    registration = register_selected_provider(runtime, root)
    try:
        _selected_provider._validate_selected_private_stage_predecessor_port(registration)
        state = _selected_provider._registration_state(registration)
        original = state.private_stage_predecessor_input
        state.private_stage_predecessor_input = replace(original)
        with pytest.raises(ContractViolation, match="original predecessor port changed"):
            _selected_provider._validate_selected_private_stage_predecessor_port(registration)
        state.private_stage_predecessor_input = original
        object.__setattr__(original, "role", "coherently-substituted")
        with pytest.raises(ContractViolation, match="input binding changed"):
            _selected_provider._validate_selected_private_stage_predecessor_port(registration)
    finally:
        close_selected_provider_registration(runtime, registration)
