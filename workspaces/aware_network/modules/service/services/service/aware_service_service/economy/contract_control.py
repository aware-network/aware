from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from aware_code.types import JsonObject
from aware_meta_service.local_sdk import MaterializationLaneContext
from aware_orm.session.session import Session
from aware_service_runtime.api_ingress.contract_access_context import (
    ServiceContractAccessContextBootstrapReadModel,
    read_service_contract_access_context_bootstrap,
    service_contract_access_context_bootstrap_payload,
)
from aware_service_runtime.materialization.snapshot_commit import (
    ServiceContractAccessSnapshotCommitResult,
    commit_service_contract_access_snapshot,
)
from aware_service_ontology.stable_ids import stable_service_config_id
from aware_service_service.activation.runtime_context import (
    ActivatedImplementationRuntimeContext,
    bind_service_host_runtime_lane,
)
from aware_service_service.ontology.projections import (
    resolve_canonical_service_host_projection,
)


LoadCommittedServiceLaneSession = Callable[..., Awaitable[object]]


@dataclass(frozen=True, slots=True)
class WalletBackedServiceContractAccessContextResolution:
    read_model: ServiceContractAccessContextBootstrapReadModel
    payload: JsonObject
    session: Session

    @property
    def ready(self) -> bool:
        return self.read_model.ready

    @property
    def blockers(self) -> tuple[str, ...]:
        return self.read_model.blockers


@dataclass(frozen=True, slots=True)
class EnsuredWalletBackedServiceContractAccessContextResolution:
    read_model: ServiceContractAccessContextBootstrapReadModel
    payload: JsonObject
    session: Session
    ensured: bool
    admission: JsonObject | None = None
    snapshot_commit: ServiceContractAccessSnapshotCommitResult | None = None

    @property
    def ready(self) -> bool:
        return self.read_model.ready

    @property
    def blockers(self) -> tuple[str, ...]:
        return self.read_model.blockers


async def _load_committed_service_lane_session(**kwargs: object) -> object:
    from aware_service_runtime.implementation_package import (
        load_committed_service_lane_session,
    )

    return await load_committed_service_lane_session(**kwargs)


def build_service_subscription_lane(
    *,
    runtime_context: ActivatedImplementationRuntimeContext,
    branch_id: UUID,
) -> MaterializationLaneContext:
    return bind_service_contract_control_lane(
        runtime_context=runtime_context,
        projection="ServiceSubscription",
        branch_id=branch_id,
    )


def build_service_contract_lane(
    *,
    runtime_context: ActivatedImplementationRuntimeContext,
    branch_id: UUID,
) -> MaterializationLaneContext:
    return bind_service_contract_control_lane(
        runtime_context=runtime_context,
        projection="ServiceContract",
        branch_id=branch_id,
    )


def bind_service_contract_control_lane(
    *,
    runtime_context: ActivatedImplementationRuntimeContext,
    projection: str,
    branch_id: UUID,
) -> MaterializationLaneContext:
    runtime_lane = bind_service_host_runtime_lane(
        runtime=runtime_context.runtime,
        projection=resolve_canonical_service_host_projection(
            index=runtime_context.index,
            projection=projection,
        ),
        branch_id=branch_id,
    )
    return _materialization_lane_context(runtime_lane)


async def load_contract_access_context_bootstrap_session(
    *,
    index: object,
    service_config_session: Session | None = None,
    service_config_lane: MaterializationLaneContext,
    service_lane: MaterializationLaneContext,
    service_contract_lane: MaterializationLaneContext,
    service_subscription_lane: MaterializationLaneContext,
    load_session: LoadCommittedServiceLaneSession = _load_committed_service_lane_session,
) -> Session:
    service_config_lane = _materialization_lane_context(service_config_lane)
    service_lane = _materialization_lane_context(service_lane)
    service_contract_lane = _materialization_lane_context(service_contract_lane)
    service_subscription_lane = _materialization_lane_context(service_subscription_lane)
    if service_config_session is None:
        service_config_session = require_service_session(
            await load_session(
                index=index,
                lane=service_config_lane,
                error_context="Service host contract access context bootstrap",
            ),
            error_context=(
                "Service host contract access context bootstrap ServiceConfig lane"
            ),
        )
    else:
        service_config_session = require_service_session(
            service_config_session,
            error_context=(
                "Service host contract access context bootstrap ServiceConfig lane"
            ),
        )
    sessions: list[Session] = [service_config_session]
    lane_sessions: list[tuple[MaterializationLaneContext, Session]] = [
        (service_config_lane, service_config_session),
    ]
    for lane, label, required in (
        (service_lane, "Service", True),
        (service_contract_lane, "ServiceContract", False),
        (service_subscription_lane, "ServiceSubscription", False),
    ):
        existing = next(
            (
                session
                for candidate_lane, session in lane_sessions
                if same_materialization_lane(candidate_lane, lane)
            ),
            None,
        )
        if existing is not None:
            sessions.append(existing)
            continue
        try:
            session = require_service_session(
                await load_session(
                    index=index,
                    lane=lane,
                    error_context="Service host contract access context bootstrap",
                ),
                error_context=(
                    "Service host contract access context bootstrap " f"{label} lane"
                ),
            )
        except RuntimeError as exc:
            if required or "requires a committed lane head" not in str(exc):
                raise
            session = Session(branch_id=lane.branch_id, skip_db=True)
        sessions.append(session)
        lane_sessions.append((lane, session))
    return merge_service_sessions(*sessions)


async def resolve_wallet_backed_service_contract_access_context(
    *,
    index: object,
    service_id: UUID,
    consumer_finance_entity_id: UUID | None,
    service_config_lane: MaterializationLaneContext,
    service_lane: MaterializationLaneContext,
    service_contract_lane: MaterializationLaneContext,
    service_subscription_lane: MaterializationLaneContext,
    service_operation_config_id: UUID | None = None,
    service_subscription_id: UUID | None = None,
    service_contract_id: UUID | None = None,
    service_contract_config_id: UUID | None = None,
    smart_contract_id: UUID | None = None,
    service_config_session: Session | None = None,
    load_session: LoadCommittedServiceLaneSession = _load_committed_service_lane_session,
) -> WalletBackedServiceContractAccessContextResolution:
    session = await load_contract_access_context_bootstrap_session(
        index=index,
        service_config_session=service_config_session,
        service_config_lane=service_config_lane,
        service_lane=service_lane,
        service_contract_lane=service_contract_lane,
        service_subscription_lane=service_subscription_lane,
        load_session=load_session,
    )
    read_model = read_service_contract_access_context_bootstrap(
        session=session,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_operation_config_id=service_operation_config_id,
        service_subscription_id=service_subscription_id,
        service_contract_id=service_contract_id,
        service_contract_config_id=service_contract_config_id,
        smart_contract_id=smart_contract_id,
    )
    return WalletBackedServiceContractAccessContextResolution(
        read_model=read_model,
        payload=service_contract_access_context_bootstrap_payload(read_model),
        session=session,
    )


async def ensure_wallet_backed_service_contract_access_context(
    *,
    index: object,
    service_name: str,
    service_id: UUID,
    consumer_finance_entity_id: UUID | None,
    service_config_lane: MaterializationLaneContext,
    service_lane: MaterializationLaneContext,
    service_contract_lane: MaterializationLaneContext,
    service_subscription_lane: MaterializationLaneContext,
    service_operation_config_id: UUID | None = None,
    service_subscription_id: UUID | None = None,
    service_contract_id: UUID | None = None,
    service_contract_config_id: UUID | None = None,
    smart_contract_id: UUID | None = None,
    service_contract_config_name: str = "local_dev",
    commercial_profile_id: UUID | None = None,
    producer_finance_entity_id: UUID | None = None,
    service_plan_id: UUID | None = None,
    load_session: LoadCommittedServiceLaneSession = _load_committed_service_lane_session,
) -> EnsuredWalletBackedServiceContractAccessContextResolution:
    initial = await resolve_wallet_backed_service_contract_access_context(
        index=index,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_operation_config_id=service_operation_config_id,
        service_subscription_id=service_subscription_id,
        service_contract_id=service_contract_id,
        service_contract_config_id=service_contract_config_id,
        smart_contract_id=smart_contract_id,
        service_config_lane=service_config_lane,
        service_lane=service_lane,
        service_contract_lane=service_contract_lane,
        service_subscription_lane=service_subscription_lane,
        load_session=load_session,
    )
    if initial.ready or consumer_finance_entity_id is None:
        return EnsuredWalletBackedServiceContractAccessContextResolution(
            read_model=initial.read_model,
            payload=initial.payload,
            session=initial.session,
            ensured=False,
            admission=_ensure_admission_payload(
                ensured=False,
                service_id=service_id,
                consumer_finance_entity_id=consumer_finance_entity_id,
                service_contract_config_name=service_contract_config_name,
                bootstrap_before=initial.payload,
                snapshot_commit=None,
            ),
            snapshot_commit=None,
        )
    if not _can_materialize_missing_access_truth(initial.blockers):
        return EnsuredWalletBackedServiceContractAccessContextResolution(
            read_model=initial.read_model,
            payload=initial.payload,
            session=initial.session,
            ensured=False,
            admission=_ensure_admission_payload(
                ensured=False,
                service_id=service_id,
                consumer_finance_entity_id=consumer_finance_entity_id,
                service_contract_config_name=service_contract_config_name,
                bootstrap_before=initial.payload,
                snapshot_commit=None,
            ),
            snapshot_commit=None,
        )
    service_config_lane = _materialization_lane_context(service_config_lane)
    service_contract_lane = _materialization_lane_context(service_contract_lane)
    service_subscription_lane = _materialization_lane_context(service_subscription_lane)
    snapshot_commit = await commit_service_contract_access_snapshot(
        index=index,
        actor_id=None,
        service_config_branch_id=service_config_lane.branch_id,
        service_config_projection_hash=service_config_lane.projection_hash,
        service_contract_branch_id=service_contract_lane.branch_id,
        service_contract_projection_hash=service_contract_lane.projection_hash,
        service_subscription_branch_id=service_subscription_lane.branch_id,
        service_subscription_projection_hash=service_subscription_lane.projection_hash,
        service_config_id=stable_service_config_id(name=service_name),
        service_name=service_name,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_contract_config_name=service_contract_config_name,
        service_contract_config_id=service_contract_config_id,
        service_contract_id=service_contract_id,
        service_subscription_id=service_subscription_id,
        smart_contract_id=smart_contract_id,
        commercial_profile_id=commercial_profile_id,
        producer_finance_entity_id=producer_finance_entity_id,
        service_plan_id=service_plan_id,
    )
    final = await resolve_wallet_backed_service_contract_access_context(
        index=index,
        service_id=service_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_operation_config_id=service_operation_config_id,
        service_subscription_id=snapshot_commit.service_subscription.id,
        service_contract_id=snapshot_commit.service_contract.id,
        service_contract_config_id=snapshot_commit.service_contract_config.id,
        smart_contract_id=snapshot_commit.service_contract.smart_contract_id,
        service_config_lane=service_config_lane,
        service_lane=service_lane,
        service_contract_lane=service_contract_lane,
        service_subscription_lane=service_subscription_lane,
        load_session=load_session,
    )
    return EnsuredWalletBackedServiceContractAccessContextResolution(
        read_model=final.read_model,
        payload=final.payload,
        session=final.session,
        ensured=final.ready,
        admission=_ensure_admission_payload(
            ensured=final.ready,
            service_id=service_id,
            consumer_finance_entity_id=consumer_finance_entity_id,
            service_contract_config_name=service_contract_config_name,
            bootstrap_before=initial.payload,
            snapshot_commit=snapshot_commit,
        ),
        snapshot_commit=snapshot_commit,
    )


def _can_materialize_missing_access_truth(blockers: tuple[str, ...]) -> bool:
    materializable = {
        "missing_subscription",
        "missing_service_contract",
        "missing_contract_config",
    }
    return bool(blockers) and set(blockers).issubset(materializable)


def _ensure_admission_payload(
    *,
    ensured: bool,
    service_id: UUID,
    consumer_finance_entity_id: UUID | None,
    service_contract_config_name: str,
    bootstrap_before: JsonObject,
    snapshot_commit: ServiceContractAccessSnapshotCommitResult | None,
) -> JsonObject:
    payload: dict[str, object] = {
        "schema": "aware.service.contract_access.ensure_admission.v0",
        "source": "aware_service_service.economy.contract_control",
        "ensured": ensured,
        "service_id": str(service_id),
        "service_contract_config_name": service_contract_config_name,
        "bootstrap_before": bootstrap_before,
    }
    if consumer_finance_entity_id is not None:
        payload["consumer_finance_entity_id"] = str(consumer_finance_entity_id)
    if snapshot_commit is not None:
        payload.update(
            {
                "service_contract_config_id": str(
                    snapshot_commit.service_contract_config.id
                ),
                "service_contract_id": str(snapshot_commit.service_contract.id),
                "service_subscription_id": str(snapshot_commit.service_subscription.id),
                "smart_contract_id": str(
                    snapshot_commit.service_contract.smart_contract_id
                ),
                "service_contract_config_commit_id": str(
                    snapshot_commit.service_contract_config_commit_id
                ),
                "service_contract_commit_id": str(
                    snapshot_commit.service_contract_commit_id
                ),
                "service_subscription_commit_id": str(
                    snapshot_commit.service_subscription_commit_id
                ),
                "object_count": snapshot_commit.object_count,
                "change_count": snapshot_commit.change_count,
            }
        )
    return cast(JsonObject, payload)


def same_materialization_lane(left: object, right: object) -> bool:
    left_branch_id = _lane_branch_id(left)
    right_branch_id = _lane_branch_id(right)
    left_projection_hash = _lane_projection_hash(left)
    right_projection_hash = _lane_projection_hash(right)
    return (
        left_branch_id is not None
        and left_branch_id == right_branch_id
        and left_projection_hash is not None
        and left_projection_hash == right_projection_hash
    )


def _lane_branch_id(lane: object) -> object:
    branch_id = getattr(lane, "branch_id", None)
    if branch_id is not None:
        return branch_id
    return getattr(getattr(lane, "binding", None), "branch_id", None)


def _lane_projection_hash(lane: object) -> str | None:
    value = getattr(lane, "projection_hash", None)
    if value is None:
        value = getattr(getattr(lane, "binding", None), "projection_hash", None)
    text = str(value or "").strip()
    return text or None


def _materialization_lane_context(lane: object) -> MaterializationLaneContext:
    if isinstance(lane, MaterializationLaneContext):
        return lane
    branch_id = _lane_branch_id(lane)
    projection_hash = _lane_projection_hash(lane)
    if not isinstance(branch_id, UUID) or projection_hash is None:
        raise TypeError(
            "Service contract bootstrap requires materialization lane identity."
        )
    return MaterializationLaneContext(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )


def require_service_session(value: object, *, error_context: str) -> Session:
    if isinstance(value, Session):
        return value
    raise TypeError(f"{error_context} did not resolve an ORM Session.")


def merge_service_sessions(*sessions: Session) -> Session:
    unique_sessions: list[Session] = []
    for session in sessions:
        if not any(session is candidate for candidate in unique_sessions):
            unique_sessions.append(session)
    if not unique_sessions:
        raise RuntimeError("Service contract access context bootstrap has no sessions.")
    if len(unique_sessions) == 1:
        return unique_sessions[0]
    merged = Session(branch_id=unique_sessions[0].branch_id, skip_db=True)
    for session in unique_sessions:
        for obj in session.imap_all_objects():
            merged.merge(obj)
    return merged


def resolve_activated_service_lane(
    *,
    activated: object,
    service_name: str,
    lane_attr: str,
    fallback: MaterializationLaneContext,
) -> MaterializationLaneContext:
    lane = activated_service_lane_or_none(
        activated=activated,
        service_name=service_name,
        lane_attr=lane_attr,
    )
    if lane is not None:
        return lane
    return fallback


def activated_service_lane_or_none(
    *,
    activated: object,
    service_name: str,
    lane_attr: str,
) -> MaterializationLaneContext | None:
    lanes_by_name = getattr(activated, lane_attr, None)
    if isinstance(lanes_by_name, Mapping):
        lane = lanes_by_name.get(service_name)
        if isinstance(lane, MaterializationLaneContext):
            return lane
    return None


__all__ = [
    "WalletBackedServiceContractAccessContextResolution",
    "activated_service_lane_or_none",
    "build_service_contract_lane",
    "build_service_subscription_lane",
    "load_contract_access_context_bootstrap_session",
    "merge_service_sessions",
    "require_service_session",
    "resolve_activated_service_lane",
    "resolve_wallet_backed_service_contract_access_context",
    "same_materialization_lane",
]
