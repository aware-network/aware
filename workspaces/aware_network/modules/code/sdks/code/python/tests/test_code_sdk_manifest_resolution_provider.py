from __future__ import annotations

import pytest

from aware_code_sdk import (
    AwareCodeSdk,
    BlockingCodeSdkManifestResolutionProvider,
    CodeSdkSemanticContractCatalog,
    CodeSemanticContract,
    CodeSemanticManifestResolutionDescriptor,
    FindCodeSemanticManifestResolutionRequest,
    LocalCatalogCodeSdkManifestResolutionProvider,
)


def _catalog() -> CodeSdkSemanticContractCatalog:
    return CodeSdkSemanticContractCatalog(
        semantic_contracts=(
            CodeSemanticContract(
                provider_key="aware_api",
                semantic_scope_keys=["api.semantic_contract"],
                manifest_resolution=[
                    CodeSemanticManifestResolutionDescriptor(
                        semantic_owner="aware_api.package",
                        manifest_kind="aware_api_toml",
                        filename="aware.api.toml",
                        contract="aware.api",
                        loader_module="aware_api_runtime.manifest.loader",
                        loader_name="load_aware_api_toml_spec",
                        workspace_manifest_kind="api",
                        semantic_package_family="api",
                        semantic_package_kind="api_package",
                        code_package_surface="api",
                        priority=20,
                    )
                ],
            ),
        )
    )


def test_manifest_resolution_provider_uses_local_catalog_synchronously() -> None:
    sdk = AwareCodeSdk.local(catalog=_catalog())

    provider = sdk.manifest_resolution_provider()
    response = provider.find_manifest_resolution(
        filename="aware.api.toml",
        workspace_manifest_kind="api",
    )

    assert isinstance(provider, LocalCatalogCodeSdkManifestResolutionProvider)
    assert response.success is True
    assert len(response.matches) == 1
    assert response.matches[0].provider_key == "aware_api"
    assert response.matches[0].manifest_resolution.loader_module == (
        "aware_api_runtime.manifest.loader"
    )


@pytest.mark.asyncio
async def test_async_manifest_resolution_provider_uses_generated_facade() -> None:
    sdk = AwareCodeSdk.local(catalog=_catalog())

    provider = sdk.async_manifest_resolution_provider()
    response = await provider.find_manifest_resolution(
        FindCodeSemanticManifestResolutionRequest(
            manifest_kind="aware_api_toml",
            filename="aware.api.toml",
            workspace_manifest_kind="api",
        )
    )

    assert response.success is True
    assert len(response.matches) == 1
    assert response.matches[0].semantic_contract.provider_key == "aware_api"


def test_code_sdk_has_no_service_locator() -> None:
    service_locator_name = "local" + "_service"
    assert service_locator_name not in vars(AwareCodeSdk)


@pytest.mark.asyncio
async def test_blocking_provider_rejects_active_event_loop() -> None:
    provider = AwareCodeSdk.local(catalog=_catalog()).manifest_resolution_provider()
    blocking_provider = BlockingCodeSdkManifestResolutionProvider(
        async_provider=AwareCodeSdk.local(
            catalog=_catalog()
        ).async_manifest_resolution_provider()
    )

    assert isinstance(provider, LocalCatalogCodeSdkManifestResolutionProvider)
    with pytest.raises(RuntimeError, match="active event loop"):
        blocking_provider.find_manifest_resolution(filename="aware.api.toml")
