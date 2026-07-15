from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol, cast
from uuid import UUID

from aware_types import JsonArray, JsonObject
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionCallTarget,
)
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionRequest,
)
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionResponse,
)
from aware_environment_service_dto.environment.environment import (
    ResolveRuntimeFunctionTargetQuery,
)
from aware_environment_service_dto.environment.environment import (
    ResolveRuntimeRefsRequest,
)
from aware_environment_service_dto.environment.environment import (
    ResolveRuntimeRefsResponse,
)

EnvironmentGraphCallTarget = Literal["constructor", "instance"]


class _EnvironmentRuntimeRefCapabilityClient(Protocol):
    async def resolve_runtime_refs(
        self,
        request: ResolveRuntimeRefsRequest,
    ) -> ResolveRuntimeRefsResponse: ...


class _EnvironmentFunctionCallCapabilityClient(Protocol):
    async def invoke_function(
        self,
        request: InvokeFunctionRequest,
    ) -> InvokeFunctionResponse: ...


class _EnvironmentApiClient(Protocol):
    @property
    def runtime_ref(self) -> _EnvironmentRuntimeRefCapabilityClient: ...

    @property
    def function_call(self) -> _EnvironmentFunctionCallCapabilityClient: ...


class EnvironmentGeneratedApiClient(Protocol):
    @property
    def environment(self) -> _EnvironmentApiClient: ...


@dataclass(frozen=True, slots=True)
class EnvironmentGraphContext:
    environment_id: UUID
    actor_id: UUID | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None

    @classmethod
    def from_object(cls, context: object) -> "EnvironmentGraphContext":
        return cls(
            actor_id=_optional_uuid(getattr(context, "actor_id", None)),
            environment_id=_required_uuid(
                getattr(context, "environment_id", None),
                field_name="environment_id",
            ),
            process_id=_optional_uuid(getattr(context, "process_id", None)),
            thread_id=_optional_uuid(getattr(context, "thread_id", None)),
            branch_id=_optional_uuid(getattr(context, "branch_id", None)),
            projection_hash=_optional_text(getattr(context, "projection_hash", None)),
        )


@dataclass(frozen=True, slots=True)
class EnvironmentGraphFunctionTarget:
    function_ref: str
    call_target: EnvironmentGraphCallTarget
    function_id: UUID
    projection_hash: str
    object_projection_graph_id: UUID | None = None
    object_projection_graph_identity_id: UUID | None = None
    class_config_id: UUID | None = None
    class_fqn: str | None = None
    function_name: str | None = None
    evidence: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EnvironmentGraphInvocationReceipt:
    status: str
    object_id: str | None
    commit_id: str | None
    branch_id: str | None
    projection_hash: str | None
    object_instance_graph_commit_id: str | None
    object_projection_graph_id: str | None
    object_projection_graph_identity_id: str | None
    object_instance_graph_id: str | None
    object_instance_graph_identity_id: str | None
    object_instance_graph_branch_id: str | None
    graph_hash_post: str | None
    payload: object | None
    evidence: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EnvironmentGraphClient:
    api_client: EnvironmentGeneratedApiClient
    context: EnvironmentGraphContext
    commit: bool = True
    publish: bool = False

    async def resolve_function_target(
        self,
        *,
        function_ref: str,
        call_target: EnvironmentGraphCallTarget,
        projection_hash_hint: str | None = None,
        query_key: str = "environment_graph_target",
    ) -> EnvironmentGraphFunctionTarget:
        api_call_target = _api_call_target(call_target)
        response = await self.api_client.environment.runtime_ref.resolve_runtime_refs(
            ResolveRuntimeRefsRequest(
                actor_id=self.context.actor_id,
                environment_id=self.context.environment_id,
                process_id=self.context.process_id,
                thread_id=self.context.thread_id,
                branch_id=self.context.branch_id,
                projection_hash=self.context.projection_hash,
                function_targets=[
                    ResolveRuntimeFunctionTargetQuery(
                        query_key=query_key,
                        function_ref=function_ref,
                        call_target=api_call_target,
                        projection_hash_hint=projection_hash_hint,
                    )
                ],
            )
        )
        if not response.function_targets:
            raise RuntimeError(
                "Environment graph SDK target resolution returned no target: "
                f"function_ref={function_ref!r}"
            )
        target = response.function_targets[0]
        if target.status != "resolved":
            raise RuntimeError(
                "Environment graph SDK target resolution failed: "
                f"function_ref={function_ref!r} "
                f"status={target.status!r} error={target.error!r}"
            )
        function_id = _required_uuid(target.function_id, field_name="function_id")
        projection_hash = _required_text(
            target.projection_hash,
            field_name="projection_hash",
        )
        object_projection_graph_id = _optional_uuid(target.object_projection_graph_id)
        if call_target == "constructor" and object_projection_graph_id is None:
            raise RuntimeError(
                "Environment graph SDK constructor target is missing "
                f"object_projection_graph_id: function_ref={function_ref!r}"
            )
        return EnvironmentGraphFunctionTarget(
            function_ref=target.function_ref,
            call_target=call_target,
            function_id=function_id,
            projection_hash=projection_hash,
            object_projection_graph_id=object_projection_graph_id,
            object_projection_graph_identity_id=_optional_uuid(
                target.object_projection_graph_identity_id
            ),
            class_config_id=_optional_uuid(target.class_config_id),
            class_fqn=target.class_fqn,
            function_name=target.function_name,
            evidence={
                "resolver": "environment_sdk.generated_api_runtime_ref",
                "environment_status": response.status,
                "target": target.model_dump(mode="json", exclude_none=True),
                "response_evidence": dict(response.evidence),
            },
        )

    async def invoke_function_ref(
        self,
        *,
        function_ref: str,
        call_target: EnvironmentGraphCallTarget,
        receiver_object_id: UUID | str | None = None,
        args: Sequence[object] = (),
        kwargs: Mapping[str, object] | None = None,
        projection_hash_hint: str | None = None,
        expected_graph_hash_pre: str | None = None,
        expected_head_commit_id: UUID | str | None = None,
    ) -> EnvironmentGraphInvocationReceipt:
        target = await self.resolve_function_target(
            function_ref=function_ref,
            call_target=call_target,
            projection_hash_hint=projection_hash_hint,
        )
        return await self.invoke_resolved_target(
            target=target,
            receiver_object_id=receiver_object_id,
            args=args,
            kwargs=kwargs,
            expected_graph_hash_pre=expected_graph_hash_pre,
            expected_head_commit_id=expected_head_commit_id,
        )

    async def invoke_resolved_target(
        self,
        *,
        target: EnvironmentGraphFunctionTarget,
        receiver_object_id: UUID | str | None = None,
        args: Sequence[object] = (),
        kwargs: Mapping[str, object] | None = None,
        expected_graph_hash_pre: str | None = None,
        expected_head_commit_id: UUID | str | None = None,
    ) -> EnvironmentGraphInvocationReceipt:
        request = self._build_invoke_request(
            target=target,
            receiver_object_id=receiver_object_id,
            args=args,
            kwargs=kwargs or {},
            expected_graph_hash_pre=expected_graph_hash_pre,
            expected_head_commit_id=expected_head_commit_id,
        )
        response = await self.api_client.environment.function_call.invoke_function(
            request
        )
        if (response.status or "").strip().lower() != "succeeded":
            raise RuntimeError(
                "Environment graph SDK invocation failed: "
                f"function_ref={target.function_ref!r} "
                f"status={response.status!r} error={response.error!r}"
            )
        object_id = _result_object_id(response=response)
        return EnvironmentGraphInvocationReceipt(
            status=response.status,
            object_id=str(object_id) if object_id is not None else None,
            commit_id=(
                str(response.commit_id) if response.commit_id is not None else None
            ),
            branch_id=(
                str(response.branch_id) if response.branch_id is not None else None
            ),
            projection_hash=response.projection_hash,
            object_instance_graph_commit_id=(
                str(response.object_instance_graph_commit_id)
                if response.object_instance_graph_commit_id is not None
                else None
            ),
            object_projection_graph_id=(
                str(response.object_projection_graph_id)
                if response.object_projection_graph_id is not None
                else None
            ),
            object_projection_graph_identity_id=(
                str(response.object_projection_graph_identity_id)
                if response.object_projection_graph_identity_id is not None
                else None
            ),
            object_instance_graph_id=(
                str(response.object_instance_graph_id)
                if response.object_instance_graph_id is not None
                else None
            ),
            object_instance_graph_identity_id=(
                str(response.object_instance_graph_identity_id)
                if response.object_instance_graph_identity_id is not None
                else None
            ),
            object_instance_graph_branch_id=(
                str(response.object_instance_graph_branch_id)
                if response.object_instance_graph_branch_id is not None
                else None
            ),
            graph_hash_post=response.graph_hash_post,
            payload=response.payload,
            evidence={
                "invoker": "environment_sdk.generated_api_function_call",
                "target": dict(target.evidence),
                "response": {
                    "status": response.status,
                    "object_instance_graph_commit_id": (
                        str(response.object_instance_graph_commit_id)
                        if response.object_instance_graph_commit_id is not None
                        else None
                    ),
                    "object_projection_graph_identity_id": (
                        str(response.object_projection_graph_identity_id)
                        if response.object_projection_graph_identity_id is not None
                        else None
                    ),
                    "object_instance_graph_branch_id": (
                        str(response.object_instance_graph_branch_id)
                        if response.object_instance_graph_branch_id is not None
                        else None
                    ),
                    "graph_hash_post": response.graph_hash_post,
                },
            },
        )

    def _build_invoke_request(
        self,
        *,
        target: EnvironmentGraphFunctionTarget,
        receiver_object_id: UUID | str | None,
        args: Sequence[object],
        kwargs: Mapping[str, object],
        expected_graph_hash_pre: str | None,
        expected_head_commit_id: UUID | str | None,
    ) -> InvokeFunctionRequest:
        api_call_target = _api_call_target(target.call_target)
        object_id = (
            None
            if target.call_target == "constructor"
            else _required_uuid(
                receiver_object_id,
                field_name="receiver_object_id",
            )
        )
        object_projection_graph_id = target.object_projection_graph_id
        if target.call_target == "constructor":
            object_projection_graph_id = _required_uuid(
                object_projection_graph_id,
                field_name="object_projection_graph_id",
            )
        return InvokeFunctionRequest(
            actor_id=self.context.actor_id,
            environment_id=self.context.environment_id,
            process_id=self.context.process_id,
            thread_id=self.context.thread_id,
            branch_id=(
                None if target.call_target == "constructor" else self.context.branch_id
            ),
            projection_hash=target.projection_hash,
            call_target=api_call_target,
            object_id=object_id,
            object_projection_graph_id=object_projection_graph_id,
            object_projection_graph_identity_id=(
                target.object_projection_graph_identity_id
            ),
            function_id=target.function_id,
            args=cast(JsonArray, list(args)),
            kwargs=cast(JsonObject, dict(kwargs)),
            expected_graph_hash_pre=expected_graph_hash_pre,
            expected_head_commit_id=_optional_uuid(expected_head_commit_id),
            commit=self.commit,
            publish=self.publish,
        )


def _api_call_target(
    call_target: EnvironmentGraphCallTarget,
) -> InvokeFunctionCallTarget:
    if call_target == "constructor":
        return InvokeFunctionCallTarget.opg_constructor
    return InvokeFunctionCallTarget.instance


def _result_object_id(*, response: InvokeFunctionResponse) -> UUID | str | None:
    if response.root_object_id is not None:
        return response.root_object_id
    payload = response.payload
    if isinstance(payload, Mapping):
        raw_id = payload.get("id")
        if raw_id is not None:
            return str(raw_id)
        if set(str(key) for key in payload.keys()) == {"value"}:
            value = payload.get("value")
            if isinstance(value, Mapping) and value.get("id") is not None:
                return str(value["id"])
    return None


def _required_text(value: object, *, field_name: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise RuntimeError(
            f"Environment graph SDK missing required field: {field_name}"
        )
    return text


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_uuid(value: object, *, field_name: str) -> UUID:
    parsed = _optional_uuid(value)
    if parsed is None:
        raise RuntimeError(f"Environment graph SDK missing required UUID: {field_name}")
    return parsed


def _optional_uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if value is None:
        return None
    try:
        return UUID(str(value))
    except ValueError:
        return None
