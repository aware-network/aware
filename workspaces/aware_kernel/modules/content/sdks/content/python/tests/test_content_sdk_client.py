from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_content_sdk import AwareContentSdk, ContentSdkError
from aware_content_service_dto.content.content_service_operation import (
    ContentPackageExportDocumentV1,
    ContentPackageMaterializationResultV1,
    ContentTextResolutionV1,
    MaterializeContentPackageResponse,
    ResolveContentTextResponse,
)


class _TextClient:
    def __init__(self) -> None:
        self.request = None

    async def resolve_content_text(self, request):
        self.request = request
        return ResolveContentTextResponse(
            success=True,
            resolution=ContentTextResolutionV1(
                content_id=request.content_id,
                content_key="post/demo",
                title="Demo",
                text="hello aware",
                digest="1" * 64,
                size_bytes=11,
            ),
        )


class _PackageClient:
    def __init__(self) -> None:
        self.request = None

    async def materialize_content_package(self, request):
        self.request = request
        return MaterializeContentPackageResponse(
            success=True,
            materialization=ContentPackageMaterializationResultV1(
                content_package_id=uuid4(),
                content_id=uuid4(),
                package_name=request.package_export.package_name,
                content_key=request.package_export.content_key,
                source_provider_key=request.package_export.source_provider_key,
                source_ref=request.package_export.source_ref,
                target_path=request.package_export.target_path,
                digest="2" * 64,
                size_bytes=12,
            ),
        )


@pytest.mark.asyncio
async def test_content_sdk_wraps_generated_api_client() -> None:
    text = _TextClient()
    api_client = SimpleNamespace(content=SimpleNamespace(text=text))
    sdk = AwareContentSdk(api_client=api_client)
    content_id = uuid4()
    branch_id = uuid4()

    response = await sdk.resolve_content_text(
        content_id=content_id,
        branch_id=branch_id,
        max_chars=280,
    )

    assert response.resolution is not None
    assert response.resolution.content_id == content_id
    assert response.resolution.text == "hello aware"
    assert text.request.content_id == content_id
    assert text.request.branch_id == branch_id
    assert text.request.max_chars == 280


@pytest.mark.asyncio
async def test_content_sdk_raises_on_failed_response() -> None:
    class _FailingTextClient:
        async def resolve_content_text(self, request):
            return ResolveContentTextResponse(success=False, error="missing content")

    api_client = SimpleNamespace(content=SimpleNamespace(text=_FailingTextClient()))
    sdk = AwareContentSdk(api_client=api_client)

    with pytest.raises(ContentSdkError, match="missing content"):
        await sdk.resolve_content_text(content_id=uuid4())


@pytest.mark.asyncio
async def test_content_sdk_materializes_content_package_export() -> None:
    package = _PackageClient()
    api_client = SimpleNamespace(content=SimpleNamespace(package=package))
    sdk = AwareContentSdk(api_client=api_client)
    branch_id = uuid4()
    package_export = ContentPackageExportDocumentV1(
        package_name="aware_goal/latest",
        source_provider_key="aware_goal",
        source_ref="goal:demo",
        content_key="aware_goal:goal:demo:latest",
        target_path="docs/goals/LATEST.md",
        content_text="hello aware",
    )

    response = await sdk.materialize_content_package(
        package_export=package_export,
        branch_id=branch_id,
    )

    assert response.materialization is not None
    assert response.materialization.package_name == "aware_goal/latest"
    assert response.materialization.source_provider_key == "aware_goal"
    assert package.request.branch_id == branch_id
    assert package.request.package_export is package_export


@pytest.mark.asyncio
async def test_content_sdk_enriches_materialization_with_servicehost_receipt() -> None:
    package = _PackageClient()
    service_operation_commit_id = uuid4()
    network_request_id = uuid4()
    api_client = SimpleNamespace(
        content=SimpleNamespace(package=package),
        _client=SimpleNamespace(
            last_invocation_diagnostics=SimpleNamespace(
                transport_receipt={
                    "network_request_id": str(network_request_id),
                    "service_operation_commit_id": str(service_operation_commit_id),
                }
            )
        ),
    )
    sdk = AwareContentSdk(api_client=api_client)

    response = await sdk.materialize_content_package(
        package_export=ContentPackageExportDocumentV1(
            package_name="aware_goal/latest",
            source_provider_key="aware_goal",
            source_ref="goal:demo",
            content_key="aware_goal:goal:demo:latest",
            target_path="docs/goals/LATEST.md",
            content_text="hello aware",
        )
    )

    assert response.materialization is not None
    assert response.materialization.domain_commit_id == service_operation_commit_id
    assert response.materialization.service_host_receipt_ref == (
        f"service-host:{network_request_id}"
    )
    assert response.materialization.provenance["service_host_transport_receipt"] == {
        "network_request_id": str(network_request_id),
        "service_operation_commit_id": str(service_operation_commit_id),
    }


@pytest.mark.asyncio
async def test_content_sdk_raises_on_failed_materialization() -> None:
    class _FailingPackageClient:
        async def materialize_content_package(self, request):
            return MaterializeContentPackageResponse(
                success=False,
                error="package rejected",
            )

    api_client = SimpleNamespace(
        content=SimpleNamespace(package=_FailingPackageClient())
    )
    sdk = AwareContentSdk(api_client=api_client)

    with pytest.raises(ContentSdkError, match="package rejected"):
        await sdk.materialize_content_package(
            package_export=ContentPackageExportDocumentV1(
                package_name="aware_goal/latest",
                source_provider_key="aware_goal",
                source_ref="goal:demo",
                target_path="docs/goals/LATEST.md",
                content_text="hello aware",
            )
        )
