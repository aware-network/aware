from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_experience.program.language import (
    compile_invocation_plans,
    encode_invocation_plan_artifact,
)
from aware_code.types.json import JsonObject
from aware_experience.program import service as program_service
from aware_experience.program.operations import apply_program_ref
from aware_experience_service_dto.experience.program import ApplyProgramRefRequest


class _ResolverStub:
    def __init__(
        self,
        *,
        manifest_path: Path,
        runtime: object | None = None,
    ):
        self._manifest_path = manifest_path
        self._runtime = runtime

    async def get_manifest(self):
        return self._manifest_path, object()

    async def get_runtime(self, *, environment_id):
        if self._runtime is not None:
            return self._runtime
        raise AssertionError(
            f"get_runtime should not be called in this test ({environment_id})"
        )


def _invocation_plan_payload(*, source: str, program_name: str) -> dict[str, object]:
    plans = compile_invocation_plans(source)
    matches = [plan for plan in plans if plan.name == program_name]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected one InvocationPlan for {program_name!r}, got {len(matches)}"
        )
    return encode_invocation_plan_artifact(matches[0])


def _request(
    *,
    environment_id,
    program_ref: str,
    symbols: dict[str, object],
    validate_only: bool = False,
    commit: bool = True,
) -> ApplyProgramRefRequest:
    return ApplyProgramRefRequest(
        actor_id=uuid4(),
        environment_id=environment_id,
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=None,
        projection_hash=None,
        program_ref=program_ref,
        symbols=JsonObject(symbols),
        validate_only=validate_only,
        commit=commit,
        publish=False,
    )


@pytest.mark.asyncio
async def test_apply_program_ref_requires_symbol_invocation_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_id = uuid4()
    resolver = _ResolverStub(manifest_path=tmp_path / "environment.manifest.json")
    request = _request(
        environment_id=env_id,
        program_ref="interface:EnsureBootInterfaceGraph_v0",
        symbols={},
    )

    monkeypatch.setenv("AWARE_RUNTIME_REQUIRE_PROGRAM_REGISTRY", "1")
    response = await apply_program_ref(
        resolver,
        request,
    )

    assert response.status == "failed"
    assert response.error is not None
    assert "symbols.plan.invocation_plan_artifact" in response.error


@pytest.mark.asyncio
async def test_apply_program_ref_accepts_symbol_invocation_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_id = uuid4()
    program_source = """
program EnsureBootInterfaceGraph_v0 {
    let marker = "ok"
}
"""
    invocation_plan_payload = _invocation_plan_payload(
        source=program_source,
        program_name="EnsureBootInterfaceGraph_v0",
    )

    class _ExecutorStub:
        def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            _ = args
            assert "repo_root" not in kwargs
            assert "manifest" not in kwargs
            assert "require_program_registry" not in kwargs

        async def execute(self, plan, *, symbols, validate_only):  # noqa: ANN001
            _ = symbols, validate_only
            assert plan.name == "EnsureBootInterfaceGraph_v0"
            return [{"target": "noop"}]

        def resolved_lane(self):
            return None

    monkeypatch.setattr(program_service, "RuntimeInvocationPlanExecutor", _ExecutorStub)

    resolver = _ResolverStub(
        manifest_path=tmp_path / "environment.manifest.json",
        runtime=SimpleNamespace(invoker=SimpleNamespace(get_index=lambda: object())),
    )
    request = _request(
        environment_id=env_id,
        program_ref="interface:EnsureBootInterfaceGraph_v0",
        symbols={"plan.invocation_plan_artifact": invocation_plan_payload},
    )

    response = await apply_program_ref(
        resolver,
        request,
    )

    assert response.status == "succeeded"
    assert response.error is None


@pytest.mark.asyncio
async def test_apply_program_ref_fails_on_invalid_symbol_invocation_plan_payload(
    tmp_path: Path,
) -> None:
    env_id = uuid4()
    resolver = _ResolverStub(manifest_path=tmp_path / "environment.manifest.json")
    request = _request(
        environment_id=env_id,
        program_ref="interface:EnsureBootInterfaceGraph_v0",
        symbols={"plan.invocation_plan_artifact": {"invalid": True}},
    )

    response = await apply_program_ref(
        resolver,
        request,
    )

    assert response.status == "failed"
    assert response.error is not None
    assert "Invalid invocation plan symbol payload" in response.error


@pytest.mark.asyncio
async def test_apply_program_ref_symbol_plan_fails_when_required_symbol_missing(
    tmp_path: Path,
) -> None:
    env_id = uuid4()
    program_source = """
program EnsureBootInterfaceGraph_v0 {
    input interface_id from plan.interface_id
    let marker = interface_id
}
"""
    invocation_plan_payload = _invocation_plan_payload(
        source=program_source,
        program_name="EnsureBootInterfaceGraph_v0",
    )
    resolver = _ResolverStub(manifest_path=tmp_path / "environment.manifest.json")
    request = _request(
        environment_id=env_id,
        program_ref="interface:EnsureBootInterfaceGraph_v0",
        symbols={"plan.invocation_plan_artifact": invocation_plan_payload},
    )

    response = await apply_program_ref(
        resolver,
        request,
    )

    assert response.status == "failed"
    assert response.error is not None
    assert "missing required symbols" in response.error
    assert "plan.interface_id" in response.error


@pytest.mark.asyncio
async def test_apply_program_ref_requires_symbol_plan_for_any_module(
    tmp_path: Path,
) -> None:
    env_id = uuid4()
    resolver = _ResolverStub(manifest_path=tmp_path / "environment.manifest.json")
    request = _request(
        environment_id=env_id,
        program_ref="economy:SettleSmartContractReservation_v1",
        symbols={},
    )

    response = await apply_program_ref(
        resolver,
        request,
    )

    assert response.status == "failed"
    assert response.error is not None
    assert "symbols.plan.invocation_plan_artifact" in response.error


@pytest.mark.asyncio
async def test_apply_program_ref_contract_validation_succeeds_when_intent_is_bound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_id = uuid4()
    event_config_id = uuid4()
    action_config_id = uuid4()
    program_source = """
program ContractPolicy_v1 {
    input event_config_id from plan.event_config_id
    input action_config_id from plan.action_config_id
    expect event_config event_config_id
    intent action_config action_config_id on event_config event_config_id
}
"""
    invocation_plan_payload = _invocation_plan_payload(
        source=program_source,
        program_name="ContractPolicy_v1",
    )

    class _ConditionEvaluatorStub:
        def __init__(self, *, manifest_path: str, invoker) -> None:  # noqa: ANN001
            _ = manifest_path, invoker

        async def resolve_bindings_for_event_config_ids(
            self,
            *,
            event_config_ids,
            include_disabled: bool,
            force_refresh: bool,
        ):
            _ = include_disabled, force_refresh
            binding = SimpleNamespace(
                action_bindings=[
                    SimpleNamespace(
                        is_enabled=True,
                        action_config_id=action_config_id,
                    )
                ]
            )
            return {
                event_id: [binding]
                for event_id in event_config_ids
                if event_id == event_config_id
            }

    monkeypatch.setattr(
        "aware_reactivity.condition.evaluator.LaneMaterializedConditionEvaluator",
        _ConditionEvaluatorStub,
    )

    class _InvokerStub:
        def get_index(self):  # noqa: ANN001
            return SimpleNamespace()

        async def invoke_function(self, _request):  # noqa: ANN001
            raise AssertionError(
                "invoke_function should not be called in this contract-only test"
            )

    resolver = _ResolverStub(
        manifest_path=tmp_path / "environment.manifest.json",
        runtime=SimpleNamespace(invoker=_InvokerStub()),
    )
    request = _request(
        environment_id=env_id,
        program_ref="conversation:ContractPolicy_v1",
        symbols={
            "plan.invocation_plan_artifact": invocation_plan_payload,
            "plan.event_config_id": str(event_config_id),
            "plan.action_config_id": str(action_config_id),
        },
        validate_only=True,
        commit=False,
    )

    response = await apply_program_ref(
        resolver,
        request,
    )

    assert response.status == "succeeded"
    assert response.error is None


@pytest.mark.asyncio
async def test_apply_program_ref_contract_validation_fails_when_intent_is_unbound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_id = uuid4()
    event_config_id = uuid4()
    action_config_id = uuid4()
    other_action_config_id = uuid4()
    program_source = """
program ContractPolicy_v1 {
    input event_config_id from plan.event_config_id
    input action_config_id from plan.action_config_id
    expect event_config event_config_id
    intent action_config action_config_id on event_config event_config_id
}
"""
    invocation_plan_payload = _invocation_plan_payload(
        source=program_source,
        program_name="ContractPolicy_v1",
    )

    class _ConditionEvaluatorStub:
        def __init__(self, *, manifest_path: str, invoker) -> None:  # noqa: ANN001
            _ = manifest_path, invoker

        async def resolve_bindings_for_event_config_ids(
            self,
            *,
            event_config_ids,
            include_disabled: bool,
            force_refresh: bool,
        ):
            _ = include_disabled, force_refresh
            binding = SimpleNamespace(
                action_bindings=[
                    SimpleNamespace(
                        is_enabled=True,
                        action_config_id=other_action_config_id,
                    )
                ]
            )
            return {
                event_id: [binding]
                for event_id in event_config_ids
                if event_id == event_config_id
            }

    monkeypatch.setattr(
        "aware_reactivity.condition.evaluator.LaneMaterializedConditionEvaluator",
        _ConditionEvaluatorStub,
    )

    class _InvokerStub:
        def get_index(self):  # noqa: ANN001
            return SimpleNamespace()

        async def invoke_function(self, _request):  # noqa: ANN001
            raise AssertionError(
                "invoke_function should not be called in this contract-only test"
            )

    resolver = _ResolverStub(
        manifest_path=tmp_path / "environment.manifest.json",
        runtime=SimpleNamespace(invoker=_InvokerStub()),
    )
    request = _request(
        environment_id=env_id,
        program_ref="conversation:ContractPolicy_v1",
        symbols={
            "plan.invocation_plan_artifact": invocation_plan_payload,
            "plan.event_config_id": str(event_config_id),
            "plan.action_config_id": str(action_config_id),
        },
        validate_only=True,
        commit=False,
    )

    response = await apply_program_ref(
        resolver,
        request,
    )

    assert response.status == "failed"
    assert response.error is not None
    assert "intent action_config is not bound to event_config" in response.error
