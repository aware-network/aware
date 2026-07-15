from __future__ import annotations

from aware_experience_service_api import AwareExperienceServiceApiClient


def build_experience_sdk_client(api_client: AwareExperienceServiceApiClient) -> object:
    from aware_experience_sdk import build_experience_sdk_client as _build_client

    return _build_client(api_client)


__all__ = ["build_experience_sdk_client"]
