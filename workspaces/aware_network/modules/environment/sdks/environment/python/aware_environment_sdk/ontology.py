from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

from aware_types import JsonObject
from aware_environment_service_dto.environment.environment import (
    AttachEnvironmentOntologyRequest,
    AttachEnvironmentOntologyResponse,
    EnsureEnvironmentOntologyRuntimeRequest,
    EnsureEnvironmentOntologyRuntimeResponse,
    EnvironmentOntologyMembership as DtoEnvironmentOntologyMembership,
    ListEnvironmentOntologiesRequest,
    ListEnvironmentOntologiesResponse,
)


class EnvironmentOntologyError(RuntimeError):
    """Raised when Environment ontology membership operations fail closed."""


class _EnvironmentOntologyCapabilityClient(Protocol):
    async def attach_environment_ontology(
        self,
        request: AttachEnvironmentOntologyRequest,
    ) -> AttachEnvironmentOntologyResponse: ...

    async def list_environment_ontologies(
        self,
        request: ListEnvironmentOntologiesRequest,
    ) -> ListEnvironmentOntologiesResponse: ...

    async def ensure_environment_ontology_runtime(
        self,
        request: EnsureEnvironmentOntologyRuntimeRequest,
    ) -> EnsureEnvironmentOntologyRuntimeResponse: ...


class _EnvironmentApiClient(Protocol):
    @property
    def ontology(self) -> _EnvironmentOntologyCapabilityClient: ...


class EnvironmentOntologyGeneratedApiClient(Protocol):
    @property
    def environment(self) -> _EnvironmentApiClient: ...


@dataclass(frozen=True, slots=True)
class EnvironmentOntologyContext:
    environment_id: UUID
    actor_id: UUID | None = None
    process_id: UUID | None = None
    thread_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None

    @classmethod
    def from_object(cls, context: object) -> "EnvironmentOntologyContext":
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
class EnvironmentOntologyMembership:
    environment_ontology_id: UUID | None
    ontology_id: UUID
    role: str
    status: str
    title: str | None
    description: str | None
    commit_id: UUID | None
    graph_hash_post: str | None
    evidence: Mapping[str, object] = field(default_factory=dict)
    dto_membership: DtoEnvironmentOntologyMembership | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentOntologyAttachResult:
    status: str
    error: str | None
    membership: EnvironmentOntologyMembership | None
    commit_id: UUID | None
    object_instance_graph_commit_id: UUID | None
    graph_hash_pre: str | None
    graph_hash_post: str | None
    evidence: Mapping[str, object] = field(default_factory=dict)
    raw_response: AttachEnvironmentOntologyResponse | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentOntologyListResult:
    status: str
    error: str | None
    memberships: tuple[EnvironmentOntologyMembership, ...]
    commit_id: UUID | None
    object_instance_graph_commit_id: UUID | None
    graph_hash_post: str | None
    evidence: Mapping[str, object] = field(default_factory=dict)
    raw_response: ListEnvironmentOntologiesResponse | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentOntologyRuntimeResult:
    status: str
    error: str | None
    ontology_id: UUID | None
    package_name: str | None
    fqn_prefix: str | None
    artifact_set_id: str | None
    runtime_projection_descriptor_count: int
    capability_object_count: int
    capability_function_count: int
    registered_artifact_ref_count: int
    registry_artifact_ref_count: int
    membership_commit_id: UUID | None
    evidence: Mapping[str, object] = field(default_factory=dict)
    raw_response: EnsureEnvironmentOntologyRuntimeResponse | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentOntologyClient:
    api_client: EnvironmentOntologyGeneratedApiClient
    context: EnvironmentOntologyContext

    async def attach_ontology(
        self,
        *,
        ontology_id: UUID | str,
        role: str = "runtime",
        status: str = "active",
        title: str | None = None,
        description: str | None = None,
        expected_graph_hash_pre: str | None = None,
        expected_head_commit_id: UUID | str | None = None,
        commit: bool = True,
        publish: bool = False,
    ) -> EnvironmentOntologyAttachResult:
        response = (
            await self.api_client.environment.ontology.attach_environment_ontology(
                AttachEnvironmentOntologyRequest(
                    actor_id=self.context.actor_id,
                    environment_id=self.context.environment_id,
                    process_id=self.context.process_id,
                    thread_id=self.context.thread_id,
                    branch_id=self.context.branch_id,
                    projection_hash=self.context.projection_hash,
                    ontology_id=_required_uuid(ontology_id, field_name="ontology_id"),
                    role=role,
                    status=status,
                    title=title,
                    description=description,
                    expected_graph_hash_pre=expected_graph_hash_pre,
                    expected_head_commit_id=_optional_uuid(expected_head_commit_id),
                    commit=commit,
                    publish=publish,
                )
            )
        )
        result = _attach_result_from_response(response)
        if _status(response.status) != "succeeded":
            raise EnvironmentOntologyError(
                "Environment ontology attach failed: "
                f"{response.error or response.status}"
            )
        return result

    async def list_ontologies(
        self,
        *,
        commit_id: UUID | str | None = None,
        root_object_id: UUID | str | None = None,
        expected_graph_hash_post: str | None = None,
    ) -> EnvironmentOntologyListResult:
        response = (
            await self.api_client.environment.ontology.list_environment_ontologies(
                ListEnvironmentOntologiesRequest(
                    actor_id=self.context.actor_id,
                    environment_id=self.context.environment_id,
                    process_id=self.context.process_id,
                    thread_id=self.context.thread_id,
                    branch_id=self.context.branch_id,
                    projection_hash=self.context.projection_hash,
                    commit_id=_optional_uuid(commit_id),
                    root_object_id=_optional_uuid(root_object_id),
                    expected_graph_hash_post=expected_graph_hash_post,
                )
            )
        )
        result = _list_result_from_response(response)
        if _status(response.status) != "succeeded":
            raise EnvironmentOntologyError(
                "Environment ontology list failed: "
                f"{response.error or response.status}"
            )
        return result

    async def ensure_runtime(
        self,
        *,
        ontology_id: UUID | str | None = None,
        package_name: str | None = None,
        fqn_prefix: str | None = None,
        artifact_set_id: str | None = None,
        workspace_revision_id: str | None = None,
        materialization_ref: str | None = None,
        include_artifacts: bool = True,
        source_payload: Mapping[str, object] | None = None,
        membership_commit_id: UUID | str | None = None,
    ) -> EnvironmentOntologyRuntimeResult:
        response = await self.api_client.environment.ontology.ensure_environment_ontology_runtime(
            EnsureEnvironmentOntologyRuntimeRequest(
                actor_id=self.context.actor_id,
                environment_id=self.context.environment_id,
                process_id=self.context.process_id,
                thread_id=self.context.thread_id,
                branch_id=self.context.branch_id,
                projection_hash=self.context.projection_hash,
                ontology_id=_optional_uuid(ontology_id),
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                artifact_set_id=artifact_set_id,
                workspace_revision_id=workspace_revision_id,
                materialization_ref=materialization_ref,
                include_artifacts=include_artifacts,
                source_payload=(
                    JsonObject(dict(source_payload or {}))
                    if source_payload is not None
                    else None
                ),
                membership_commit_id=_optional_uuid(membership_commit_id),
            )
        )
        result = _runtime_result_from_response(response)
        if _status(response.status) != "succeeded":
            raise EnvironmentOntologyError(
                "Environment ontology runtime activation failed: "
                f"{response.error or response.status}"
            )
        return result


def _attach_result_from_response(
    response: AttachEnvironmentOntologyResponse,
) -> EnvironmentOntologyAttachResult:
    return EnvironmentOntologyAttachResult(
        status=response.status,
        error=response.error,
        membership=(
            _membership_from_dto(response.membership)
            if response.membership is not None
            else None
        ),
        commit_id=response.commit_id,
        object_instance_graph_commit_id=response.object_instance_graph_commit_id,
        graph_hash_pre=response.graph_hash_pre,
        graph_hash_post=response.graph_hash_post,
        evidence=dict(response.evidence),
        raw_response=response,
    )


def _list_result_from_response(
    response: ListEnvironmentOntologiesResponse,
) -> EnvironmentOntologyListResult:
    return EnvironmentOntologyListResult(
        status=response.status,
        error=response.error,
        memberships=tuple(_membership_from_dto(item) for item in response.memberships),
        commit_id=response.commit_id,
        object_instance_graph_commit_id=response.object_instance_graph_commit_id,
        graph_hash_post=response.graph_hash_post,
        evidence=dict(response.evidence),
        raw_response=response,
    )


def _runtime_result_from_response(
    response: EnsureEnvironmentOntologyRuntimeResponse,
) -> EnvironmentOntologyRuntimeResult:
    return EnvironmentOntologyRuntimeResult(
        status=response.status,
        error=response.error,
        ontology_id=response.ontology_id,
        package_name=response.package_name,
        fqn_prefix=response.fqn_prefix,
        artifact_set_id=response.artifact_set_id,
        runtime_projection_descriptor_count=(
            response.runtime_projection_descriptor_count
        ),
        capability_object_count=response.capability_object_count,
        capability_function_count=response.capability_function_count,
        registered_artifact_ref_count=response.registered_artifact_ref_count,
        registry_artifact_ref_count=response.registry_artifact_ref_count,
        membership_commit_id=response.membership_commit_id,
        evidence=dict(response.evidence),
        raw_response=response,
    )


def _membership_from_dto(
    membership: DtoEnvironmentOntologyMembership,
) -> EnvironmentOntologyMembership:
    return EnvironmentOntologyMembership(
        environment_ontology_id=membership.environment_ontology_id,
        ontology_id=membership.ontology_id,
        role=membership.role,
        status=membership.status,
        title=membership.title,
        description=membership.description,
        commit_id=membership.commit_id,
        graph_hash_post=membership.graph_hash_post,
        evidence=dict(membership.evidence),
        dto_membership=membership,
    )


def _status(value: object) -> str:
    return str(value or "").strip().casefold()


def _required_uuid(value: object, *, field_name: str) -> UUID:
    uuid_value = _optional_uuid(value)
    if uuid_value is None:
        raise ValueError(f"{field_name} is required.")
    return uuid_value


def _optional_uuid(value: object | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    text = str(value).strip()
    if not text:
        return None
    return UUID(text)


def _optional_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "EnvironmentOntologyAttachResult",
    "EnvironmentOntologyClient",
    "EnvironmentOntologyContext",
    "EnvironmentOntologyError",
    "EnvironmentOntologyGeneratedApiClient",
    "EnvironmentOntologyListResult",
    "EnvironmentOntologyMembership",
    "EnvironmentOntologyRuntimeResult",
]
