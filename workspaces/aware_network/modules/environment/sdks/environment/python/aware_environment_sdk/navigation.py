from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol, cast
from uuid import UUID

from aware_types import JsonObject
from aware_environment_service_dto.environment.environment import (
    CreateEnvironmentNavigationContextRequest,
    CreateEnvironmentNavigationContextResponse,
    DescribeEnvironmentNavigationContextRequest,
    DescribeEnvironmentNavigationContextResponse,
    EnvironmentNavigationCommitReceipt as DtoEnvironmentNavigationCommitReceipt,
    EnvironmentNavigationContextView as DtoEnvironmentNavigationContextView,
    EnvironmentSessionJoinReceipt as DtoEnvironmentSessionJoinReceipt,
    ListEnvironmentNavigationContextsRequest,
    ListEnvironmentNavigationContextsResponse,
    SelectEnvironmentNavigationTargetRequest,
    SelectEnvironmentNavigationTargetResponse,
)

from aware_environment_sdk.session import (
    EnvironmentSessionJoinReceipt as SdkEnvironmentSessionJoinReceipt,
    EnvironmentSessionJoinResult,
    EnvironmentSessionStartResult,
)


class EnvironmentNavigationError(RuntimeError):
    """Raised when Environment navigation context operations fail closed."""

    def __init__(
        self,
        message: str,
        *,
        receipt: "EnvironmentNavigationCommitReceipt | None" = None,
    ) -> None:
        super().__init__(message)
        self.receipt = receipt


class _EnvironmentNavigationCapabilityClient(Protocol):
    async def create_navigation_context(
        self,
        request: CreateEnvironmentNavigationContextRequest,
    ) -> CreateEnvironmentNavigationContextResponse: ...

    async def select_navigation_target(
        self,
        request: SelectEnvironmentNavigationTargetRequest,
    ) -> SelectEnvironmentNavigationTargetResponse: ...

    async def describe_navigation_context(
        self,
        request: DescribeEnvironmentNavigationContextRequest,
    ) -> DescribeEnvironmentNavigationContextResponse: ...

    async def list_navigation_contexts(
        self,
        request: ListEnvironmentNavigationContextsRequest,
    ) -> ListEnvironmentNavigationContextsResponse: ...


class _EnvironmentApiClient(Protocol):
    @property
    def navigation(self) -> _EnvironmentNavigationCapabilityClient: ...


class EnvironmentNavigationGeneratedApiClient(Protocol):
    @property
    def environment(self) -> _EnvironmentApiClient: ...


@dataclass(frozen=True, slots=True)
class EnvironmentNavigationClientContext:
    actor_id: UUID
    environment_id: UUID

    @classmethod
    def from_object(cls, context: object) -> "EnvironmentNavigationClientContext":
        return cls(
            actor_id=_required_uuid(
                getattr(context, "actor_id", None),
                field_name="actor_id",
            ),
            environment_id=_required_uuid(
                getattr(context, "environment_id", None),
                field_name="environment_id",
            ),
        )


@dataclass(frozen=True, slots=True)
class EnvironmentNavigationContext:
    environment_navigation_context_id: UUID
    environment_session_id: UUID
    environment_id: UUID
    key: str
    title: str | None
    status: str
    is_default: bool
    selected_process_id: UUID | None
    selected_thread_id: UUID | None
    branch_id: UUID | None
    projection_hash: str | None
    root_object_id: UUID | None
    commit_id: UUID | None
    object_instance_graph_commit_id: UUID | None
    graph_hash_post: str | None
    evidence: Mapping[str, object] = field(default_factory=dict)
    dto_context: DtoEnvironmentNavigationContextView | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentNavigationCommitReceipt:
    accepted: bool
    status: str
    error: str | None
    reason: str | None
    actor_id: UUID | None
    environment_id: UUID
    environment_session_id: UUID
    environment_navigation_context_id: UUID | None
    key: str | None
    is_default: bool
    branch_id: UUID | None
    projection_hash: str | None
    root_object_id: UUID | None
    commit_id: UUID | None
    object_instance_graph_commit_id: UUID | None
    graph_hash_pre: str | None
    graph_hash_post: str | None
    function_call_id: UUID | None
    function_call_response_id: UUID | None
    selected_process_id: UUID | None
    selected_thread_id: UUID | None
    blockers: tuple[str, ...]
    evidence: Mapping[str, object] = field(default_factory=dict)
    dto_receipt: DtoEnvironmentNavigationCommitReceipt | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentNavigationCreateResult:
    accepted: bool
    status: str
    error: str | None
    context: EnvironmentNavigationContext | None
    receipt: EnvironmentNavigationCommitReceipt
    evidence: Mapping[str, object] = field(default_factory=dict)
    raw_response: CreateEnvironmentNavigationContextResponse | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentNavigationSelectResult:
    accepted: bool
    status: str
    error: str | None
    context: EnvironmentNavigationContext | None
    receipt: EnvironmentNavigationCommitReceipt
    evidence: Mapping[str, object] = field(default_factory=dict)
    raw_response: SelectEnvironmentNavigationTargetResponse | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentNavigationDescribeResult:
    status: str
    error: str | None
    context: EnvironmentNavigationContext | None
    blockers: tuple[str, ...]
    evidence: Mapping[str, object] = field(default_factory=dict)
    raw_response: DescribeEnvironmentNavigationContextResponse | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentNavigationListResult:
    status: str
    error: str | None
    contexts: tuple[EnvironmentNavigationContext, ...]
    blockers: tuple[str, ...]
    evidence: Mapping[str, object] = field(default_factory=dict)
    raw_response: ListEnvironmentNavigationContextsResponse | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentNavigationClient:
    api_client: EnvironmentNavigationGeneratedApiClient
    context: EnvironmentNavigationClientContext

    async def create_navigation_context(
        self,
        *,
        environment_session_id: UUID | str,
        session_join_receipt: object,
        key: str,
        request_id: UUID | str | None = None,
        title: str | None = None,
        status: str = "active",
        is_default: bool = False,
        selected_process_id: UUID | str | None = None,
        selected_thread_id: UUID | str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> EnvironmentNavigationCreateResult:
        response = (
            await self.api_client.environment.navigation.create_navigation_context(
                CreateEnvironmentNavigationContextRequest(
                    actor_id=self.context.actor_id,
                    environment_id=self.context.environment_id,
                    request_id=_optional_uuid(request_id),
                    environment_session_id=_required_uuid(
                        environment_session_id,
                        field_name="environment_session_id",
                    ),
                    session_join_receipt=_dto_session_join_receipt(
                        session_join_receipt
                    ),
                    key=key,
                    title=title,
                    status=status,
                    is_default=is_default,
                    selected_process_id=_optional_uuid(selected_process_id),
                    selected_thread_id=_optional_uuid(selected_thread_id),
                    metadata=cast(JsonObject, dict(metadata or {})),
                )
            )
        )
        result = _create_result_from_response(response)
        if not result.accepted:
            raise EnvironmentNavigationError(
                f"Environment navigation create failed: {result.error or result.status}",
                receipt=result.receipt,
            )
        return result

    async def select_navigation_target(
        self,
        *,
        environment_session_id: UUID | str,
        environment_navigation_context_id: UUID | str,
        session_join_receipt: object,
        request_id: UUID | str | None = None,
        selected_process_id: UUID | str | None = None,
        selected_thread_id: UUID | str | None = None,
        expected_head_commit_id: UUID | str | None = None,
        expected_graph_hash_pre: str | None = None,
        reason: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> EnvironmentNavigationSelectResult:
        response = (
            await self.api_client.environment.navigation.select_navigation_target(
                SelectEnvironmentNavigationTargetRequest(
                    actor_id=self.context.actor_id,
                    environment_id=self.context.environment_id,
                    request_id=_optional_uuid(request_id),
                    environment_session_id=_required_uuid(
                        environment_session_id,
                        field_name="environment_session_id",
                    ),
                    environment_navigation_context_id=_required_uuid(
                        environment_navigation_context_id,
                        field_name="environment_navigation_context_id",
                    ),
                    session_join_receipt=_dto_session_join_receipt(
                        session_join_receipt
                    ),
                    selected_process_id=_optional_uuid(selected_process_id),
                    selected_thread_id=_optional_uuid(selected_thread_id),
                    expected_head_commit_id=_optional_uuid(expected_head_commit_id),
                    expected_graph_hash_pre=expected_graph_hash_pre,
                    reason=reason,
                    metadata=cast(JsonObject, dict(metadata or {})),
                )
            )
        )
        result = _select_result_from_response(response)
        if not result.accepted:
            raise EnvironmentNavigationError(
                f"Environment navigation select failed: {result.error or result.status}",
                receipt=result.receipt,
            )
        return result

    async def describe_navigation_context(
        self,
        *,
        environment_session_id: UUID | str,
        environment_navigation_context_id: UUID | str,
        session_join_receipt: object,
        include_commit: bool = True,
    ) -> EnvironmentNavigationDescribeResult:
        response = (
            await self.api_client.environment.navigation.describe_navigation_context(
                DescribeEnvironmentNavigationContextRequest(
                    actor_id=self.context.actor_id,
                    environment_id=self.context.environment_id,
                    environment_session_id=_required_uuid(
                        environment_session_id,
                        field_name="environment_session_id",
                    ),
                    environment_navigation_context_id=_required_uuid(
                        environment_navigation_context_id,
                        field_name="environment_navigation_context_id",
                    ),
                    session_join_receipt=_dto_session_join_receipt(
                        session_join_receipt
                    ),
                    include_commit=include_commit,
                )
            )
        )
        result = _describe_result_from_response(response)
        if result.error is not None:
            raise EnvironmentNavigationError(
                f"Environment navigation describe failed: {result.error}",
            )
        return result

    async def list_navigation_contexts(
        self,
        *,
        environment_session_id: UUID | str,
        session_join_receipt: object,
        include_closed: bool = False,
    ) -> EnvironmentNavigationListResult:
        response = (
            await self.api_client.environment.navigation.list_navigation_contexts(
                ListEnvironmentNavigationContextsRequest(
                    actor_id=self.context.actor_id,
                    environment_id=self.context.environment_id,
                    environment_session_id=_required_uuid(
                        environment_session_id,
                        field_name="environment_session_id",
                    ),
                    session_join_receipt=_dto_session_join_receipt(
                        session_join_receipt
                    ),
                    include_closed=include_closed,
                )
            )
        )
        result = _list_result_from_response(response)
        if result.error is not None:
            raise EnvironmentNavigationError(
                f"Environment navigation list failed: {result.error}",
            )
        return result


def _create_result_from_response(
    response: CreateEnvironmentNavigationContextResponse,
) -> EnvironmentNavigationCreateResult:
    return EnvironmentNavigationCreateResult(
        accepted=response.accepted,
        status=response.status,
        error=response.error,
        context=_context_from_dto(response.context),
        receipt=_receipt_from_dto(response.receipt),
        evidence=dict(response.evidence),
        raw_response=response,
    )


def _select_result_from_response(
    response: SelectEnvironmentNavigationTargetResponse,
) -> EnvironmentNavigationSelectResult:
    return EnvironmentNavigationSelectResult(
        accepted=response.accepted,
        status=response.status,
        error=response.error,
        context=_context_from_dto(response.context),
        receipt=_receipt_from_dto(response.receipt),
        evidence=dict(response.evidence),
        raw_response=response,
    )


def _describe_result_from_response(
    response: DescribeEnvironmentNavigationContextResponse,
) -> EnvironmentNavigationDescribeResult:
    return EnvironmentNavigationDescribeResult(
        status=response.status,
        error=response.error,
        context=_context_from_dto(response.context),
        blockers=tuple(response.blockers),
        evidence=dict(response.evidence),
        raw_response=response,
    )


def _list_result_from_response(
    response: ListEnvironmentNavigationContextsResponse,
) -> EnvironmentNavigationListResult:
    return EnvironmentNavigationListResult(
        status=response.status,
        error=response.error,
        contexts=tuple(
            _required_context_from_dto(context) for context in response.contexts
        ),
        blockers=tuple(response.blockers),
        evidence=dict(response.evidence),
        raw_response=response,
    )


def _context_from_dto(
    context: DtoEnvironmentNavigationContextView | None,
) -> EnvironmentNavigationContext | None:
    if context is None:
        return None
    return _required_context_from_dto(context)


def _required_context_from_dto(
    context: DtoEnvironmentNavigationContextView,
) -> EnvironmentNavigationContext:
    return EnvironmentNavigationContext(
        environment_navigation_context_id=context.environment_navigation_context_id,
        environment_session_id=context.environment_session_id,
        environment_id=context.environment_id,
        key=context.key,
        title=context.title,
        status=context.status,
        is_default=context.is_default,
        selected_process_id=context.selected_process_id,
        selected_thread_id=context.selected_thread_id,
        branch_id=context.branch_id,
        projection_hash=context.projection_hash,
        root_object_id=context.root_object_id,
        commit_id=context.commit_id,
        object_instance_graph_commit_id=context.object_instance_graph_commit_id,
        graph_hash_post=context.graph_hash_post,
        evidence=dict(context.evidence),
        dto_context=context,
    )


def _receipt_from_dto(
    receipt: DtoEnvironmentNavigationCommitReceipt,
) -> EnvironmentNavigationCommitReceipt:
    return EnvironmentNavigationCommitReceipt(
        accepted=receipt.accepted,
        status=receipt.status,
        error=receipt.error,
        reason=receipt.reason,
        actor_id=receipt.actor_id,
        environment_id=receipt.environment_id,
        environment_session_id=receipt.environment_session_id,
        environment_navigation_context_id=receipt.environment_navigation_context_id,
        key=receipt.key,
        is_default=receipt.is_default,
        branch_id=receipt.branch_id,
        projection_hash=receipt.projection_hash,
        root_object_id=receipt.root_object_id,
        commit_id=receipt.commit_id,
        object_instance_graph_commit_id=receipt.object_instance_graph_commit_id,
        graph_hash_pre=receipt.graph_hash_pre,
        graph_hash_post=receipt.graph_hash_post,
        function_call_id=receipt.function_call_id,
        function_call_response_id=receipt.function_call_response_id,
        selected_process_id=receipt.selected_process_id,
        selected_thread_id=receipt.selected_thread_id,
        blockers=tuple(receipt.blockers),
        evidence=dict(receipt.evidence),
        dto_receipt=receipt,
    )


def _dto_session_join_receipt(value: object) -> DtoEnvironmentSessionJoinReceipt:
    if isinstance(value, DtoEnvironmentSessionJoinReceipt):
        return value
    if isinstance(value, SdkEnvironmentSessionJoinReceipt):
        if value.dto_receipt is None:
            raise ValueError("session_join_receipt does not carry a DTO receipt.")
        return value.dto_receipt
    if isinstance(value, EnvironmentSessionStartResult):
        return _dto_session_join_receipt(value.join_receipt)
    if isinstance(value, EnvironmentSessionJoinResult):
        return _dto_session_join_receipt(value.receipt)
    return DtoEnvironmentSessionJoinReceipt.model_validate(value)


def _required_uuid(value: object, *, field_name: str) -> UUID:
    resolved = _optional_uuid(value)
    if resolved is None:
        raise ValueError(f"{field_name} is required.")
    return resolved


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        return UUID(text)
    raise TypeError(f"Expected UUID or UUID string, got {type(value).__name__}.")


__all__ = [
    "EnvironmentNavigationClient",
    "EnvironmentNavigationClientContext",
    "EnvironmentNavigationCommitReceipt",
    "EnvironmentNavigationContext",
    "EnvironmentNavigationCreateResult",
    "EnvironmentNavigationDescribeResult",
    "EnvironmentNavigationError",
    "EnvironmentNavigationGeneratedApiClient",
    "EnvironmentNavigationListResult",
    "EnvironmentNavigationSelectResult",
]
