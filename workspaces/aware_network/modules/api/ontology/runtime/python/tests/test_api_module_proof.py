from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, cast
from uuid import UUID, uuid4

import pytest
from aware_api_runtime.handlers._generated import meta_handlers as api_meta_handlers
from aware_api_runtime.models import (
    APICapabilityEndpointOwnership,
    APICapabilityEndpointRequestConfigOwnership,
    APICapabilityOwnership,
    APIOwnership,
    APIViewCapabilityEndpointOwnership,
    APIViewOwnership,
    APIViewStreamPolicyOwnership,
)
from aware_api_runtime.ontology_graph.materialization import (
    materialize_api_graph_ontology,
)
from aware_api_runtime.ontology_graph.ontology import (
    build_api_ontology_plans,
    encode_api_ontology_plan_payload,
)
from aware_api_runtime.snapshots.commit import (
    commit_api_reference_snapshot,
)
from aware_api_ontology.stable_ids import (
    stable_api_capability_endpoint_id,
    stable_api_capability_id,
    stable_api_id,
    stable_api_view_capability_endpoint_id,
    stable_api_view_id,
    stable_api_view_stream_policy_id,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
    find_meta_graph_projection_hash_by_name,
)
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot,
    MetaOIGAssertions,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from _api_runtime_test_paths import (
    API_META_PACKAGE_MANIFEST_PATHS,
    API_META_PYTHON_ROOTS,
    REPO_ROOT,
)


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
        "Expected one compiled inline_value ClassConfig for the API module proof"
    )


async def _assertions_for_committed_head(
    *,
    runtime_index,
    branch_id: UUID,
    projection_hash: str,
) -> MetaOIGAssertions:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head is not None
    assert head.get("commit_id")
    assert head.get("object_instance_graph_id")
    opg = runtime_index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=runtime_index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        oig_id=UUID(str(head["object_instance_graph_id"])),
        attribute_configs_by_id=runtime_index.attribute_configs_by_id,
        class_configs_by_id=runtime_index.class_configs_by_id,
    )
    return MetaOIGAssertions(oig=oig, index=runtime_index)


@pytest.mark.asyncio
async def test_api_projection_chain_module_proof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = REPO_ROOT
    _prepend_api_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    import aware_api_ontology  # noqa: F401
    from aware_api_ontology.stable_ids import (
        stable_api_capability_endpoint_id,
        stable_api_capability_endpoint_request_config_id,
        stable_api_capability_id,
        stable_api_id,
    )

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
        class_config_id = request_class_config.id
        assert class_config_id is not None
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index, projection_name="Api"
        )

        api_id = stable_api_id(name="openai-api")
        capability_id = stable_api_capability_id(api_id=api_id, name="door")
        endpoint_id = stable_api_capability_endpoint_id(
            api_capability_id=capability_id,
            name="open",
        )
        request_config_id = stable_api_capability_endpoint_request_config_id(
            api_capability_endpoint_id=endpoint_id,
            class_config_id=class_config_id,
        )
        branch_id = uuid4()

        snapshot = await commit_api_reference_snapshot(
            index=runtime_index,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
            api_name="openai-api",
            endpoint_refs=("openai-api.door.open",),
            endpoint_request_class_config_ids={
                "openai-api.door.open": class_config_id,
            },
        )
        assert snapshot.api.id == api_id
        assert snapshot.endpoint_ids_by_ref["openai-api.door.open"] == endpoint_id
        assert snapshot.commit_id == snapshot.head_commit_id
        assert snapshot.object_count == 4
        assert snapshot.change_count > 0

        api_assertions = await _assertions_for_committed_head(
            runtime_index=runtime_index,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
        )
        api_assertions.expect_root(api_id)
        for instance_id in (api_id, capability_id, endpoint_id, request_config_id):
            api_assertions.expect_instance(instance_id)
        api_assertions.expect_edge(
            source_id=api_id,
            target_id=capability_id,
            relationship_name="api_capabilities",
        )
        api_assertions.expect_edge(
            source_id=capability_id,
            target_id=endpoint_id,
            relationship_name="api_capability_endpoints",
        )
        api_assertions.expect_edge(
            source_id=endpoint_id,
            target_id=request_config_id,
            relationship_name="request_config",
        )
        api_assertions.expect_primitive(
            instance_id=api_id,
            field_name="name",
            expected="openai-api",
        )
        api_assertions.expect_primitive(
            instance_id=capability_id,
            field_name="name",
            expected="door",
        )
        api_assertions.expect_primitive(
            instance_id=endpoint_id,
            field_name="name",
            expected="open",
        )
        assert api_assertions.primitive(
            instance_id=request_config_id,
            field_name="api_capability_endpoint_id",
        ) in {endpoint_id, str(endpoint_id)}
        assert api_assertions.primitive(
            instance_id=request_config_id,
            field_name="class_config_id",
        ) in {class_config_id, str(class_config_id)}


@pytest.mark.asyncio
async def test_api_view_projection_chain_commits_full_traversal(
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
        state_model = _select_runtime_inline_request_class_config(runtime_index)
        state_model_id = state_model.id
        assert state_model_id is not None
        assert state_model.class_fqn is not None
        api_projection_hash = find_meta_graph_projection_hash_by_name(
            index=runtime_index, projection_name="Api"
        )
        _ocgi, api_opgi = resolve_meta_graph_ocgi_opgi(
            index=runtime_index,
            projection_hash=api_projection_hash,
        )
        assert api_opgi is not None
        api_observable = next(
            observable
            for observable in api_opgi.object_projection_graph_observables
            if observable.observable_key == "api"
        )
        branch_id = uuid4()
        api_id = stable_api_id(name="openai-api")
        capability_id = stable_api_capability_id(
            api_id=api_id,
            name="view_action",
        )
        endpoint_id = stable_api_capability_endpoint_id(
            api_capability_id=capability_id,
            name="select_api_home",
        )
        api_view_id = stable_api_view_id(
            api_id=api_id,
            object_projection_graph_observable_id=api_observable.id,
            name="api_home",
        )
        api_view_capability_endpoint_id = stable_api_view_capability_endpoint_id(
            api_view_id=api_view_id,
            api_capability_endpoint_id=endpoint_id,
        )
        stream_policy_id = stable_api_view_stream_policy_id(
            api_view_id=api_view_id,
            stream_mode="snapshot",
        )
        api_ontology_plans = build_api_ontology_plans(
            api_ownership=(
                APIOwnership(
                    name="openai-api",
                    source_path="runtime-api-view-proof",
                    capabilities=(
                        APICapabilityOwnership(
                            name="view_action",
                            source_path="runtime-api-view-proof",
                            endpoints=(
                                APICapabilityEndpointOwnership(
                                    name="select_api_home",
                                    source_path="runtime-api-view-proof",
                                    request_config=APICapabilityEndpointRequestConfigOwnership(
                                        class_ref=state_model.class_fqn,
                                        source_path="runtime-api-view-proof",
                                        class_config_id=state_model_id,
                                    ),
                                ),
                            ),
                        ),
                    ),
                    graphs=(),
                    views=(
                        APIViewOwnership(
                            name="api_home",
                            observable_ref="Api.api",
                            state_model_ref=state_model.class_fqn,
                            state_model_id=state_model_id,
                            view_ref="openai-api.api-home",
                            view_key="api_home",
                            stream_policy=APIViewStreamPolicyOwnership(
                                stream_mode="snapshot",
                                source_path="runtime-api-view-proof",
                            ),
                            capability_endpoints=(
                                APIViewCapabilityEndpointOwnership(
                                    action_key="select_api_home",
                                    endpoint_ref="openai-api.view_action.select_api_home",
                                    source_path="runtime-api-view-proof",
                                ),
                            ),
                            source_path="runtime-api-view-proof",
                        ),
                    ),
                ),
            )
        )

        receipt = await materialize_api_graph_ontology(
            index=runtime_index,
            actor_id=None,
            lane=MaterializationLaneContext(
                branch_id=branch_id,
                projection_hash=api_projection_hash,
            ),
            compile_plan_payloads=[
                {
                    "api_ontology": encode_api_ontology_plan_payload(
                        plans=api_ontology_plans
                    )
                }
            ],
        )
        assert receipt is not None
        assert receipt.status == "succeeded"
        assert len(receipt.steps) == 1
        step = receipt.steps[0]
        assert step.status == "succeeded"
        assert step.commit_id is not None
        assert step.head_commit_id is not None
        assert step.details["api_name"] == "openai-api"
        assert step.details["view_count"] == 1
        assert step.details["view_stream_policy_count"] == 1
        assert step.details["view_capability_endpoint_count"] == 1

        api_assertions = await _assertions_for_committed_head(
            runtime_index=runtime_index,
            branch_id=branch_id,
            projection_hash=api_projection_hash,
        )
        api_assertions.expect_root(api_id)
        for instance_id in (
            api_id,
            capability_id,
            endpoint_id,
            api_view_id,
            api_view_capability_endpoint_id,
            stream_policy_id,
        ):
            api_assertions.expect_instance(instance_id)
        api_assertions.expect_edge(
            source_id=api_id,
            target_id=capability_id,
            relationship_name="api_capabilities",
        )
        api_assertions.expect_edge(
            source_id=capability_id,
            target_id=endpoint_id,
            relationship_name="api_capability_endpoints",
        )
        api_assertions.expect_edge(
            source_id=api_id,
            target_id=api_view_id,
            relationship_name="api_views",
        )
        api_assertions.expect_edge(
            source_id=api_view_id,
            target_id=api_view_capability_endpoint_id,
            relationship_name="capability_endpoints",
        )
        api_assertions.expect_edge(
            source_id=api_view_capability_endpoint_id,
            target_id=endpoint_id,
            relationship_name="api_capability_endpoint",
        )
        api_assertions.expect_edge(
            source_id=api_view_id,
            target_id=stream_policy_id,
            relationship_name="stream_policy",
        )
        api_assertions.expect_primitive(
            instance_id=api_view_id,
            field_name="name",
            expected="api_home",
        )
        api_assertions.expect_primitive(
            instance_id=api_view_id,
            field_name="view_ref",
            expected="openai-api.api-home",
        )
        api_assertions.expect_primitive(
            instance_id=api_view_id,
            field_name="view_key",
            expected="api_home",
        )
        assert api_assertions.primitive(
            instance_id=api_view_id,
            field_name="object_projection_graph_observable_id",
        ) in {api_observable.id, str(api_observable.id)}
        assert api_assertions.primitive(
            instance_id=api_view_id,
            field_name="state_model_id",
        ) in {state_model_id, str(state_model_id)}
        api_assertions.expect_primitive(
            instance_id=api_view_capability_endpoint_id,
            field_name="action_key",
            expected="select_api_home",
        )
        api_assertions.expect_primitive(
            instance_id=api_view_capability_endpoint_id,
            field_name="endpoint_ref",
            expected="openai-api.view_action.select_api_home",
        )
        assert api_assertions.primitive(
            instance_id=api_view_capability_endpoint_id,
            field_name="api_capability_endpoint_id",
        ) in {endpoint_id, str(endpoint_id)}
        assert api_assertions.primitive(
            instance_id=stream_policy_id,
            field_name="stream_mode",
        ) in {"snapshot", "ApiViewStreamMode.snapshot"}
