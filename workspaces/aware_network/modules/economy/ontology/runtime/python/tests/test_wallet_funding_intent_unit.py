from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from ._economy_runtime_test_paths import REPO_ROOT, economy_package_manifest_paths
from aware_economy.handlers._generated import meta_handlers as economy_meta_handlers
from aware_economy.handlers.impl.transaction.transaction_intent import create
from aware_economy_ontology.external_capital.external_capital_enums import (
    ExternalCapitalConversionMode,
)
from aware_economy_ontology.stable_ids import (
    stable_capital_conversion_quote_id,
    stable_coin_id,
    stable_transaction_intent_id,
)
from aware_economy_ontology.transaction.transaction_intent_enums import (
    TransactionIntentStatus,
)
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
    run_meta_runtime_proof,
)


TRANSACTION_INTENT_CLASS_FQN = "aware_economy.transaction.TransactionIntent"

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


@pytest.mark.asyncio
async def test_transaction_intent_contains_exact_direct_denomination_quote(
    tmp_path: Path,
) -> None:
    provider_config_id = uuid4()
    recipient_finance_entity_id = uuid4()
    recipient_wallet_id = uuid4()
    recipient_wallet_public_id = uuid4()
    provider_route_id = uuid4()
    coin_id = stable_coin_id(symbol="USD")
    intent_id = stable_transaction_intent_id(
        provider_config_id=provider_config_id,
        recipient_finance_entity_id=recipient_finance_entity_id,
        funding_intent_key="wallet-topup-1",
    )
    quote_id = stable_capital_conversion_quote_id(
        quote_key=f"transaction-intent:{intent_id}:direct-denomination-v0"
    )
    create_args = [
        provider_config_id,
        recipient_finance_entity_id,
        recipient_wallet_id,
        recipient_wallet_public_id,
        " WALLET-TOPUP-1 ",
        coin_id,
        "25.50",
        " Stripe ",
        "checkout-attempt-1",
        provider_route_id,
        "usd",
        2,
        ExternalCapitalConversionMode.direct_denomination.value,
        "2026-07-10T06:45:00Z",
    ]

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(
            repo_root=REPO_ROOT,
            aware_root=aware_root,
        )
        _, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=LaneIds(branch_id=uuid4(), actor_id=uuid4()),
            opg_name="TransactionIntent",
            root_class_fqn=TRANSACTION_INTENT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=TRANSACTION_INTENT_CLASS_FQN,
                    function_name="create",
                    args=create_args,
                    expected_root_object_id=intent_id,
                ),
                ProofCall(
                    target="constructor",
                    class_fqn=TRANSACTION_INTENT_CLASS_FQN,
                    function_name="create",
                    args=create_args,
                    expected_root_object_id=intent_id,
                    allow_noop_commit=True,
                ),
                ProofCall(
                    target="instance",
                    object_id=ROOT_OBJECT_ID,
                    class_fqn=TRANSACTION_INTENT_CLASS_FQN,
                    function_name="mark_pending",
                    args=["2026-07-10T06:46:00Z"],
                ),
                ProofCall(
                    target="instance",
                    object_id=ROOT_OBJECT_ID,
                    class_fqn=TRANSACTION_INTENT_CLASS_FQN,
                    function_name="confirm",
                    args=["2026-07-10T06:47:00Z"],
                ),
            ],
        )

    assertions.expect_root(intent_id)
    assertions.expect_instance(intent_id)
    assertions.expect_instance(quote_id)
    assertions.expect_edge(
        source_id=intent_id,
        target_id=quote_id,
        relationship_name="capital_conversion_quote",
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=intent_id,
        field_name="provider_config_id",
        expected=provider_config_id,
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=intent_id,
        field_name="recipient_wallet_id",
        expected=recipient_wallet_id,
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=intent_id,
        field_name="recipient_wallet_public_id",
        expected=recipient_wallet_public_id,
    )
    assertions.expect_primitive(
        instance_id=intent_id,
        field_name="funding_intent_key",
        expected="wallet-topup-1",
    )
    assertions.expect_primitive(
        instance_id=intent_id,
        field_name="provider_key",
        expected="stripe",
    )
    assertions.expect_primitive(
        instance_id=intent_id,
        field_name="idempotency_key",
        expected="checkout-attempt-1",
    )
    assertions.expect_primitive(
        instance_id=intent_id,
        field_name="status",
        expected=TransactionIntentStatus.confirmed.value,
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=quote_id,
        field_name="provider_route_id",
        expected=provider_route_id,
    )
    assertions.expect_primitive(
        instance_id=quote_id,
        field_name="external_amount_minor",
        expected=2550,
    )
    assertions.expect_primitive(
        instance_id=quote_id,
        field_name="external_currency",
        expected="USD",
    )
    assertions.expect_primitive(
        instance_id=quote_id,
        field_name="target_amount",
        expected="25.5",
    )
    quote_hash = assertions.primitive(
        instance_id=quote_id,
        field_name="quote_hash",
    )
    assert isinstance(quote_hash, str)
    assert len(quote_hash) == 64


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"funding_intent_key": " "}, "funding_intent_key"),
        ({"amount": "0"}, "must be > 0"),
        ({"amount": "25.501"}, "minor-unit precision"),
        ({"coin_id": stable_coin_id(symbol="EUR")}, "target Coin"),
        (
            {"conversion_mode": "unsupported"},
            "direct_denomination",
        ),
    ],
)
async def test_transaction_intent_rejects_ambiguous_quote_inputs(
    overrides: dict[str, object],
    message: str,
) -> None:
    kwargs: dict[str, object] = {
        "provider_config_id": uuid4(),
        "recipient_finance_entity_id": uuid4(),
        "recipient_wallet_id": uuid4(),
        "recipient_wallet_public_id": uuid4(),
        "funding_intent_key": "wallet-topup-1",
        "coin_id": stable_coin_id(symbol="USD"),
        "amount": "25.50",
        "provider_key": "fake",
        "idempotency_key": "attempt-1",
        "provider_route_id": uuid4(),
        "external_currency": "USD",
        "external_minor_unit_exponent": 2,
        "conversion_mode": ExternalCapitalConversionMode.direct_denomination,
        "created_at": datetime(2026, 7, 10, 6, 45, tzinfo=UTC),
    }
    kwargs.update(overrides)

    with pytest.raises((TypeError, ValueError), match=message):
        await create(**kwargs)  # type: ignore[arg-type]
