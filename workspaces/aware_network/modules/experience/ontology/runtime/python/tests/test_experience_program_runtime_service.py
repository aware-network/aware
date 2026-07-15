from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest

from aware_code.types.json import JsonArray
from ._experience_runtime_test_paths import REPO_ROOT

_REPO_ROOT = REPO_ROOT
for _path in (
    _REPO_ROOT / "apis" / "environment" / "python" / "aware_environment_service_dto",
    _REPO_ROOT / "apis" / "experience" / "python" / "aware_experience_service_dto",
    _REPO_ROOT / "libs" / "comms" / "python",
    _REPO_ROOT / "modules" / "experience" / "runtime",
    _REPO_ROOT / "modules" / "history" / "structure" / "ontology" / "python",
    _REPO_ROOT / "modules" / "meta" / "runtime",
    _REPO_ROOT / "modules" / "meta" / "structure" / "ontology" / "python",
    _REPO_ROOT / "modules" / "environment" / "runtime",
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_code.types.json import JsonObject
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionCallTarget,
    InvokeFunctionResponse,
)
from aware_experience_service_dto.experience.program import (
    RunProgramRequest,
    SubmitProgramTurnRequest,
    SubmitProgramTurnResponse,
)
from aware_experience.program import service as program_service
from aware_experience.program import ExperienceProgramRuntimeService
from aware_experience.program.runtime_invocation import (
    ProgramApplyError,
    ProgramIntentRecord,
)


def _invocation_plan_artifact(*, program_name: str) -> dict[str, object]:
    return {
        "schema_version": "aware.program.invocation.v1",
        "content_type": "application/x-aware-program-invocation+json",
        "program_name": program_name,
        "plan": {"nodes": [], "edges": []},
    }


def _build_submit_response(
    *,
    request: SubmitProgramTurnRequest,
    turn_id: UUID,
) -> SubmitProgramTurnResponse:
    return SubmitProgramTurnResponse(
        actor_id=request.actor_id,
        environment_id=request.environment_id,
        process_id=request.process_id,
        thread_id=request.thread_id,
        branch_id=request.branch_id,
        projection_hash=request.projection_hash,
        status="accepted",
        error=None,
        turn_id=turn_id,
        mailbox_key=request.mailbox_key,
        deduped=False,
    )


def _resolver_stub_for_manifest_lookup() -> Any:
    class _ResolverStub:
        async def get_manifest(self):
            return Path("/tmp/aware-test/environment.manifest.json"), object()

    return _ResolverStub()


@pytest.mark.asyncio
async def test_runtime_program_intent_recorder_records_action_intent_and_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    action_projection_hash = "sha256:action-intent"
    program_projection_hash = "sha256:program"
    action_opg_id = uuid4()
    action_intent_function_id = uuid4()
    record_action_function_id = uuid4()
    action_intent_id = uuid4()
    calls = []

    def _find_projection_hash_by_name(*, index: object, projection_name: str) -> str:
        _ = index
        if projection_name == "ActionIntent":
            return action_projection_hash
        if projection_name == "Program":
            return program_projection_hash
        raise AssertionError(projection_name)

    def _resolve_public_function_id(
        *,
        index: object,
        class_name_suffix: str,
        function_name: str,
    ) -> UUID:
        _ = index
        if (
            class_name_suffix.endswith(".ActionIntent")
            and function_name == "create_via_event"
        ):
            return action_intent_function_id
        if (
            class_name_suffix.endswith(".ProgramTurnInstruction")
            and function_name == "record_action"
        ):
            return record_action_function_id
        raise AssertionError((class_name_suffix, function_name))

    class _Invoker:
        async def invoke_function_with_index(self, *, index: object, request: object):
            _ = index
            calls.append(request)
            payload = (
                {"id": str(action_intent_id)}
                if len(calls) == 1
                else {"id": str(uuid4())}
            )
            return InvokeFunctionResponse(
                actor_id=getattr(request, "actor_id"),
                environment_id=getattr(request, "environment_id"),
                process_id=getattr(request, "process_id"),
                thread_id=getattr(request, "thread_id"),
                branch_id=getattr(request, "branch_id"),
                projection_hash=getattr(request, "projection_hash"),
                status="succeeded",
                payload=payload,
                logs=[],
                changes=JsonArray([]),
            )

    monkeypatch.setattr(
        program_service.ocg_support,
        "find_projection_hash_by_name",
        _find_projection_hash_by_name,
    )
    monkeypatch.setattr(
        program_service.ocg_support,
        "resolve_public_function_id",
        _resolve_public_function_id,
    )

    actor_id = uuid4()
    environment_id = uuid4()
    process_id = uuid4()
    thread_id = uuid4()
    branch_id = uuid4()
    record = ProgramIntentRecord(
        event_id=uuid4(),
        action_config_id=uuid4(),
        event_config_id=uuid4(),
        intent_key="program-turn:test-intent",
        step_index=0,
        program_turn_instruction_id=uuid4(),
        program_impl_instruction_intent_id=uuid4(),
    )
    recorder = program_service._RuntimeProgramIntentRecorder(
        runtime=SimpleNamespace(invoker=_Invoker()),
        index=SimpleNamespace(
            opg_by_hash={
                action_projection_hash: SimpleNamespace(id=action_opg_id),
            }
        ),
        actor_id=actor_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=branch_id,
    )

    await recorder.record_program_intent(record)

    assert len(calls) == 2
    create_intent = calls[0]
    assert create_intent.call_target == InvokeFunctionCallTarget.opg_constructor
    assert create_intent.object_projection_graph_id == action_opg_id
    assert create_intent.function_id == action_intent_function_id
    assert create_intent.projection_hash == action_projection_hash
    assert list(create_intent.args) == [
        str(record.event_id),
        str(record.action_config_id),
        record.intent_key,
    ]

    record_action = calls[1]
    assert record_action.call_target == InvokeFunctionCallTarget.instance
    assert record_action.object_id == record.program_turn_instruction_id
    assert record_action.function_id == record_action_function_id
    assert record_action.projection_hash == program_projection_hash
    assert list(record_action.args) == [
        str(record.program_impl_instruction_intent_id),
        str(record.action_config_id),
        str(record.event_config_id),
        str(action_intent_id),
        record.intent_key,
    ]


@pytest.mark.asyncio
async def test_runtime_program_intent_recorder_requires_event_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        program_service.ocg_support,
        "find_projection_hash_by_name",
        lambda *, index, projection_name: f"sha256:{projection_name}",
    )
    monkeypatch.setattr(
        program_service.ocg_support,
        "resolve_public_function_id",
        lambda *, index, class_name_suffix, function_name: uuid4(),
    )
    recorder = program_service._RuntimeProgramIntentRecorder(
        runtime=SimpleNamespace(invoker=object()),
        index=SimpleNamespace(
            opg_by_hash={
                "sha256:ActionIntent": SimpleNamespace(id=uuid4()),
            }
        ),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
    )

    with pytest.raises(ProgramApplyError, match=r"plan\.intent\.0\.event_id"):
        await recorder.record_program_intent(
            ProgramIntentRecord(
                event_id=None,
                action_config_id=uuid4(),
                event_config_id=uuid4(),
                intent_key="program-turn:missing-event",
                step_index=0,
                program_turn_instruction_id=uuid4(),
                program_impl_instruction_intent_id=uuid4(),
            )
        )


@pytest.mark.asyncio
async def test_run_program_materializes_stable_program_run_id_for_idempotent_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor_id = uuid4()
    environment_id = uuid4()
    process_id = uuid4()
    thread_id = uuid4()
    target_actor_id = uuid4()
    program_config_id = uuid4()
    persisted_program_id = uuid4()
    captured_submit_requests: list[SubmitProgramTurnRequest] = []

    class _FakeProgramPersistence:
        def __init__(
            self,
            *,
            resolver,
            actor_id,
            environment_id,
            process_id,
            thread_id,
        ) -> None:
            _ = resolver, actor_id, environment_id, process_id, thread_id

        async def create_or_get_program(self, **kwargs):
            assert kwargs["program_config_id"] == program_config_id
            return persisted_program_id

        async def set_running(self, *, program_id, **kwargs) -> None:
            _ = program_id, kwargs

        async def attach_turn(self, *, program_id, **kwargs) -> None:
            _ = program_id, kwargs

        async def finish_terminal(self, *, program_id, **kwargs) -> None:
            _ = program_id, kwargs

    monkeypatch.setattr(
        program_service,
        "ProgramProjectionPersistenceService",
        _FakeProgramPersistence,
    )

    async def _resolve_invocation_plan_from_ontology(
        self,  # noqa: ANN001
        *,
        resolver,  # noqa: ANN001
        request,  # noqa: ANN001
        program_config_id,  # noqa: ANN001
    ) -> dict[str, object]:
        _ = self, resolver, request, program_config_id
        return _invocation_plan_artifact(program_name="HumanConversationMessage_v1")

    monkeypatch.setattr(
        program_service.ExperienceProgramRuntimeService,
        "_resolve_invocation_plan_artifact_from_ontology",
        _resolve_invocation_plan_from_ontology,
    )

    async def _submit(
        resolver,
        request: SubmitProgramTurnRequest,
        *,
        apply_program_ref_op=object(),
        store=None,
    ) -> SubmitProgramTurnResponse:
        _ = apply_program_ref_op, store
        captured_submit_requests.append(request)
        return _build_submit_response(
            request=request,
            turn_id=uuid4(),
        )

    service = ExperienceProgramRuntimeService(submit_program_turn_op=_submit)
    resolver = _resolver_stub_for_manifest_lookup()
    request = RunProgramRequest(
        actor_id=actor_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=None,
        projection_hash=None,
        target_actor_id=target_actor_id,
        program_ref="conversation_default:HumanConversationMessage_v1",
        symbols=JsonObject(
            {
                "plan.program_config_id": str(program_config_id),
                "plan.message_text": "hello",
            }
        ),
        message="hello",
        turn_index=1,
        mailbox_key=None,
        idempotency_key="idem-1",
        max_attempts=1,
        wait_for_terminal=False,
    )

    first = await service.run_program(
        resolver=resolver,
        request=request,
        apply_program_ref_op=object(),
    )
    second = await service.run_program(
        resolver=resolver,
        request=request,
        apply_program_ref_op=object(),
    )

    assert first.operation == "run_program"
    assert second.operation == "run_program"
    assert first.program_run_id == persisted_program_id
    assert second.program_run_id == persisted_program_id
    assert len(captured_submit_requests) == 2
    assert captured_submit_requests[0].symbols.get("plan.program_run_id") == str(
        first.program_run_id
    )
    assert captured_submit_requests[1].symbols.get("plan.program_run_id") == str(
        second.program_run_id
    )
    assert first.mailbox_key == f"{environment_id}:{target_actor_id}"
    assert second.mailbox_key == f"{environment_id}:{target_actor_id}"


@pytest.mark.asyncio
async def test_run_program_passthrough_for_submit_program_turn_request() -> None:
    expected_response = SubmitProgramTurnResponse(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=None,
        projection_hash=None,
        status="accepted",
        error=None,
        turn_id=uuid4(),
        mailbox_key="mailbox:test",
        deduped=False,
    )

    async def _submit(
        resolver,
        request: SubmitProgramTurnRequest,
        *,
        apply_program_ref_op=object(),
        store=None,
    ) -> SubmitProgramTurnResponse:
        _ = request, apply_program_ref_op, store
        return expected_response

    service = ExperienceProgramRuntimeService(submit_program_turn_op=_submit)
    resolver = _resolver_stub_for_manifest_lookup()
    request = SubmitProgramTurnRequest(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=None,
        projection_hash=None,
        target_actor_id=uuid4(),
        program_ref="conversation_default:HumanConversationMessage_v1",
        symbols=JsonObject({"plan.message_text": "hello"}),
        message="hello",
        turn_index=1,
        mailbox_key="mailbox:test",
        idempotency_key=None,
        max_attempts=1,
        wait_for_terminal=False,
    )

    response = await service.run_program(
        resolver=resolver,
        request=request,
        apply_program_ref_op=object(),
    )
    assert response is expected_response


@pytest.mark.asyncio
async def test_run_program_materializes_program_when_program_config_symbol_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor_id = uuid4()
    environment_id = uuid4()
    process_id = uuid4()
    thread_id = uuid4()
    target_actor_id = uuid4()
    program_config_id = uuid4()
    persisted_program_id = uuid4()
    captured_submit_requests: list[SubmitProgramTurnRequest] = []
    sync_calls: list[tuple[str, UUID]] = []

    class _FakeProgramPersistence:
        def __init__(
            self,
            *,
            resolver,
            actor_id,
            environment_id,
            process_id,
            thread_id,
        ) -> None:
            _ = resolver
            assert actor_id is not None
            assert environment_id is not None
            assert process_id is not None
            assert thread_id is not None

        async def create_or_get_program(self, **kwargs):
            assert kwargs["program_config_id"] == program_config_id
            return persisted_program_id

        async def set_running(self, *, program_id, **kwargs) -> None:
            _ = kwargs
            sync_calls.append(("set_running", program_id))

        async def attach_turn(self, *, program_id, **kwargs) -> None:
            _ = kwargs
            sync_calls.append(("attach_turn", program_id))

        async def finish_terminal(self, *, program_id, **kwargs) -> None:
            _ = kwargs
            sync_calls.append(("finish_terminal", program_id))

    monkeypatch.setattr(
        program_service,
        "ProgramProjectionPersistenceService",
        _FakeProgramPersistence,
    )

    async def _resolve_invocation_plan_from_ontology(
        self,  # noqa: ANN001
        *,
        resolver,  # noqa: ANN001
        request,  # noqa: ANN001
        program_config_id,  # noqa: ANN001
    ) -> dict[str, object]:
        _ = self, resolver, request, program_config_id
        return _invocation_plan_artifact(program_name="HumanConversationMessage_v1")

    monkeypatch.setattr(
        program_service.ExperienceProgramRuntimeService,
        "_resolve_invocation_plan_artifact_from_ontology",
        _resolve_invocation_plan_from_ontology,
    )

    async def _submit(
        resolver,
        request: SubmitProgramTurnRequest,
        *,
        apply_program_ref_op=object(),
        store=None,
    ) -> SubmitProgramTurnResponse:
        _ = apply_program_ref_op, store
        captured_submit_requests.append(request)
        return SubmitProgramTurnResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=None,
            projection_hash=None,
            status="succeeded",
            error=None,
            turn_id=uuid4(),
            mailbox_key=request.mailbox_key,
            deduped=False,
            terminal_status="succeeded",
            result_summary="ok",
            resolved_branch_id=uuid4(),
            resolved_projection_hash="Conversation",
            lane_resolution_source="program_lane_intent",
        )

    service = ExperienceProgramRuntimeService(submit_program_turn_op=_submit)
    resolver = _resolver_stub_for_manifest_lookup()
    request = RunProgramRequest(
        actor_id=actor_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=uuid4(),
        projection_hash="legacy-ignored",
        target_actor_id=target_actor_id,
        program_ref="conversation_default:HumanConversationMessage_v1",
        symbols=JsonObject(
            {
                "plan.program_config_id": str(program_config_id),
                "plan.message_text": "hello",
            }
        ),
        message="hello",
        turn_index=1,
        mailbox_key=None,
        idempotency_key="idem-program",
        max_attempts=1,
        wait_for_terminal=True,
    )

    response = await service.run_program(
        resolver=resolver,
        request=request,
        apply_program_ref_op=object(),
    )

    assert response.operation == "run_program"
    assert response.program_run_id == persisted_program_id
    assert len(captured_submit_requests) == 1
    submit_request = captured_submit_requests[0]
    assert submit_request.branch_id is None
    assert submit_request.projection_hash is None
    assert submit_request.symbols.get("plan.program_id") == str(persisted_program_id)
    assert submit_request.symbols.get("plan.program_run_id") == str(
        persisted_program_id
    )
    assert sync_calls == [
        ("set_running", persisted_program_id),
        ("attach_turn", persisted_program_id),
        ("finish_terminal", persisted_program_id),
    ]


@pytest.mark.asyncio
async def test_run_program_materializes_program_without_lane_resolution_syncs_core_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor_id = uuid4()
    environment_id = uuid4()
    process_id = uuid4()
    thread_id = uuid4()
    target_actor_id = uuid4()
    program_config_id = uuid4()
    persisted_program_id = uuid4()
    captured_submit_requests: list[SubmitProgramTurnRequest] = []
    sync_calls: list[tuple[str, UUID]] = []

    class _FakeProgramPersistence:
        def __init__(
            self,
            *,
            resolver,
            actor_id,
            environment_id,
            process_id,
            thread_id,
        ) -> None:
            _ = resolver, actor_id, environment_id, process_id, thread_id

        async def create_or_get_program(self, **kwargs):
            assert kwargs["program_config_id"] == program_config_id
            return persisted_program_id

        async def set_running(self, *, program_id, **kwargs) -> None:
            _ = kwargs
            sync_calls.append(("set_running", program_id))

        async def attach_turn(self, *, program_id, **kwargs) -> None:
            _ = kwargs
            sync_calls.append(("attach_turn", program_id))

        async def finish_terminal(self, *, program_id, **kwargs) -> None:
            _ = kwargs
            sync_calls.append(("finish_terminal", program_id))

    monkeypatch.setattr(
        program_service,
        "ProgramProjectionPersistenceService",
        _FakeProgramPersistence,
    )

    async def _resolve_invocation_plan_from_ontology(
        self,  # noqa: ANN001
        *,
        resolver,  # noqa: ANN001
        request,  # noqa: ANN001
        program_config_id,  # noqa: ANN001
    ) -> dict[str, object]:
        _ = self, resolver, request, program_config_id
        return _invocation_plan_artifact(program_name="HumanConversationMessage_v1")

    monkeypatch.setattr(
        program_service.ExperienceProgramRuntimeService,
        "_resolve_invocation_plan_artifact_from_ontology",
        _resolve_invocation_plan_from_ontology,
    )

    async def _submit(
        resolver,
        request: SubmitProgramTurnRequest,
        *,
        apply_program_ref_op=object(),
        store=None,
    ) -> SubmitProgramTurnResponse:
        _ = apply_program_ref_op, store
        captured_submit_requests.append(request)
        return SubmitProgramTurnResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=None,
            projection_hash=None,
            status="succeeded",
            error=None,
            turn_id=uuid4(),
            mailbox_key=request.mailbox_key,
            deduped=False,
            terminal_status="succeeded",
            result_summary="ok",
            resolved_branch_id=None,
            resolved_projection_hash=None,
            lane_resolution_source=None,
        )

    service = ExperienceProgramRuntimeService(submit_program_turn_op=_submit)
    resolver = _resolver_stub_for_manifest_lookup()
    request = RunProgramRequest(
        actor_id=actor_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=uuid4(),
        projection_hash="legacy-ignored",
        target_actor_id=target_actor_id,
        program_ref="conversation_default:HumanConversationMessage_v1",
        symbols=JsonObject(
            {
                "plan.program_config_id": str(program_config_id),
                "plan.message_text": "hello",
            }
        ),
        message="hello",
        turn_index=1,
        mailbox_key=None,
        idempotency_key="idem-program-no-lane",
        max_attempts=1,
        wait_for_terminal=True,
    )

    response = await service.run_program(
        resolver=resolver,
        request=request,
        apply_program_ref_op=object(),
    )

    assert response.operation == "run_program"
    assert response.program_run_id == persisted_program_id
    assert len(captured_submit_requests) == 1
    submit_request = captured_submit_requests[0]
    assert submit_request.symbols.get("plan.program_id") == str(persisted_program_id)
    assert sync_calls == [
        ("attach_turn", persisted_program_id),
        ("finish_terminal", persisted_program_id),
    ]


@pytest.mark.asyncio
async def test_run_program_explicit_program_config_requires_thread_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _submit(
        resolver,
        request: SubmitProgramTurnRequest,
        *,
        apply_program_ref_op=object(),
        store=None,
    ) -> SubmitProgramTurnResponse:
        _ = request, apply_program_ref_op, store
        return SubmitProgramTurnResponse(
            actor_id=uuid4(),
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=None,
            projection_hash=None,
            status="accepted",
            error=None,
            turn_id=uuid4(),
            mailbox_key="mailbox:test",
            deduped=False,
        )

    service = ExperienceProgramRuntimeService(submit_program_turn_op=_submit)

    async def _resolve_invocation_plan_from_ontology(
        self,  # noqa: ANN001
        *,
        resolver,  # noqa: ANN001
        request,  # noqa: ANN001
        program_config_id,  # noqa: ANN001
    ) -> dict[str, object]:
        _ = self, resolver, request, program_config_id
        return _invocation_plan_artifact(program_name="HumanConversationMessage_v1")

    monkeypatch.setattr(
        program_service.ExperienceProgramRuntimeService,
        "_resolve_invocation_plan_artifact_from_ontology",
        _resolve_invocation_plan_from_ontology,
    )
    resolver = _resolver_stub_for_manifest_lookup()
    request = RunProgramRequest(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=None,
        branch_id=None,
        projection_hash=None,
        target_actor_id=uuid4(),
        program_ref="conversation_default:HumanConversationMessage_v1",
        symbols=JsonObject(
            {
                "plan.program_config_id": str(uuid4()),
            }
        ),
        message="hello",
        turn_index=1,
        mailbox_key=None,
        idempotency_key="idem-1",
        max_attempts=1,
        wait_for_terminal=False,
    )

    with pytest.raises(
        ValueError,
        match="run_program with explicit plan.program_config_id requires thread_id",
    ):
        await service.run_program(
            resolver=resolver,
            request=request,
            apply_program_ref_op=object(),
        )


@pytest.mark.asyncio
async def test_run_program_requires_program_config_id_symbol() -> None:
    async def _submit(
        resolver,
        request: SubmitProgramTurnRequest,
        *,
        apply_program_ref_op=object(),
        store=None,
    ) -> SubmitProgramTurnResponse:
        _ = request, apply_program_ref_op, store
        raise AssertionError(
            "submit_program_turn should not be called when ontology mapping is missing"
        )

    service = ExperienceProgramRuntimeService(submit_program_turn_op=_submit)
    request = RunProgramRequest(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=None,
        projection_hash=None,
        target_actor_id=uuid4(),
        program_ref="assistance:AssistantRun_v1",
        symbols=JsonObject({}),
        message="hello",
        turn_index=1,
        mailbox_key=None,
        idempotency_key="idem-ontology-required",
        max_attempts=1,
        wait_for_terminal=False,
    )

    with pytest.raises(
        ValueError,
        match="requires ontology-mapped `plan.program_config_id`",
    ):
        await service.run_program(
            resolver=object(),
            request=request,
            apply_program_ref_op=object(),
        )


@pytest.mark.asyncio
async def test_run_program_requires_ontology_invocation_decode_when_program_config_id_present() -> (
    None
):
    async def _submit(
        resolver,
        request: SubmitProgramTurnRequest,
        *,
        apply_program_ref_op=object(),
        store=None,
    ) -> SubmitProgramTurnResponse:
        _ = request, apply_program_ref_op, store
        raise AssertionError(
            "submit_program_turn should not be called when ontology-only gate fails"
        )

    service = ExperienceProgramRuntimeService(submit_program_turn_op=_submit)
    request = RunProgramRequest(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=None,
        projection_hash=None,
        target_actor_id=uuid4(),
        program_ref="assistance:AssistantRun_v1",
        symbols=JsonObject({"plan.program_config_id": str(uuid4())}),
        message="hello",
        turn_index=1,
        mailbox_key=None,
        idempotency_key="idem-ontology-only",
        max_attempts=1,
        wait_for_terminal=False,
    )

    with pytest.raises(
        ValueError,
        match="requires ontology-derived invocation plan artifacts",
    ):
        await service.run_program(
            resolver=object(),
            request=request,
            apply_program_ref_op=object(),
        )


@pytest.mark.asyncio
async def test_run_program_rejects_caller_invocation_plan_artifact_symbol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    program_config_id = uuid4()
    persisted_program_id = uuid4()
    actor_id = uuid4()
    environment_id = uuid4()
    process_id = uuid4()
    thread_id = uuid4()
    target_actor_id = uuid4()
    captured_submit_requests: list[SubmitProgramTurnRequest] = []
    invocation_plan_artifact: dict[str, object] = {
        "schema_version": "aware.program.invocation.v1",
        "content_type": "application/x-aware-program-invocation+json",
        "program_name": "AssistantRun_v1",
        "plan": {"nodes": [], "edges": []},
    }

    class _FakeProgramPersistence:
        def __init__(
            self,
            *,
            resolver,
            actor_id,
            environment_id,
            process_id,
            thread_id,
        ) -> None:
            _ = resolver, actor_id, environment_id, process_id, thread_id

        async def create_or_get_program(self, **kwargs):
            _ = kwargs
            return persisted_program_id

        async def set_running(self, *, program_id, **kwargs) -> None:
            _ = program_id, kwargs

        async def attach_turn(self, *, program_id, **kwargs) -> None:
            _ = program_id, kwargs

        async def finish_terminal(self, *, program_id, **kwargs) -> None:
            _ = program_id, kwargs

    monkeypatch.setattr(
        program_service,
        "ProgramProjectionPersistenceService",
        _FakeProgramPersistence,
    )

    async def _submit(
        resolver,
        request: SubmitProgramTurnRequest,
        *,
        apply_program_ref_op=object(),
        store=None,
    ) -> SubmitProgramTurnResponse:
        _ = apply_program_ref_op, store
        captured_submit_requests.append(request)
        return SubmitProgramTurnResponse(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            branch_id=None,
            projection_hash=None,
            status="accepted",
            error=None,
            turn_id=uuid4(),
            mailbox_key=request.mailbox_key,
            deduped=False,
        )

    service = ExperienceProgramRuntimeService(submit_program_turn_op=_submit)
    request = RunProgramRequest(
        actor_id=actor_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=None,
        projection_hash=None,
        target_actor_id=target_actor_id,
        program_ref="assistance:AssistantRun_v1",
        symbols=JsonObject(
            {
                "plan.program_config_id": str(program_config_id),
                "plan.invocation_plan_artifact": dict(invocation_plan_artifact),
            }
        ),
        message="hello",
        turn_index=1,
        mailbox_key=None,
        idempotency_key="idem-invocation-plan-inject",
        max_attempts=1,
        wait_for_terminal=False,
    )

    with pytest.raises(
        ValueError,
        match="forbids caller-supplied `plan.invocation_plan_artifact`",
    ):
        await service.run_program(
            resolver=object(),
            request=request,
            apply_program_ref_op=object(),
        )
    assert len(captured_submit_requests) == 0
