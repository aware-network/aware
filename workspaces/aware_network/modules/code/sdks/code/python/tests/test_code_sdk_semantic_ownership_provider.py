from __future__ import annotations

from typing import Any, cast

from aware_code_sdk import (
    AwareCodeSdk,
    CodeSdkSemanticArtifactBinding,
)


class _RecordingSemanticOwnershipProvider:
    def semantic_provider_ownerships_for_manifest_kind(
        self,
        *,
        manifest_kind: str,
    ) -> tuple[dict[str, object], ...]:
        return (
            {
                "provider_key": "aware_api",
                "role": "aware_api.provider",
                "contract": "aware.semantic_provider",
                "module": "aware_api_runtime.semantic_contract",
                "code_package_surface": "api",
                "owned_manifest_kind_count": 1,
                "echo_manifest_kind": manifest_kind,
            },
        )

    def claim_semantic_artifact_leaf(
        self,
        *,
        workspace_root: str,
        owner: dict[str, object],
        leaf: dict[str, object],
    ) -> dict[str, object]:
        assert workspace_root == "/workspace"
        assert owner["manifest_relative_path"] == "apis/demo/aware.api.toml"
        assert leaf["manifest_kind"] == "pyproject_toml"
        return {
            "owned": True,
            "owner_semantic_package_manifest": "apis/demo/aware.api.toml",
            "ownership_role": "semantic_generated_artifact",
            "artifact_manifest_kind": "pyproject_toml",
            "artifact_package_root": "apis/demo/python/aware_demo_api",
            "production": {
                "provider_key": "aware_api",
                "producer_key": "aware_api.python.public_package",
                "producer_kind": "semantic_materialization.package_output",
                "provider_payload": {
                    "package_output_key": "python.public_package",
                },
                "output_digest": "sha256:demo",
            },
        }


class _RecordingApiClient:
    def __init__(self) -> None:
        self.code = object()

    def semantic_ownership_provider(self) -> _RecordingSemanticOwnershipProvider:
        return _RecordingSemanticOwnershipProvider()


def test_code_sdk_semantic_ownership_provider_normalizes_service_payloads() -> None:
    provider = AwareCodeSdk(
        api_client=cast(Any, _RecordingApiClient()),
    ).semantic_ownership_provider()

    ownerships = provider.semantic_provider_ownerships_for_manifest_kind(
        manifest_kind="aware_api_toml",
    )
    assert len(ownerships) == 1
    assert ownerships[0].provider_key == "aware_api"
    assert ownerships[0].role == "aware_api.provider"
    assert ownerships[0].code_package_surface == "api"

    claim = provider.claim_semantic_artifact_leaf(
        workspace_root="/workspace",
        owner=CodeSdkSemanticArtifactBinding(
            module_id=None,
            package_name="demo-api",
            language="aware",
            surface="api",
            manifest_kind="aware_api_toml",
            manifest_relative_path="apis/demo/aware.api.toml",
            package_root="apis/demo",
            sources_root="apis/demo/bindings",
            package_kind="api",
            semantic_contract_provider_key="aware_api",
            semantic_contract_role="aware_api.provider",
            semantic_contract_name="aware.semantic_provider",
            semantic_contract_module="aware_api_runtime.semantic_contract",
        ),
        leaf=CodeSdkSemanticArtifactBinding(
            module_id=None,
            package_name="aware_demo_api",
            language="python",
            surface="runtime",
            manifest_kind="pyproject_toml",
            manifest_relative_path="apis/demo/python/aware_demo_api/pyproject.toml",
            package_root="apis/demo/python/aware_demo_api",
            sources_root="apis/demo/python/aware_demo_api/src",
        ),
    )

    assert claim is not None
    assert claim.owned is True
    assert claim.production is not None
    assert claim.production.provider_key == "aware_api"
    assert claim.production.producer_key == "aware_api.python.public_package"
    assert claim.production.provider_payload == {
        "package_output_key": "python.public_package",
    }
