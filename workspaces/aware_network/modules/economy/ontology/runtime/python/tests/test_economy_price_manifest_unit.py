from __future__ import annotations

from decimal import Decimal

import pytest

from aware_economy.manifest import (
    AwareEconomyPriceType,
    AwareEconomyTomlError,
    load_aware_economy_toml_spec_from_text,
)


_BASE = """
aware_economy = 1

[economy]
package_name = "aware-inference-economy"
fqn_prefix = "aware_inference_economy"

[build]
sources_dir = "."

[[prices]]
name = "inference.submit"
coin = "USD"
type = "dynamic"

[prices.pricing_policy]
name = "inference.submit.provider-margin"
fail_closed = true

[[prices.schedules]]
name = "default"
effective_from = "2026-07-12T00:00:00Z"
markup_percentage = "20"
"""


def test_economy_manifest_loads_dynamic_price_authority() -> None:
    spec = load_aware_economy_toml_spec_from_text(toml_text=_BASE)

    assert len(spec.prices) == 1
    price = spec.prices[0]
    assert price.name == "inference.submit"
    assert price.coin == "USD"
    assert price.type is AwareEconomyPriceType.dynamic
    assert price.pricing_policy.fail_closed is True
    assert price.schedules[0].markup_percentage == Decimal("20")
    assert price.schedules[0].fixed_amount is None


@pytest.mark.parametrize(
    "target, replacement, expected",
    (
        (
            'markup_percentage = "20"',
            "markup_percentage = 20",
            "canonical decimal text",
        ),
        (
            'markup_percentage = "20"',
            'markup_percentage = "20"\nfixed_amount = "1"',
            "dynamic price requires",
        ),
        (
            'effective_from = "2026-07-12T00:00:00Z"',
            'effective_from = "2026-07-12T00:00:00"',
            "must include a timezone",
        ),
    ),
)
def test_economy_manifest_rejects_incoherent_price_authority(
    target: str,
    replacement: str,
    expected: str,
) -> None:
    source = _BASE.replace(target, replacement)
    with pytest.raises(AwareEconomyTomlError, match=expected):
        load_aware_economy_toml_spec_from_text(toml_text=source)


def test_economy_manifest_rejects_duplicate_price_names() -> None:
    price_table_start = _BASE.index("[[prices]]")
    duplicate = _BASE + _BASE[price_table_start:]
    with pytest.raises(AwareEconomyTomlError, match="Duplicate Economy price name"):
        load_aware_economy_toml_spec_from_text(toml_text=duplicate)
