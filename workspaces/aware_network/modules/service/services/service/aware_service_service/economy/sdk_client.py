from __future__ import annotations

from aware_economy_sdk import EconomySdkClient, build_economy_sdk_client


def build_service_economy_sdk_client(*, api_invoker: object) -> EconomySdkClient:
    """Construct the public Economy SDK for a Service-owned API route."""

    return build_economy_sdk_client(api_invoker=api_invoker)


__all__ = ["build_service_economy_sdk_client"]
