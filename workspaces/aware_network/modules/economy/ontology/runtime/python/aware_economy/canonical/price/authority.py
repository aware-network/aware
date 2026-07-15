from __future__ import annotations

from uuid import UUID

from decimal import Decimal

from aware_economy.capital_amount import non_negative_amount
from aware_economy_ontology.smart_contract.smart_contract_permit import (
    SmartContractPermit,
)
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.runtime.handler_context import (
    current_handler_context,
    current_handler_index,
)
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.portal_lane_resolution import (
    ensure_portal_target_lane_ref_for_object,
    resolve_portal_target_lane_ref_for_object,
)
from aware_meta.runtime.portal_context import current_handler_portal_client
from aware_economy_ontology.price.price_schedule import PriceSchedule


async def ensure_price_schedule_lane_via_permit(
    *,
    smart_contract_permit: SmartContractPermit,
) -> UUID:
    """
    Verify committed portal branch routing from the current smart-contract lane to the
    sibling Price lane referenced by this permit.

    Meta owns portal branch relationships. Economy only resolves committed
    relationship truth and fails closed when the price schedule lane is missing.
    """

    if smart_contract_permit.price_schedule_id is None:
        raise ValueError(
            "price authority lane bootstrap requires smart_contract_permit.price_schedule_id"
        )

    ctx = current_handler_context()
    if ctx.branch_id is None or ctx.projection_hash is None:
        raise RuntimeError(
            "price authority lane bootstrap requires source lane context: "
            f"permit_id={smart_contract_permit.id} branch_id={ctx.branch_id} projection_hash={ctx.projection_hash}"
        )
    idx = current_handler_index()
    portal = current_handler_portal_client().portal_for_model_field(
        orm_model=smart_contract_permit,
        reference_field_name="price_schedule",
    )
    await ensure_portal_target_lane_ref_for_object(
        index=idx,
        author_id=ctx.requester_id,
        source_domain_branch_id=ctx.branch_id,
        source_projection_hash=ctx.projection_hash,
        target_projection_hash=portal.target_projection_hash,
        target_class_config_id=portal.target_class_config_id,
        target_object_id=smart_contract_permit.price_schedule_id,
    )
    return smart_contract_permit.price_schedule_id


async def resolve_rate_snapshot_quote_via_permit(
    *,
    smart_contract_permit: SmartContractPermit,
    rate_snapshot_id: UUID,
    expected_coin_id: UUID,
) -> Decimal:
    """
    Resolve authoritative quoted_amount for a permit-bound price schedule.

    Requires the permit-bound PriceSchedule to be materialized by the caller's
    service/read model context. Ontology function reads are intentionally not
    invoked from this authority.
    """

    price_schedule = getattr(smart_contract_permit, "price_schedule", None)
    if price_schedule is None:
        price_schedule = await _materialize_price_schedule_via_permit(
            smart_contract_permit=smart_contract_permit,
        )
    quoted_amount = await _resolve_rate_snapshot_quote_from_schedule(
        price_schedule,
        rate_snapshot_id=rate_snapshot_id,
        expected_coin_id=expected_coin_id,
    )

    return non_negative_amount(
        quoted_amount,
        field_name="price authority quoted_amount",
    )


async def _materialize_price_schedule_via_permit(
    *,
    smart_contract_permit: SmartContractPermit,
) -> PriceSchedule:
    price_schedule_id = smart_contract_permit.price_schedule_id
    if price_schedule_id is None:
        raise ValueError(
            "price authority requires smart_contract_permit.price_schedule_id"
        )

    ctx = current_handler_context()
    if ctx.branch_id is None or ctx.projection_hash is None:
        raise RuntimeError(
            "price authority materialization requires source lane context: "
            f"permit_id={smart_contract_permit.id} branch_id={ctx.branch_id} "
            f"projection_hash={ctx.projection_hash}"
        )
    idx = current_handler_index()
    portal = current_handler_portal_client().portal_for_model_field(
        orm_model=smart_contract_permit,
        reference_field_name="price_schedule",
    )
    lane_ref = await resolve_portal_target_lane_ref_for_object(
        index=idx,
        source_domain_branch_id=ctx.branch_id,
        source_projection_hash=ctx.projection_hash,
        target_projection_hash=portal.target_projection_hash,
        target_class_config_id=portal.target_class_config_id,
        target_object_id=price_schedule_id,
        target_domain_branch_id=None,
    )
    target_opg = idx.opg_by_hash.get(portal.target_projection_hash)
    if target_opg is None:
        raise RuntimeError(
            "price authority target projection missing from Meta index: "
            f"projection_hash={portal.target_projection_hash}"
        )
    target_oig, _ = await CachedLaneMaterializer().get(
        branch_id=lane_ref.target_branch_id,
        ocg=idx.ocg,
        opg=target_opg,
        commit_id=lane_ref.target_head_commit_id,
        oig_id=lane_ref.target_object_instance_graph_id,
        attribute_configs_by_id=idx.attribute_configs_by_id,
        class_configs_by_id=idx.class_configs_by_id,
    )
    session = reify_oig_session(
        index=idx,
        opg=target_opg,
        oig=target_oig,
        branch_id=lane_ref.target_branch_id,
        preferred_model_type=PriceSchedule,
    )
    hydrated = session.imap_get(PriceSchedule, price_schedule_id)
    if hydrated is None:
        raise ValueError(
            "price authority could not hydrate permit price_schedule from committed lane: "
            f"price_schedule_id={price_schedule_id}"
        )
    smart_contract_permit.price_schedule = hydrated
    return hydrated


async def _resolve_rate_snapshot_quote_from_schedule(
    price_schedule: PriceSchedule,
    *,
    rate_snapshot_id: UUID,
    expected_coin_id: UUID,
) -> Decimal:
    price = getattr(price_schedule, "price", None)
    if price is not None and str(getattr(price, "coin_id", "")) != str(
        expected_coin_id
    ):
        raise ValueError("price authority price_schedule coin_id mismatch")

    for snapshot in getattr(price_schedule, "rate_snapshots", ()) or ():
        if str(getattr(snapshot, "id", "")) != str(rate_snapshot_id):
            continue
        quoted_amount = getattr(snapshot, "quoted_amount", None)
        return non_negative_amount(
            quoted_amount,
            field_name="price authority quoted_amount",
        )

    raise ValueError(
        "price authority rate_snapshot not found on materialized price_schedule: "
        f"price_schedule_id={price_schedule.id} rate_snapshot_id={rate_snapshot_id}"
    )
