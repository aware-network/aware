from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Mapping


class AwareEconomyPriceType(str, Enum):
    fixed = "fixed"
    dynamic = "dynamic"


@dataclass(frozen=True, slots=True)
class AwareEconomyTomlPackageSpec:
    package_name: str
    fqn_prefix: str
    version_number: int = 1
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AwareEconomyTomlBuildSpec:
    sources_dir: str = "economy"
    include_paths: list[str] = field(default_factory=lambda: ["**/*.aware"])
    exclude_paths: list[str] = field(default_factory=list)
    force_fresh_scan: bool = True


@dataclass(frozen=True, slots=True)
class AwareEconomyTomlPricingPolicySpec:
    name: str
    version: int = 1
    description: str | None = None
    policy_json: Mapping[str, object] = field(default_factory=dict)
    fail_closed: bool = True


@dataclass(frozen=True, slots=True)
class AwareEconomyTomlPriceScheduleSpec:
    name: str
    effective_from: datetime
    version: int = 1
    effective_until: datetime | None = None
    fixed_amount: Decimal | None = None
    markup_percentage: Decimal | None = None


@dataclass(frozen=True, slots=True)
class AwareEconomyTomlPriceSpec:
    name: str
    coin: str
    type: AwareEconomyPriceType
    pricing_policy: AwareEconomyTomlPricingPolicySpec
    schedules: tuple[AwareEconomyTomlPriceScheduleSpec, ...]


@dataclass(frozen=True, slots=True)
class AwareEconomyTomlSpec:
    aware_economy: int
    economy: AwareEconomyTomlPackageSpec
    build: AwareEconomyTomlBuildSpec
    prices: tuple[AwareEconomyTomlPriceSpec, ...] = ()


__all__ = [
    "AwareEconomyTomlBuildSpec",
    "AwareEconomyTomlPackageSpec",
    "AwareEconomyTomlPriceScheduleSpec",
    "AwareEconomyTomlPriceSpec",
    "AwareEconomyTomlPricingPolicySpec",
    "AwareEconomyTomlSpec",
    "AwareEconomyPriceType",
]
