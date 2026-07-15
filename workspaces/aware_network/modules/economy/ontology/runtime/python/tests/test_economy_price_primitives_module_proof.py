from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any, NamedTuple, cast
from uuid import UUID, uuid4

import pytest

from ._economy_runtime_test_paths import REPO_ROOT, economy_package_manifest_paths
from aware_economy.handlers._generated import meta_handlers as economy_meta_handlers
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    MetaOIGAssertions,
    ProofCall,
    ROOT_OBJECT_ID,
    SourceObjectId,
    run_meta_runtime_proof,
)


ECONOMY_COIN_CLASS_FQN = "aware_economy.coin.Coin"
ECONOMY_PRICE_CLASS_FQN = "aware_economy.price.Price"
ECONOMY_PRICE_SCHEDULE_CLASS_FQN = "aware_economy.price.PriceSchedule"
ECONOMY_PRICING_POLICY_CLASS_FQN = "aware_economy.price.PricingPolicy"

_ECONOMY_META_HANDLERS_ANY: Any = economy_meta_handlers
_ECONOMY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _ECONOMY_META_HANDLERS_ANY,
)
_ECONOMY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _ECONOMY_META_HANDLERS_ANY,
)


def _build_economy_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=economy_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_ECONOMY_META_HANDLER_MODULE,),
        bootstrap_modules=(_ECONOMY_META_BOOTSTRAP_MODULE,),
    )
    assert runtime.context is not None
    return runtime


def _expect_uuid_primitive(
    assertions: MetaOIGAssertions,
    *,
    instance_id: UUID,
    field_name: str,
    expected: UUID,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


class PriceCase(NamedTuple):
    price_name: str
    price_type: str
    schedule_name: str
    fixed_amount: Decimal | None
    markup_percentage: Decimal | None
    snapshot_key: str
    quoted_amount: Decimal


@pytest.mark.asyncio
async def test_economy_price_primitives_are_deterministic(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    from aware_economy.stable_ids import (
        stable_coin_id,
        stable_price_id,
        stable_price_schedule_id,
        stable_pricing_policy_id,
        stable_rate_snapshot_id,
    )
    from aware_economy_ontology.coin.coin_enums import CoinType
    from aware_economy_ontology.price.price_enums import PriceType
    import aware_economy_ontology  # noqa: F401

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_economy_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )

        coin_id = stable_coin_id(symbol="USD")
        pricing_policy_id = stable_pricing_policy_id(
            name="default-service-policy",
            version=1,
        )
        cases = [
            PriceCase(
                price_name="default-fixed-price",
                price_type=PriceType.fixed.value,
                schedule_name="default-fixed",
                fixed_amount=Decimal("12.5"),
                markup_percentage=None,
                snapshot_key="default-fixed-v1",
                quoted_amount=Decimal("12.5"),
            ),
            PriceCase(
                price_name="default-dynamic-price",
                price_type=PriceType.dynamic.value,
                schedule_name="default-dynamic",
                fixed_amount=None,
                markup_percentage=Decimal("5"),
                snapshot_key="default-dynamic-v1",
                quoted_amount=Decimal("13.125"),
            ),
        ]

        for idx, case in enumerate(cases):
            case_lane = LaneIds(
                branch_id=uuid4(),
                actor_id=uuid4(),
            )

            await run_meta_runtime_proof(
                runtime=runtime,
                lane=case_lane,
                opg_name="Coin",
                root_class_fqn=ECONOMY_COIN_CLASS_FQN,
                calls=[
                    ProofCall(
                        target="constructor",
                        class_fqn=ECONOMY_COIN_CLASS_FQN,
                        function_name="build",
                        args=["USD", "US Dollar", CoinType.fiat.value],
                        expected_root_object_id=coin_id,
                    )
                ],
            )

            _, pricing_policy_assertions = await run_meta_runtime_proof(
                runtime=runtime,
                lane=case_lane,
                opg_name="PricingPolicy",
                root_class_fqn=ECONOMY_PRICING_POLICY_CLASS_FQN,
                calls=[
                    ProofCall(
                        target="constructor",
                        class_fqn=ECONOMY_PRICING_POLICY_CLASS_FQN,
                        function_name="build",
                        args=["default-service-policy", 1],
                        expected_root_object_id=pricing_policy_id,
                    )
                ],
            )
            if idx == 0:
                pricing_policy_assertions.expect_root(pricing_policy_id)
                pricing_policy_assertions.expect_instance(pricing_policy_id)
                pricing_policy_assertions.expect_primitive(
                    instance_id=pricing_policy_id,
                    field_name="fail_closed",
                    expected=True,
                )

            price_id = stable_price_id(
                coin_id=coin_id,
                name=case.price_name,
                type=case.price_type,
            )
            price_schedule_id = stable_price_schedule_id(
                price_id=price_id,
                pricing_policy_id=pricing_policy_id,
                name=case.schedule_name,
                version=1,
            )
            rate_snapshot_id = stable_rate_snapshot_id(
                price_schedule_id=price_schedule_id,
                snapshot_key=case.snapshot_key,
            )

            _, price_assertions = await run_meta_runtime_proof(
                runtime=runtime,
                lane=case_lane,
                opg_name="Price",
                root_class_fqn=ECONOMY_PRICE_CLASS_FQN,
                calls=[
                    ProofCall(
                        target="constructor",
                        class_fqn=ECONOMY_PRICE_CLASS_FQN,
                        function_name="build",
                        args=[
                            coin_id,
                            case.price_name,
                            case.price_type,
                        ],
                        expected_root_object_id=price_id,
                    ),
                    ProofCall(
                        target="instance",
                        object_id=ROOT_OBJECT_ID,
                        class_fqn=ECONOMY_PRICE_CLASS_FQN,
                        function_name="create_price_schedule",
                        args=[
                            pricing_policy_id,
                            case.schedule_name,
                            "2026-03-25T00:00:00Z",
                            1,
                            None,
                            (
                                str(case.fixed_amount)
                                if case.fixed_amount is not None
                                else None
                            ),
                            (
                                str(case.markup_percentage)
                                if case.markup_percentage is not None
                                else None
                            ),
                        ],
                    ),
                    ProofCall(
                        target="instance",
                        object_id=SourceObjectId(price_schedule_id),
                        class_fqn=ECONOMY_PRICE_SCHEDULE_CLASS_FQN,
                        function_name="capture_rate_snapshot",
                        args=[
                            case.snapshot_key,
                            str(case.quoted_amount),
                            "2026-03-25T00:00:01Z",
                            (
                                "12.5"
                                if case.markup_percentage is not None
                                else None
                            ),
                            (
                                str(case.markup_percentage)
                                if case.markup_percentage is not None
                                else None
                            ),
                            (
                                "0.625"
                                if case.markup_percentage is not None
                                else None
                            ),
                            (
                                "meter://price-module-proof/actual"
                                if case.markup_percentage is not None
                                else None
                            ),
                        ],
                    ),
                ],
            )

            price_assertions.expect_root(price_id)
            price_assertions.expect_instance(price_id)
            price_assertions.expect_instance(price_schedule_id)
            price_assertions.expect_instance(rate_snapshot_id)
            price_assertions.expect_edge(
                source_id=price_id,
                target_id=price_schedule_id,
                relationship_name="price_schedules",
            )
            price_assertions.expect_edge(
                source_id=price_schedule_id,
                target_id=rate_snapshot_id,
                relationship_name="rate_snapshots",
            )
            _expect_uuid_primitive(
                price_assertions,
                instance_id=price_id,
                field_name="coin_id",
                expected=coin_id,
            )
            price_assertions.expect_primitive(
                instance_id=price_id,
                field_name="name",
                expected=case.price_name,
            )
            price_assertions.expect_primitive(
                instance_id=price_id,
                field_name="type",
                expected=case.price_type,
            )
            _expect_uuid_primitive(
                price_assertions,
                instance_id=price_schedule_id,
                field_name="pricing_policy_id",
                expected=pricing_policy_id,
            )
            price_assertions.expect_primitive(
                instance_id=price_schedule_id,
                field_name="name",
                expected=case.schedule_name,
            )
            if case.fixed_amount is not None:
                price_assertions.expect_primitive(
                    instance_id=price_schedule_id,
                    field_name="fixed_amount",
                    expected=str(case.fixed_amount),
                )
            if case.markup_percentage is not None:
                price_assertions.expect_primitive(
                    instance_id=price_schedule_id,
                    field_name="markup_percentage",
                        expected=str(case.markup_percentage),
                )
            price_assertions.expect_primitive(
                instance_id=rate_snapshot_id,
                field_name="snapshot_key",
                expected=case.snapshot_key,
            )
            price_assertions.expect_primitive(
                instance_id=rate_snapshot_id,
                field_name="quoted_amount",
                expected=str(case.quoted_amount),
            )
            if case.markup_percentage is not None:
                price_assertions.expect_primitive(
                    instance_id=rate_snapshot_id,
                    field_name="cost_basis_amount",
                    expected="12.5",
                )
                price_assertions.expect_primitive(
                    instance_id=rate_snapshot_id,
                    field_name="markup_percentage",
                    expected=str(case.markup_percentage),
                )
                price_assertions.expect_primitive(
                    instance_id=rate_snapshot_id,
                    field_name="markup_amount",
                    expected="0.625",
                )
                price_assertions.expect_primitive(
                    instance_id=rate_snapshot_id,
                    field_name="meter_evidence_ref",
                    expected="meter://price-module-proof/actual",
                )
