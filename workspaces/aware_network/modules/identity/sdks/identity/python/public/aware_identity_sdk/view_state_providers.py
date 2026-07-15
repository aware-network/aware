from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID

from aware_identity_service_dto.actor.view import (
    ActorCommitEntryV1,
    ActorCommitsViewStateV1,
    ActorRoleEntryV1,
    ActorRolesViewStateV1,
    ActorSubscriptionEntryV1,
    ActorSubscriptionsViewStateV1,
)
from aware_identity_ontology_dto.identity.identity import Identity
from aware_identity_service_dto.actor.commit import ActorCommitRecord
from aware_identity_service_dto.actor.commit import ActorCommitResolveResult
from aware_identity_service_dto.actor.subscription import ActorSubscriptionBridgeConfig
from aware_identity_service_dto.actor.subscription import ActorSubscriptionResolveResult
from aware_identity_service_dto.identity.view import IdentityAdmissionViewStateV1
from aware_identity_service_dto.role.assignment import RoleAssignmentBinding
from aware_identity_service_dto.role.assignment import RoleAssignmentResolveResult
from pydantic import BaseModel, ConfigDict, Field

ACTOR_ROLES_API_VIEW_REF = "identity.actor_roles"
ACTOR_ROLES_PROJECTION_VIEW_KEY = "actor.roles.v1"
ACTOR_COMMITS_API_VIEW_REF = "identity.actor_commits"
ACTOR_COMMITS_PROJECTION_VIEW_KEY = "actor.commits.v1"
ACTOR_SUBSCRIPTIONS_API_VIEW_REF = "identity.actor_subscriptions"
ACTOR_SUBSCRIPTIONS_PROJECTION_VIEW_KEY = "actor.subscriptions.v1"
IDENTITY_ADMISSION_API_VIEW_REF = "identity.identity_admission"
IDENTITY_ADMISSION_PROJECTION_VIEW_KEY = "identity.admission.v1"


class RawOntologyDeltaV1(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    delta_id: str | None = Field(default=None)
    commit_id: str | None = Field(default=None)
    kind: str = Field(default="raw")
    payload: dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class ViewProviderProvenanceV1(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    source_kind: str | None = Field(default=None)
    request_id: str | None = Field(default=None)
    branch_id: str | None = Field(default=None)
    head_commit_id: str | None = Field(default=None)
    previous_head_commit_id: str | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    root_class_instance_id: str | None = Field(default=None)
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    state_provider_ref: str | None = Field(default=None)

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class IdentityAdmissionV1ProviderInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    latest: Identity | None = Field(default=None)
    raw_deltas: list[RawOntologyDeltaV1] = Field(default_factory=list)
    provenance: ViewProviderProvenanceV1 = Field(
        default_factory=ViewProviderProvenanceV1
    )

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class ActorRolesV1ProviderInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    result: RoleAssignmentResolveResult | None = Field(default=None)
    actor_id: str | None = Field(default=None)
    actor_display_name: str | None = Field(default=None)
    error: str | None = Field(default=None)
    provenance: ViewProviderProvenanceV1 = Field(
        default_factory=ViewProviderProvenanceV1
    )

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class ActorCommitsV1ProviderInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    result: ActorCommitResolveResult | None = Field(default=None)
    actor_id: str | None = Field(default=None)
    actor_display_name: str | None = Field(default=None)
    error: str | None = Field(default=None)
    provenance: ViewProviderProvenanceV1 = Field(
        default_factory=ViewProviderProvenanceV1
    )

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class ActorSubscriptionsV1ProviderInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    result: ActorSubscriptionResolveResult | None = Field(default=None)
    actor_id: str | None = Field(default=None)
    actor_display_name: str | None = Field(default=None)
    error: str | None = Field(default=None)
    provenance: ViewProviderProvenanceV1 = Field(
        default_factory=ViewProviderProvenanceV1
    )

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class ActorReadClient(Protocol):
    async def resolve_role_assignments(
        self,
        *,
        class_instance_identity_id: UUID,
        actor_id: UUID | None = None,
        role_config_id: UUID | None = None,
        role_config_name: str | None = None,
        object_instance_graph_branch_key: str = "all",
        object_instance_graph_branch_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> RoleAssignmentResolveResult: ...

    async def resolve_actor_commits(
        self,
        *,
        actor_id: UUID,
        domain_branch_id: UUID | None = None,
        domain_projection_hash: str | None = None,
        domain_commit_id: UUID | None = None,
        environment_id: UUID | None = None,
        process_id: UUID | None = None,
        thread_id: UUID | None = None,
        receipt_actor_id: UUID | None = None,
        function_id: UUID | None = None,
        object_id: UUID | None = None,
        class_instance_identity_id: UUID | None = None,
        object_instance_graph_id: UUID | None = None,
        root_object_id: UUID | None = None,
        source: str | None = None,
        limit: int = 100,
        request_id: UUID | None = None,
    ) -> ActorCommitResolveResult: ...

    async def resolve_actor_subscriptions(
        self,
        *,
        actor_id: UUID | None = None,
        event_config_condition_config_id: UUID | None = None,
        object_instance_graph_identity_id: UUID | None = None,
        object_instance_graph_branch_id: UUID | None = None,
        include_inactive: bool = False,
        include_disabled: bool = False,
        request_id: UUID | None = None,
    ) -> ActorSubscriptionResolveResult: ...


def identity_admission_view_state_from_input(
    provider_input: IdentityAdmissionV1ProviderInput | Mapping[str, Any],
) -> IdentityAdmissionViewStateV1:
    typed_input = IdentityAdmissionV1ProviderInput.model_validate(provider_input)
    identity = typed_input.latest
    if identity is None:
        return IdentityAdmissionViewStateV1(
            admitted=False,
            status="pending",
            provenance=_provenance_payload(typed_input),
        )

    profile = getattr(identity, "identity_profile", None)
    admitted = profile is not None
    return IdentityAdmissionViewStateV1(
        admitted=admitted,
        identity_id=_model_id(identity),
        identity_profile_id=_model_id(profile),
        display_name=_optional_text(getattr(profile, "display_name", None)),
        public_handle=_optional_text(getattr(profile, "public_handle", None)),
        bio=_optional_text(getattr(profile, "bio", None)),
        status="admitted" if admitted else "pending",
        provenance=_provenance_payload(typed_input),
    )


def identity_admission_view_state(
    *,
    provider_input: IdentityAdmissionV1ProviderInput | Mapping[str, Any],
) -> IdentityAdmissionViewStateV1:
    return identity_admission_view_state_from_input(provider_input)


async def actor_roles_v1_provider_input_from_client(
    *,
    client: ActorReadClient,
    class_instance_identity_id: UUID,
    actor_id: UUID | None = None,
    actor_display_name: str | None = None,
    role_config_id: UUID | None = None,
    role_config_name: str | None = None,
    object_instance_graph_branch_key: str = "all",
    object_instance_graph_branch_id: UUID | None = None,
    request_id: UUID | None = None,
    provenance: ViewProviderProvenanceV1 | Mapping[str, Any] | None = None,
    raise_errors: bool = False,
) -> ActorRolesV1ProviderInput:
    base_provenance = _provider_provenance(provenance)
    try:
        result = await client.resolve_role_assignments(
            class_instance_identity_id=class_instance_identity_id,
            actor_id=actor_id,
            role_config_id=role_config_id,
            role_config_name=role_config_name,
            object_instance_graph_branch_key=object_instance_graph_branch_key,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            request_id=request_id,
        )
    except Exception as exc:
        if raise_errors:
            raise
        return ActorRolesV1ProviderInput(
            actor_id=_uuid_text(actor_id),
            actor_display_name=actor_display_name,
            error=str(exc),
            provenance=base_provenance,
        )
    return ActorRolesV1ProviderInput(
        result=result,
        actor_id=_uuid_text(actor_id),
        actor_display_name=actor_display_name,
        provenance=_provider_provenance(
            {
                **base_provenance.to_json(),
                "source_kind": base_provenance.source_kind or "identity_sdk",
                "request_id": _optional_text(result.request_id)
                or base_provenance.request_id,
            }
        ),
    )


async def actor_commits_v1_provider_input_from_client(
    *,
    client: ActorReadClient,
    actor_id: UUID,
    actor_display_name: str | None = None,
    domain_branch_id: UUID | None = None,
    domain_projection_hash: str | None = None,
    domain_commit_id: UUID | None = None,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    receipt_actor_id: UUID | None = None,
    function_id: UUID | None = None,
    object_id: UUID | None = None,
    class_instance_identity_id: UUID | None = None,
    object_instance_graph_id: UUID | None = None,
    root_object_id: UUID | None = None,
    source: str | None = None,
    limit: int = 100,
    request_id: UUID | None = None,
    provenance: ViewProviderProvenanceV1 | Mapping[str, Any] | None = None,
    raise_errors: bool = False,
) -> ActorCommitsV1ProviderInput:
    base_provenance = _provider_provenance(provenance)
    try:
        result = await client.resolve_actor_commits(
            actor_id=actor_id,
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            domain_commit_id=domain_commit_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            receipt_actor_id=receipt_actor_id,
            function_id=function_id,
            object_id=object_id,
            class_instance_identity_id=class_instance_identity_id,
            object_instance_graph_id=object_instance_graph_id,
            root_object_id=root_object_id,
            source=source,
            limit=limit,
            request_id=request_id,
        )
    except Exception as exc:
        if raise_errors:
            raise
        return ActorCommitsV1ProviderInput(
            actor_id=_uuid_text(actor_id),
            actor_display_name=actor_display_name,
            error=str(exc),
            provenance=base_provenance,
        )
    return ActorCommitsV1ProviderInput(
        result=result,
        actor_id=_uuid_text(actor_id),
        actor_display_name=actor_display_name,
        provenance=_provider_provenance(
            {
                **base_provenance.to_json(),
                "source_kind": base_provenance.source_kind or "identity_sdk",
                "request_id": _optional_text(result.request_id)
                or base_provenance.request_id,
            }
        ),
    )


async def actor_subscriptions_v1_provider_input_from_client(
    *,
    client: ActorReadClient,
    actor_id: UUID | None = None,
    actor_display_name: str | None = None,
    event_config_condition_config_id: UUID | None = None,
    object_instance_graph_identity_id: UUID | None = None,
    object_instance_graph_branch_id: UUID | None = None,
    include_inactive: bool = False,
    include_disabled: bool = False,
    request_id: UUID | None = None,
    provenance: ViewProviderProvenanceV1 | Mapping[str, Any] | None = None,
    raise_errors: bool = False,
) -> ActorSubscriptionsV1ProviderInput:
    base_provenance = _provider_provenance(provenance)
    try:
        result = await client.resolve_actor_subscriptions(
            actor_id=actor_id,
            event_config_condition_config_id=event_config_condition_config_id,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            include_inactive=include_inactive,
            include_disabled=include_disabled,
            request_id=request_id,
        )
    except Exception as exc:
        if raise_errors:
            raise
        return ActorSubscriptionsV1ProviderInput(
            actor_id=_uuid_text(actor_id),
            actor_display_name=actor_display_name,
            error=str(exc),
            provenance=base_provenance,
        )
    return ActorSubscriptionsV1ProviderInput(
        result=result,
        actor_id=_uuid_text(actor_id),
        actor_display_name=actor_display_name,
        provenance=_provider_provenance(
            {
                **base_provenance.to_json(),
                "source_kind": base_provenance.source_kind or "identity_sdk",
                "request_id": _optional_text(result.request_id)
                or base_provenance.request_id,
            }
        ),
    )


def actor_roles_view_state_from_result(
    result: RoleAssignmentResolveResult | Mapping[str, Any] | None,
    *,
    actor_id: str | UUID | None = None,
    actor_display_name: str | None = None,
    error: str | None = None,
    provenance: ViewProviderProvenanceV1 | Mapping[str, Any] | None = None,
):
    return actor_roles_view_state_from_input(
        ActorRolesV1ProviderInput(
            result=(
                RoleAssignmentResolveResult.model_validate(result)
                if result is not None
                else None
            ),
            actor_id=_optional_text(actor_id),
            actor_display_name=actor_display_name,
            error=error,
            provenance=_provider_provenance(provenance),
        )
    )


def actor_commits_view_state_from_result(
    result: ActorCommitResolveResult | Mapping[str, Any] | None,
    *,
    actor_id: str | UUID | None = None,
    actor_display_name: str | None = None,
    error: str | None = None,
    provenance: ViewProviderProvenanceV1 | Mapping[str, Any] | None = None,
):
    return actor_commits_view_state_from_input(
        ActorCommitsV1ProviderInput(
            result=(
                ActorCommitResolveResult.model_validate(result)
                if result is not None
                else None
            ),
            actor_id=_optional_text(actor_id),
            actor_display_name=actor_display_name,
            error=error,
            provenance=_provider_provenance(provenance),
        )
    )


def actor_subscriptions_view_state_from_result(
    result: ActorSubscriptionResolveResult | Mapping[str, Any] | None,
    *,
    actor_id: str | UUID | None = None,
    actor_display_name: str | None = None,
    error: str | None = None,
    provenance: ViewProviderProvenanceV1 | Mapping[str, Any] | None = None,
):
    return actor_subscriptions_view_state_from_input(
        ActorSubscriptionsV1ProviderInput(
            result=(
                ActorSubscriptionResolveResult.model_validate(result)
                if result is not None
                else None
            ),
            actor_id=_optional_text(actor_id),
            actor_display_name=actor_display_name,
            error=error,
            provenance=_provider_provenance(provenance),
        )
    )


def actor_roles_view_state_from_input(
    provider_input: ActorRolesV1ProviderInput | Mapping[str, Any],
):
    _, ActorRolesViewStateV1 = _actor_roles_contracts()
    typed_input = ActorRolesV1ProviderInput.model_validate(provider_input)
    entries = [_actor_role_entry(binding) for binding in _role_bindings(typed_input)]
    status = _provider_status(
        result=typed_input.result, entries=entries, error=typed_input.error
    )
    return ActorRolesViewStateV1(
        status=status,
        actor_id=typed_input.actor_id
        or _first_entry_actor_id(_role_bindings(typed_input)),
        actor_display_name=typed_input.actor_display_name,
        entries=entries,
        summary=_count_summary(
            entries, singular="role assignment", plural="role assignments"
        ),
        error=typed_input.error,
        provenance=_actor_provenance_payload(
            typed_input.provenance,
            view_ref=ACTOR_ROLES_API_VIEW_REF,
            view_key=ACTOR_ROLES_PROJECTION_VIEW_KEY,
            entry_count=len(entries),
        ),
    )


def actor_commits_view_state_from_input(
    provider_input: ActorCommitsV1ProviderInput | Mapping[str, Any],
):
    _, ActorCommitsViewStateV1 = _actor_commits_contracts()
    typed_input = ActorCommitsV1ProviderInput.model_validate(provider_input)
    commits = _actor_commits(typed_input)
    entries = [_actor_commit_entry(commit) for commit in commits]
    status = _provider_status(
        result=typed_input.result, entries=entries, error=typed_input.error
    )
    return ActorCommitsViewStateV1(
        status=status,
        actor_id=typed_input.actor_id or _first_entry_actor_id(commits),
        actor_display_name=typed_input.actor_display_name,
        entries=entries,
        summary=_count_summary(entries, singular="commit", plural="commits"),
        error=typed_input.error,
        provenance=_actor_provenance_payload(
            typed_input.provenance,
            view_ref=ACTOR_COMMITS_API_VIEW_REF,
            view_key=ACTOR_COMMITS_PROJECTION_VIEW_KEY,
            entry_count=len(entries),
        ),
    )


def actor_subscriptions_view_state_from_input(
    provider_input: ActorSubscriptionsV1ProviderInput | Mapping[str, Any],
):
    _, ActorSubscriptionsViewStateV1 = _actor_subscriptions_contracts()
    typed_input = ActorSubscriptionsV1ProviderInput.model_validate(provider_input)
    subscriptions = _actor_subscriptions(typed_input)
    entries = [
        _actor_subscription_entry(subscription) for subscription in subscriptions
    ]
    status = _provider_status(
        result=typed_input.result, entries=entries, error=typed_input.error
    )
    return ActorSubscriptionsViewStateV1(
        status=status,
        actor_id=typed_input.actor_id or _first_entry_actor_id(subscriptions),
        actor_display_name=typed_input.actor_display_name,
        entries=entries,
        summary=_count_summary(
            entries, singular="subscription", plural="subscriptions"
        ),
        error=typed_input.error,
        provenance=_actor_provenance_payload(
            typed_input.provenance,
            view_ref=ACTOR_SUBSCRIPTIONS_API_VIEW_REF,
            view_key=ACTOR_SUBSCRIPTIONS_PROJECTION_VIEW_KEY,
            entry_count=len(entries),
        ),
    )


def actor_roles_view_state(
    *,
    provider_input: ActorRolesV1ProviderInput | Mapping[str, Any],
):
    return actor_roles_view_state_from_input(provider_input)


def actor_commits_view_state(
    *,
    provider_input: ActorCommitsV1ProviderInput | Mapping[str, Any],
):
    return actor_commits_view_state_from_input(provider_input)


def actor_subscriptions_view_state(
    *,
    provider_input: ActorSubscriptionsV1ProviderInput | Mapping[str, Any],
):
    return actor_subscriptions_view_state_from_input(provider_input)


def identity_admission_v1_provider_input(
    provider_context: object,
) -> IdentityAdmissionV1ProviderInput:
    latest_ontology = getattr(provider_context, "latest_ontology", None)
    raw_ontology_deltas = getattr(provider_context, "raw_ontology_deltas", None)
    if not callable(latest_ontology) or not callable(raw_ontology_deltas):
        raise TypeError(
            "Identity admission view provider input requires Interface Host "
            "provider context with latest_ontology and raw_ontology_deltas."
        )
    latest_value = latest_ontology(Identity)
    return IdentityAdmissionV1ProviderInput(
        latest=(
            Identity.model_validate(latest_value) if latest_value is not None else None
        ),
        raw_deltas=_raw_deltas(raw_ontology_deltas()),
        provenance=ViewProviderProvenanceV1.model_validate(
            dict(getattr(provider_context, "provenance", {}) or {})
        ),
    )


setattr(
    identity_admission_view_state,
    "provider_input_resolver",
    identity_admission_v1_provider_input,
)

setattr(
    actor_roles_view_state,
    "provider_input_resolver",
    ActorRolesV1ProviderInput.model_validate,
)
setattr(
    actor_commits_view_state,
    "provider_input_resolver",
    ActorCommitsV1ProviderInput.model_validate,
)
setattr(
    actor_subscriptions_view_state,
    "provider_input_resolver",
    ActorSubscriptionsV1ProviderInput.model_validate,
)


def _provenance_payload(
    provider_input: IdentityAdmissionV1ProviderInput,
) -> dict[str, Any]:
    payload = provider_input.provenance.to_json()
    payload["view_ref"] = payload.get("view_ref") or IDENTITY_ADMISSION_API_VIEW_REF
    payload["projection_view_key"] = (
        payload.get("projection_view_key") or IDENTITY_ADMISSION_PROJECTION_VIEW_KEY
    )
    payload["raw_delta_count"] = len(provider_input.raw_deltas)
    return payload


def _provider_provenance(
    value: ViewProviderProvenanceV1 | Mapping[str, Any] | None,
) -> ViewProviderProvenanceV1:
    if isinstance(value, ViewProviderProvenanceV1):
        return value
    payload = dict(value or {})
    payload.setdefault("source_kind", "identity_sdk")
    return ViewProviderProvenanceV1.model_validate(payload)


def _actor_role_entry(binding: RoleAssignmentBinding):
    ActorRoleEntryV1, _ = _actor_roles_contracts()
    return ActorRoleEntryV1(
        role_assignment_id=_optional_text(binding.actor_role_id),
        role_config_id=_optional_text(binding.role_config_id),
        scope=binding.object_instance_graph_branch_key,
        status="active",
        metadata={
            "role_id": _optional_text(binding.role_id),
            "role_class_instance_id": _optional_text(binding.role_class_instance_id),
            "class_instance_identity_id": _optional_text(
                binding.class_instance_identity_id
            ),
            "role_config_class_config_id": _optional_text(
                binding.role_config_class_config_id
            ),
            "object_instance_graph_identity_id": _optional_text(
                binding.object_instance_graph_identity_id
            ),
            "object_instance_graph_branch_id": _optional_text(
                binding.object_instance_graph_branch_id
            ),
        },
    )


def _actor_commit_entry(commit: ActorCommitRecord):
    ActorCommitEntryV1, _ = _actor_commits_contracts()
    return ActorCommitEntryV1(
        actor_commit_id=_optional_text(commit.actor_commit_id),
        commit_id=_optional_text(commit.domain_commit_id),
        branch_id=_optional_text(commit.domain_branch_id),
        summary=_commit_summary(commit),
        action_label=commit.operation_label,
        target_kind=commit.call_target,
        target_label=_optional_text(commit.object_id) or commit.call_target,
        authored_at=_unix_ms_to_iso(commit.created_at_unix_ms),
        metadata={
            "domain_projection_hash": commit.domain_projection_hash,
            "object_instance_graph_commit_id": _optional_text(
                commit.object_instance_graph_commit_id
            ),
            "object_instance_graph_identity_id": _optional_text(
                commit.object_instance_graph_identity_id
            ),
            "environment_id": _optional_text(commit.environment_id),
            "process_id": _optional_text(commit.process_id),
            "thread_id": _optional_text(commit.thread_id),
            "receipt_actor_id": _optional_text(commit.receipt_actor_id),
            "function_id": _optional_text(commit.function_id),
            "class_instance_identity_id": _optional_text(
                commit.class_instance_identity_id
            ),
            "graph_hash_post": commit.graph_hash_post,
            "object_instance_graph_id": _optional_text(commit.object_instance_graph_id),
            "root_object_id": _optional_text(commit.root_object_id),
            "head_version": commit.head_version,
            "source": commit.source,
        },
    )


def _actor_subscription_entry(subscription: ActorSubscriptionBridgeConfig):
    ActorSubscriptionEntryV1, _ = _actor_subscriptions_contracts()
    return ActorSubscriptionEntryV1(
        actor_subscription_id=_optional_text(subscription.id),
        event_kind=subscription.action_type,
        event_label=subscription.name,
        scope=_optional_text(subscription.object_instance_graph_branch_id)
        or _optional_text(subscription.object_instance_graph_identity_id),
        status=subscription.status if subscription.is_enabled else "disabled",
        metadata={
            "event_config_condition_config_scope_id": _optional_text(
                subscription.event_config_condition_config_scope_id
            ),
            "event_config_condition_config_id": _optional_text(
                subscription.event_config_condition_config_id
            ),
            "object_instance_graph_identity_id": _optional_text(
                subscription.object_instance_graph_identity_id
            ),
            "event_config_action_config_ids": [
                str(value) for value in subscription.event_config_action_config_ids
            ],
            "addressing_policy": subscription.addressing_policy,
            "is_enabled": subscription.is_enabled,
            "priority": subscription.priority,
            "filter_config": subscription.filter_config,
        },
    )


def _role_bindings(
    provider_input: ActorRolesV1ProviderInput,
) -> list[RoleAssignmentBinding]:
    return list(
        provider_input.result.bindings if provider_input.result is not None else []
    )


def _actor_commits(
    provider_input: ActorCommitsV1ProviderInput,
) -> list[ActorCommitRecord]:
    return list(
        provider_input.result.actor_commits if provider_input.result is not None else []
    )


def _actor_subscriptions(
    provider_input: ActorSubscriptionsV1ProviderInput,
) -> list[ActorSubscriptionBridgeConfig]:
    return list(
        provider_input.result.subscriptions if provider_input.result is not None else []
    )


def _provider_status(
    *, result: object | None, entries: Sequence[object], error: str | None
) -> str:
    if error:
        return "error"
    if result is None:
        return "waiting"
    return "ready" if entries else "empty"


def _count_summary(entries: Sequence[object], *, singular: str, plural: str) -> str:
    count = len(entries)
    label = singular if count == 1 else plural
    return f"{count} {label}."


def _actor_provenance_payload(
    provenance: ViewProviderProvenanceV1,
    *,
    view_ref: str,
    view_key: str,
    entry_count: int,
) -> dict[str, Any]:
    payload = provenance.to_json()
    payload["view_ref"] = view_ref
    payload["projection_view_key"] = payload.get("projection_view_key") or view_key
    payload["entry_count"] = entry_count
    return payload


def _first_entry_actor_id(entries: Sequence[object]) -> str | None:
    if not entries:
        return None
    return _optional_text(getattr(entries[0], "actor_id", None))


def _commit_summary(commit: ActorCommitRecord) -> str:
    if commit.operation_label:
        return commit.operation_label
    if commit.call_target:
        return commit.call_target
    return f"Commit {commit.domain_commit_id}"


def _unix_ms_to_iso(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()


def _uuid_text(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _actor_roles_contracts():
    return ActorRoleEntryV1, ActorRolesViewStateV1


def _actor_commits_contracts():
    return ActorCommitEntryV1, ActorCommitsViewStateV1


def _actor_subscriptions_contracts():
    return ActorSubscriptionEntryV1, ActorSubscriptionsViewStateV1


def _raw_deltas(value: object) -> list[RawOntologyDeltaV1]:
    if value is None:
        return []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [RawOntologyDeltaV1.model_validate(item) for item in value]
    return [RawOntologyDeltaV1.model_validate(value)]


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _model_id(model: object | None) -> str | None:
    if model is None:
        return None
    for attr in ("id", "identity_id", "source_object_id"):
        value = _optional_text(getattr(model, attr, None))
        if value is not None:
            return value
    return None


__all__ = [
    "ActorCommitsV1ProviderInput",
    "ActorReadClient",
    "ActorRolesV1ProviderInput",
    "ActorSubscriptionsV1ProviderInput",
    "IdentityAdmissionV1ProviderInput",
    "RawOntologyDeltaV1",
    "ViewProviderProvenanceV1",
    "actor_commits_v1_provider_input_from_client",
    "actor_commits_view_state",
    "actor_commits_view_state_from_input",
    "actor_commits_view_state_from_result",
    "actor_roles_v1_provider_input_from_client",
    "actor_roles_view_state",
    "actor_roles_view_state_from_input",
    "actor_roles_view_state_from_result",
    "actor_subscriptions_v1_provider_input_from_client",
    "actor_subscriptions_view_state",
    "actor_subscriptions_view_state_from_input",
    "actor_subscriptions_view_state_from_result",
    "identity_admission_v1_provider_input",
    "identity_admission_view_state",
    "identity_admission_view_state_from_input",
]
