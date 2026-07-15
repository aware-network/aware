from __future__ import annotations

from typing import cast

from aware_hub_sdk.artifact import (
    HubArtifactClient,
    HubGeneratedArtifactApiClient,
)
from aware_hub_sdk.code_package import (
    HubCodePackageClient,
    HubGeneratedApiClient,
)
from aware_hub_sdk.deployment_artifact import (
    HubDeploymentArtifactClient,
    HubGeneratedDeploymentArtifactApiClient,
)
from aware_hub_sdk.public_map import (
    HubGeneratedPublicMapApiClient,
    HubPublicMapClient,
)


class AwareHubSdk:
    def __init__(
        self,
        api_client: HubGeneratedApiClient,
        *,
        authority_base_url: str | None = None,
        index_url: str | None = None,
    ) -> None:
        self.api_client = api_client
        self.artifact = HubArtifactClient(
            api_client=cast(HubGeneratedArtifactApiClient, cast(object, api_client)),
            authority_base_url=authority_base_url,
            index_url=index_url,
        )
        self.code_package = HubCodePackageClient(
            api_client=api_client,
            authority_base_url=authority_base_url,
            index_url=index_url,
        )
        self.deployment_artifact = HubDeploymentArtifactClient(
            api_client=cast(
                HubGeneratedDeploymentArtifactApiClient,
                cast(object, api_client),
            ),
            authority_base_url=authority_base_url,
            index_url=index_url,
        )
        self.public_map = HubPublicMapClient(
            api_client=cast(HubGeneratedPublicMapApiClient, cast(object, api_client)),
            authority_base_url=authority_base_url,
            index_url=index_url,
        )


__all__ = ["AwareHubSdk"]
