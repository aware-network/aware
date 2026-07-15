from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, field
import inspect
from typing import Protocol
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
)

from .state import (
    DEFAULT_SERVICE_ONTOLOGY_REPLICA_PROJECTOR_ID,
    ServiceOntologyReplicaApplyOutcome,
    ServiceOntologyReplicaCommitReceipt,
    ServiceOntologyReplicaStateStore,
    ServiceOntologyReplicaSubscriptionSpec,
    service_ontology_replica_subscription_id,
)
from .projector import (
    ServiceOntologyCommitSource,
    ServiceOntologyProjectionStore,
)


class EnvironmentCommitReceiptSdkClient(Protocol):
    def subscribe_lane_commit_receipts(
        self,
        *,
        watcher: Callable[
            [LaneCommitReceiptNotification],
            Awaitable[None] | None,
        ],
        branch_id: UUID | None = None,
        projection_hash: str | None = None,
    ) -> Callable[[], None]: ...


@dataclass(slots=True)
class ServiceOntologyReplicaWorker:
    store: ServiceOntologyReplicaStateStore
    subscriptions: tuple[ServiceOntologyReplicaSubscriptionSpec, ...]
    projector_id: str = DEFAULT_SERVICE_ONTOLOGY_REPLICA_PROJECTOR_ID
    commit_source: ServiceOntologyCommitSource | None = None
    projection_store: ServiceOntologyProjectionStore | None = None
    close_store_on_stop: bool = True
    _unsubscribe_by_lane: list[Callable[[], None]] = field(
        default_factory=list,
        init=False,
    )
    _subscription_ids_by_lane: dict[tuple[UUID, str], tuple[UUID, ...]] = field(
        default_factory=dict,
        init=False,
    )
    _environment_api_client: EnvironmentCommitReceiptSdkClient | None = field(
        default=None,
        init=False,
    )

    async def start(
        self,
        *,
        environment_api_client: EnvironmentCommitReceiptSdkClient,
    ) -> None:
        if self._unsubscribe_by_lane:
            return
        self._environment_api_client = environment_api_client
        lane_to_subscription_ids: dict[tuple[UUID, str], list[UUID]] = {}
        for spec in self.subscriptions:
            self._ensure_lane_subscription(spec=spec, subscribe=False)
            subscription_id = service_ontology_replica_subscription_id(spec=spec)
            lane_to_subscription_ids.setdefault(
                (spec.branch_id, _projection_hash(spec.projection_hash)),
                [],
            ).append(subscription_id)
        self._subscription_ids_by_lane = {
            lane: tuple(subscription_ids)
            for lane, subscription_ids in lane_to_subscription_ids.items()
        }
        if not self._subscription_ids_by_lane:
            return
        await _ensure_environment_sdk_notifications_started(environment_api_client)
        for branch_id, projection_hash in sorted(
            self._subscription_ids_by_lane,
            key=lambda item: (str(item[0]), item[1]),
        ):
            self._unsubscribe_by_lane.append(
                environment_api_client.subscribe_lane_commit_receipts(
                    watcher=self._build_lane_watcher(),
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                )
            )

    async def stop(self) -> None:
        while self._unsubscribe_by_lane:
            unsubscribe = self._unsubscribe_by_lane.pop()
            unsubscribe()
        self._subscription_ids_by_lane = {}
        self._environment_api_client = None
        if self.close_store_on_stop:
            self.store.close()
            if self.projection_store is not None:
                self.projection_store.close()

    async def handle_local_invoke_response(
        self,
        *,
        request: MetaGraphInvokeFunctionRequest,
        response: MetaGraphInvokeFunctionResponse,
        service_package_id: UUID | None = None,
        service_name: str | None = None,
    ) -> tuple[ServiceOntologyReplicaApplyOutcome, ...]:
        receipt = _lane_commit_receipt_from_invoke_response(
            request=request,
            response=response,
        )
        if receipt is None:
            return ()
        return await self.handle_local_commit_receipt(
            receipt=receipt,
            service_package_id=service_package_id,
            service_name=service_name,
        )

    async def handle_local_commit_receipt(
        self,
        *,
        receipt: ServiceOntologyReplicaCommitReceipt,
        service_package_id: UUID | None = None,
        service_name: str | None = None,
    ) -> tuple[ServiceOntologyReplicaApplyOutcome, ...]:
        self._ensure_lane_subscription(
            spec=ServiceOntologyReplicaSubscriptionSpec(
                service_package_id=service_package_id,
                service_name=service_name,
                branch_id=receipt.branch_id,
                projection_hash=receipt.projection_hash,
            ),
            subscribe=True,
        )
        return await self.handle_receipt(receipt=receipt)

    async def handle_receipt(
        self,
        *,
        receipt: ServiceOntologyReplicaCommitReceipt,
    ) -> tuple[ServiceOntologyReplicaApplyOutcome, ...]:
        outcomes: list[ServiceOntologyReplicaApplyOutcome] = []
        lane_key = (receipt.branch_id, _projection_hash(receipt.projection_hash))
        for subscription_id in self._subscription_ids_by_lane.get(lane_key, ()):
            commit_receipt_id = self.store.record_commit_receipt(
                subscription_id=subscription_id,
                receipt=receipt,
            )
            if self.commit_source is not None and self.projection_store is not None:
                try:
                    commit = await self.commit_source.get_object_instance_graph_commit(
                        receipt=receipt,
                    )
                    stats = self.projection_store.apply_commit(
                        receipt=receipt,
                        commit=commit,
                    )
                    outcomes.append(
                        self.store.record_apply_success(
                            subscription_id=subscription_id,
                            commit_receipt_id=commit_receipt_id,
                            receipt=receipt,
                            projector_id=self.projector_id,
                            class_row_count=stats.class_row_count,
                            association_row_count=stats.association_row_count,
                            mutation_row_count=stats.mutation_row_count,
                        )
                    )
                except Exception as exc:
                    outcomes.append(
                        self.store.record_apply_failure(
                            subscription_id=subscription_id,
                            commit_receipt_id=commit_receipt_id,
                            receipt=receipt,
                            projector_id=self.projector_id,
                            error=str(exc),
                        )
                    )
                continue
            outcomes.append(
                self.store.record_apply_success(
                    subscription_id=subscription_id,
                    commit_receipt_id=commit_receipt_id,
                    receipt=receipt,
                    projector_id=self.projector_id,
                )
            )
        return tuple(outcomes)

    def _build_lane_watcher(
        self,
    ) -> Callable[[LaneCommitReceiptNotification], Awaitable[None]]:
        async def _watcher(notification: LaneCommitReceiptNotification) -> None:
            await self.handle_receipt(
                receipt=service_ontology_replica_commit_receipt_from_environment_notification(
                    notification
                )
            )

        return _watcher

    def _ensure_lane_subscription(
        self,
        *,
        spec: ServiceOntologyReplicaSubscriptionSpec,
        subscribe: bool,
    ) -> UUID:
        subscription_id = self.store.ensure_subscription(spec=spec)
        lane = (spec.branch_id, _projection_hash(spec.projection_hash))
        existing_subscription_ids = self._subscription_ids_by_lane.get(lane, ())
        if subscription_id not in existing_subscription_ids:
            self._subscription_ids_by_lane[lane] = (
                *existing_subscription_ids,
                subscription_id,
            )
        if (
            subscribe
            and not existing_subscription_ids
            and self._environment_api_client is not None
        ):
            self._unsubscribe_by_lane.append(
                self._environment_api_client.subscribe_lane_commit_receipts(
                    watcher=self._build_lane_watcher(),
                    branch_id=spec.branch_id,
                    projection_hash=_projection_hash(spec.projection_hash),
                )
            )
        return subscription_id


def service_ontology_replica_subscription_specs_from_bindings(
    *,
    packages: Iterable[object],
) -> tuple[ServiceOntologyReplicaSubscriptionSpec, ...]:
    specs: list[ServiceOntologyReplicaSubscriptionSpec] = []
    seen_ids: set[UUID] = set()
    for package in packages:
        service_package_id = _uuid_or_none(getattr(package, "service_package_id", None))
        binding = getattr(package, "binding", None)
        prepared = getattr(binding, "prepared", None)
        subscriptions_by_name = (
            getattr(prepared, "service_subscriptions_by_name", None)
            or getattr(binding, "service_subscriptions_by_name", None)
            or {}
        )
        if not isinstance(subscriptions_by_name, dict):
            continue
        for service_name, subscriptions in subscriptions_by_name.items():
            service_name_text = str(service_name).strip() or None
            for subscription in tuple(subscriptions or ()):
                spec = _spec_from_binding(
                    subscription=subscription,
                    service_name=service_name_text,
                    service_package_id=service_package_id,
                )
                subscription_id = service_ontology_replica_subscription_id(spec=spec)
                if subscription_id in seen_ids:
                    continue
                seen_ids.add(subscription_id)
                specs.append(spec)
    return tuple(specs)


def _spec_from_binding(
    *,
    subscription: object,
    service_name: str | None,
    service_package_id: UUID | None,
) -> ServiceOntologyReplicaSubscriptionSpec:
    return ServiceOntologyReplicaSubscriptionSpec(
        branch_id=_required_uuid(subscription, "branch_id"),
        projection_hash=_projection_hash(getattr(subscription, "projection_hash")),
        service_package_id=service_package_id,
        service_name=service_name,
        source_api_projection_id=_uuid_or_none(
            getattr(subscription, "service_config_api_projection_id", None)
        ),
        api_graph_projection_id=_uuid_or_none(
            getattr(subscription, "api_graph_projection_id", None)
        ),
    )


async def _ensure_environment_sdk_notifications_started(
    client: EnvironmentCommitReceiptSdkClient,
) -> None:
    ensure_registered = getattr(client, "ensure_interface_session_registered", None)
    if not callable(ensure_registered):
        return
    result = ensure_registered()
    if inspect.isawaitable(result):
        await result


def _required_uuid(value: object, attr: str) -> UUID:
    parsed = _uuid_or_none(getattr(value, attr, None))
    if parsed is None:
        raise ValueError(f"Service ontology replica subscription missing {attr}.")
    return parsed


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value)
    return None


def _projection_hash(value: object) -> str:
    token = str(value or "").strip()
    if not token:
        raise ValueError("projection_hash must be non-empty")
    return token


def _lane_commit_receipt_from_invoke_response(
    *,
    request: MetaGraphInvokeFunctionRequest,
    response: MetaGraphInvokeFunctionResponse,
) -> ServiceOntologyReplicaCommitReceipt | None:
    status = _enum_or_token_value(response.status)
    if status not in {"succeeded", "success", "ok"}:
        return None
    if response.domain_commit_id is None:
        return None
    branch_id = _uuid_or_none(response.domain_branch_id) or _uuid_or_none(
        request.domain_branch_id
    )
    projection_hash = str(
        response.domain_projection_hash or request.domain_projection_hash or ""
    ).strip()
    if branch_id is None or not projection_hash:
        return None
    return ServiceOntologyReplicaCommitReceipt(
        actor_id=response.actor_id or request.actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=response.domain_commit_id,
        object_instance_graph_commit_id=response.object_instance_graph_commit_id,
        created_at_unix_ms=None,
        operation_label="service_host.local_invoke_function",
        call_target=request.call_target,
        function_id=request.function_id,
        object_id=request.target_object_id,
        graph_hash_post=response.graph_hash_post,
        object_instance_graph_id=None,
        root_object_id=response.root_object_id,
        head_version=None,
    )


def service_ontology_replica_commit_receipt_from_environment_notification(
    notification: LaneCommitReceiptNotification,
) -> ServiceOntologyReplicaCommitReceipt:
    return ServiceOntologyReplicaCommitReceipt(
        actor_id=notification.actor_id,
        branch_id=notification.branch_id,
        projection_hash=notification.projection_hash,
        commit_id=notification.commit_id,
        object_instance_graph_commit_id=notification.object_instance_graph_commit_id,
        graph_hash_post=notification.graph_hash_post,
        object_instance_graph_id=notification.object_instance_graph_id,
        root_object_id=notification.root_object_id,
        head_version=notification.head_version,
        created_at_unix_ms=notification.created_at_unix_ms,
        operation_label=notification.operation_label,
        call_target=notification.call_target,
        function_id=notification.function_id,
        object_id=notification.object_id,
        class_instance_identity_id=notification.class_instance_identity_id,
    )


def _enum_or_token_value(value: object) -> str:
    raw_value = getattr(value, "value", value)
    token = str(raw_value or "").strip().casefold()
    if "." in token:
        token = token.rsplit(".", 1)[-1]
    return token


__all__ = [
    "EnvironmentCommitReceiptSdkClient",
    "ServiceOntologyReplicaWorker",
    "service_ontology_replica_commit_receipt_from_environment_notification",
    "service_ontology_replica_subscription_specs_from_bindings",
]
