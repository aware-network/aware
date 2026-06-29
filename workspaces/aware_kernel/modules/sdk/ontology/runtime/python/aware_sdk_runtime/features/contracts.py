from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aware_sdk_runtime.builder import SdkCompilePlan
    from aware_sdk_runtime.models import SdkConfigPlan


JsonMapping = Mapping[str, object]


@dataclass(frozen=True, slots=True)
class SdkOperationCatalogFeaturePayloadUpdate:
    target_ref: str
    fields: JsonMapping


@dataclass(frozen=True, slots=True)
class SdkOperationCatalogFeatureContext:
    plan: SdkCompilePlan
    sdk_config: SdkConfigPlan
    catalog_payload: JsonMapping


@dataclass(frozen=True, slots=True)
class SdkOperationCatalogFeatureResult:
    feature_key: str
    catalog_fields: JsonMapping = field(default_factory=dict)
    operation_fields: tuple[SdkOperationCatalogFeaturePayloadUpdate, ...] = ()
    surface_fields: tuple[SdkOperationCatalogFeaturePayloadUpdate, ...] = ()
    surface_method_fields: tuple[SdkOperationCatalogFeaturePayloadUpdate, ...] = ()


SdkOperationCatalogFeatureBuilder = Callable[
    [SdkOperationCatalogFeatureContext],
    SdkOperationCatalogFeatureResult,
]


@dataclass(frozen=True, slots=True)
class SdkOperationCatalogFeatureProvider:
    feature_key: str
    catalog_builder: SdkOperationCatalogFeatureBuilder


__all__ = [
    "JsonMapping",
    "SdkOperationCatalogFeatureBuilder",
    "SdkOperationCatalogFeatureContext",
    "SdkOperationCatalogFeaturePayloadUpdate",
    "SdkOperationCatalogFeatureProvider",
    "SdkOperationCatalogFeatureResult",
]
