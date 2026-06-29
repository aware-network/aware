from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.runtime.graph_context import build_meta_graph_runtime_context
import aware_meta.runtime.read_model_provider as read_model_provider_module
from aware_meta.runtime.read_model_provider import (
    MetaRuntimeReadModelProvider,
    MetaRuntimeReadModelRequest,
    read_workspace_meta_runtime_read_model,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)


def _runtime_graph(
    *,
    projection_name: str = "Workspace",
    projection_hash: str = "sha256:test:Workspace",
) -> ObjectConfigGraph:
    graph_id = uuid4()
    class_config = ClassConfig(
        class_fqn="aware_workspace.Workspace",
        name="Workspace",
    )
    return ObjectConfigGraph(
        id=graph_id,
        name="Workspace Runtime Graph",
        hash="sha256:test:workspace-runtime-graph",
        fqn_prefix="aware_workspace",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                object_config_graph_id=graph_id,
                type=ObjectConfigGraphNodeType.class_,
                node_key=class_config.class_fqn,
                class_config=class_config,
            )
        ],
        object_projection_graphs=[
            ObjectProjectionGraph(
                object_config_graph_id=graph_id,
                language=CodeLanguage.aware,
                name=projection_name,
                projection_hash=projection_hash,
            )
        ],
    )


def test_meta_runtime_read_model_provider_caches_workspace_projection_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    environment_config_id = uuid4()
    calls: list[tuple[Path, tuple[str, ...]]] = []

    def _build_context(
        *,
        repo_root: Path,
        aware_root: Path | None,
        required_projection_names: tuple[str, ...],
        required_package_names: tuple[str, ...],
        environment_config_id: UUID | None,
        semantic_ontology_package_catalog: object | None,
        composite_name: str,
    ) -> object:
        assert aware_root == repo_root
        assert environment_config_id is not None
        assert semantic_ontology_package_catalog is None
        calls.append((repo_root, required_projection_names))
        return build_meta_graph_runtime_context(
            runtime_graphs=(_runtime_graph(),),
            environment_config_id=environment_config_id,
            composite_name=composite_name,
        )

    monkeypatch.setattr(
        "aware_meta.runtime.read_model_provider."
        "build_meta_graph_runtime_context_for_workspace_required_projections",
        _build_context,
    )
    provider = MetaRuntimeReadModelProvider()
    request = MetaRuntimeReadModelRequest(
        repo_root=tmp_path,
        required_projection_names=("Workspace",),
        environment_config_id=environment_config_id,
    )

    first = provider.read_workspace_required_projections(request)
    second = provider.read_workspace_required_projections(request)

    assert len(calls) == 1
    assert first.cache_status == "miss"
    assert second.cache_status == "hit"
    assert first.context is second.context
    assert first.index.environment_config_id == environment_config_id
    assert first.projection_hash_for_name("Workspace") == "sha256:test:Workspace"
    assert second.projection_hash_by_name["Workspace"] == "sha256:test:Workspace"
    assert first.provider_duration_s >= 0.0
    assert first.read_model_version == "aware.meta.runtime.read_model.v1"


def test_meta_runtime_read_model_provider_force_refresh_and_invalidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def _build_context(
        *,
        repo_root: Path,
        aware_root: Path | None,
        required_projection_names: tuple[str, ...],
        required_package_names: tuple[str, ...],
        environment_config_id: UUID | None,
        semantic_ontology_package_catalog: object | None,
        composite_name: str,
    ) -> object:
        nonlocal calls
        _ = (
            repo_root,
            aware_root,
            required_projection_names,
            environment_config_id,
            semantic_ontology_package_catalog,
            composite_name,
        )
        calls += 1
        return build_meta_graph_runtime_context(runtime_graphs=(_runtime_graph(),))

    monkeypatch.setattr(
        "aware_meta.runtime.read_model_provider."
        "build_meta_graph_runtime_context_for_workspace_required_projections",
        _build_context,
    )
    provider = MetaRuntimeReadModelProvider()
    request = MetaRuntimeReadModelRequest(
        repo_root=tmp_path,
        required_projection_names=("Workspace",),
    )

    provider.read_workspace_required_projections(request)
    refreshed = provider.read_workspace_required_projections(
        MetaRuntimeReadModelRequest(
            repo_root=tmp_path,
            required_projection_names=("Workspace",),
            force_refresh=True,
        )
    )
    provider.invalidate_workspace(repo_root=tmp_path)
    invalidated = provider.read_workspace_required_projections(request)

    assert calls == 3
    assert refreshed.cache_status == "miss"
    assert invalidated.cache_status == "miss"


def test_meta_runtime_read_model_provider_uses_persistent_cache_across_instances(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    closure_fingerprint_calls = 0
    stored_manifest_fingerprint_calls = 0
    source_fingerprint = {
        "schema": "aware.meta.runtime.read_model.source_fingerprint.v1",
        "status": "ok",
        "packages": [
            {
                "manifest_path": "modules/workspace/structure/ontology/aware.toml",
                "manifest_sha256": "sha256:manifest",
                "source_manifest_hash": "sha256:source",
            }
        ],
    }

    def _build_context(
        *,
        repo_root: Path,
        aware_root: Path | None,
        required_projection_names: tuple[str, ...],
        required_package_names: tuple[str, ...],
        environment_config_id: UUID | None,
        semantic_ontology_package_catalog: object | None,
        composite_name: str,
    ) -> object:
        nonlocal calls
        _ = (
            repo_root,
            aware_root,
            required_projection_names,
            required_package_names,
            environment_config_id,
            semantic_ontology_package_catalog,
            composite_name,
        )
        calls += 1
        return build_meta_graph_runtime_context(runtime_graphs=(_runtime_graph(),))

    monkeypatch.setattr(
        read_model_provider_module,
        "build_meta_graph_runtime_context_for_workspace_required_projections",
        _build_context,
    )

    def _source_fingerprint(**kwargs: object) -> object:
        nonlocal closure_fingerprint_calls
        _ = kwargs
        closure_fingerprint_calls += 1
        return source_fingerprint

    def _stored_manifest_fingerprint(**kwargs: object) -> object:
        nonlocal stored_manifest_fingerprint_calls
        _ = kwargs
        stored_manifest_fingerprint_calls += 1
        return source_fingerprint

    monkeypatch.setattr(
        read_model_provider_module,
        "_read_model_source_fingerprint",
        _source_fingerprint,
    )
    monkeypatch.setattr(
        read_model_provider_module,
        "_read_model_source_fingerprint_for_manifest_paths",
        _stored_manifest_fingerprint,
    )

    request = MetaRuntimeReadModelRequest(
        repo_root=tmp_path,
        required_projection_names=("Workspace",),
    )
    first = MetaRuntimeReadModelProvider().read_workspace_required_projections(request)
    second = MetaRuntimeReadModelProvider().read_workspace_required_projections(request)

    assert calls == 1
    assert first.cache_status == "miss"
    assert second.cache_status == "persistent_hit"
    assert second.projection_hash_for_name("Workspace") == "sha256:test:Workspace"
    assert closure_fingerprint_calls == 1
    assert stored_manifest_fingerprint_calls == 1

    sidecar_paths = list(
        (tmp_path / ".aware" / "meta" / "runtime" / "read_model").glob(
            "*.context.pickle"
        )
    )
    assert len(sidecar_paths) == 1

    def _fail_context_from_persistent_payload(payload: object) -> object:
        _ = payload
        raise AssertionError("sidecar should avoid JSON context hydration")

    monkeypatch.setattr(
        read_model_provider_module,
        "_context_from_persistent_payload",
        _fail_context_from_persistent_payload,
    )

    third = MetaRuntimeReadModelProvider().read_workspace_required_projections(request)

    assert calls == 1
    assert third.cache_status == "persistent_hit"
    assert third.projection_hash_for_name("Workspace") == "sha256:test:Workspace"
    assert stored_manifest_fingerprint_calls == 2


def test_meta_api_activation_read_model_sidecar_avoids_context_hydration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    source_fingerprint = {
        "schema": "aware.meta.runtime.read_model.source_fingerprint.v1",
        "status": "ok",
        "packages": [
            {
                "manifest_path": "modules/workspace/structure/ontology/aware.toml",
                "manifest_sha256": "sha256:manifest",
                "source_manifest_hash": "sha256:source",
            }
        ],
    }

    def _build_context(
        *,
        repo_root: Path,
        aware_root: Path | None,
        required_projection_names: tuple[str, ...],
        required_package_names: tuple[str, ...],
        environment_config_id: UUID | None,
        semantic_ontology_package_catalog: object | None,
        composite_name: str,
    ) -> object:
        nonlocal calls
        _ = (
            repo_root,
            aware_root,
            required_projection_names,
            required_package_names,
            environment_config_id,
            semantic_ontology_package_catalog,
            composite_name,
        )
        calls += 1
        return build_meta_graph_runtime_context(runtime_graphs=(_runtime_graph(),))

    monkeypatch.setattr(
        read_model_provider_module,
        "build_meta_graph_runtime_context_for_workspace_required_projections",
        _build_context,
    )
    monkeypatch.setattr(
        read_model_provider_module,
        "_read_model_source_fingerprint",
        lambda **kwargs: source_fingerprint,
    )
    monkeypatch.setattr(
        read_model_provider_module,
        "_read_model_source_fingerprint_for_manifest_paths",
        lambda **kwargs: source_fingerprint,
    )
    monkeypatch.setattr(
        read_model_provider_module,
        "_read_model_fast_source_fingerprint_for_manifest_paths",
        lambda **kwargs: {
            "schema": "aware.meta.runtime.read_model.fast_source_fingerprint.v1",
            "status": "ok",
            "packages": [{"manifest_path": "aware.toml"}],
        },
    )

    request = MetaRuntimeReadModelRequest(
        repo_root=tmp_path,
        required_projection_names=("Workspace",),
    )

    first = MetaRuntimeReadModelProvider().read_api_activation(request)

    assert first.cache_status == "miss"
    assert first.projection_hash_for_name("Workspace") == "sha256:test:Workspace"

    sidecar_paths = list(
        (tmp_path / ".aware" / "meta" / "runtime" / "read_model").glob(
            "*.api_activation.json"
        )
    )
    assert len(sidecar_paths) == 1

    def _fail_candidate(**kwargs: object) -> object:
        _ = kwargs
        raise AssertionError("compact sidecar should avoid context JSON candidate")

    monkeypatch.setattr(
        read_model_provider_module,
        "_try_read_persistent_read_model_candidate",
        _fail_candidate,
    )

    second = MetaRuntimeReadModelProvider().read_api_activation(request)

    assert calls == 1
    assert second.cache_status == "persistent_hit"
    assert second.projection_hash_for_name("Workspace") == "sha256:test:Workspace"
    assert second.read_model_version == "aware.meta.api_activation.read_model.v1"


def test_meta_runtime_read_model_pickle_sidecar_can_be_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    source_fingerprint = {
        "schema": "aware.meta.runtime.read_model.source_fingerprint.v1",
        "status": "ok",
        "packages": [
            {
                "manifest_path": "modules/workspace/structure/ontology/aware.toml",
                "manifest_sha256": "sha256:manifest",
                "source_manifest_hash": "sha256:source",
            }
        ],
    }

    def _build_context(
        *,
        repo_root: Path,
        aware_root: Path | None,
        required_projection_names: tuple[str, ...],
        required_package_names: tuple[str, ...],
        environment_config_id: UUID | None,
        semantic_ontology_package_catalog: object | None,
        composite_name: str,
    ) -> object:
        nonlocal calls
        _ = (
            repo_root,
            aware_root,
            required_projection_names,
            required_package_names,
            environment_config_id,
            semantic_ontology_package_catalog,
            composite_name,
        )
        calls += 1
        return build_meta_graph_runtime_context(runtime_graphs=(_runtime_graph(),))

    monkeypatch.setenv("AWARE_META_READ_MODEL_PICKLE_SIDECAR_ENABLED", "0")
    monkeypatch.setattr(
        read_model_provider_module,
        "build_meta_graph_runtime_context_for_workspace_required_projections",
        _build_context,
    )
    monkeypatch.setattr(
        read_model_provider_module,
        "_read_model_source_fingerprint",
        lambda **kwargs: source_fingerprint,
    )
    monkeypatch.setattr(
        read_model_provider_module,
        "_read_model_source_fingerprint_for_manifest_paths",
        lambda **kwargs: source_fingerprint,
    )

    request = MetaRuntimeReadModelRequest(
        repo_root=tmp_path,
        required_projection_names=("Workspace",),
    )

    first = MetaRuntimeReadModelProvider().read_workspace_required_projections(request)
    second = MetaRuntimeReadModelProvider().read_workspace_required_projections(request)

    assert calls == 1
    assert first.cache_status == "miss"
    assert second.cache_status == "persistent_hit"
    assert not list(
        (tmp_path / ".aware" / "meta" / "runtime" / "read_model").glob(
            "*.context.pickle"
        )
    )


def test_meta_runtime_read_model_provider_rejects_stale_persistent_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    fingerprints = [
        {
            "schema": "aware.meta.runtime.read_model.source_fingerprint.v1",
            "status": "ok",
            "packages": [
                {
                    "manifest_path": "modules/workspace/structure/ontology/aware.toml",
                    "manifest_sha256": "sha256:manifest",
                    "source_manifest_hash": "sha256:source:v1",
                }
            ],
        },
        {
            "schema": "aware.meta.runtime.read_model.source_fingerprint.v1",
            "status": "ok",
            "packages": [
                {
                    "manifest_path": "modules/workspace/structure/ontology/aware.toml",
                    "manifest_sha256": "sha256:manifest",
                    "source_manifest_hash": "sha256:source:v2",
                }
            ],
        },
    ]

    def _build_context(
        *,
        repo_root: Path,
        aware_root: Path | None,
        required_projection_names: tuple[str, ...],
        required_package_names: tuple[str, ...],
        environment_config_id: UUID | None,
        semantic_ontology_package_catalog: object | None,
        composite_name: str,
    ) -> object:
        nonlocal calls
        _ = (
            repo_root,
            aware_root,
            required_projection_names,
            required_package_names,
            environment_config_id,
            semantic_ontology_package_catalog,
            composite_name,
        )
        calls += 1
        return build_meta_graph_runtime_context(runtime_graphs=(_runtime_graph(),))

    def _source_fingerprint(**kwargs: object) -> object:
        _ = kwargs
        return fingerprints[min(calls, 1)]

    def _stored_manifest_fingerprint(**kwargs: object) -> object:
        _ = kwargs
        return fingerprints[min(calls, 1)]

    monkeypatch.setattr(
        read_model_provider_module,
        "build_meta_graph_runtime_context_for_workspace_required_projections",
        _build_context,
    )
    monkeypatch.setattr(
        read_model_provider_module,
        "_read_model_source_fingerprint",
        _source_fingerprint,
    )
    monkeypatch.setattr(
        read_model_provider_module,
        "_read_model_source_fingerprint_for_manifest_paths",
        _stored_manifest_fingerprint,
    )

    request = MetaRuntimeReadModelRequest(
        repo_root=tmp_path,
        required_projection_names=("Workspace",),
    )
    first = MetaRuntimeReadModelProvider().read_workspace_required_projections(request)
    second = MetaRuntimeReadModelProvider().read_workspace_required_projections(request)

    assert calls == 2
    assert first.cache_status == "miss"
    assert second.cache_status == "miss"


def test_meta_runtime_read_model_provider_caches_custom_catalog_by_signature(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    catalog: dict[str, object] = {
        "schema": "aware.code.semantic_ontology_package_catalog.v1",
        "entries": [
            {
                "module_id": "workspace",
                "package_name": "workspace-ontology",
                "fqn_prefix": "aware_workspace",
                "manifest_path": "modules/workspace/structure/ontology/aware.toml",
                "dependency_package_names": ["meta-ontology"],
            }
        ],
    }
    catalog_equivalent: dict[str, object] = {
        "entries": [
            {
                "dependency_package_names": ["meta-ontology"],
                "fqn_prefix": "aware_workspace",
                "manifest_path": "modules/workspace/structure/ontology/aware.toml",
                "module_id": "workspace",
                "package_name": "workspace-ontology",
            }
        ],
        "schema": "aware.code.semantic_ontology_package_catalog.v1",
    }
    changed_catalog: dict[str, object] = {
        **catalog,
        "entries": [
            {
                "module_id": "home",
                "package_name": "home-ontology",
                "fqn_prefix": "aware_home",
                "manifest_path": (
                    "workspaces/aware_home/modules/home/structure/ontology/"
                    "aware.toml"
                ),
                "dependency_package_names": ["meta-ontology"],
            }
        ],
    }
    seen_catalogs: list[object | None] = []

    def _build_context(
        *,
        repo_root: Path,
        aware_root: Path | None,
        required_projection_names: tuple[str, ...],
        required_package_names: tuple[str, ...],
        environment_config_id: UUID | None,
        semantic_ontology_package_catalog: object | None,
        composite_name: str,
    ) -> object:
        nonlocal calls
        _ = (
            repo_root,
            aware_root,
            required_projection_names,
            environment_config_id,
            composite_name,
        )
        seen_catalogs.append(semantic_ontology_package_catalog)
        calls += 1
        return build_meta_graph_runtime_context(runtime_graphs=(_runtime_graph(),))

    monkeypatch.setattr(
        "aware_meta.runtime.read_model_provider."
        "build_meta_graph_runtime_context_for_workspace_required_projections",
        _build_context,
    )
    provider = MetaRuntimeReadModelProvider()
    request = MetaRuntimeReadModelRequest(
        repo_root=tmp_path,
        required_projection_names=("Workspace",),
        semantic_ontology_package_catalog=catalog,
    )

    first = provider.read_workspace_required_projections(request)
    second = provider.read_workspace_required_projections(
        MetaRuntimeReadModelRequest(
            repo_root=tmp_path,
            required_projection_names=("Workspace",),
            semantic_ontology_package_catalog=catalog_equivalent,
        )
    )
    changed = provider.read_workspace_required_projections(
        MetaRuntimeReadModelRequest(
            repo_root=tmp_path,
            required_projection_names=("Workspace",),
            semantic_ontology_package_catalog=changed_catalog,
        )
    )

    assert calls == 2
    assert seen_catalogs == [catalog, changed_catalog]
    assert first.cache_status == "miss"
    assert second.cache_status == "hit"
    assert changed.cache_status == "miss"
    assert first.context is second.context
    assert changed.context is not first.context


def test_meta_runtime_read_model_provider_carries_requested_workspace_commit_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = {
        "summary_source": "fixture",
        "revision_count": 1,
        "latest_revision": {
            "revision_id": str(uuid4()),
            "source_revision_id": "git-commit-demo",
            "source_revision_kind": "git",
            "code_package_count": 1,
        },
    }

    def _build_context(
        *,
        repo_root: Path,
        aware_root: Path | None,
        required_projection_names: tuple[str, ...],
        required_package_names: tuple[str, ...],
        environment_config_id: UUID | None,
        semantic_ontology_package_catalog: object | None,
        composite_name: str,
    ) -> object:
        _ = (
            repo_root,
            aware_root,
            required_projection_names,
            environment_config_id,
            semantic_ontology_package_catalog,
            composite_name,
        )
        return build_meta_graph_runtime_context(runtime_graphs=(_runtime_graph(),))

    monkeypatch.setattr(
        "aware_meta.runtime.read_model_provider."
        "build_meta_graph_runtime_context_for_workspace_required_projections",
        _build_context,
    )
    provider = MetaRuntimeReadModelProvider()

    read_model = provider.read_workspace_required_projections(
        MetaRuntimeReadModelRequest(
            repo_root=tmp_path,
            required_projection_names=("Workspace",),
            include_workspace_commit_truth=True,
            workspace_commit_truth=summary,
        )
    )
    omitted = provider.read_workspace_required_projections(
        MetaRuntimeReadModelRequest(
            repo_root=tmp_path,
            required_projection_names=("Workspace",),
            include_workspace_commit_truth=False,
            workspace_commit_truth=summary,
        )
    )

    assert read_model.workspace_commit_truth == summary
    assert omitted.workspace_commit_truth is None


def test_meta_runtime_read_model_provider_rejects_empty_projection_set(
    tmp_path: Path,
) -> None:
    provider = MetaRuntimeReadModelProvider()

    with pytest.raises(ValueError, match="requires at least one projection or package"):
        provider.read_workspace_required_projections(
            MetaRuntimeReadModelRequest(
                repo_root=tmp_path,
                required_projection_names=("",),
            )
        )


def test_meta_runtime_read_model_provider_allows_package_only_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = MetaRuntimeReadModelProvider()
    seen: list[tuple[tuple[str, ...], tuple[str, ...]]] = []

    def _build_context(
        *,
        repo_root: Path,
        aware_root: Path | None,
        required_projection_names: tuple[str, ...],
        required_package_names: tuple[str, ...],
        environment_config_id: UUID | None,
        semantic_ontology_package_catalog: object | None,
        composite_name: str,
    ) -> object:
        _ = (
            repo_root,
            aware_root,
            environment_config_id,
            semantic_ontology_package_catalog,
            composite_name,
        )
        seen.append((required_projection_names, required_package_names))
        return build_meta_graph_runtime_context(runtime_graphs=(_runtime_graph(),))

    monkeypatch.setattr(
        "aware_meta.runtime.read_model_provider."
        "build_meta_graph_runtime_context_for_workspace_required_projections",
        _build_context,
    )

    read_model = provider.read_workspace_required_projections(
        MetaRuntimeReadModelRequest(
            repo_root=tmp_path,
            required_projection_names=(),
            required_package_names=("environment-ontology",),
        )
    )

    assert read_model.required_projection_names == ()
    assert read_model.required_package_names == ("environment-ontology",)
    assert seen == [((), ("environment-ontology",))]


def test_workspace_meta_runtime_read_model_default_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _build_context(
        *,
        repo_root: Path,
        aware_root: Path | None,
        required_projection_names: tuple[str, ...],
        required_package_names: tuple[str, ...],
        environment_config_id: UUID | None,
        semantic_ontology_package_catalog: object | None,
        composite_name: str,
    ) -> object:
        _ = (
            repo_root,
            aware_root,
            required_projection_names,
            environment_config_id,
            semantic_ontology_package_catalog,
            composite_name,
        )
        return build_meta_graph_runtime_context(runtime_graphs=(_runtime_graph(),))

    monkeypatch.setattr(
        "aware_meta.runtime.read_model_provider."
        "build_meta_graph_runtime_context_for_workspace_required_projections",
        _build_context,
    )

    read_model = read_workspace_meta_runtime_read_model(
        repo_root=tmp_path,
        required_projection_names=("Workspace",),
        force_refresh=True,
    )

    assert read_model.cache_status == "miss"
    assert read_model.projection_hash_for_name("Workspace") == "sha256:test:Workspace"
