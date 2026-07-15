from __future__ import annotations

import asyncio
from dataclasses import dataclass
import time
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.types.json import JsonArray, JsonObject
from aware_meta.receipts.notifications import LaneCommitReceiptNotification
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_identity_id,
)
from aware_meta.receipts.notifications import (
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
)
from aware_reactivity_service_dto.reactivity.event_condition_binding_resolution import (
    EventConditionBindingResolution,
)
from aware_reactivity.stable_ids import (
    stable_action_id,
    stable_condition_id,
    stable_event_condition_id,
    stable_event_id,
)
from aware_meta.runtime.author import SYSTEM_ACTOR_ID
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_utils.logging import logger


class _InvokeFunctionResponse(Protocol):
    status: str
    error: str | None


class _EvidenceFunctionInvoker(Protocol):
    async def ensure_index(self) -> None: ...

    def get_index(self) -> MetaGraphRuntimeIndex: ...

    async def invoke_function_with_index(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        request: InvokeFunctionRequest,
    ) -> _InvokeFunctionResponse: ...


def _build_function_call_invoker(
    *,
    manifest_path: str | None,
) -> _EvidenceFunctionInvoker:
    _ = manifest_path
    raise RuntimeError(
        "LaneReactivityEvidenceWriter requires an explicit Meta runtime "
        "invoker. The deprecated FunctionCallInvoker fallback has been "
        "removed from Reactivity."
    )


def _resolve_projection_by_name(
    *, index: MetaGraphRuntimeIndex, projection_name: str
):  # noqa: ANN001
    wanted = projection_name.strip()
    return next(
        (
            opg
            for opg in index.ocg.object_projection_graphs
            if (opg.name or "").strip() == wanted
        ),
        None,
    )


def _resolve_class_function_id(
    *,
    index: MetaGraphRuntimeIndex,
    opg,  # noqa: ANN001
    class_name: str,
    function_name: str,
) -> UUID | None:
    class_config_id: UUID | None = None
    for node in opg.object_projection_graph_nodes:
        class_config = index.class_configs_by_id.get(node.class_config_id)
        if class_config is None:
            continue
        if (class_config.name or "").strip() == class_name:
            class_config_id = class_config.id
            break
    if class_config_id is None:
        return None

    class_config = index.class_configs_by_id.get(class_config_id)
    if class_config is None:
        return None
    for link in class_config.class_config_function_configs:
        fn_cfg = link.function_config
        if fn_cfg is None:
            continue
        if (fn_cfg.name or "").strip() != function_name:
            continue
        return fn_cfg.id
    return None


@dataclass(frozen=True, slots=True)
class PersistedReactivityEvidence:
    condition_id: UUID
    event_id: UUID
    event_condition_id: UUID
    action_ids: tuple[UUID, ...]


class LaneReactivityEvidenceWriter:
    """Persist canonical Condition/Event/EventCondition/Action evidence for one trigger."""

    def __init__(
        self,
        *,
        manifest_path: str | None = None,
        condition_projection_name: str = "Condition",
        event_projection_name: str = "Event",
        default_actor_id: UUID | None = None,
        invoker: _EvidenceFunctionInvoker | None = None,
        perf_log_enabled: bool = False,
    ) -> None:
        self._invoker = invoker or _build_function_call_invoker(
            manifest_path=manifest_path
        )
        self._condition_projection_name = (
            condition_projection_name.strip() or "Condition"
        )
        self._event_projection_name = event_projection_name.strip() or "Event"
        self._default_actor_id = default_actor_id or SYSTEM_ACTOR_ID
        self._perf_log_enabled = bool(perf_log_enabled)

        self._condition_projection_hash: str | None = None
        self._condition_opg_id: UUID | None = None
        self._condition_create_function_id: UUID | None = None

        self._event_projection_hash: str | None = None
        self._event_opg_id: UUID | None = None
        self._event_create_function_id: UUID | None = None
        self._event_add_event_condition_function_id: UUID | None = None
        self._event_add_action_function_id: UUID | None = None

        self._resolve_lock = asyncio.Lock()

    async def persist_for_binding(
        self,
        *,
        receipt: LaneCommitReceiptNotification,
        activation_id: UUID,
        event_type: str,
        source: str,
        actor_subscription_id: UUID | None,
        target_actor_id: UUID | None,
        binding: EventConditionBindingResolution,
    ) -> PersistedReactivityEvidence:
        total_started = time.monotonic()
        if receipt.branch_id is None:
            raise ValueError("receipt.branch_id is required for evidence writes")
        if receipt.commit_id is None:
            raise ValueError("receipt.commit_id is required for evidence writes")
        projection_hash = (receipt.projection_hash or "").strip()
        if not projection_hash:
            raise ValueError("receipt.projection_hash is required for evidence writes")
        if receipt.object_instance_graph_id is None:
            raise ValueError(
                "receipt.object_instance_graph_id is required for evidence writes"
            )

        ensure_resolved_started = time.monotonic()
        await self._ensure_resolved()
        ensure_resolved_ms = _duration_ms(ensure_resolved_started, time.monotonic())
        assert self._condition_projection_hash is not None
        assert self._condition_opg_id is not None
        assert self._condition_create_function_id is not None
        assert self._event_projection_hash is not None
        assert self._event_opg_id is not None
        assert self._event_create_function_id is not None
        assert self._event_add_event_condition_function_id is not None
        assert self._event_add_action_function_id is not None

        index = self._invoker.get_index()
        _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
            index=index,
            projection_hash=projection_hash,
        )
        if opgi is None:
            raise RuntimeError(
                "receipt.projection_hash does not resolve to a canonical ObjectProjectionGraphIdentity: "
                f"projection_hash={projection_hash}"
            )
        object_instance_graph_identity_id = stable_object_instance_graph_identity_id(
            object_projection_graph_identity_id=opgi.id,
            object_instance_graph_id=receipt.object_instance_graph_id,
        )
        trigger_object_instance_graph_commit_id = (
            stable_object_instance_graph_commit_id(
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                commit_id=receipt.commit_id,
            )
        )

        actor_id = receipt.actor_id or self._default_actor_id
        condition_branch_id = uuid5(
            NAMESPACE_URL,
            f"aware://reactivity/evidence/condition:{receipt.branch_id}:{activation_id}",
        )
        event_branch_id = uuid5(
            NAMESPACE_URL,
            f"aware://reactivity/evidence/event:{receipt.branch_id}:{activation_id}",
        )

        condition_id = stable_condition_id(
            config_id=binding.condition_config_id,
            activation_id=activation_id,
        )
        event_id = stable_event_id(
            config_id=binding.event_config_id,
            activation_id=activation_id,
        )
        event_condition_id = stable_event_condition_id(
            condition_id=condition_id,
            config_id=binding.id,
            event_id=event_id,
        )

        condition_arguments = JsonObject(
            {
                "activation_id": str(activation_id),
                "event_type": event_type,
                "source": source,
                "actor_subscription_id": (
                    str(actor_subscription_id)
                    if actor_subscription_id is not None
                    else None
                ),
                "target_actor_id": (
                    str(target_actor_id) if target_actor_id is not None else None
                ),
                "receipt": {
                    "branch_id": str(receipt.branch_id),
                    "projection_hash": projection_hash,
                    "commit_id": str(receipt.commit_id),
                    "object_instance_graph_id": (
                        str(receipt.object_instance_graph_id)
                        if receipt.object_instance_graph_id is not None
                        else None
                    ),
                    "root_object_id": (
                        str(receipt.root_object_id)
                        if receipt.root_object_id is not None
                        else None
                    ),
                },
            }
        )
        condition_create_started = time.monotonic()
        await self._invoke_constructor(
            actor_id=actor_id,
            branch_id=condition_branch_id,
            projection_hash=self._condition_projection_hash,
            object_projection_graph_id=self._condition_opg_id,
            function_id=self._condition_create_function_id,
            args=JsonArray(
                [
                    str(binding.condition_config_id),
                    str(activation_id),
                    str(trigger_object_instance_graph_commit_id),
                    condition_arguments,
                ]
            ),
        )
        condition_create_ms = _duration_ms(condition_create_started, time.monotonic())

        event_create_started = time.monotonic()
        await self._invoke_constructor(
            actor_id=actor_id,
            branch_id=event_branch_id,
            projection_hash=self._event_projection_hash,
            object_projection_graph_id=self._event_opg_id,
            function_id=self._event_create_function_id,
            args=JsonArray(
                [
                    str(binding.event_config_id),
                    str(activation_id),
                    event_type,
                    source,
                    "raised",
                ]
            ),
        )
        event_create_ms = _duration_ms(event_create_started, time.monotonic())

        add_event_condition_started = time.monotonic()
        await self._invoke_instance(
            actor_id=actor_id,
            branch_id=event_branch_id,
            projection_hash=self._event_projection_hash,
            object_id=event_id,
            function_id=self._event_add_event_condition_function_id,
            args=JsonArray(
                [
                    str(condition_id),
                    str(binding.id),
                    True,
                    {
                        "event_config_condition_config_id": str(binding.id),
                        "event_config_id": str(binding.event_config_id),
                        "condition_config_id": str(binding.condition_config_id),
                        "matched": True,
                    },
                ]
            ),
        )
        add_event_condition_ms = _duration_ms(
            add_event_condition_started,
            time.monotonic(),
        )

        action_ids: list[UUID] = []
        add_action_total_started = time.monotonic()
        for action_binding in binding.action_bindings:
            if not action_binding.is_enabled:
                continue
            action_id = stable_action_id(
                event_id=event_id,
                config_id=action_binding.action_config_id,
            )
            try:
                await self._invoke_instance(
                    actor_id=actor_id,
                    branch_id=event_branch_id,
                    projection_hash=self._event_projection_hash,
                    object_id=event_id,
                    function_id=self._event_add_action_function_id,
                    args=JsonArray(
                        [
                            str(action_binding.action_config_id),
                            {
                                "event_id": str(event_id),
                                "event_config_action_config_id": str(action_binding.id),
                                "actor_subscription_id": (
                                    str(actor_subscription_id)
                                    if actor_subscription_id is not None
                                    else None
                                ),
                                "target_actor_id": (
                                    str(target_actor_id)
                                    if target_actor_id is not None
                                    else None
                                ),
                            },
                        ]
                    ),
                )
                action_ids.append(action_id)
            except Exception as exc:
                if action_binding.continue_on_fail:
                    logger.warning(
                        "[reactivity-bridge] action evidence persist failed but continue_on_fail=1 "
                        "(binding=%s): %s",
                        action_binding.id,
                        exc,
                    )
                    continue
                raise

        add_action_total_ms = _duration_ms(add_action_total_started, time.monotonic())
        if self._perf_log_enabled:
            logger.info(
                "[reactivity-evidence] perf activation_id=%s commit_id=%s binding_id=%s ensure_resolved_ms=%d condition_create_ms=%d event_create_ms=%d add_event_condition_ms=%d add_action_total_ms=%d action_count=%d total_ms=%d",
                activation_id,
                receipt.commit_id,
                binding.id,
                ensure_resolved_ms,
                condition_create_ms,
                event_create_ms,
                add_event_condition_ms,
                add_action_total_ms,
                len(action_ids),
                _duration_ms(total_started, time.monotonic()),
            )

        return PersistedReactivityEvidence(
            condition_id=condition_id,
            event_id=event_id,
            event_condition_id=event_condition_id,
            action_ids=tuple(action_ids),
        )

    async def _ensure_resolved(self) -> None:
        if (
            self._condition_projection_hash is not None
            and self._condition_opg_id is not None
            and self._condition_create_function_id is not None
            and self._event_projection_hash is not None
            and self._event_opg_id is not None
            and self._event_create_function_id is not None
            and self._event_add_event_condition_function_id is not None
            and self._event_add_action_function_id is not None
        ):
            return

        async with self._resolve_lock:
            if (
                self._condition_projection_hash is not None
                and self._condition_opg_id is not None
                and self._condition_create_function_id is not None
                and self._event_projection_hash is not None
                and self._event_opg_id is not None
                and self._event_create_function_id is not None
                and self._event_add_event_condition_function_id is not None
                and self._event_add_action_function_id is not None
            ):
                return

            await self._invoker.ensure_index()
            index = self._invoker.get_index()

            condition_opg = _resolve_projection_by_name(
                index=index,
                projection_name=self._condition_projection_name,
            )
            event_opg = _resolve_projection_by_name(
                index=index,
                projection_name=self._event_projection_name,
            )
            if condition_opg is None or event_opg is None:
                available = sorted(
                    {
                        (opg.name or "").strip()
                        for opg in index.ocg.object_projection_graphs
                    }
                )
                raise RuntimeError(
                    "reactivity evidence projection(s) not found "
                    f"(condition={self._condition_projection_name!r}, "
                    f"event={self._event_projection_name!r}, available={available})"
                )

            condition_create = _resolve_class_function_id(
                index=index,
                opg=condition_opg,
                class_name="Condition",
                function_name="create",
            )
            event_create = _resolve_class_function_id(
                index=index,
                opg=event_opg,
                class_name="Event",
                function_name="create",
            )
            event_add_event_condition = _resolve_class_function_id(
                index=index,
                opg=event_opg,
                class_name="Event",
                function_name="add_event_condition",
            )
            event_add_action = _resolve_class_function_id(
                index=index,
                opg=event_opg,
                class_name="Event",
                function_name="add_action",
            )
            if (
                condition_create is None
                or event_create is None
                or event_add_event_condition is None
                or event_add_action is None
            ):
                raise RuntimeError(
                    "reactivity evidence function resolution failed "
                    f"(condition={condition_create}, event={event_create}, "
                    f"event_add_event_condition={event_add_event_condition}, "
                    f"event_add_action={event_add_action})"
                )

            self._condition_projection_hash = condition_opg.projection_hash
            self._condition_opg_id = condition_opg.id
            self._condition_create_function_id = condition_create

            self._event_projection_hash = event_opg.projection_hash
            self._event_opg_id = event_opg.id
            self._event_create_function_id = event_create
            self._event_add_event_condition_function_id = event_add_event_condition
            self._event_add_action_function_id = event_add_action

    async def _invoke_constructor(
        self,
        *,
        actor_id: UUID,
        branch_id: UUID,
        projection_hash: str,
        object_projection_graph_id: UUID,
        function_id: UUID,
        args: JsonArray,
    ) -> None:
        await self._invoker.ensure_index()
        index = self._invoker.get_index()
        request = InvokeFunctionRequest(
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            call_target=InvokeFunctionCallTarget.opg_constructor,
            object_id=None,
            object_projection_graph_id=object_projection_graph_id,
            function_id=function_id,
            args=args,
            kwargs=JsonObject({}),
            commit=True,
            publish=False,
        )
        response = await self._invoker.invoke_function_with_index(
            index=index,
            request=request,
        )
        if response.status != "succeeded":
            raise RuntimeError(
                response.error or "reactivity evidence constructor failed"
            )

    async def _invoke_instance(
        self,
        *,
        actor_id: UUID,
        branch_id: UUID,
        projection_hash: str,
        object_id: UUID,
        function_id: UUID,
        args: JsonArray,
    ) -> None:
        await self._invoker.ensure_index()
        index = self._invoker.get_index()
        request = InvokeFunctionRequest(
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            call_target=InvokeFunctionCallTarget.instance,
            object_id=object_id,
            object_projection_graph_id=None,
            function_id=function_id,
            args=args,
            kwargs=JsonObject({}),
            commit=True,
            publish=False,
        )
        response = await self._invoker.invoke_function_with_index(
            index=index,
            request=request,
        )
        if response.status != "succeeded":
            raise RuntimeError(
                response.error or "reactivity evidence instance call failed"
            )


__all__ = [
    "LaneReactivityEvidenceWriter",
    "PersistedReactivityEvidence",
]


def _duration_ms(start: float, end: float) -> int:
    return max(int((end - start) * 1000), 0)
