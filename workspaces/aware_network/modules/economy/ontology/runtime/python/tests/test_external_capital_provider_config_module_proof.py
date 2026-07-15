from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from ._economy_runtime_test_paths import REPO_ROOT, economy_package_manifest_paths
from aware_experience.program.language import (
    compile_invocation_plans,
    encode_invocation_plan_artifact,
)
from aware_economy.handlers._generated import meta_handlers as economy_meta_handlers
from aware_economy.handlers.impl.external_capital.external_capital_provider_config import (
    build as build_provider_config,
)
from aware_economy.handlers.impl.external_capital.external_capital_provider_route import (
    build_via_external_capital_provider_config as build_provider_route,
)
from aware_economy_ontology.external_capital.external_capital_enums import (
    ExternalCapitalConversionMode,
)
from aware_economy_ontology.stable_ids import (
    stable_coin_id,
    stable_external_capital_provider_config_id,
    stable_external_capital_provider_route_id,
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


PROVIDER_CONFIG_CLASS_FQN = "aware_economy.external_capital.ExternalCapitalProviderConfig"

_ECONOMY_META_HANDLERS_ANY: Any = economy_meta_handlers
_ECONOMY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _ECONOMY_META_HANDLERS_ANY,
)
_ECONOMY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _ECONOMY_META_HANDLERS_ANY,
)

_PROVIDER_ROUTE_PROGRAM_PATH = (
    REPO_ROOT
    / "workspaces"
    / "aware_network"
    / "modules"
    / "economy"
    / "experiences"
    / "aware_economy"
    / "programs"
    / "seed"
    / "ensure_external_capital_provider_route_v0.aware"
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


def test_external_capital_provider_route_program_is_provider_neutral() -> None:
    plans = compile_invocation_plans(_PROVIDER_ROUTE_PROGRAM_PATH.read_text(encoding="utf-8"))
    assert [plan.name for plan in plans] == ["EnsureExternalCapitalProviderRoute_v0"]
    artifact = encode_invocation_plan_artifact(plans[0])
    plan = cast(dict[str, object], artifact["plan"])
    steps = cast(list[dict[str, object]], plan["steps"])
    call_targets = [cast(dict[str, object], step["call"])["target"] for step in steps if step.get("$step") == "invoke"]

    assert call_targets == [
        "bind",
        "coin.Coin.build",
        "bind",
        "external_capital.ExternalCapitalProviderConfig.build",
        "external_capital.ExternalCapitalProviderConfig.add_route",
    ]
    source = _PROVIDER_ROUTE_PROGRAM_PATH.read_text(encoding="utf-8")
    assert "direct_denomination" in source
    lowered_artifact = str(artifact).casefold()
    assert "stripe" not in lowered_artifact
    assert "endpoint" not in lowered_artifact
    assert "secret" not in lowered_artifact


@pytest.mark.asyncio
async def test_external_capital_provider_config_projection_is_deterministic(
    tmp_path: Path,
) -> None:
    provider_finance_entity_id = uuid4()
    target_coin_id = stable_coin_id(symbol="USD")
    config_id = stable_external_capital_provider_config_id(
        provider_finance_entity_id=provider_finance_entity_id,
        provider_key="stripe",
    )
    route_id = stable_external_capital_provider_route_id(
        external_capital_provider_config_id=config_id,
        target_coin_id=target_coin_id,
        route_key="usd-hosted-checkout",
    )

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
            opg_name="ExternalCapitalProviderConfig",
            root_class_fqn=PROVIDER_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=PROVIDER_CONFIG_CLASS_FQN,
                    function_name="build",
                    args=[provider_finance_entity_id, " Stripe ", "Stripe"],
                    expected_root_object_id=config_id,
                ),
                ProofCall(
                    target="instance",
                    object_id=ROOT_OBJECT_ID,
                    class_fqn=PROVIDER_CONFIG_CLASS_FQN,
                    function_name="add_route",
                    args=[
                        " USD-HOSTED-CHECKOUT ",
                        target_coin_id,
                        "usd",
                        2,
                        ExternalCapitalConversionMode.direct_denomination.value,
                        50,
                        1_000_000,
                    ],
                ),
            ],
        )

    assertions.expect_root(config_id)
    assertions.expect_instance(config_id)
    assertions.expect_instance(route_id)
    assertions.expect_edge(
        source_id=config_id,
        target_id=route_id,
        relationship_name="routes",
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=config_id,
        field_name="provider_finance_entity_id",
        expected=provider_finance_entity_id,
    )
    assertions.expect_primitive(
        instance_id=config_id,
        field_name="provider_key",
        expected="stripe",
    )
    _expect_uuid_primitive(
        assertions,
        instance_id=route_id,
        field_name="target_coin_id",
        expected=target_coin_id,
    )
    assertions.expect_primitive(
        instance_id=route_id,
        field_name="route_key",
        expected="usd-hosted-checkout",
    )
    assertions.expect_primitive(
        instance_id=route_id,
        field_name="external_currency",
        expected="USD",
    )
    assertions.expect_primitive(
        instance_id=route_id,
        field_name="external_minor_unit_exponent",
        expected=2,
    )


@pytest.mark.asyncio
async def test_provider_config_normalizes_provider_key() -> None:
    provider_finance_entity_id = uuid4()

    config = await build_provider_config(
        provider_finance_entity_id=provider_finance_entity_id,
        provider_key=" Stripe ",
        label=" Stripe Hosted Checkout ",
    )

    assert config.id == stable_external_capital_provider_config_id(
        provider_finance_entity_id=provider_finance_entity_id,
        provider_key="stripe",
    )
    assert config.provider_key == "stripe"
    assert config.label == "Stripe Hosted Checkout"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"external_currency": "US"}, "three-letter ASCII"),
        ({"external_minor_unit_exponent": -1}, "between 0 and 18"),
        ({"target_coin_id": stable_coin_id(symbol="EUR")}, "target Coin"),
        ({"min_external_amount_minor": 0}, "must be positive"),
        (
            {
                "min_external_amount_minor": 200,
                "max_external_amount_minor": 100,
            },
            "must be >=",
        ),
    ],
)
async def test_provider_route_rejects_ambiguous_capital_coordinates(
    overrides: dict[str, object],
    message: str,
) -> None:
    kwargs: dict[str, object] = {
        "external_capital_provider_config_id": uuid4(),
        "route_key": "usd-hosted-checkout",
        "target_coin_id": stable_coin_id(symbol="USD"),
        "external_currency": "USD",
        "external_minor_unit_exponent": 2,
        "min_external_amount_minor": 50,
        "max_external_amount_minor": 1_000_000,
    }
    kwargs.update(overrides)

    with pytest.raises(ValueError, match=message):
        await build_provider_route(**kwargs)  # type: ignore[arg-type]
