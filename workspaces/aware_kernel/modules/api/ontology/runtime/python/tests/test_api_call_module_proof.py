from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, cast
from uuid import UUID, uuid4

import pytest
from aware_api_runtime.handlers._generated import meta_handlers as api_meta_handlers
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
    find_meta_graph_projection_hash_by_name,
)
from aware_meta.runtime.generated_handler_discovery import (
    discover_meta_graph_generated_handler_provider_set,
)
from aware_meta.runtime.testing import IsolatedMetaAwareRoot, MetaOIGAssertions
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from _api_runtime_test_paths import (
    API_META_PACKAGE_MANIFEST_PATHS,
    API_META_PYTHON_ROOTS,
    REPO_ROOT,
)
from aware_api_runtime.invocation import resolve_api_invocation_ir
from aware_api_runtime.snapshots.commit import (
    commit_api_reference_snapshot,
)
from aware_api_runtime.models import (
    APICapabilityEndpointOwnership,
    APICapabilityEndpointRequestConfigOwnership,
    APICapabilityOwnership,
    APIOwnership,
)
from aware_api_runtime.invocation.materialization import materialize_api_call


_API_META_HANDLERS_ANY: Any = api_meta_handlers
_API_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _API_META_HANDLERS_ANY,
)
_API_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _API_META_HANDLERS_ANY,
)


def _api_meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return API_META_PACKAGE_MANIFEST_PATHS


def _api_meta_python_roots(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return API_META_PYTHON_ROOTS


def _prepend_api_meta_python_roots(
    *,
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    syspath_prepend = cast(Callable[[str], None], monkeypatch.syspath_prepend)
    for python_root in _api_meta_python_roots(repo_root):
        if python_root.exists():
            syspath_prepend(str(python_root))


def _build_api_meta_runtime(*, repo_root: Path, aware_root: Path) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_api_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_API_META_HANDLER_MODULE,),
        bootstrap_modules=(_API_META_BOOTSTRAP_MODULE,),
    )
    assert runtime.context is not None
    return runtime


def _select_runtime_inline_request_class_config(runtime_index) -> ClassConfig:
    class_configs = sorted(
        runtime_index.class_configs_by_id.values(),
        key=lambda item: ((item.class_fqn or ""), str(item.id)),
    )
    for class_config in class_configs:
        if class_config.value_mode == ClassValueMode.inline_value:
            return class_config
    raise AssertionError(
        "Expected one compiled inline_value ClassConfig for the API call module proof"
    )


def test_api_runtime_index_advertises_generated_handler_provider_root(
    tmp_path: Path,
) -> None:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_api_meta_package_manifest_paths(REPO_ROOT),
        workspace_root=REPO_ROOT,
        aware_root=tmp_path / "aware_root",
    )
    runtime_context = runtime.context
    assert runtime_context is not None
    runtime_index = runtime_context.index

    assert "aware_api_runtime" in tuple(
        runtime_index.runtime_handler_provider_import_roots
    )
    provider_set = discover_meta_graph_generated_handler_provider_set(
        index=runtime_index,
    )
    assert provider_set is not None
    assert "aware_api_runtime.handlers._generated.meta_handlers" in (
        provider_set.provider_module_names
    )
    assert provider_set.empty_lane_bootstrap_resolver is not None
    assert (
        MetaGraphGeneratedLanguageHandlerKey(
            owner_key="aware_api.api.ApiCall",
            function_name="create_via_api_capability_endpoint",
            is_constructor=True,
            owner_class_fqn="aware_api.api.ApiCall",
            owner_class_name="ApiCall",
        )
        in provider_set.empty_lane_bootstrap_resolver.bootstraps_by_key
    )


def _api_ownership_for_runtime(*, request_class_ref: str) -> tuple[APIOwnership, ...]:
    return (
        APIOwnership(
            name="openai-api",
            source_path="runtime-proof",
            capabilities=(
                APICapabilityOwnership(
                    name="door",
                    source_path="runtime-proof",
                    endpoints=(
                        APICapabilityEndpointOwnership(
                            name="open",
                            source_path="runtime-proof",
                            request_config=APICapabilityEndpointRequestConfigOwnership(
                                class_ref=request_class_ref,
                                source_path="runtime-proof",
                            ),
                            description="Open the API proof door.",
                        ),
                    ),
                    description="Door operations",
                ),
            ),
            graphs=(),
        ),
    )


@pytest.mark.asyncio
async def test_api_call_projection_module_proof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = REPO_ROOT
    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_api_ontology  # noqa: F401

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_api_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        runtime_context = runtime.context
        assert runtime_context is not None
        runtime_index = runtime_context.index
        request_class_config = _select_runtime_inline_request_class_config(
            runtime_index
        )
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index, projection_name="Api"
        )
        api_call_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index,
            projection_name="ApiCall",
        )
        assert api_call_projection_hash != api_projection_hash
        branch_id = uuid4()
        actor_id: UUID | None = None
        class_config_id = request_class_config.id
        assert class_config_id is not None
        api_snapshot = await commit_api_reference_snapshot(
            index=runtime_index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
            api_name="openai-api",
            endpoint_refs=("openai-api.door.open",),
            endpoint_request_class_config_ids={
                "openai-api.door.open": class_config_id,
            },
        )
        assert api_snapshot.endpoint_ids_by_ref["openai-api.door.open"]

        ir = resolve_api_invocation_ir(
            api_ownership=_api_ownership_for_runtime(
                request_class_ref=str(request_class_config.class_fqn or ""),
            ),
            endpoint_ref="openai-api.door.open",
            request_payload={},
        )
        result = await materialize_api_call(
            runtime=runtime,
            index=runtime_index,
            actor_id=actor_id,
            source_lane=MaterializationLaneContext(
                branch_id=branch_id,
                projection_hash=api_projection_hash,
            ),
            target_lane=MaterializationLaneContext(
                branch_id=branch_id,
                projection_hash=api_call_projection_hash,
            ),
            ir=ir,
        )
        api_call_id = result.binding.api_call_id

        api_call_head = await FSCommitStore().head(
            branch_id=branch_id,
            projection_hash=api_call_projection_hash,
        )
        assert api_call_head is not None
        assert api_call_head.get("commit_id")
        assert api_call_head.get("object_instance_graph_id")

        opg = runtime_index.opg_by_hash[api_call_projection_hash]
        oig, _ = await OIGMaterializer().get(
            branch_id=branch_id,
            ocg=runtime_index.ocg,
            opg=opg,
            commit_id=UUID(str(api_call_head["commit_id"])),
            oig_id=UUID(str(api_call_head["object_instance_graph_id"])),
            attribute_configs_by_id=runtime_index.attribute_configs_by_id,
            class_configs_by_id=runtime_index.class_configs_by_id,
        )
        assertions = MetaOIGAssertions(oig=oig, index=runtime_index)
        assertions.expect_root(api_call_id)
        assertions.expect_instance(api_call_id)
        assert assertions.primitive(
            instance_id=api_call_id,
            field_name="call_key",
        ) in {result.binding.call_key, str(result.binding.call_key)}
