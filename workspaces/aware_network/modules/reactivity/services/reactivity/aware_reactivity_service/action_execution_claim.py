from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

from aware_code.types import JsonArray, JsonObject
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
    InvokeFunctionResponse,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_reactivity.stable_ids import (
    stable_action_execution_id,
    stable_action_intent_id,
    stable_event_id,
)
from aware_reactivity_service_dto.reactivity.action_execution import (
    ActionExecution,
    ReactivityActionExecutionClaimRequest,
    ReactivityActionExecutionClaimResponse,
)
from aware_reactivity_service_dto.reactivity.action_feedback_enums import (
    ActionExecutionClaimStatus,
    ActionExecutionStatus,
    ActionIntentStatus,
)
from aware_service_runtime.api_ingress.host_context import (
    ServiceApiHostContext,
    current_service_api_host_context,
)
from aware_service_runtime.api_ingress.ontology_replica_orm_context import (
    current_service_ontology_replica_orm_session,
)
from aware_service_runtime.contracts import ServiceGraphGateway

_EVENT_PROJECTION_NAME = "Event"
_ACTION_INTENT_PROJECTION_NAME = "ActionIntent"
_EVENT_CLASS_FQN = "aware_reactivity_ontology.event.event.Event"
_ACTION_INTENT_CLASS_FQN = "aware_reactivity_ontology.action.action_intent.ActionIntent"
_TERMINAL_STATUSES = frozenset(
    {
        ActionExecutionStatus.canceled,
        ActionExecutionStatus.failed,
        ActionExecutionStatus.rejected,
        ActionExecutionStatus.succeeded,
        ActionExecutionStatus.timed_out,
    }
)


@dataclass(frozen=True, slots=True)
class _ClaimRuntimeContext:
    graph_gateway: ServiceGraphGateway
    runtime_index: MetaGraphRuntimeIndex
    event_projection_id: UUID
    event_projection_hash: str
    action_intent_projection_hash: str
    event_create_function_id: UUID
    event_add_action_intent_function_id: UUID
    action_intent_start_execution_function_id: UUID


async def claim_action_execution(
    request: ReactivityActionExecutionClaimRequest,
    *,
    lock: asyncio.Lock,
) -> ReactivityActionExecutionClaimResponse:
    error = _validate_request(request)
    if error is not None:
        return _rejected(request=request, error=error)

    intent = request.intent
    action_config_id = cast(UUID, intent.action_config_id)
    action_execution_id = stable_action_execution_id(
        action_intent_id=intent.action_intent_id,
        execution_key=request.execution_key,
    )
    async with lock:
        existing = await _load_action_execution(action_execution_id)
        if existing is not None:
            return _existing_response(
                request=request,
                execution=existing,
                action_execution_id=action_execution_id,
            )

        try:
            runtime = await _resolve_runtime_context()
            event_response = await _invoke_constructor(
                runtime=runtime,
                branch_id=intent.event_id,
                projection_hash=runtime.event_projection_hash,
                object_projection_graph_id=runtime.event_projection_id,
                function_id=runtime.event_create_function_id,
                kwargs={
                    "config_id": str(intent.event_config_id),
                    "activation_id": str(intent.activation_id),
                    "event_type": intent.event_type,
                    "source": intent.source,
                },
            )
            intent_response = await _invoke_instance(
                runtime=runtime,
                branch_id=intent.event_id,
                projection_hash=runtime.event_projection_hash,
                object_id=intent.event_id,
                function_id=runtime.event_add_action_intent_function_id,
                kwargs={
                    "config_id": str(action_config_id),
                    "intent_key": intent.intent_key,
                    "action_type": intent.action_type,
                    "actor_id": _uuid_text(intent.actor_id),
                    "target_actor_id": _uuid_text(intent.target_actor_id),
                    "actor_subscription_id": _uuid_text(intent.actor_subscription_id),
                    "action_payload": {},
                    "subscription_filter_config": _json_object_value(
                        intent.subscription_filter_config
                    ),
                    "priority": intent.subscription_priority,
                    "status": ActionIntentStatus.requested.value,
                },
            )
            execution_response = await _invoke_instance(
                runtime=runtime,
                branch_id=intent.action_intent_id,
                projection_hash=runtime.action_intent_projection_hash,
                object_id=intent.action_intent_id,
                function_id=runtime.action_intent_start_execution_function_id,
                kwargs={
                    "execution_key": request.execution_key,
                    "status": ActionExecutionStatus.created.value,
                    "execution_context": dict(request.execution_context),
                },
            )
        except (RuntimeError, ValueError) as exc:
            return _rejected(request=request, error=str(exc))

        return ReactivityActionExecutionClaimResponse(
            request_id=request.request_id,
            accepted=True,
            claim_status=ActionExecutionClaimStatus.claimed,
            action_execution=_execution_dto(
                request=request,
                action_execution_id=action_execution_id,
                status=ActionExecutionStatus.created,
                executor_ref=request.claimant_id,
            ),
            event_commit_id=_commit_id(event_response),
            action_intent_commit_id=_commit_id(intent_response),
            action_execution_commit_id=_commit_id(execution_response),
            info="canonical ActionExecution claimed",
        )


def _validate_request(request: ReactivityActionExecutionClaimRequest) -> str | None:
    claimant_id = request.claimant_id.strip()
    if not claimant_id:
        return "claimant_id is required"
    execution_key = request.execution_key.strip()
    if not execution_key:
        return "execution_key is required"
    intent = request.intent
    if intent.status is not ActionIntentStatus.requested:
        return "ActionExecution claim requires requested ActionIntent status"
    if intent.action_config_id is None:
        return "ActionExecution claim requires action_config_id"
    if intent.object_instance_graph_id is None:
        return "ActionExecution claim requires object_instance_graph_id"
    if intent.object_instance_graph_commit_id is None:
        return "ActionExecution claim requires object_instance_graph_commit_id"
    if intent.object_instance_graph_branch_id is None:
        return "ActionExecution claim requires object_instance_graph_branch_id"
    expected_event_id = stable_event_id(
        config_id=intent.event_config_id,
        activation_id=intent.activation_id,
    )
    if intent.event_id != expected_event_id:
        return "ActionExecution claim event identity mismatch"
    expected_intent_id = stable_action_intent_id(
        event_id=intent.event_id,
        config_id=intent.action_config_id,
        intent_key=intent.intent_key,
    )
    if intent.action_intent_id != expected_intent_id:
        return "ActionExecution claim intent identity mismatch"
    return None


async def _resolve_runtime_context() -> _ClaimRuntimeContext:
    host_context = current_service_api_host_context()
    if host_context is None:
        raise RuntimeError(
            "Reactivity ActionExecution claim requires Service API host context."
        )
    if host_context.graph_gateway is None:
        raise RuntimeError(
            "Reactivity ActionExecution claim requires Service graph gateway."
        )
    if current_service_ontology_replica_orm_session() is None:
        raise RuntimeError(
            "Reactivity ActionExecution claim requires Service ontology replica."
        )
    runtime_index = await _resolve_runtime_index(
        host_context=host_context,
        graph_gateway=host_context.graph_gateway,
    )
    event_projection = _require_projection(runtime_index, _EVENT_PROJECTION_NAME)
    action_intent_projection = _require_projection(
        runtime_index, _ACTION_INTENT_PROJECTION_NAME
    )
    event_class = _require_class(runtime_index, _EVENT_CLASS_FQN)
    action_intent_class = _require_class(runtime_index, _ACTION_INTENT_CLASS_FQN)
    return _ClaimRuntimeContext(
        graph_gateway=host_context.graph_gateway,
        runtime_index=runtime_index,
        event_projection_id=_required_uuid(event_projection, "Event projection"),
        event_projection_hash=_projection_hash(event_projection, "Event"),
        action_intent_projection_hash=_projection_hash(
            action_intent_projection, "ActionIntent"
        ),
        event_create_function_id=_require_function(event_class, "create"),
        event_add_action_intent_function_id=_require_function(
            event_class, "add_action_intent"
        ),
        action_intent_start_execution_function_id=_require_function(
            action_intent_class, "start_execution"
        ),
    )


async def _resolve_runtime_index(
    *,
    host_context: ServiceApiHostContext,
    graph_gateway: object,
) -> MetaGraphRuntimeIndex:
    if host_context.materialization is not None:
        graph_context = host_context.materialization.graph_context
    elif host_context.graph_context_provider is not None:
        graph_context = (
            await host_context.graph_context_provider.resolve_graph_context()
        )
    else:
        resolve_graph_context = getattr(graph_gateway, "resolve_graph_context", None)
        if not callable(resolve_graph_context):
            raise RuntimeError(
                "Reactivity ActionExecution claim requires Service graph context."
            )
        graph_context = await cast(Any, resolve_graph_context)()
    return cast(MetaGraphRuntimeIndex, getattr(graph_context, "index", graph_context))


async def _invoke_constructor(
    *,
    runtime: _ClaimRuntimeContext,
    branch_id: UUID,
    projection_hash: str,
    object_projection_graph_id: UUID,
    function_id: UUID,
    kwargs: dict[str, object],
) -> InvokeFunctionResponse:
    return await _invoke(
        runtime=runtime,
        branch_id=branch_id,
        projection_hash=projection_hash,
        call_target=InvokeFunctionCallTarget.opg_constructor,
        object_projection_graph_id=object_projection_graph_id,
        object_id=None,
        function_id=function_id,
        kwargs=kwargs,
    )


async def _invoke_instance(
    *,
    runtime: _ClaimRuntimeContext,
    branch_id: UUID,
    projection_hash: str,
    object_id: UUID,
    function_id: UUID,
    kwargs: dict[str, object],
) -> InvokeFunctionResponse:
    return await _invoke(
        runtime=runtime,
        branch_id=branch_id,
        projection_hash=projection_hash,
        call_target=InvokeFunctionCallTarget.instance,
        object_projection_graph_id=None,
        object_id=object_id,
        function_id=function_id,
        kwargs=kwargs,
    )


async def _invoke(
    *,
    runtime: _ClaimRuntimeContext,
    branch_id: UUID,
    projection_hash: str,
    call_target: InvokeFunctionCallTarget,
    object_projection_graph_id: UUID | None,
    object_id: UUID | None,
    function_id: UUID,
    kwargs: dict[str, object],
) -> InvokeFunctionResponse:
    host_context = cast(ServiceApiHostContext, current_service_api_host_context())
    environment = host_context.environment_context
    if environment is None:
        raise RuntimeError(
            "Reactivity ActionExecution claim requires Environment operation context."
        )
    response = await runtime.graph_gateway.invoke_function(
        request=cast(
            Any,
            InvokeFunctionRequest(
                actor_id=host_context.operation_context.actor_id,
                environment_id=environment.environment_id,
                process_id=environment.process_id,
                thread_id=environment.thread_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                call_target=call_target,
                object_projection_graph_id=object_projection_graph_id,
                object_id=object_id,
                function_id=function_id,
                args=cast(JsonArray, []),
                kwargs=cast(JsonObject, kwargs),
                expected_graph_hash_pre=None,
                expected_head_commit_id=None,
                commit=True,
                publish=False,
            ),
        ),
        graph_context=runtime.runtime_index,
    )
    if (response.status or "").strip().casefold() != "succeeded":
        raise RuntimeError(
            "Reactivity ActionExecution claim ontology invocation failed: "
            f"status={response.status!r} error={response.error!r}"
        )
    return cast(InvokeFunctionResponse, cast(object, response))


async def _load_action_execution(action_execution_id: UUID) -> object | None:
    if current_service_ontology_replica_orm_session() is None:
        return None
    try:
        from aware_reactivity_ontology_orm_models.action.action_execution import (
            ActionExecution as ActionExecutionOrmModel,
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Reactivity ActionExecution claim requires generated ontology ORM models."
        ) from exc
    return await ActionExecutionOrmModel.by_id(action_execution_id)


def _existing_response(
    *,
    request: ReactivityActionExecutionClaimRequest,
    execution: object,
    action_execution_id: UUID,
) -> ReactivityActionExecutionClaimResponse:
    status = ActionExecutionStatus(
        str(
            getattr(getattr(execution, "status", None), "value", None)
            or getattr(execution, "status", "created")
        )
    )
    claim_status = (
        ActionExecutionClaimStatus.already_terminal
        if status in _TERMINAL_STATUSES
        else ActionExecutionClaimStatus.already_running
    )
    return ReactivityActionExecutionClaimResponse(
        request_id=request.request_id,
        accepted=True,
        claim_status=claim_status,
        action_execution=_execution_dto(
            request=request,
            action_execution_id=action_execution_id,
            status=status,
            executor_ref=getattr(execution, "executor_ref", None),
            result_info=getattr(execution, "result_info", None),
        ),
        info="canonical ActionExecution already exists",
    )


def _execution_dto(
    *,
    request: ReactivityActionExecutionClaimRequest,
    action_execution_id: UUID,
    status: ActionExecutionStatus,
    executor_ref: str | None,
    result_info: str | None = None,
) -> ActionExecution:
    intent = request.intent
    return ActionExecution(
        action_execution_id=action_execution_id,
        action_intent_id=intent.action_intent_id,
        event_id=intent.event_id,
        event_type=intent.event_type,
        source=intent.source,
        branch_id=intent.branch_id,
        projection_hash=intent.projection_hash,
        commit_id=intent.commit_id,
        event_config_condition_config_id=(intent.event_config_condition_config_id),
        action_config_id=intent.action_config_id,
        action_type=intent.action_type,
        root_object_id=intent.root_object_id,
        object_instance_graph_id=intent.object_instance_graph_id,
        graph_hash_post=intent.graph_hash_post,
        execution_key=request.execution_key,
        status=status,
        execution_context=dict(request.execution_context),
        executor_ref=executor_ref,
        result_info=result_info,
    )


def _rejected(
    *, request: ReactivityActionExecutionClaimRequest, error: str
) -> ReactivityActionExecutionClaimResponse:
    return ReactivityActionExecutionClaimResponse(
        request_id=request.request_id,
        accepted=False,
        error=error,
    )


def _require_projection(index: MetaGraphRuntimeIndex, name: str) -> object:
    matches = [
        projection
        for projection in getattr(
            getattr(index, "ocg", None), "object_projection_graphs", []
        )
        or []
        if str(getattr(projection, "name", "") or "").strip() == name
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Reactivity projection {name!r} must resolve exactly once; found {len(matches)}."
        )
    return matches[0]


def _require_class(index: MetaGraphRuntimeIndex, fqn: str) -> object:
    matches = [
        config
        for config in getattr(index, "class_configs_by_id", {}).values()
        if str(getattr(config, "fqn", None) or getattr(config, "class_fqn", "")) == fqn
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Reactivity class {fqn!r} must resolve exactly once; found {len(matches)}."
        )
    return matches[0]


def _require_function(class_config: object, name: str) -> UUID:
    matches = [
        function.id
        for link in getattr(class_config, "class_config_function_configs", []) or []
        for function in [getattr(link, "function_config", None)]
        if function is not None
        and str(getattr(function, "name", "") or "").strip() == name
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Reactivity function {name!r} must resolve exactly once; found {len(matches)}."
        )
    return cast(UUID, matches[0])


def _required_uuid(value: object, label: str) -> UUID:
    candidate = getattr(value, "id", None)
    if not isinstance(candidate, UUID):
        raise ValueError(f"{label} requires UUID identity.")
    return candidate


def _projection_hash(value: object, label: str) -> str:
    candidate = str(getattr(value, "projection_hash", "") or "").strip()
    if not candidate:
        raise ValueError(f"{label} projection requires projection hash.")
    return candidate


def _commit_id(response: InvokeFunctionResponse) -> UUID | None:
    return response.commit_id or response.object_instance_graph_commit_id


def _uuid_text(value: UUID | None) -> str | None:
    return None if value is None else str(value)


def _json_object_value(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


__all__ = ["claim_action_execution"]
