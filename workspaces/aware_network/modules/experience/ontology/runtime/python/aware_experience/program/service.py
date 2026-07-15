from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
import time
from typing import Any, Protocol, cast
from typing import override
from uuid import UUID

from aware_code.types.json import JsonArray, JsonObject, JsonValue
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
    InvokeFunctionResponse,
)
from aware_experience_service_dto.experience.program.service_operation import (
    ApplyProgramRefRequest,
    ApplyProgramRefResponse,
    RunProgramRequest,
    RunProgramResponse,
    SubmitProgramTurnRequest,
    SubmitProgramTurnResponse,
)
from aware_experience.program.runtime_invocation import (
    ProgramApplyError,
    ProgramContractValidator,
    ProgramIntentRecord,
    ProgramIntentRecorder,
    ProgramRegistryError,
    RuntimeInvocationPlanExecutor,
    load_invocation_plan_from_symbol_payload,
    required_symbols_from_invocation_plan,
    validate_required_symbols,
)

from .contracts import ProgramRunIdentity
from .ontology_decode import resolve_invocation_plan_artifact_from_ontology
from .persistence import ProgramProjectionPersistenceService
from .runtime_support import ocg_support, stable_ids
from .stable_ids import resolve_program_run_id

_PROGRAM_RUN_ID_SYMBOL_KEY = "plan.program_run_id"
_PROGRAM_CONFIG_ID_SYMBOL_KEY = "plan.program_config_id"
_PROGRAM_ID_SYMBOL_KEY = "plan.program_id"
_PROGRAM_KEY_SYMBOL_KEY = "plan.program_key"
_INVOCATION_PLAN_ARTIFACT_SYMBOL_KEY = "plan.invocation_plan_artifact"


class _ConditionEvaluatorProtocol(Protocol):
    async def resolve_bindings_for_event_config_ids(
        self,
        *,
        event_config_ids: set[UUID],
        include_disabled: bool,
        force_refresh: bool,
    ) -> Mapping[UUID, object]: ...


class _ReactivityProgramContractValidator(ProgramContractValidator):
    _condition_evaluator: _ConditionEvaluatorProtocol

    def __init__(self, *, condition_evaluator: _ConditionEvaluatorProtocol) -> None:
        self._condition_evaluator = condition_evaluator

    @override
    async def validate_event_action_contracts(
        self,
        *,
        event_expectations: Mapping[UUID, bool],
        action_intents: Iterable[tuple[UUID, UUID]],
    ) -> None:
        action_intents_list = list(action_intents)
        expected_event_config_ids: set[UUID] = set(event_expectations.keys())
        expected_event_config_ids.update(
            event_config_id for _, event_config_id in action_intents_list
        )
        if not expected_event_config_ids:
            return

        bindings_by_event = (
            await self._condition_evaluator.resolve_bindings_for_event_config_ids(
                event_config_ids=expected_event_config_ids,
                include_disabled=False,
                force_refresh=True,
            )
        )
        bindings_by_event_id: dict[UUID, list[object]] = defaultdict(list)
        for event_config_id, bindings in dict(bindings_by_event).items():
            if bindings is None:
                continue
            if not isinstance(bindings, Iterable):
                raise ProgramApplyError(
                    "Reactivity binding resolution returned non-iterable payload for event_config: "
                    + f"{event_config_id}"
                )
            bindings_by_event_id[event_config_id].extend(list(bindings))

        for event_config_id, required in dict(event_expectations).items():
            if not required:
                continue
            event_bindings = list(bindings_by_event_id.get(event_config_id, []))
            if event_bindings:
                continue
            raise ProgramApplyError(
                "Required expect event_config has no enabled reactivity binding: "
                f"{event_config_id}"
            )

        for action_config_id, event_config_id in action_intents_list:
            event_bindings = list(bindings_by_event_id.get(event_config_id, []))
            event_required = bool(event_expectations.get(event_config_id, True))
            if not event_bindings and not event_required:
                continue
            if not event_bindings and event_required:
                raise ProgramApplyError(
                    "intent references unresolved required event_config: "
                    f"{event_config_id}"
                )

            bound_action_ids: set[UUID] = set()
            for binding in event_bindings:
                action_bindings = list(getattr(binding, "action_bindings", []) or [])
                for action_binding in action_bindings:
                    if not bool(getattr(action_binding, "is_enabled", True)):
                        continue
                    action_id = getattr(action_binding, "action_config_id", None)
                    if isinstance(action_id, UUID):
                        bound_action_ids.add(action_id)
            if action_config_id in bound_action_ids:
                continue
            raise ProgramApplyError(
                "intent action_config is not bound to event_config in reactivity policy: "
                f"action_config_id={action_config_id} event_config_id={event_config_id}"
            )


class _RuntimeProgramIntentRecorder(ProgramIntentRecorder):
    def __init__(
        self,
        *,
        runtime: Any,
        index: Any,
        actor_id: UUID | None,
        environment_id: UUID,
        process_id: UUID,
        thread_id: UUID,
        branch_id: UUID,
    ) -> None:
        self._runtime = runtime
        self._index = index
        self._actor_id = actor_id
        self._environment_id = environment_id
        self._process_id = process_id
        self._thread_id = thread_id
        self._branch_id = branch_id
        self._action_intent_projection_hash = ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="ActionIntent",
        )
        self._program_projection_hash = ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="Program",
        )
        self._action_intent_create_function_id = ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix="aware_reactivity_ontology.action.action_intent.ActionIntent",
            function_name="create_via_event",
        )
        self._record_action_function_id = ocg_support.resolve_public_function_id(
            index=index,
            class_name_suffix="aware_experience_ontology.program.program_turn_instruction.ProgramTurnInstruction",
            function_name="record_action",
        )

    async def record_program_intent(self, record: ProgramIntentRecord) -> None:
        if record.event_id is None:
            raise ProgramApplyError(
                "Program intent recording requires event context: "
                f"plan.intent.{record.step_index}.event_id"
            )

        action_intent_response = await self._invoke_action_intent_constructor(
            record=record,
        )
        self._assert_invoke_succeeded(
            response=action_intent_response,
            label="ActionIntent.create_via_event",
        )
        action_intent_id = self._payload_uuid(
            payload=action_intent_response.payload,
            key="id",
            label="ActionIntent.create_via_event",
        )

        receipt_response = await self._invoke_program_turn_instruction_record_action(
            record=record,
            action_intent_id=action_intent_id,
            branch_id=UUID(str(action_intent_response.branch_id or self._branch_id)),
        )
        self._assert_invoke_succeeded(
            response=receipt_response,
            label="ProgramTurnInstruction.record_action",
        )

    async def _invoke_action_intent_constructor(
        self,
        *,
        record: ProgramIntentRecord,
    ) -> InvokeFunctionResponse:
        opg = self._index.opg_by_hash.get(self._action_intent_projection_hash)
        if opg is None:
            raise ProgramApplyError(
                "Program intent recording could not resolve ActionIntent OPG: "
                + self._action_intent_projection_hash
            )
        request = InvokeFunctionRequest(
            operation="invoke_function",
            actor_id=self._actor_id,
            environment_id=self._environment_id,
            process_id=self._process_id,
            thread_id=self._thread_id,
            branch_id=self._branch_id,
            projection_hash=self._action_intent_projection_hash,
            call_target=InvokeFunctionCallTarget.opg_constructor,
            object_id=None,
            object_projection_graph_id=opg.id,
            function_id=self._action_intent_create_function_id,
            args=JsonArray(
                [
                    str(record.event_id) if record.event_id is not None else None,
                    str(record.action_config_id),
                    record.intent_key,
                ]
            ),
            kwargs=JsonObject({}),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=True,
            publish=False,
        )
        return await self._runtime.invoker.invoke_function_with_index(
            index=self._index,
            request=request,
        )

    async def _invoke_program_turn_instruction_record_action(
        self,
        *,
        record: ProgramIntentRecord,
        action_intent_id: UUID,
        branch_id: UUID,
    ) -> InvokeFunctionResponse:
        request = InvokeFunctionRequest(
            operation="invoke_function",
            actor_id=self._actor_id,
            environment_id=self._environment_id,
            process_id=self._process_id,
            thread_id=self._thread_id,
            branch_id=branch_id,
            projection_hash=self._program_projection_hash,
            call_target=InvokeFunctionCallTarget.instance,
            object_id=record.program_turn_instruction_id,
            object_projection_graph_id=None,
            function_id=self._record_action_function_id,
            args=JsonArray(
                [
                    str(record.program_impl_instruction_intent_id),
                    str(record.action_config_id),
                    str(record.event_config_id),
                    str(action_intent_id),
                    record.intent_key,
                ]
            ),
            kwargs=JsonObject({}),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=True,
            publish=False,
        )
        return await self._runtime.invoker.invoke_function_with_index(
            index=self._index,
            request=request,
        )

    @staticmethod
    def _assert_invoke_succeeded(
        *,
        response: InvokeFunctionResponse,
        label: str,
    ) -> None:
        if response.status == "succeeded":
            return
        if response.error:
            raise ProgramApplyError(f"{label} failed: {response.error}")
        raise ProgramApplyError(f"{label} failed")

    @staticmethod
    def _payload_uuid(*, payload: object, key: str, label: str) -> UUID:
        if not isinstance(payload, Mapping):
            raise ProgramApplyError(f"{label} returned non-object payload")
        value = payload.get(key)
        if value is None:
            raise ProgramApplyError(f"{label} payload missing {key!r}")
        return UUID(str(value))


class SubmitProgramTurnOperation(Protocol):
    async def __call__(
        self,
        resolver: Any,
        request: SubmitProgramTurnRequest,
        *,
        apply_program_ref_op: object = ...,
        store: Any | None = None,
    ) -> SubmitProgramTurnResponse: ...


def _plan_declares_intent(*, plan: Any) -> bool:
    return any(
        step.__class__.__name__ == "PlanIntentActionConfig" for step in plan.steps
    )


def _plan_requires_contract_validation(*, plan: Any) -> bool:
    return any(
        step.__class__.__name__ in {"PlanExpectEventConfig", "PlanIntentActionConfig"}
        for step in plan.steps
    )


class ExperienceProgramRuntimeService:
    """Experience-owned program boundary.

    Program-first contract:
    - callers execute `run_program`
    - Experience materializes one `program_run_id`
    - Experience delegates turn lifecycle internals to submit-turn rails
    """

    _submit_program_turn_op: SubmitProgramTurnOperation

    def __init__(self, *, submit_program_turn_op: SubmitProgramTurnOperation) -> None:
        self._submit_program_turn_op = submit_program_turn_op

    async def apply_program_ref(
        self,
        resolver: Any,
        request: ApplyProgramRefRequest,
    ) -> ApplyProgramRefResponse:
        lane_resolution_source = "plan.lane"
        resolved_branch_id = None
        resolved_projection_hash = None
        executor: RuntimeInvocationPlanExecutor | None = None
        try:
            if request.actor_id is None:
                raise ValueError("actor_id is required for apply_program_ref")
            if request.thread_id is None:
                raise ValueError("thread_id is required for apply_program_ref")

            manifest_path, _manifest = await resolver.get_manifest()

            symbols = dict(getattr(request, "symbols", None) or {})
            invocation_plan_symbol = symbols.get("plan.invocation_plan_artifact")
            if invocation_plan_symbol is None:
                raise ProgramApplyError(
                    "apply_program_ref requires symbols.plan.invocation_plan_artifact; "
                    + "manifest/registry fallback is removed on ontology-only rail"
                )

            plan = load_invocation_plan_from_symbol_payload(
                symbol_value=invocation_plan_symbol,
                program_ref=request.program_ref,
            )
            validate_required_symbols(
                required_symbols=required_symbols_from_invocation_plan(plan=plan),
                provided_symbols=symbols,
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                program_ref=request.program_ref,
                context="apply_program_ref",
            )

            runtime = await resolver.get_runtime(environment_id=request.environment_id)
            index = runtime.invoker.get_index()
            contract_validator = None
            if _plan_requires_contract_validation(plan=plan):
                from aware_reactivity.condition.evaluator import (
                    LaneMaterializedConditionEvaluator,
                )

                contract_validator = _ReactivityProgramContractValidator(
                    condition_evaluator=LaneMaterializedConditionEvaluator(
                        manifest_path=str(manifest_path),
                        invoker=runtime.invoker,
                    )
                )
            validate_only = bool(getattr(request, "validate_only", False))
            process_id = request.process_id or stable_ids.stable_boot_process_id(
                environment_id=request.environment_id,
            )
            branch_id = request.branch_id or stable_ids.stable_branch_id(
                environment_id=request.environment_id,
                thread_id=request.thread_id,
            )
            intent_recorder = None
            if not validate_only and _plan_declares_intent(plan=plan):
                intent_recorder = _RuntimeProgramIntentRecorder(
                    runtime=runtime,
                    index=index,
                    actor_id=request.actor_id,
                    environment_id=request.environment_id,
                    process_id=process_id,
                    thread_id=request.thread_id,
                    branch_id=branch_id,
                )
            executor = RuntimeInvocationPlanExecutor(
                invoker=runtime.invoker,
                index=index,
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=process_id,
                thread_id=request.thread_id,
                commit=bool(getattr(request, "commit", True)),
                publish=bool(getattr(request, "publish", False)),
                symbols=symbols,
                program_ref_stack=(request.program_ref,),
                contract_validator=contract_validator,
                intent_recorder=intent_recorder,
            )

            results = await executor.execute(
                plan,
                symbols=symbols,
                validate_only=validate_only,
            )
            resolved_lane = executor.resolved_lane()
            if resolved_lane is not None:
                resolved_branch_id, resolved_projection_hash = resolved_lane

            return ApplyProgramRefResponse(
                operation="apply_program_ref",
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="succeeded",
                error=None,
                program_ref=request.program_ref,
                results=JsonArray(results),
                resolved_branch_id=resolved_branch_id,
                resolved_projection_hash=resolved_projection_hash,
                lane_resolution_source=lane_resolution_source,
            )

        except (ProgramRegistryError, ProgramApplyError, ValueError) as exc:
            if executor is not None:
                resolved_lane = executor.resolved_lane()
                if resolved_lane is not None:
                    resolved_branch_id, resolved_projection_hash = resolved_lane
            return ApplyProgramRefResponse(
                operation="apply_program_ref",
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="failed",
                error=str(exc),
                program_ref=request.program_ref,
                results=JsonArray([]),
                resolved_branch_id=resolved_branch_id,
                resolved_projection_hash=resolved_projection_hash,
                lane_resolution_source=lane_resolution_source,
            )

    async def run_program(
        self,
        resolver: Any,
        request: RunProgramRequest | SubmitProgramTurnRequest,
        *,
        apply_program_ref_op: object,
        store: Any | None = None,
    ) -> RunProgramResponse | SubmitProgramTurnResponse:
        if isinstance(request, SubmitProgramTurnRequest):
            return await self._submit_program_turn_op(
                resolver,
                request,
                apply_program_ref_op=apply_program_ref_op,
                store=store,
            )

        run_identity = self._materialize_run_identity(request=request)
        injected_symbols = await self._resolve_submit_symbol_injections(
            resolver=resolver,
            request=request,
        )
        (
            program_persistence,
            materialized_program_id,
        ) = await self._materialize_program_if_explicit(
            resolver=resolver,
            request=request,
            run_identity=run_identity,
        )
        if materialized_program_id is not None:
            run_identity = ProgramRunIdentity(
                program_run_id=materialized_program_id,
                mailbox_key=run_identity.mailbox_key,
                program_id=materialized_program_id,
            )
        submit_request = self._build_submit_request_for_run(
            request=request,
            run_identity=run_identity,
            injected_symbols=injected_symbols,
        )
        submit_response = await self._submit_program_turn_op(
            resolver,
            submit_request,
            apply_program_ref_op=apply_program_ref_op,
            store=store,
        )
        if run_identity.program_id is not None and program_persistence is not None:
            await self._sync_program_lifecycle_after_turn(
                persistence=program_persistence,
                run_identity=run_identity,
                submit_response=submit_response,
            )
        return RunProgramResponse(
            operation="run_program",
            actor_id=submit_response.actor_id,
            environment_id=submit_response.environment_id,
            process_id=submit_response.process_id,
            thread_id=submit_response.thread_id,
            branch_id=submit_response.branch_id,
            projection_hash=submit_response.projection_hash,
            status=submit_response.status,
            error=submit_response.error,
            program_ref=request.program_ref,
            program_run_id=run_identity.program_run_id,
            turn_id=submit_response.turn_id,
            mailbox_key=submit_response.mailbox_key,
            deduped=submit_response.deduped,
            terminal_status=submit_response.terminal_status,
            result_summary=submit_response.result_summary,
            feedback_count=submit_response.feedback_count,
            resolved_branch_id=submit_response.resolved_branch_id,
            resolved_projection_hash=submit_response.resolved_projection_hash,
            lane_resolution_source=submit_response.lane_resolution_source,
        )

    def _materialize_run_identity(
        self, *, request: RunProgramRequest
    ) -> ProgramRunIdentity:
        mailbox_key = self._resolve_mailbox_key_for_run_program(request=request)
        return ProgramRunIdentity(
            program_run_id=resolve_program_run_id(
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                target_actor_id=request.target_actor_id,
                program_ref=request.program_ref,
                mailbox_key=mailbox_key,
                idempotency_key=request.idempotency_key,
            ),
            mailbox_key=mailbox_key,
        )

    @staticmethod
    def _resolve_mailbox_key_for_run_program(*, request: RunProgramRequest) -> str:
        explicit_mailbox_key = str(request.mailbox_key or "").strip()
        if explicit_mailbox_key:
            return explicit_mailbox_key
        return f"{request.environment_id}:{request.target_actor_id}"

    @staticmethod
    def _build_submit_request_for_run(
        *,
        request: RunProgramRequest,
        run_identity: ProgramRunIdentity,
        injected_symbols: Mapping[str, object] | None = None,
    ) -> SubmitProgramTurnRequest:
        symbols: dict[str, object] = dict(request.symbols or {})
        if injected_symbols:
            symbols.update(injected_symbols)
        symbols[_PROGRAM_RUN_ID_SYMBOL_KEY] = str(run_identity.program_run_id)
        if run_identity.program_id is not None:
            symbols[_PROGRAM_ID_SYMBOL_KEY] = str(run_identity.program_id)
        symbols_json = JsonObject()
        for symbol_key, symbol_value in symbols.items():
            symbols_json[symbol_key] = cast(JsonValue, symbol_value)
        return SubmitProgramTurnRequest(
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
            # submit_program_turn lane context is owned by the Experience run
            # service and fail-closed; request-level lane metadata is omitted.
            branch_id=None,
            projection_hash=None,
            target_actor_id=request.target_actor_id,
            program_ref=request.program_ref,
            symbols=symbols_json,
            message=request.message,
            turn_index=request.turn_index,
            mailbox_key=run_identity.mailbox_key,
            idempotency_key=request.idempotency_key,
            max_attempts=request.max_attempts,
            input_received_unix_ms=request.input_received_unix_ms,
            turn_accepted_unix_ms=request.turn_accepted_unix_ms,
            wait_for_terminal=request.wait_for_terminal,
            wait_timeout_ms=request.wait_timeout_ms,
        )

    async def _materialize_program_if_explicit(
        self,
        *,
        resolver: Any,
        request: RunProgramRequest,
        run_identity: ProgramRunIdentity,
    ) -> tuple[ProgramProjectionPersistenceService | None, UUID | None]:
        symbols: dict[str, object] = dict(request.symbols or {})
        program_config_id = self._coerce_uuid_symbol_or_none(
            symbols=symbols,
            key=_PROGRAM_CONFIG_ID_SYMBOL_KEY,
        )
        if program_config_id is None:
            return None, None

        if request.thread_id is None:
            raise ValueError(
                "run_program with explicit plan.program_config_id requires thread_id"
            )
        persistence = ProgramProjectionPersistenceService(
            resolver=resolver,
            actor_id=request.actor_id,
            environment_id=request.environment_id,
            process_id=request.process_id,
            thread_id=request.thread_id,
        )
        program_key = self._resolve_program_key(
            request=request,
            run_identity=run_identity,
            symbols=symbols,
        )
        program_id = await persistence.create_or_get_program(
            program_config_id=program_config_id,
            key=program_key,
            title=None,
            description=None,
            resolved_branch_id=None,
            resolved_projection_hash=None,
            position=None,
            is_default=False,
        )
        return persistence, program_id

    async def _sync_program_lifecycle_after_turn(
        self,
        *,
        persistence: ProgramProjectionPersistenceService,
        run_identity: ProgramRunIdentity,
        submit_response: SubmitProgramTurnResponse,
    ) -> None:
        program_id = run_identity.program_id
        if program_id is None:
            return

        resolved_projection_hash = str(
            submit_response.resolved_projection_hash or ""
        ).strip()
        resolved_branch_id = submit_response.resolved_branch_id
        if resolved_branch_id is not None and resolved_projection_hash:
            await persistence.set_running(
                program_id=program_id,
                resolved_branch_id=resolved_branch_id,
                resolved_projection_hash=resolved_projection_hash,
                started_at_unix_ms=int(time.time() * 1000),
            )

        turn_id = submit_response.turn_id
        if turn_id is not None:
            await persistence.attach_turn(program_id=program_id, turn_id=turn_id)

        terminal_status = str(submit_response.terminal_status or "")
        terminal_status = terminal_status.strip()
        if terminal_status:
            await persistence.finish_terminal(
                program_id=program_id,
                terminal_at_unix_ms=int(time.time() * 1000),
                terminal_status=terminal_status,
                result_summary=(
                    str(submit_response.result_summary or "").strip() or None
                ),
            )

    async def _resolve_submit_symbol_injections(
        self,
        *,
        resolver: Any,
        request: RunProgramRequest,
    ) -> dict[str, object]:
        symbols = dict(request.symbols or {})
        program_config_id = self._coerce_uuid_symbol_or_none(
            symbols=symbols,
            key=_PROGRAM_CONFIG_ID_SYMBOL_KEY,
        )
        if program_config_id is None:
            raise ValueError(
                "run_program requires ontology-mapped `plan.program_config_id`; "
                + "ref-only program execution is not allowed on this rail"
            )

        if _INVOCATION_PLAN_ARTIFACT_SYMBOL_KEY in symbols:
            raise ValueError(
                "run_program forbids caller-supplied `plan.invocation_plan_artifact`; "
                + "invocation artifacts must be derived from ontology at runtime"
            )

        invocation_plan_artifact = (
            await self._resolve_invocation_plan_artifact_from_ontology(
                resolver=resolver,
                request=request,
                program_config_id=program_config_id,
            )
        )
        return {_INVOCATION_PLAN_ARTIFACT_SYMBOL_KEY: invocation_plan_artifact}

    async def _resolve_invocation_plan_artifact_from_ontology(
        self,
        *,
        resolver: Any,
        request: RunProgramRequest,
        program_config_id: UUID,
    ) -> dict[str, object]:
        request_symbols = dict(request.symbols or {})
        program_id = self._coerce_uuid_symbol_or_none(
            symbols=request_symbols,
            key=_PROGRAM_ID_SYMBOL_KEY,
        )
        try:
            return await resolve_invocation_plan_artifact_from_ontology(
                resolver=resolver,
                environment_id=request.environment_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                program_config_id=program_config_id,
                program_ref=request.program_ref,
                program_id=program_id,
            )
        except Exception as exc:  # noqa: BLE001
            raise ValueError(
                "run_program requires ontology-derived invocation plan artifacts; "
                + str(exc)
            ) from exc

    @staticmethod
    def _resolve_program_key(
        *,
        request: RunProgramRequest,
        run_identity: ProgramRunIdentity,
        symbols: Mapping[str, object],
    ) -> str:
        explicit_key = ExperienceProgramRuntimeService._coerce_string_symbol_or_none(
            symbols=symbols,
            key=_PROGRAM_KEY_SYMBOL_KEY,
        )
        if explicit_key is not None:
            return explicit_key
        normalized_idempotency_key = str(request.idempotency_key or "")
        normalized_idempotency_key = normalized_idempotency_key.strip()
        if normalized_idempotency_key:
            return f"idem:{normalized_idempotency_key}"
        return str(run_identity.program_run_id)

    @staticmethod
    def _extract_wrapped_value(raw: object) -> object:
        if not isinstance(raw, Mapping):
            return raw
        mapping = cast(Mapping[object, object], raw)
        if "value" in mapping:
            return mapping["value"]
        return mapping

    @staticmethod
    def _coerce_string_symbol_or_none(
        *,
        symbols: Mapping[str, object],
        key: str,
    ) -> str | None:
        raw = ExperienceProgramRuntimeService._extract_wrapped_value(symbols.get(key))
        text = str(raw or "").strip()
        return text or None

    @staticmethod
    def _coerce_uuid_symbol_or_none(
        *,
        symbols: Mapping[str, object],
        key: str,
    ) -> UUID | None:
        raw = ExperienceProgramRuntimeService._extract_wrapped_value(symbols.get(key))
        if raw is None:
            return None
        if isinstance(raw, UUID):
            return raw
        text = str(raw).strip()
        if not text:
            return None
        try:
            return UUID(text)
        except Exception:  # noqa: BLE001
            return None
