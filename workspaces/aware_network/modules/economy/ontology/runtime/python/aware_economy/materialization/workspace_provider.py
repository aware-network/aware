from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from aware_code.semantic_materialization import (
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
)
from aware_code.types import JsonObject
from aware_economy.manifest import load_aware_economy_toml_spec
from aware_economy_ontology.economy.economy_package import EconomyPackage
from aware_economy_ontology.price.price import Price
from aware_economy_ontology.price.price_enums import PriceType
from aware_economy_ontology.price.pricing_policy import PricingPolicy
from aware_economy_ontology.stable_ids import stable_economy_package_id
from aware_economy.stable_ids import stable_coin_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    spec = load_aware_economy_toml_spec(toml_path=request.manifest_path)
    package_name = spec.economy.package_name
    context_package_name = str(
        request.context.get("semantic_package_name") or ""
    ).strip()
    if context_package_name and context_package_name != package_name:
        raise RuntimeError(
            "Economy materialization package mismatch: "
            f"context={context_package_name!r} manifest={package_name!r}"
        )
    economy_package_id = stable_economy_package_id(name=package_name)
    source_code_package_id = _uuid_or_none(
        request.context.get("source_code_package_id")
    )

    runtime = cast(Any, request.runtime)
    package_lane = runtime.bind(
        branch_id=request.branch_id,
        projection="EconomyPackage",
        actor_id=request.actor_id,
    )
    with package_lane.activate(commit=True, publish=False):
        _ = await EconomyPackage.build(
            name=package_name,
            source_code_package_id=source_code_package_id,
        )

    materialized_prices: list[dict[str, object]] = []
    last_price_domain_commit_id: UUID | None = None
    last_price_head_commit_id: UUID | None = None
    for price_spec in spec.prices:
        policy_lane = runtime.bind(
            branch_id=request.branch_id,
            projection="PricingPolicy",
            actor_id=request.actor_id,
        )
        with policy_lane.activate(commit=True, publish=False):
            pricing_policy = await PricingPolicy.build(
                name=price_spec.pricing_policy.name,
                version=price_spec.pricing_policy.version,
                description=price_spec.pricing_policy.description,
                policy_json=JsonObject(dict(price_spec.pricing_policy.policy_json)),
                fail_closed=price_spec.pricing_policy.fail_closed,
            )
        if pricing_policy.id is None:
            raise RuntimeError(
                f"Economy pricing policy materialization omitted id: {price_spec.name!r}"
            )

        price_lane = runtime.bind(
            branch_id=request.branch_id,
            projection="Price",
            actor_id=request.actor_id,
        )
        with price_lane.activate(commit=True, publish=False):
            price = await Price.build(
                coin_id=stable_coin_id(symbol=price_spec.coin),
                name=price_spec.name,
                type=PriceType(price_spec.type.value),
            )
            schedule_ids: list[str] = []
            for schedule_spec in price_spec.schedules:
                schedule = await price.create_price_schedule(
                    pricing_policy_id=pricing_policy.id,
                    name=schedule_spec.name,
                    effective_from=schedule_spec.effective_from,
                    version=schedule_spec.version,
                    effective_until=schedule_spec.effective_until,
                    fixed_amount=schedule_spec.fixed_amount,
                    markup_percentage=schedule_spec.markup_percentage,
                )
                if schedule.id is not None:
                    schedule_ids.append(str(schedule.id))
        if price.id is None:
            raise RuntimeError(
                f"Economy price materialization omitted id: {price_spec.name!r}"
            )
        last_price_domain_commit_id = price_lane.last_commit_id
        last_price_head_commit_id = price_lane.last_head_commit_id
        materialized_prices.append(
            {
                "name": price_spec.name,
                "price_id": str(price.id),
                "pricing_policy_id": str(pricing_policy.id),
                "schedule_ids": schedule_ids,
                "coin": price_spec.coin,
                "type": price_spec.type.value,
                "price_domain_commit_id": (
                    str(price_lane.last_commit_id)
                    if price_lane.last_commit_id is not None
                    else None
                ),
                "price_object_instance_graph_commit_id": (
                    str(price_lane.last_head_commit_id)
                    if price_lane.last_head_commit_id is not None
                    else None
                ),
            }
        )

    package_domain_commit_id, package_object_instance_graph_commit_id = (
        await _resolve_committed_package_receipts(
            branch_id=request.branch_id,
            projection_hash=package_lane.binding.projection_hash,
            domain_commit_id=package_lane.last_commit_id,
            object_instance_graph_commit_id=package_lane.last_head_commit_id,
        )
    )
    if (
        package_domain_commit_id is None
        or package_object_instance_graph_commit_id is None
    ):
        raise RuntimeError(
            "Economy semantic package materialization did not produce committed package receipts"
        )
    return SemanticPackageMaterializationResult(
        details={
            "economy_toml_path": request.manifest_path.as_posix(),
            "economy_package_name": package_name,
            "economy_package_id": str(economy_package_id),
            "source_code_package_id": (
                str(source_code_package_id)
                if source_code_package_id is not None
                else None
            ),
            "semantic_branch_id": str(request.branch_id),
            "economy_package_commit_id": str(package_domain_commit_id),
            "economy_package_object_instance_graph_commit_id": str(
                package_object_instance_graph_commit_id
            ),
            "materialized_prices": materialized_prices,
            "last_price_commit_id": (
                str(last_price_domain_commit_id)
                if last_price_domain_commit_id is not None
                else None
            ),
            "last_price_object_instance_graph_commit_id": (
                str(last_price_head_commit_id)
                if last_price_head_commit_id is not None
                else None
            ),
        },
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=package_name,
                manifest_toml_path=request.manifest_path,
                semantic_package_id=economy_package_id,
                semantic_root_id=economy_package_id,
                semantic_branch_id=request.branch_id,
                semantic_head_commit_id=package_domain_commit_id,
                semantic_object_instance_graph_commit_id=(
                    package_object_instance_graph_commit_id
                ),
                semantic_root_object_instance_graph_commit_id=(
                    package_object_instance_graph_commit_id
                ),
                semantic_root_kind="economy_package",
                semantic_projection_name="EconomyPackage",
                source_code_package_id=source_code_package_id,
            ),
        ),
        commit_id=package_domain_commit_id,
        head_commit_id=package_domain_commit_id,
    )


async def _resolve_committed_package_receipts(
    *,
    branch_id: UUID,
    projection_hash: str,
    domain_commit_id: UUID | None,
    object_instance_graph_commit_id: UUID | None,
) -> tuple[UUID | None, UUID | None]:
    commit_store = FSCommitStore()
    resolved_domain_commit_id = domain_commit_id
    if resolved_domain_commit_id is None:
        head = await commit_store.head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        if head is not None and head.get("commit_id") is not None:
            resolved_domain_commit_id = UUID(str(head["commit_id"]))

    resolved_object_instance_graph_commit_id = object_instance_graph_commit_id
    if (
        resolved_object_instance_graph_commit_id is None
        and resolved_domain_commit_id is not None
    ):
        identity_metadata = await commit_store.get_commit_identity_metadata(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=resolved_domain_commit_id,
        )
        if identity_metadata is not None:
            resolved_object_instance_graph_commit_id = (
                stable_object_instance_graph_commit_id(
                    object_instance_graph_identity_id=(
                        identity_metadata.object_instance_graph_identity_id
                    ),
                    commit_id=resolved_domain_commit_id,
                )
            )
    return resolved_domain_commit_id, resolved_object_instance_graph_commit_id


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        return UUID(value.strip())
    return None


__all__ = ["materialize"]
