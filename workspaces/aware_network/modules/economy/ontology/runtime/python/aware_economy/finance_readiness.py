from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar
from uuid import UUID

from aware_economy.meta_runtime import (
    EconomyMetaRuntimeLane,
    EconomyMetaRuntimeLaneBinder,
)
from aware_economy.wallet_custody import (
    derive_wallet_custody_material,
    normalize_finance_role_key,
)
from aware_economy_ontology.finance.finance_entity import FinanceEntity
from aware_economy_ontology.stable_ids import (
    stable_finance_entity_id,
    stable_wallet_id,
    stable_wallet_public_id,
)
from aware_economy_ontology.wallet.wallet import Wallet
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_orm.models.orm_model import ORMModel

_TModel = TypeVar("_TModel", bound=ORMModel)


@dataclass(frozen=True, slots=True)
class EconomyFinanceReadinessLanes:
    finance_entity_projection_hash: str
    wallet_projection_hash: str


@dataclass(frozen=True, slots=True)
class EconomyFinanceReadinessRuntimeContext:
    lane_binder: EconomyMetaRuntimeLaneBinder
    index: MetaGraphRuntimeIndex
    lanes: EconomyFinanceReadinessLanes


@dataclass(frozen=True, slots=True)
class EconomyFinanceReadinessOperationContext:
    actor_id: UUID | None


@dataclass(frozen=True, slots=True)
class FinanceEntityReadinessReceipt:
    actor_id: UUID
    finance_role_key: str
    finance_entity_id: UUID
    wallet_id: UUID
    wallet_public_id: UUID
    finance_entity_ready: bool
    wallet_ready: bool
    idempotent_replay: bool


def build_economy_finance_readiness_lanes(
    *,
    index: MetaGraphRuntimeIndex,
) -> EconomyFinanceReadinessLanes:
    return EconomyFinanceReadinessLanes(
        finance_entity_projection_hash=_find_projection_hash_by_name(
            index=index,
            projection_name="FinanceEntity",
        ),
        wallet_projection_hash=_find_projection_hash_by_name(
            index=index,
            projection_name="Wallet",
        ),
    )


def resolve_economy_finance_readiness_runtime_context(
    *,
    lane_binder: EconomyMetaRuntimeLaneBinder,
    index: MetaGraphRuntimeIndex,
) -> EconomyFinanceReadinessRuntimeContext:
    return EconomyFinanceReadinessRuntimeContext(
        lane_binder=lane_binder,
        index=index,
        lanes=build_economy_finance_readiness_lanes(index=index),
    )


async def resolve_finance_entity_readiness(
    *,
    runtime_context: EconomyFinanceReadinessRuntimeContext,
    actor_id: UUID,
    finance_role_key: str | None,
) -> FinanceEntityReadinessReceipt:
    expected = _expected_readiness_ids(
        actor_id=actor_id,
        finance_role_key=finance_role_key,
    )
    wallet = await _maybe_hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=expected.wallet_id,
        projection_hash=runtime_context.lanes.wallet_projection_hash,
        orm_class=Wallet,
        object_id=expected.wallet_id,
    )
    finance_entity = await _maybe_hydrate_committed_lane_object(
        index=runtime_context.index,
        branch_id=expected.finance_entity_id,
        projection_hash=runtime_context.lanes.finance_entity_projection_hash,
        orm_class=FinanceEntity,
        object_id=expected.finance_entity_id,
    )
    wallet_ready = wallet is not None
    finance_entity_ready = finance_entity is not None
    if wallet is not None:
        _validate_wallet(
            wallet,
            expected=expected,
            error_context="finance readiness wallet hydration",
        )
    if finance_entity is not None:
        _validate_finance_entity(
            finance_entity,
            expected=expected,
            error_context="finance readiness finance_entity hydration",
        )
    return FinanceEntityReadinessReceipt(
        actor_id=actor_id,
        finance_role_key=expected.finance_role_key,
        finance_entity_id=expected.finance_entity_id,
        wallet_id=expected.wallet_id,
        wallet_public_id=expected.wallet_public_id,
        finance_entity_ready=finance_entity_ready,
        wallet_ready=wallet_ready,
        idempotent_replay=wallet_ready and finance_entity_ready,
    )


async def ensure_finance_entity(
    *,
    runtime_context: EconomyFinanceReadinessRuntimeContext,
    operation_context: EconomyFinanceReadinessOperationContext,
    actor_id: UUID,
    finance_role_key: str | None,
    commit: bool,
    publish: bool,
) -> FinanceEntityReadinessReceipt:
    expected = _expected_readiness_ids(
        actor_id=actor_id,
        finance_role_key=finance_role_key,
    )
    existing = await resolve_finance_entity_readiness(
        runtime_context=runtime_context,
        actor_id=actor_id,
        finance_role_key=expected.finance_role_key,
    )
    if existing.finance_entity_ready and existing.wallet_ready:
        return existing

    if not existing.wallet_ready:
        wallet_lane = _bind_lane(
            runtime_context=runtime_context,
            operation_context=operation_context,
            branch_id=expected.wallet_id,
            projection=runtime_context.lanes.wallet_projection_hash,
        )
        with wallet_lane.activate(commit=commit, publish=publish):
            wallet = await Wallet.build(
                address=expected.address,
                public_key=expected.public_key,
                private_key_encrypted=expected.private_key_encrypted,
            )
        _validate_wallet(
            wallet,
            expected=expected,
            error_context="finance readiness wallet creation",
        )

    if not existing.finance_entity_ready:
        finance_entity_lane = _bind_lane(
            runtime_context=runtime_context,
            operation_context=operation_context,
            branch_id=expected.finance_entity_id,
            projection=runtime_context.lanes.finance_entity_projection_hash,
        )
        with finance_entity_lane.activate(commit=commit, publish=publish):
            finance_entity = await FinanceEntity.build(
                identity_id=actor_id,
                wallet_id=expected.wallet_id,
                role_key=expected.finance_role_key,
            )
        _validate_finance_entity(
            finance_entity,
            expected=expected,
            error_context="finance readiness finance_entity creation",
        )

    ready = await resolve_finance_entity_readiness(
        runtime_context=runtime_context,
        actor_id=actor_id,
        finance_role_key=expected.finance_role_key,
    )
    return FinanceEntityReadinessReceipt(
        actor_id=ready.actor_id,
        finance_role_key=ready.finance_role_key,
        finance_entity_id=ready.finance_entity_id,
        wallet_id=ready.wallet_id,
        wallet_public_id=ready.wallet_public_id,
        finance_entity_ready=ready.finance_entity_ready,
        wallet_ready=ready.wallet_ready,
        idempotent_replay=existing.finance_entity_ready and existing.wallet_ready,
    )


@dataclass(frozen=True, slots=True)
class _ExpectedReadinessIds:
    actor_id: UUID
    finance_role_key: str
    finance_entity_id: UUID
    wallet_id: UUID
    wallet_public_id: UUID
    public_key: str
    address: str
    private_key_encrypted: str


def _expected_readiness_ids(
    *,
    actor_id: UUID,
    finance_role_key: str | None,
) -> _ExpectedReadinessIds:
    role_key = normalize_finance_role_key(finance_role_key)
    custody = derive_wallet_custody_material(
        identity_id=actor_id,
        role_key=role_key,
    )
    return _ExpectedReadinessIds(
        actor_id=actor_id,
        finance_role_key=role_key,
        finance_entity_id=stable_finance_entity_id(identity_id=actor_id),
        wallet_id=stable_wallet_id(
            public_key=custody.public_key,
            private_key_encrypted=custody.private_key_encrypted,
        ),
        wallet_public_id=stable_wallet_public_id(public_key=custody.public_key),
        public_key=custody.public_key,
        address=custody.address,
        private_key_encrypted=custody.private_key_encrypted,
    )


def _validate_wallet(
    wallet: Wallet,
    *,
    expected: _ExpectedReadinessIds,
    error_context: str,
) -> None:
    if wallet.id != expected.wallet_id:
        raise ValueError(f"{error_context}: wallet id mismatch")
    if wallet.wallet_public_id != expected.wallet_public_id:
        raise ValueError(f"{error_context}: wallet_public_id mismatch")
    if wallet.public_key != expected.public_key:
        raise ValueError(f"{error_context}: public_key mismatch")
    if wallet.private_key_encrypted != expected.private_key_encrypted:
        raise ValueError(f"{error_context}: custody handle mismatch")


def _validate_finance_entity(
    finance_entity: FinanceEntity,
    *,
    expected: _ExpectedReadinessIds,
    error_context: str,
) -> None:
    if finance_entity.id != expected.finance_entity_id:
        raise ValueError(f"{error_context}: finance_entity id mismatch")
    if finance_entity.identity_id != expected.actor_id:
        raise ValueError(f"{error_context}: identity_id mismatch")
    if finance_entity.wallet_id != expected.wallet_id:
        raise ValueError(f"{error_context}: wallet_id mismatch")
    if getattr(finance_entity, "role_key", None) != expected.finance_role_key:
        raise ValueError(f"{error_context}: role_key mismatch")


def _bind_lane(
    *,
    runtime_context: EconomyFinanceReadinessRuntimeContext,
    operation_context: EconomyFinanceReadinessOperationContext,
    branch_id: UUID,
    projection: str,
) -> EconomyMetaRuntimeLane:
    return runtime_context.lane_binder.bind(
        branch_id=branch_id,
        projection=projection,
        actor_id=operation_context.actor_id,
    )


async def _maybe_hydrate_committed_lane_object(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    orm_class: type[_TModel],
    object_id: UUID,
) -> _TModel | None:
    target_head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        return None

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "Economy finance readiness could not resolve projection hash for committed lane hydration: "
            + repr(projection_hash)
        )
    target_oig, _ = await CachedLaneMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(target_head["commit_id"])),
        oig_id=(
            UUID(str(target_head["object_instance_graph_id"]))
            if target_head.get("object_instance_graph_id")
            else None
        ),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    session = reify_oig_session(
        index=index,
        opg=opg,
        oig=target_oig,
        branch_id=branch_id,
        preferred_model_type=orm_class,
    )
    hydrated = session.imap_get(orm_class, object_id)
    if hydrated is None:
        return None
    return hydrated


def _find_projection_hash_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> str:
    target = (projection_name or "").strip()
    matches = tuple(
        sorted(
            str(projection_hash)
            for projection_hash, opg in index.opg_by_hash.items()
            if (opg.name or "").strip() == target
        )
    )
    if len(matches) != 1:
        raise ValueError(
            f"Expected one Economy runtime projection named {projection_name!r}, got {matches!r}"
        )
    return matches[0]


__all__ = [
    "EconomyFinanceReadinessLanes",
    "EconomyFinanceReadinessOperationContext",
    "EconomyFinanceReadinessRuntimeContext",
    "FinanceEntityReadinessReceipt",
    "build_economy_finance_readiness_lanes",
    "ensure_finance_entity",
    "resolve_economy_finance_readiness_runtime_context",
    "resolve_finance_entity_readiness",
]
