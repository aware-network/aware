from __future__ import annotations

from typing import Any, cast

import pytest

from aware_code_sdk import (
    AwareCodeSdk,
    ClassifyCodeSourceOwnershipRequest,
    ClassifyCodeSourceOwnershipResponse,
    CodeSourceOwnershipClassification,
    CodeSourceOwnershipObservedPath,
    CodeSourceOwnershipPackageBinding,
    CodeSourceOwnershipPathMatch,
    CodeSourceOwnershipResult,
)


class _RecordingSourceOwnershipCapability:
    def __init__(self) -> None:
        self.requests: list[ClassifyCodeSourceOwnershipRequest] = []

    async def classify(
        self,
        request: ClassifyCodeSourceOwnershipRequest,
    ) -> ClassifyCodeSourceOwnershipResponse:
        self.requests.append(request)
        return ClassifyCodeSourceOwnershipResponse(
            request_id=request.request_id,
            success=True,
            ownership_result=CodeSourceOwnershipResult(
                matches=[
                    CodeSourceOwnershipPathMatch(
                        path=request.ownership_request.observed_paths[0].path,
                        classification=(
                            CodeSourceOwnershipClassification.source_owned
                        ),
                        binding_index=0,
                        package_relative_path="src/main.py",
                    )
                ],
                package_count=1,
                path_count=1,
                source_owned_path_count=1,
            ),
        )


class _RecordingCodeClient:
    def __init__(self) -> None:
        self.source_ownership = _RecordingSourceOwnershipCapability()


class _RecordingApiClient:
    def __init__(self) -> None:
        self.code = _RecordingCodeClient()


@pytest.mark.asyncio
async def test_code_sdk_classifies_source_ownership_through_facade() -> None:
    api_client = _RecordingApiClient()
    sdk = AwareCodeSdk(api_client=cast(Any, api_client))

    response = await sdk.classify_source_ownership(
        package_bindings=[
            CodeSourceOwnershipPackageBinding(
                package_name="aware-demo",
                package_root="packages/demo",
                sources_root="packages/demo/src",
            )
        ],
        observed_paths=[
            CodeSourceOwnershipObservedPath(path="packages/demo/src/main.py")
        ],
    )

    assert response.success is True
    assert response.ownership_result is not None
    assert response.ownership_result.source_owned_path_count == 1
    assert len(api_client.code.source_ownership.requests) == 1
    request = api_client.code.source_ownership.requests[0]
    assert request.ownership_request.package_bindings[0].package_name == "aware-demo"
    assert request.ownership_request.observed_paths[0].path == (
        "packages/demo/src/main.py"
    )
