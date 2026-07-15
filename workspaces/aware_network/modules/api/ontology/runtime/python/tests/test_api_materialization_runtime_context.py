from __future__ import annotations

from pathlib import Path

from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_TARGET_MANIFEST_PATHS_CONTEXT_KEY,
    SemanticPackageMaterializationRuntimeContextRequest,
)

import aware_api_runtime.runtime_context.workspace_materialization as api_runtime_context


def test_api_runtime_context_routes_api_dto_without_meta_target_manifest(
    tmp_path: Path,
    monkeypatch,
) -> None:
    dto_manifest_path = tmp_path / "apis" / "node" / "dto" / "aware.toml"
    captured: dict[str, object] = {}

    def fake_meta_runtime_context(
        request: SemanticPackageMaterializationRuntimeContextRequest,
    ) -> object:
        captured["request"] = request
        return object()

    monkeypatch.setattr(
        api_runtime_context,
        "build_meta_workspace_materialization_runtime_context",
        fake_meta_runtime_context,
    )

    result = api_runtime_context.build_api_workspace_materialization_runtime_context(
        SemanticPackageMaterializationRuntimeContextRequest(
            provider_key="aware_api",
            semantic_owner="aware_api.provider",
            workspace_root=tmp_path,
            repo_root=tmp_path,
            manifest_path=dto_manifest_path,
            context={
                "workspace_manifest_kind": "api_dto",
                "semantic_package_kind": "api_dto_package",
                SEMANTIC_MATERIALIZATION_TARGET_MANIFEST_PATHS_CONTEXT_KEY: (
                    dto_manifest_path.as_posix(),
                ),
            },
            provider_payload={"runtime_ontology_package_names": ("api-ontology",)},
        )
    )

    assert result is not None
    adapted_request = captured["request"]
    assert isinstance(
        adapted_request, SemanticPackageMaterializationRuntimeContextRequest
    )
    assert adapted_request.manifest_path is None
    assert (
        SEMANTIC_MATERIALIZATION_TARGET_MANIFEST_PATHS_CONTEXT_KEY
        not in adapted_request.context
    )
    assert adapted_request.context["workspace_manifest_kind"] == "api_dto"
    assert adapted_request.provider_payload == {
        "runtime_ontology_package_names": ("api-ontology",)
    }


def test_api_runtime_context_preserves_api_manifest_request(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api_manifest_path = tmp_path / "apis" / "node" / "aware.api.toml"
    captured: dict[str, object] = {}

    def fake_meta_runtime_context(
        request: SemanticPackageMaterializationRuntimeContextRequest,
    ) -> object:
        captured["request"] = request
        return object()

    monkeypatch.setattr(
        api_runtime_context,
        "build_meta_workspace_materialization_runtime_context",
        fake_meta_runtime_context,
    )
    request = SemanticPackageMaterializationRuntimeContextRequest(
        provider_key="aware_api",
        semantic_owner="aware_api.provider",
        workspace_root=tmp_path,
        repo_root=tmp_path,
        manifest_path=api_manifest_path,
        context={"workspace_manifest_kind": "api"},
        provider_payload={"runtime_ontology_package_names": ("api-ontology",)},
    )

    result = api_runtime_context.build_api_workspace_materialization_runtime_context(
        request
    )

    assert result is not None
    assert captured["request"] is request
