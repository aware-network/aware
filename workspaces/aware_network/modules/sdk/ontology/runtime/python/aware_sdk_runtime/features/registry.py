from __future__ import annotations

from aware_sdk_runtime.features.contracts import (
    SdkOperationCatalogFeatureContext,
    SdkOperationCatalogFeatureProvider,
    SdkOperationCatalogFeatureResult,
)
from aware_sdk_runtime.features.delta_event_policy.provider import (
    SDK_DELTA_EVENT_POLICY_FEATURE_PROVIDER,
)


_CATALOG_FEATURE_PROVIDERS = (SDK_DELTA_EVENT_POLICY_FEATURE_PROVIDER,)


def registered_operation_catalog_feature_providers() -> tuple[
    SdkOperationCatalogFeatureProvider,
    ...,
]:
    return _CATALOG_FEATURE_PROVIDERS


def operation_catalog_feature_results(
    context: SdkOperationCatalogFeatureContext,
) -> tuple[SdkOperationCatalogFeatureResult, ...]:
    return tuple(
        provider.catalog_builder(context)
        for provider in registered_operation_catalog_feature_providers()
    )


__all__ = [
    "operation_catalog_feature_results",
    "registered_operation_catalog_feature_providers",
]
