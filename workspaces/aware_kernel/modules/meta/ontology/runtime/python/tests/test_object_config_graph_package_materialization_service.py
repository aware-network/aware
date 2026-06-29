from __future__ import annotations

import asyncio
from collections.abc import Mapping
import json
from pathlib import Path
import shutil
import threading
from types import SimpleNamespace
from typing import Any, TypeVar
from uuid import UUID, uuid4

import pytest

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_history_ontology.change.change_enums import ChangeType
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.graph.config.runtime_derivation.schemas import (
    RuntimeObjectConfigGraphDerivationRequest,
)
from aware_meta.graph.config.runtime_derivation.service import (
    RuntimeObjectConfigGraphDerivationService,
)
from aware_meta.graph.config.namespace.membership import (
    build_namespace_membership_payload_from_ocg_identity,
)
import aware_meta.materialization.workspace_provider as meta_workspace_provider
from aware_meta.graph.projection.stable_ids import stable_object_projection_graph_id
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_delta import (
    ObjectConfigGraphNodeDelta,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)
from aware_meta_ontology.graph.projection.object_projection_graph_binding import (
    ObjectProjectionGraphBinding,
)
from aware_meta_ontology.graph.projection.object_projection_graph_declaration import (
    ObjectProjectionGraphDeclaration,
)
from aware_meta.handlers._generated import meta_handlers
import aware_meta.materialization.service as materialization_service
from aware_meta.runtime import build_meta_graph_runtime_for_aware_package_manifests
from aware_meta.runtime.author import META_SYSTEM_ACTOR_ID
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.graph_runtime import MetaGraphRuntime
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_orm.models.orm_model import ORMModel
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
)
from _meta_runtime_test_paths import (
    META_FIXTURES_ROOT,
    META_PACKAGE_MANIFEST_PATHS,
    REPO_ROOT,
)

_EMPTY_OCG_HASH = "d6d404d213cd5f73e1e07789b159799aec7fd27be6c67247316c83cbd1d922d9"
_FUNCTION_CALL_CLASS_CONFIG_ID = UUID("f297283c-4508-5803-b9e7-7a85da7189f8")
_TRoot = TypeVar("_TRoot", bound=ORMModel)


def _meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    assert repo_root == REPO_ROOT
    return META_PACKAGE_MANIFEST_PATHS


def _build_meta_runtime(*, repo_root: Path, aware_root: Path) -> MetaGraphRuntime:
    repo_root = Path(repo_root)
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(meta_handlers,),
        bootstrap_modules=(meta_handlers,),
    )
    assert runtime.context is not None
    return runtime


def _meta_runtime_index(runtime: MetaGraphRuntime) -> MetaGraphRuntimeIndex:
    context = runtime.context
    assert context is not None
    return context.index


def _build_aware_code(tmp_path: Path, name: str, content: str) -> Any:
    code_path = tmp_path / name
    code_path.write_text(content, encoding="utf-8")
    return build_code_from_file(
        sections_index=CodeSectionBuilderIndex(),
        file_path=str(code_path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _namespace_and_domains(
    *,
    fqn_prefix: str,
    namespace: str,
    code_id: UUID,
) -> tuple[dict[UUID, NamespacePath], list[object]]:
    return (
        {code_id: NamespacePath(package=fqn_prefix, namespace=namespace)},
        [],
    )


def _source_code_package_config_id(
    *,
    surface: str,
) -> UUID:
    return materialization_service.stable_code_package_config_id(
        config_key=materialization_service.code_package_source_config_key(
            manifest_kind="aware_toml",
            surface=surface,
        )
    )


def test_meta_package_leaf_materialization_does_not_import_runtime_harness() -> None:
    source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/materialization/service.py"
    ).read_text(encoding="utf-8")

    assert "aware_runtime" not in source
    assert "RuntimeHarness" not in source
    assert "bind_runtime_lane" not in source
    assert "AwareRuntimeIndex" not in source


def test_meta_package_leaf_materialization_uses_meta_owned_source_helpers() -> None:
    source = Path(
        "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/materialization/service.py"
    ).read_text(encoding="utf-8")
    import_prelude = source.split("_AWARE_SOURCE_EXTENSION", maxsplit=1)[0]

    assert "aware_structure" not in import_prelude
    assert "_load_meta_code_package_source_helpers" in source
    assert "aware_meta.materialization.code_package_sources" in source


def test_semantic_lane_root_domain_commit_id_prefers_committed_head() -> None:
    detached_plan_commit_id = uuid4()
    head_commit_id = uuid4()
    summary = materialization_service._SemanticLaneCommitSummary(  # noqa: SLF001
        commit_id=detached_plan_commit_id,
        head_commit_id=head_commit_id,
        strategy="seed",
        fallback_reset=False,
        phase_timings_s={},
    )

    assert (
        materialization_service._semantic_lane_root_domain_commit_id(
            summary
        )  # noqa: SLF001
        == head_commit_id
    )


def test_semantic_lane_root_domain_commit_id_falls_back_to_plan_commit() -> None:
    commit_id = uuid4()
    summary = materialization_service._SemanticLaneCommitSummary(  # noqa: SLF001
        commit_id=commit_id,
        head_commit_id=None,
        strategy="seed",
        fallback_reset=False,
        phase_timings_s={},
    )

    assert (
        materialization_service._semantic_lane_root_domain_commit_id(
            summary
        )  # noqa: SLF001
        == commit_id
    )


@pytest.mark.asyncio
async def test_leaf_package_subphase_progress_records_success_and_failure() -> None:
    events: list[dict[str, object]] = []

    async def progress_callback(payload: Mapping[str, object]) -> None:
        events.append(dict(payload))

    success_timings: dict[str, float] = {}
    async with materialization_service._record_leaf_package_subphase(  # noqa: SLF001
        success_timings,
        "build_object_config_graph_from_code",
        progress_callback,
        detail_payload={"package_name": "demo-ontology"},
    ):
        pass

    assert [event["status"] for event in events[:2]] == ["running", "succeeded"]
    assert events[0]["phase_name"] == "meta.leaf_package.subphase"
    success_detail = events[1]["detail_payload"]
    assert isinstance(success_detail, Mapping)
    assert success_detail["subphase_name"] == "build_object_config_graph_from_code"
    assert success_detail["package_name"] == "demo-ontology"
    assert events[1]["duration_s"] >= 0.0
    assert success_timings["build_object_config_graph_from_code"] >= 0.0

    failure_timings: dict[str, float] = {}
    with pytest.raises(ValueError, match="bad leaf phase"):
        async with (
            materialization_service._record_leaf_package_subphase(  # noqa: SLF001
                failure_timings,
                "commit_object_config_graph_to_semantic_lane",
                progress_callback,
            )
        ):
            raise ValueError("bad leaf phase")

    failed_event = events[-1]
    failed_detail = failed_event["detail_payload"]
    assert failed_event["status"] == "failed"
    assert failed_event["error"] == "bad leaf phase"
    assert isinstance(failed_detail, Mapping)
    assert (
        failed_detail["subphase_name"] == "commit_object_config_graph_to_semantic_lane"
    )
    assert failed_detail["error_type"] == "ValueError"
    assert failure_timings["commit_object_config_graph_to_semantic_lane"] >= 0.0


@pytest.mark.asyncio
async def test_language_target_subphase_progress_does_not_block_worker_thread() -> None:
    events: list[dict[str, object]] = []
    progress_started = asyncio.Event()
    release_progress = asyncio.Event()

    async def progress_callback(payload: Mapping[str, object]) -> None:
        events.append(dict(payload))
        progress_started.set()
        await release_progress.wait()

    request = SimpleNamespace(progress_callback=progress_callback)
    futures: list[Any] = []
    loop = asyncio.get_running_loop()

    await asyncio.to_thread(
        meta_workspace_provider._schedule_language_target_subphase_progress,  # noqa: SLF001
        request=request,
        target_payload={
            "target_index": 0,
            "target_count": 1,
            "target_language_plugin_id": "python",
            "output_root": "modules/network/runtime/aware_network",
            "import_root": "aware_network",
            "package_name": "aware_network",
            "materialization_source": "runtime_handlers",
            "renderer_profile": None,
            "renderer_kind": "runtime_handlers_impl",
            "source_is_runtime": True,
        },
        loop=loop,
        futures=futures,
        payload={
            "phase_name": "meta.language_target.subphase",
            "status": "running",
            "detail_payload": {
                "subphase_name": "derive_runtime_graph.cache_lookup",
            },
        },
    )

    assert len(futures) == 1
    pending_future = futures[0]
    await asyncio.wait_for(progress_started.wait(), timeout=1.0)
    assert len(events) == 1
    event = events[0]
    assert event["phase_name"] == "meta.language_target.subphase"
    assert event["status"] == "running"
    detail = event["detail_payload"]
    assert isinstance(detail, Mapping)
    assert detail["subphase_name"] == "derive_runtime_graph.cache_lookup"
    assert detail["renderer_kind"] == "runtime_handlers_impl"
    await asyncio.wait_for(
        meta_workspace_provider._drain_language_target_subphase_progress(  # noqa: SLF001
            futures
        ),
        timeout=1.0,
    )
    assert futures == []
    assert not pending_future.done()
    release_progress.set()
    await asyncio.wait_for(asyncio.wrap_future(pending_future), timeout=1.0)


@pytest.mark.asyncio
async def test_language_target_worker_wait_polls_until_thread_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release_worker = threading.Event()
    wait_timeouts: list[float | None] = []
    original_wait = asyncio.wait

    async def recording_wait(
        aws: Any,
        *,
        timeout: float | None = None,
        return_when: object = asyncio.ALL_COMPLETED,
    ) -> Any:
        wait_timeouts.append(timeout)
        return await original_wait(aws, timeout=timeout, return_when=return_when)

    def worker() -> str:
        assert release_worker.wait(timeout=1.0)
        return "ready"

    monkeypatch.setattr(
        meta_workspace_provider,
        "_LANGUAGE_TARGET_WORKER_POLL_INTERVAL_S",
        0.001,
    )
    monkeypatch.setattr(meta_workspace_provider.asyncio, "wait", recording_wait)

    async def release_later() -> None:
        await asyncio.sleep(0.01)
        release_worker.set()

    release_task = asyncio.create_task(release_later())
    result = await asyncio.wait_for(
        meta_workspace_provider._await_language_target_worker(worker),  # noqa: SLF001
        timeout=1.0,
    )
    await release_task

    assert result == "ready"
    assert wait_timeouts
    assert all(timeout == 0.001 for timeout in wait_timeouts if timeout is not None)


@pytest.mark.asyncio
async def test_semantic_lane_commit_uses_source_ocg_delta(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test:ocg"
    head_commit_id = uuid4()
    previous_graph = ObjectConfigGraph(
        id=graph_id,
        name="demo",
        hash="sha256:pre",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
    )
    current_graph = previous_graph.model_copy(update={"hash": "sha256:post"})
    node_delta = ObjectConfigGraphNodeDelta(
        change_type=ChangeType.update,
        node_type=ObjectConfigGraphNodeType.class_,
        node_id=uuid4(),
        entity_id=uuid4(),
    )
    commit_calls: list[dict[str, Any]] = []
    progress_events: list[dict[str, object]] = []

    async def fake_commit_ocg_delta_to_lane(**kwargs: Any) -> object:
        commit_calls.append(kwargs)
        return SimpleNamespace(commit_id=None)

    def fake_diff_object_config_graph_nodes(
        **_: Any,
    ) -> list[ObjectConfigGraphNodeDelta]:
        return [node_delta]

    def fake_collect_lane_instance_models(**_: Any) -> dict[UUID, object]:
        return {uuid4(): object()}

    def fake_prepare_ocg_seed_projection(**_: Any) -> object:
        return SimpleNamespace(schema_graph_id=uuid4())

    async def fake_validate_projection_lane_head(**_: Any) -> None:
        return None

    class FakeStore:
        aware_root = tmp_path

        async def head(self, **_: Any) -> dict[str, str]:
            return {"commit_id": str(head_commit_id)}

    def progress_callback(payload: Mapping[str, object]) -> None:
        progress_events.append(dict(payload))

    monkeypatch.setattr(
        materialization_service,
        "commit_ocg_delta_to_lane",
        fake_commit_ocg_delta_to_lane,
    )
    monkeypatch.setattr(
        materialization_service,
        "diff_object_config_graph_nodes",
        fake_diff_object_config_graph_nodes,
    )
    monkeypatch.setattr(
        materialization_service,
        "collect_lane_instance_models",
        fake_collect_lane_instance_models,
    )
    monkeypatch.setattr(
        materialization_service,
        "prepare_ocg_seed_projection",
        fake_prepare_ocg_seed_projection,
    )
    monkeypatch.setattr(
        materialization_service,
        "_validate_projection_lane_head",
        fake_validate_projection_lane_head,
    )
    monkeypatch.setattr(materialization_service, "FSCommitStore", FakeStore)

    summary = await materialization_service._commit_object_config_graph_to_semantic_lane(  # noqa: SLF001
        built_object_config_graph=current_graph,
        existing_object_config_graph=previous_graph,
        branch_id=branch_id,
        projection_hash=projection_hash,
        index=SimpleNamespace(
            ocg=ObjectConfigGraph(
                name="meta",
                hash="sha256:meta",
                fqn_prefix="aware_meta",
                language=CodeLanguage.aware,
            )
        ),
        aware_toml_path=Path("modules/demo/structure/ontology/aware.toml"),
        external_graphs=(),
        actor_id=None,
        progress_callback=progress_callback,
        detail_payload={"package_name": "demo-ontology"},
    )

    assert summary.strategy == "delta"
    assert summary.head_commit_id == head_commit_id
    assert len(commit_calls) == 1
    delta = commit_calls[0]["delta"]
    assert delta.object_config_graph_id == graph_id
    assert delta.graph_hash_pre == "sha256:pre"
    assert delta.graph_hash_post == "sha256:post"
    assert delta.node_deltas == [node_delta]
    assert commit_calls[0]["prepared_projection"] is not None
    assert (
        summary.phase_timings_s[
            "derive_object_config_graph_semantic_delta.metric.node_delta_count"
        ]
        == 1.0
    )
    assert (
        summary.phase_timings_s[
            "semantic_delta_commit_preflight.metric.instance_models_pre"
        ]
        == 1.0
    )
    emitted_subphases = {
        event["detail_payload"]["subphase_name"]
        for event in progress_events
        if isinstance(event.get("detail_payload"), Mapping)
    }
    assert "derive_object_config_graph_semantic_delta" in emitted_subphases
    assert "semantic_delta_commit_preflight" in emitted_subphases
    assert "commit_ocg_delta_to_lane.prepare_projection" in emitted_subphases
    assert "commit_ocg_delta_to_lane" in emitted_subphases


@pytest.mark.asyncio
async def test_semantic_lane_commit_preflight_guard_reseeds_broad_lane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph_id = uuid4()
    branch_id = uuid4()
    projection_hash = "sha256:test:ocg"
    head_commit_id = uuid4()
    previous_graph = ObjectConfigGraph(
        id=graph_id,
        name="demo",
        hash="sha256:pre",
        fqn_prefix="aware_demo",
        language=CodeLanguage.aware,
    )
    current_graph = previous_graph.model_copy(update={"hash": "sha256:post"})
    node_delta = ObjectConfigGraphNodeDelta(
        change_type=ChangeType.update,
        node_type=ObjectConfigGraphNodeType.class_,
        node_id=uuid4(),
        entity_id=uuid4(),
    )
    reset_calls: list[dict[str, Any]] = []
    seed_calls: list[dict[str, Any]] = []
    progress_events: list[dict[str, object]] = []

    async def fake_commit_ocg_delta_to_lane(**_: Any) -> object:
        raise AssertionError("broad semantic lane should reset before delta commit")

    def fake_diff_object_config_graph_nodes(
        **_: Any,
    ) -> list[ObjectConfigGraphNodeDelta]:
        return [node_delta]

    def fake_collect_lane_instance_models(**_: Any) -> dict[UUID, object]:
        return {uuid4(): object(), uuid4(): object()}

    def fake_reset_generated_projection_lanes(**kwargs: Any) -> None:
        reset_calls.append(kwargs)

    async def fake_ensure_ocg_seeded_lane(**kwargs: Any) -> object:
        seed_calls.append(kwargs)
        return SimpleNamespace(commit_id=None, seeded=False)

    async def fake_validate_projection_lane_head(**_: Any) -> None:
        return None

    def progress_callback(payload: Mapping[str, object]) -> None:
        progress_events.append(dict(payload))

    class FakeStore:
        aware_root = tmp_path

        async def head(self, **_: Any) -> dict[str, str]:
            return {"commit_id": str(head_commit_id)}

    monkeypatch.setenv(
        "AWARE_META_SEMANTIC_DELTA_COMMIT_MAX_INSTANCE_MODELS",
        "1",
    )
    monkeypatch.setattr(
        materialization_service,
        "commit_ocg_delta_to_lane",
        fake_commit_ocg_delta_to_lane,
    )
    monkeypatch.setattr(
        materialization_service,
        "diff_object_config_graph_nodes",
        fake_diff_object_config_graph_nodes,
    )
    monkeypatch.setattr(
        materialization_service,
        "collect_lane_instance_models",
        fake_collect_lane_instance_models,
    )
    monkeypatch.setattr(
        materialization_service,
        "_reset_generated_projection_lanes",
        fake_reset_generated_projection_lanes,
    )
    monkeypatch.setattr(
        materialization_service,
        "ensure_ocg_seeded_lane",
        fake_ensure_ocg_seeded_lane,
    )
    monkeypatch.setattr(
        materialization_service,
        "_validate_projection_lane_head",
        fake_validate_projection_lane_head,
    )
    monkeypatch.setattr(materialization_service, "FSCommitStore", FakeStore)

    summary = await materialization_service._commit_object_config_graph_to_semantic_lane(  # noqa: SLF001
        built_object_config_graph=current_graph,
        existing_object_config_graph=previous_graph,
        branch_id=branch_id,
        projection_hash=projection_hash,
        index=SimpleNamespace(
            ocg=ObjectConfigGraph(
                name="meta",
                hash="sha256:meta",
                fqn_prefix="aware_meta",
                language=CodeLanguage.aware,
            )
        ),
        aware_toml_path=Path("modules/demo/structure/ontology/aware.toml"),
        external_graphs=(),
        actor_id=None,
        progress_callback=progress_callback,
        detail_payload={"package_name": "demo-ontology"},
    )

    assert summary.strategy == "seed_after_reset"
    assert summary.fallback_reset is True
    assert summary.head_commit_id == head_commit_id
    assert len(reset_calls) == 1
    assert reset_calls[0]["projection_hashes"] == (projection_hash,)
    assert len(seed_calls) == 1
    assert (
        summary.phase_timings_s[
            "semantic_delta_commit_preflight.metric.instance_models_pre"
        ]
        == 2.0
    )
    assert "commit_ocg_delta_to_lane" not in summary.phase_timings_s
    assert summary.phase_timings_s["reset_generated_projection_lane"] >= 0.0
    assert summary.phase_timings_s["ensure_ocg_seeded_lane_after_reset"] >= 0.0
    emitted_subphases = {
        event["detail_payload"]["subphase_name"]
        for event in progress_events
        if isinstance(event.get("detail_payload"), Mapping)
    }
    assert "reset_generated_projection_lane" in emitted_subphases
    assert "ensure_ocg_seeded_lane_after_reset" in emitted_subphases


def test_index_receipt_projection_hash_derivation_prepares_external_opgs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    reactivity_code = _build_aware_code(
        tmp_path,
        "reactivity.aware",
        """
class ActionConfig {}

projection ActionConfig {
    root action.ActionConfig
}
""".strip(),
    )
    reactivity_ns, reactivity_domains = _namespace_and_domains(
        fqn_prefix="aware_reactivity",
        namespace="action",
        code_id=reactivity_code.id,
    )
    reactivity_graph = build_object_config_graph_from_code(
        name="reactivity",
        description="reactivity",
        fqn_prefix="aware_reactivity",
        file_codes=[("reactivity.aware", reactivity_code)],
        namespace_by_code_id=reactivity_ns,
    ).graph
    assert reactivity_graph.object_projection_graph_declarations
    assert not reactivity_graph.object_projection_graphs

    experience_code = _build_aware_code(
        tmp_path,
        "experience.aware",
        """
class ActionExperience {
    action_config aware_reactivity.action.ActionConfig unique
}

projection ActionExperience {
    root action.ActionExperience
    action.ActionExperience::action_config aware_reactivity.ActionConfig
}
""".strip(),
    )
    experience_ns, experience_domains = _namespace_and_domains(
        fqn_prefix="aware_experience",
        namespace="action",
        code_id=experience_code.id,
    )
    experience_build = build_object_config_graph_from_code(
        name="experience",
        description="experience",
        fqn_prefix="aware_experience",
        file_codes=[("experience.aware", experience_code)],
        namespace_by_code_id=experience_ns,
        external_graphs=[reactivity_graph],
    )

    recorded_fqn_prefixes: list[str] = []
    original_build_object_projection_graphs = (
        materialization_service.build_object_projection_graphs
    )

    def recording_build_object_projection_graphs(
        ocg: ObjectConfigGraph,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        recorded_fqn_prefixes.append(ocg.fqn_prefix)
        return original_build_object_projection_graphs(ocg, *args, **kwargs)

    monkeypatch.setattr(
        materialization_service,
        "build_object_projection_graphs",
        recording_build_object_projection_graphs,
    )

    projection_hashes = materialization_service._derived_projection_hashes_by_id_for_index_receipt(  # noqa: SLF001
        graph=experience_build.graph,
        external_graphs=(reactivity_graph,),
        cross_relationships_by_target_ocg=(
            experience_build.cross_relationships_by_target_ocg
        ),
    )

    assert projection_hashes
    assert "aware_reactivity" in recorded_fqn_prefixes


def test_index_receipt_projection_hash_derivation_skips_external_opg_prefill_without_portals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    reactivity_code = _build_aware_code(
        tmp_path,
        "reactivity.aware",
        """
class ActionConfig {}

projection ActionConfig {
    root action.ActionConfig
}
""".strip(),
    )
    reactivity_ns, reactivity_domains = _namespace_and_domains(
        fqn_prefix="aware_reactivity",
        namespace="action",
        code_id=reactivity_code.id,
    )
    reactivity_graph = build_object_config_graph_from_code(
        name="reactivity",
        description="reactivity",
        fqn_prefix="aware_reactivity",
        file_codes=[("reactivity.aware", reactivity_code)],
        namespace_by_code_id=reactivity_ns,
    ).graph
    assert reactivity_graph.object_projection_graph_declarations
    assert not reactivity_graph.object_projection_graphs

    experience_code = _build_aware_code(
        tmp_path,
        "experience.aware",
        """
class ActionExperience {
    action_config aware_reactivity.action.ActionConfig unique
}

projection ActionExperience {
    root action.ActionExperience
    action.ActionExperience::action_config
}
""".strip(),
    )
    experience_ns, experience_domains = _namespace_and_domains(
        fqn_prefix="aware_experience",
        namespace="action",
        code_id=experience_code.id,
    )
    experience_build = build_object_config_graph_from_code(
        name="experience",
        description="experience",
        fqn_prefix="aware_experience",
        file_codes=[("experience.aware", experience_code)],
        namespace_by_code_id=experience_ns,
        external_graphs=[reactivity_graph],
    )

    recorded_fqn_prefixes: list[str] = []
    original_build_object_projection_graphs = (
        materialization_service.build_object_projection_graphs
    )

    def recording_build_object_projection_graphs(
        ocg: ObjectConfigGraph,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        recorded_fqn_prefixes.append(ocg.fqn_prefix)
        return original_build_object_projection_graphs(ocg, *args, **kwargs)

    monkeypatch.setattr(
        materialization_service,
        "build_object_projection_graphs",
        recording_build_object_projection_graphs,
    )

    projection_hashes = materialization_service._derived_projection_hashes_by_id_for_index_receipt(  # noqa: SLF001
        graph=experience_build.graph,
        external_graphs=(reactivity_graph,),
        cross_relationships_by_target_ocg=(
            experience_build.cross_relationships_by_target_ocg
        ),
    )

    assert projection_hashes
    assert recorded_fqn_prefixes == ["aware_experience"]


def test_provider_dependency_graph_resolution_loads_missing_manifest_closure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_graph = ObjectConfigGraph(
        id=uuid4(),
        name="experience",
        description="experience",
        hash="sha256:test:experience",
        fqn_prefix="aware_experience",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
        object_projection_graphs=[],
        object_config_graph_overlays=[],
        object_config_graph_annotations=[],
        object_config_graph_relationships=[],
    )
    dependency_graph = ObjectConfigGraph(
        id=uuid4(),
        name="reactivity",
        description="reactivity",
        hash="sha256:test:reactivity",
        fqn_prefix="aware_reactivity",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
        object_projection_graphs=[],
        object_config_graph_overlays=[],
        object_config_graph_annotations=[],
        object_config_graph_relationships=[],
    )
    monkeypatch.setattr(
        meta_workspace_provider,
        "_dependency_fqn_prefixes_for_manifest",
        lambda **_: ("aware_reactivity",),
    )
    monkeypatch.setattr(
        meta_workspace_provider,
        "_external_runtime_object_config_graphs_from_context",
        lambda **_: (),
    )
    monkeypatch.setattr(
        meta_workspace_provider,
        "_package_dependency_runtime_object_config_graphs_from_manifest",
        lambda **_: (dependency_graph,),
    )

    assert meta_workspace_provider._package_dependency_runtime_object_config_graphs_from_context(  # noqa: SLF001
        context={},
        source_graph=source_graph,
        aware_toml_path=tmp_path / "aware.toml",
        workspace_root=tmp_path,
    ) == (
        dependency_graph,
    )


def test_provider_language_dependency_graphs_use_direct_manifest_dependencies(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    manifest_path = workspace_root / "modules" / "sdk" / "structure" / "aware.toml"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        """
aware = 1

[package]
package_name = "sdk-ontology"
fqn_prefix = "aware_sdk"
kind = "ontology"
version_number = 1
title = "SDK"
description = "SDK"

[build]
environment_slug = "aware_sdk"

[[dependencies]]
package_name = "api-ontology"

[[dependencies]]
package_name = "code-ontology"
""".strip(),
        encoding="utf-8",
    )
    source_graph = ObjectConfigGraph(
        id=uuid4(),
        name="sdk",
        description="sdk",
        hash="sha256:test:sdk",
        fqn_prefix="aware_sdk",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
        object_projection_graphs=[],
        object_config_graph_overlays=[],
        object_config_graph_annotations=[],
        object_config_graph_relationships=[],
    )
    projection_declaration = ObjectProjectionGraphDeclaration(
        object_config_graph_id=source_graph.id,
        key="aware_sdk:ProgramConfig",
        projection_name="ProgramConfig",
    )
    projection_declaration.object_projection_graph_bindings = [
        ObjectProjectionGraphBinding(
            object_projection_graph_declaration_id=projection_declaration.id,
            fqn_prefix="aware_meta",
            namespace="meta.attribute",
            class_name="AttributeConfig",
            attribute_name=None,
            target_projection_name=None,
        )
    ]
    source_graph.object_projection_graph_declarations = [projection_declaration]

    def _graph(fqn_prefix: str) -> ObjectConfigGraph:
        return ObjectConfigGraph(
            id=uuid4(),
            name=fqn_prefix,
            description=fqn_prefix,
            hash=f"sha256:test:{fqn_prefix}",
            fqn_prefix=fqn_prefix,
            language=CodeLanguage.aware,
            object_config_graph_nodes=[],
            object_projection_graphs=[],
            object_config_graph_overlays=[],
            object_config_graph_annotations=[],
            object_config_graph_relationships=[],
        )

    graphs = meta_workspace_provider._package_dependency_runtime_object_config_graphs_from_context(  # noqa: SLF001
        context={
            "runtime_object_config_graphs": (
                source_graph,
                _graph("aware_api"),
                _graph("aware_code"),
                _graph("aware_meta"),
                _graph("aware_storage"),
            ),
            "semantic_object_config_graphs": (source_graph,),
            "semantic_ontology_package_catalog": {
                "schema": "aware.semantic_ontology_package_catalog.v1",
                "entries": (
                    {
                        "package_name": "sdk-ontology",
                        "fqn_prefix": "aware_sdk",
                        "manifest_path": manifest_path.as_posix(),
                        "dependency_package_names": (
                            "api-ontology",
                            "code-ontology",
                        ),
                    },
                    {
                        "package_name": "api-ontology",
                        "fqn_prefix": "aware_api",
                        "dependency_package_names": ("meta-ontology",),
                    },
                    {
                        "package_name": "code-ontology",
                        "fqn_prefix": "aware_code",
                        "dependency_package_names": ("storage-ontology",),
                    },
                    {
                        "package_name": "meta-ontology",
                        "fqn_prefix": "aware_meta",
                        "dependency_package_names": (),
                    },
                    {
                        "package_name": "storage-ontology",
                        "fqn_prefix": "aware_storage",
                        "dependency_package_names": (),
                    },
                ),
            },
        },
        source_graph=source_graph,
        aware_toml_path=manifest_path,
        workspace_root=workspace_root,
        include_transitive_dependencies=False,
    )

    assert tuple(graph.fqn_prefix for graph in graphs) == (
        "aware_api",
        "aware_code",
        "aware_meta",
    )


def test_provider_language_dependency_graphs_include_dependency_projection_owners(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    manifest_path = workspace_root / "modules" / "node" / "aware.ontology.toml"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        """
    aware = 1

    [package]
    package_name = "node-ontology"
    fqn_prefix = "aware_node"
    kind = "ontology"
    version_number = 1
    title = "Node"
    description = "Node"

    [build]
    environment_slug = "aware_node"

[[dependencies]]
package_name = "experience-ontology"
""".strip(),
        encoding="utf-8",
    )

    def _graph(fqn_prefix: str) -> ObjectConfigGraph:
        return ObjectConfigGraph(
            id=uuid4(),
            name=fqn_prefix,
            description=fqn_prefix,
            hash=f"sha256:test:{fqn_prefix}",
            fqn_prefix=fqn_prefix,
            language=CodeLanguage.aware,
            object_config_graph_nodes=[],
            object_projection_graphs=[],
            object_config_graph_overlays=[],
            object_config_graph_annotations=[],
            object_config_graph_relationships=[],
        )

    source_graph = _graph("aware_node")
    experience_graph = _graph("aware_experience")
    projection_declaration = ObjectProjectionGraphDeclaration(
        object_config_graph_id=experience_graph.id,
        key="aware_experience:ProgramConfig",
        projection_name="ProgramConfig",
    )
    projection_declaration.object_projection_graph_bindings = [
        ObjectProjectionGraphBinding(
            object_projection_graph_declaration_id=projection_declaration.id,
            fqn_prefix="aware_meta",
            namespace="attribute",
            class_name="AttributeConfig",
            attribute_name=None,
            target_projection_name=None,
        )
    ]
    experience_graph.object_projection_graph_declarations = [projection_declaration]
    meta_graph = _graph("aware_meta")

    graphs = meta_workspace_provider._package_dependency_runtime_object_config_graphs_from_context(  # noqa: SLF001
        context={
            "runtime_object_config_graphs": (
                source_graph,
                experience_graph,
                meta_graph,
            ),
            "semantic_object_config_graphs": (source_graph,),
            "semantic_ontology_package_catalog": {
                "schema": "aware.semantic_ontology_package_catalog.v1",
                "entries": (
                    {
                        "package_name": "node-ontology",
                        "fqn_prefix": "aware_node",
                        "manifest_path": manifest_path.as_posix(),
                        "dependency_package_names": ("experience-ontology",),
                    },
                    {
                        "package_name": "experience-ontology",
                        "fqn_prefix": "aware_experience",
                        "dependency_package_names": ("meta-ontology",),
                    },
                    {
                        "package_name": "meta-ontology",
                        "fqn_prefix": "aware_meta",
                        "dependency_package_names": (),
                    },
                ),
            },
        },
        source_graph=source_graph,
        aware_toml_path=manifest_path,
        workspace_root=workspace_root,
        include_transitive_dependencies=False,
    )

    assert tuple(graph.fqn_prefix for graph in graphs) == (
        "aware_experience",
        "aware_meta",
    )


def test_provider_language_dependency_graphs_include_portal_target_owners(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    manifest_path = workspace_root / "modules" / "node" / "aware.ontology.toml"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        """
    aware = 1

    [package]
    package_name = "node-ontology"
    fqn_prefix = "aware_node"
    kind = "ontology"
    version_number = 1
    title = "Node"
    description = "Node"

    [build]
    environment_slug = "aware_node"

[[dependencies]]
package_name = "experience-ontology"
""".strip(),
        encoding="utf-8",
    )

    def _graph(fqn_prefix: str) -> ObjectConfigGraph:
        return ObjectConfigGraph(
            id=uuid4(),
            name=fqn_prefix,
            description=fqn_prefix,
            hash=f"sha256:test:{fqn_prefix}",
            fqn_prefix=fqn_prefix,
            language=CodeLanguage.aware,
            object_config_graph_nodes=[],
            object_projection_graphs=[],
            object_config_graph_overlays=[],
            object_config_graph_annotations=[],
            object_config_graph_relationships=[],
        )

    source_graph = _graph("aware_node")
    experience_graph = _graph("aware_experience")
    projection_declaration = ObjectProjectionGraphDeclaration(
        object_config_graph_id=experience_graph.id,
        key="aware_experience:ActionExperience",
        projection_name="ActionExperience",
    )
    projection_declaration.object_projection_graph_bindings = [
        ObjectProjectionGraphBinding(
            object_projection_graph_declaration_id=projection_declaration.id,
            fqn_prefix="aware_experience",
            namespace="action",
            class_name="ActionExperience",
            attribute_name="action_config",
            target_projection_name="aware_reactivity.ActionConfig",
        )
    ]
    experience_graph.object_projection_graph_declarations = [projection_declaration]
    reactivity_graph = _graph("aware_reactivity")

    graphs = meta_workspace_provider._package_dependency_runtime_object_config_graphs_from_context(  # noqa: SLF001
        context={
            "runtime_object_config_graphs": (
                source_graph,
                experience_graph,
                reactivity_graph,
            ),
            "semantic_object_config_graphs": (source_graph,),
            "semantic_ontology_package_catalog": {
                "schema": "aware.semantic_ontology_package_catalog.v1",
                "entries": (
                    {
                        "package_name": "node-ontology",
                        "fqn_prefix": "aware_node",
                        "manifest_path": manifest_path.as_posix(),
                        "dependency_package_names": ("experience-ontology",),
                    },
                    {
                        "package_name": "experience-ontology",
                        "fqn_prefix": "aware_experience",
                        "dependency_package_names": ("reactivity-ontology",),
                    },
                    {
                        "package_name": "reactivity-ontology",
                        "fqn_prefix": "aware_reactivity",
                        "dependency_package_names": (),
                    },
                ),
            },
        },
        source_graph=source_graph,
        aware_toml_path=manifest_path,
        workspace_root=workspace_root,
        include_transitive_dependencies=False,
    )

    assert tuple(graph.fqn_prefix for graph in graphs) == (
        "aware_experience",
        "aware_reactivity",
    )


def test_leaf_external_graphs_include_dependency_ocg_relationship_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _graph(fqn_prefix: str) -> ObjectConfigGraph:
        return ObjectConfigGraph(
            id=uuid4(),
            name=fqn_prefix,
            description=fqn_prefix,
            hash=f"sha256:test:{fqn_prefix}",
            fqn_prefix=fqn_prefix,
            language=CodeLanguage.aware,
            object_config_graph_nodes=[],
            object_projection_graphs=[],
            object_config_graph_overlays=[],
            object_config_graph_annotations=[],
            object_config_graph_relationships=[],
        )

    source_graph = _graph("aware_interface")
    environment_graph = _graph("aware_environment")
    attention_graph = _graph("aware_attention")
    environment_graph.object_config_graph_relationships = [
        ObjectConfigGraphRelationship(
            object_config_graph_id=environment_graph.id,
            target_object_config_graph_id=attention_graph.id,
        )
    ]
    monkeypatch.setattr(
        meta_workspace_provider,
        "_dependency_fqn_prefixes_for_manifest",
        lambda **_: ("aware_environment",),
    )

    graphs = meta_workspace_provider._leaf_external_object_config_graphs_from_context(  # noqa: SLF001
        context={
            "runtime_object_config_graphs": (
                source_graph,
                environment_graph,
                attention_graph,
            ),
            "semantic_object_config_graphs": (source_graph,),
        },
        aware_toml_path=tmp_path / "aware.ontology.toml",
        workspace_root=tmp_path,
    )

    assert tuple(graph.fqn_prefix for graph in graphs) == (
        "aware_environment",
        "aware_attention",
    )


def test_provider_language_dependency_graphs_include_ocg_relationship_targets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _graph(fqn_prefix: str) -> ObjectConfigGraph:
        return ObjectConfigGraph(
            id=uuid4(),
            name=fqn_prefix,
            description=fqn_prefix,
            hash=f"sha256:test:{fqn_prefix}",
            fqn_prefix=fqn_prefix,
            language=CodeLanguage.aware,
            object_config_graph_nodes=[],
            object_projection_graphs=[],
            object_config_graph_overlays=[],
            object_config_graph_annotations=[],
            object_config_graph_relationships=[],
        )

    source_graph = _graph("aware_interface")
    environment_graph = _graph("aware_environment")
    attention_graph = _graph("aware_attention")
    environment_graph.object_config_graph_relationships = [
        ObjectConfigGraphRelationship(
            object_config_graph_id=environment_graph.id,
            target_object_config_graph_id=attention_graph.id,
        )
    ]
    monkeypatch.setattr(
        meta_workspace_provider,
        "_dependency_fqn_prefixes_for_manifest",
        lambda **_: ("aware_environment",),
    )

    graphs = meta_workspace_provider._package_dependency_runtime_object_config_graphs_from_context(  # noqa: SLF001
        context={
            "runtime_object_config_graphs": (
                source_graph,
                environment_graph,
                attention_graph,
            ),
            "semantic_object_config_graphs": (source_graph,),
        },
        source_graph=source_graph,
        aware_toml_path=tmp_path / "aware.ontology.toml",
        workspace_root=tmp_path,
        include_transitive_dependencies=False,
    )

    assert tuple(graph.fqn_prefix for graph in graphs) == (
        "aware_environment",
        "aware_attention",
    )


def test_namespace_membership_uses_node_identity_without_domain_schema_topology() -> (
    None
):
    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="aware_code.default.code.Code",
        name="Code",
    )
    node = ObjectConfigGraphNode(
        id=uuid4(),
        object_config_graph_id=uuid4(),
        type=ObjectConfigGraphNodeType.class_,
        node_key=class_config.class_fqn,
        class_config=class_config,
    )
    graph = ObjectConfigGraph(
        id=uuid4(),
        name="code-ontology",
        hash="sha256:test",
        fqn_prefix="aware_code",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[node],
    )

    assert build_namespace_membership_payload_from_ocg_identity(ocg=graph) == (
        {
            "entity_id": str(class_config.id),
            "entity_kind": "class",
            "fqn": "aware_code.default.code.Code",
            "node_id": str(node.id),
            "package": "aware_code",
            "symbol": "Code",
        },
    )


def test_object_config_graph_package_reuse_cache_requires_fqn_namespace_evidence() -> (
    None
):
    node_id = str(uuid4())
    stale_payload = {
        "name": "code-ontology",
        "hash": "sha256:test",
        "object_config_graph_nodes": [{"id": node_id}],
    }
    fqn_membership_payload = {
        "name": "code-ontology",
        "hash": "sha256:test",
        "object_config_graph_nodes": [{"id": node_id}],
        "namespace_membership": [
            {
                "entity_id": str(uuid4()),
                "entity_kind": "class",
                "fqn": "aware_code.default.code.Code",
                "node_id": node_id,
                "package": "aware_code",
                "symbol": "Code",
            }
        ],
    }

    assert not materialization_service._object_config_graph_payload_has_namespace_evidence(  # noqa: SLF001
        stale_payload
    )
    assert materialization_service._object_config_graph_payload_has_namespace_evidence(  # noqa: SLF001
        fqn_membership_payload
    )


def test_object_config_graph_package_reuse_cache_rejects_stale_nested_namespace_shape() -> (
    None
):
    node_id = str(uuid4())
    stale_payload = {
        "name": "content-ontology",
        "hash": "sha256:test",
        "object_config_graph_nodes": [{"id": node_id}],
        "namespace_membership": [
            {
                "entity_id": str(uuid4()),
                "entity_kind": "class",
                "fqn": "aware_content.Content",
                "node_id": node_id,
                "package": "aware_content",
                "symbol": "Content",
            }
        ],
        "object_config_graph_annotations": [
            {
                "code_section_annotation_load": {
                    "attribute_name": "content_parts",
                    "class_name": "Content",
                    "domain_name": "default",
                    "fqn_prefix": "aware_content",
                    "id": str(uuid4()),
                    "schema_name": "content",
                }
            }
        ],
        "object_projection_graph_declarations": [
            {
                "name": "Content",
                "object_projection_graph_bindings": [
                    {
                        "attribute_name": "content_parts",
                        "class_name": "Content",
                        "domain_name": "default",
                        "fqn_prefix": "aware_content",
                        "id": str(uuid4()),
                        "schema_name": "content",
                    }
                ],
            }
        ],
    }
    current_payload = {
        **stale_payload,
        "object_config_graph_annotations": [
            {
                "code_section_annotation_load": {
                    "attribute_name": "content_parts",
                    "class_name": "Content",
                    "fqn_prefix": "aware_content",
                    "id": str(uuid4()),
                    "namespace": "content",
                }
            }
        ],
        "object_projection_graph_declarations": [
            {
                "name": "Content",
                "object_projection_graph_bindings": [
                    {
                        "attribute_name": "content_parts",
                        "class_name": "Content",
                        "fqn_prefix": "aware_content",
                        "id": str(uuid4()),
                        "namespace": "content",
                    }
                ],
            }
        ],
    }

    assert not materialization_service._object_config_graph_payload_has_namespace_evidence(  # noqa: SLF001
        stale_payload
    )
    assert materialization_service._object_config_graph_payload_has_namespace_evidence(  # noqa: SLF001
        current_payload
    )


def test_object_config_graph_package_reuse_cache_rejects_bodyless_graph_payload() -> (
    None
):
    assert (
        materialization_service._object_config_graph_payload_from_reuse_cache(  # noqa: SLF001
            {
                "object_config_graph": {
                    "id": str(uuid4()),
                    "name": "history",
                    "hash": "sha256:history",
                    "fqn_prefix": "aware_history",
                    "language": "aware",
                    "object_config_graph_nodes": [],
                }
            }
        )
        is None
    )


def test_object_config_graph_package_reuse_cache_write_preserves_payload() -> None:
    graph_id = uuid4()
    graph_payload = {
        "id": str(graph_id),
        "name": "history",
        "hash": "sha256:history",
        "fqn_prefix": "aware_history",
        "language": "aware",
        "object_config_graph_nodes": [
            {
                "id": str(uuid4()),
                "type": "class",
                "node_key": "history.Change",
            }
        ],
    }
    code_package = materialization_service.CodePackage(
        id=uuid4(),
        code_package_config_id=_source_code_package_config_id(
            surface="structure",
        ),
        package_name="history-ontology",
        language=materialization_service.CodeLanguage.aware,
        surface="structure",
        manifest_kind="aware_toml",
        manifest_relative_path="structure/ontology/aware.toml",
        package_root="structure/ontology",
        sources_root="structure/ontology/aware",
        fqn_prefix="aware_history",
    )
    object_config_graph = materialization_service.ObjectConfigGraph(
        id=graph_id,
        name="history",
        hash="sha256:history",
        fqn_prefix="aware_history",
        language=materialization_service.CodeLanguage.aware,
    )
    result = materialization_service.ObjectConfigGraphPackageLeafMaterializationResult(
        aware_toml_path=Path(
            "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml"
        ),
        package_branch_id=uuid4(),
        code_package=code_package,
        object_config_graph_package=(
            materialization_service.ObjectConfigGraphPackage(
                id=uuid4(),
                package_name="history-ontology",
                fqn_prefix="aware_history",
                source_code_package=code_package,
                source_code_package_id=code_package.id,
                object_config_graph=object_config_graph,
                object_config_graph_id=object_config_graph.id,
                object_config_graph_object_instance_graph_commit_id=uuid4(),
            )
        ),
        object_config_graph=object_config_graph,
        owned_file_paths=(
            "workspaces/aware_kernel/modules/history/ontology/structure/aware/change/change.aware",
        ),
        code_package_commit_id=None,
        code_package_head_commit_id=uuid4(),
        code_package_object_instance_graph_commit_id=uuid4(),
        object_config_graph_commit_id=None,
        object_config_graph_head_commit_id=uuid4(),
        object_config_graph_object_instance_graph_commit_id=uuid4(),
        object_config_graph_package_commit_id=None,
        object_config_graph_package_head_commit_id=uuid4(),
        object_config_graph_package_object_instance_graph_commit_id=uuid4(),
        phase_timings_s={},
        code_package_build_runtime_telemetry={},
        code_package_build_invoke_perf_ms={},
        code_package_upsert_runtime_telemetry={},
        code_package_upsert_invoke_perf_ms={},
        semantic_commit_strategy="fingerprint_reuse",
        semantic_commit_fallback_reset=False,
        semantic_commit_phase_timings_s={},
        object_config_graph_payload=graph_payload,
    )

    assert (
        materialization_service._object_config_graph_payload_for_reuse_cache_write(  # noqa: SLF001
            result=result
        )
        == graph_payload
    )


def test_object_config_graph_package_reuse_cache_restores_source_function_sections(
    tmp_path: Path,
) -> None:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_aware_code(
        tmp_path,
        "code_package_code.aware",
        """
class Code {
    relative_path String key

    fn create construct(relative_path String key) -> Code {}
}

class CodePackage {
    codes Code[] @CodePackageCode

    fn create_code(relative_path String key) -> CodePackageCode {
        let created = construct codes.create(relative_path = relative_path)
    }
}

edge CodePackageCode {
    relative_path String key

    fn create construct(relative_path String key) -> CodePackageCode {
        let created_code = construct code.create(relative_path = relative_path)
    }
}
""".strip(),
    )
    namespace_by_code_id, domains = _namespace_and_domains(
        fqn_prefix="aware_code",
        namespace="code",
        code_id=code.id,
    )
    built = build_object_config_graph_from_code(
        name="code-ontology",
        description="Code ontology",
        fqn_prefix="aware_code",
        file_codes=(("code_package_code.aware", code),),
        namespace_by_code_id=namespace_by_code_id,
    )

    cache_payload = {
        "object_config_graph": built.graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
        "object_config_graph_source_sections": (
            materialization_service._object_config_graph_source_sections_payload(  # noqa: SLF001
                built.graph
            )
        ),
    }
    restored = ObjectConfigGraph.model_validate(cache_payload["object_config_graph"])

    code_package_code = next(
        node.class_config
        for node in restored.object_config_graph_nodes
        if node.class_config is not None and node.class_config.name == "CodePackageCode"
    )
    create_function = next(
        link.function_config
        for link in code_package_code.class_config_function_configs
        if link.function_config is not None and link.function_config.name == "create"
    )
    assert create_function.code_section_function is None

    materialization_service._attach_object_config_graph_source_sections_from_reuse_cache(  # noqa: SLF001
        graph=restored,
        payload=cache_payload,
    )
    materialization_service._rehydrate_object_config_graph_source_relationship_refs(  # noqa: SLF001
        restored
    )

    assert create_function.code_section_function is not None
    assert create_function.code_section_function.body_segment is not None
    code_package = next(
        node.class_config
        for node in restored.object_config_graph_nodes
        if node.class_config is not None and node.class_config.name == "CodePackage"
    )
    codes_relationship = next(
        relationship
        for relationship in code_package.class_config_relationships
        if relationship.relationship_key == "codes"
    )
    assert codes_relationship.target_class_config is not None
    assert codes_relationship.target_class_config.name == "Code"
    assert codes_relationship.class_config_relationship_attributes
    assert (
        codes_relationship.class_config_relationship_attributes[0].attribute_config
        is not None
    )
    assert (
        codes_relationship.class_config_relationship_attributes[0].attribute_config.name
        == "codes"
    )
    assert codes_relationship.class_config_relationship_association_edge is not None
    assert (
        codes_relationship.class_config_relationship_association_edge.class_config
        is not None
    )
    assert (
        codes_relationship.class_config_relationship_association_edge.class_config.name
        == "CodePackageCode"
    )

    runtime = (
        RuntimeObjectConfigGraphDerivationService()
        .derive(
            RuntimeObjectConfigGraphDerivationRequest(
                source_graph=restored,
                source_is_runtime=False,
                include_projection_graphs=False,
            )
        )
        .runtime_graph
    )
    runtime_code = next(
        node.class_config
        for node in runtime.object_config_graph_nodes
        if node.class_config is not None and node.class_config.name == "Code"
    )
    runtime_code_function_names = {
        link.function_config.name
        for link in runtime_code.class_config_function_configs
        if link.function_config is not None
    }
    assert "create" not in runtime_code_function_names
    assert "create_via_code_package_code" in runtime_code_function_names


def test_runtime_package_projection_index_writer_uses_materialization_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph_id = uuid4()
    package_id = uuid4()
    graph_payload = {
        "id": str(graph_id),
        "name": "workspace",
        "hash": "sha256:workspace",
        "fqn_prefix": "aware_workspace",
        "language": "aware",
        "object_projection_graphs": [
            {
                "id": str(uuid4()),
                "name": "Workspace",
                "projection_hash": "sha256:Workspace",
            }
        ],
        "object_config_graph_nodes": [],
    }
    code_package = materialization_service.CodePackage(
        id=uuid4(),
        code_package_config_id=_source_code_package_config_id(
            surface="structure",
        ),
        package_name="workspace-ontology",
        language=materialization_service.CodeLanguage.aware,
        surface="structure",
        manifest_kind="aware_toml",
        manifest_relative_path="structure/ontology/aware.toml",
        package_root="structure/ontology",
        sources_root="structure/ontology/aware",
        fqn_prefix="aware_workspace",
    )
    object_config_graph = materialization_service.ObjectConfigGraph(
        id=graph_id,
        name="workspace",
        hash="sha256:workspace",
        fqn_prefix="aware_workspace",
        language=materialization_service.CodeLanguage.aware,
        object_projection_graphs=[
            materialization_service.ObjectProjectionGraph(
                object_config_graph_id=graph_id,
                language=materialization_service.CodeLanguage.aware,
                name="Workspace",
                projection_hash="sha256:Workspace",
            )
        ],
    )
    result = materialization_service.ObjectConfigGraphPackageLeafMaterializationResult(
        aware_toml_path=(tmp_path / "modules/workspace/structure/ontology/aware.toml"),
        package_branch_id=uuid4(),
        code_package=code_package,
        object_config_graph_package=(
            materialization_service.ObjectConfigGraphPackage(
                id=package_id,
                package_name="workspace-ontology",
                fqn_prefix="aware_workspace",
                source_code_package=code_package,
                source_code_package_id=code_package.id,
                object_config_graph=object_config_graph,
                object_config_graph_id=object_config_graph.id,
                object_config_graph_object_instance_graph_commit_id=uuid4(),
            )
        ),
        object_config_graph=object_config_graph,
        owned_file_paths=(
            "modules/workspace/structure/ontology/aware/workspace.aware",
        ),
        code_package_commit_id=None,
        code_package_head_commit_id=uuid4(),
        code_package_object_instance_graph_commit_id=uuid4(),
        object_config_graph_commit_id=None,
        object_config_graph_head_commit_id=uuid4(),
        object_config_graph_object_instance_graph_commit_id=uuid4(),
        object_config_graph_package_commit_id=None,
        object_config_graph_package_head_commit_id=uuid4(),
        object_config_graph_package_object_instance_graph_commit_id=uuid4(),
        phase_timings_s={},
        code_package_build_runtime_telemetry={},
        code_package_build_invoke_perf_ms={},
        code_package_upsert_runtime_telemetry={},
        code_package_upsert_invoke_perf_ms={},
        semantic_commit_strategy="fingerprint_reuse",
        semantic_commit_fallback_reset=False,
        semantic_commit_phase_timings_s={},
        object_config_graph_payload=graph_payload,
        materialization_index_receipt={"source": {"owned_file_paths": []}},
    )
    calls: list[Mapping[str, object]] = []

    def fake_record_full_package_materialization_index(**kwargs: object) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(
        materialization_service,
        "record_full_package_materialization_index",
        fake_record_full_package_materialization_index,
    )

    materialization_service._record_runtime_package_projection_index(  # noqa: SLF001
        result=result,
        workspace_root=tmp_path,
        module_root=tmp_path / "modules" / "workspace",
        source_manifest_hash="sha256:source",
        dependency_signature="sha256:deps",
    )

    assert calls
    assert calls[0]["materialized_package_name"] == "workspace-ontology"
    assert calls[0]["object_config_graph_payload"] == graph_payload
    package_entries = tuple(calls[0]["package_entries"])  # type: ignore[arg-type]
    assert package_entries[0].module_id == "workspace"
    assert package_entries[0].projection_names == ("Workspace",)


@pytest.mark.asyncio
async def test_object_config_graph_package_reuse_cache_records_miss_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "v": materialization_service._PACKAGE_REUSE_CACHE_VERSION,  # noqa: SLF001
        "source_manifest_hash": "old-source-hash",
    }

    monkeypatch.setattr(
        materialization_service,
        "_read_reuse_cache_payload",
        lambda **_: payload,
    )

    phase_timings_s: dict[str, float] = {}
    result = await materialization_service._try_reuse_existing_object_config_graph_package_cache(  # noqa: SLF001
        index=SimpleNamespace(),
        branch_id=uuid4(),
        code_package_projection_hash="code-package-projection",
        object_config_graph_projection_hash="object-config-graph-projection",
        object_config_graph_package_projection_hash=(
            "object-config-graph-package-projection"
        ),
        aware_toml_path=Path("modules/demo/structure/ontology/aware.toml"),
        source_manifest_hash="current-source-hash",
        dependency_signature="dependency-signature",
        resolved_source_code_package_id=uuid4(),
        resolved_object_config_graph_id=uuid4(),
        resolved_object_config_graph_package_id=uuid4(),
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        function_impl_ownership="compiler",
        function_impl_parity_policy="error",
        implementation_policy_source="aware_toml",
        language_materialization_specs=(),
        language_materialization_package_root=Path("modules/demo/structure/ontology"),
        title=None,
        description=None,
        surface="structure",
        manifest_relative_path="modules/demo/structure/ontology/aware.toml",
        package_root_relative="modules/demo/structure/ontology",
        sources_root_relative="modules/demo/structure/ontology/aware",
        owned_file_paths=(
            "modules/demo/structure/ontology/aware/graph/config/demo.aware",
        ),
        phase_timings_s=phase_timings_s,
        package_started_at=0.0,
    )

    assert result is None
    assert phase_timings_s["reuse_existing_object_config_graph_package_cache"] >= 0.0
    assert (
        phase_timings_s[
            "reuse_existing_object_config_graph_package_cache."
            "miss.source_manifest_hash_mismatch"
        ]
        == 0.0
    )


@pytest.mark.asyncio
async def test_object_config_graph_package_reuse_cache_rejects_stale_code_package_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_code_package_id = uuid4()
    object_config_graph_id = uuid4()
    object_config_graph_package_id = uuid4()
    payload = {
        "v": materialization_service._PACKAGE_REUSE_CACHE_VERSION,  # noqa: SLF001
        "source_manifest_hash": "current-source-hash",
        "dependency_signature": "dependency-signature",
        "source_code_package_id": str(source_code_package_id),
        "object_config_graph_id": str(object_config_graph_id),
        "object_config_graph_package_id": str(object_config_graph_package_id),
        "function_impl_ownership": "compiler",
        "function_impl_parity_policy": "error",
        "implementation_policy_source": "aware_toml",
        "source_to_ocg_lowering_signature": (
            materialization_service.OBJECT_CONFIG_GRAPH_SOURCE_TO_RUNTIME_LOWERING_SIGNATURE
        ),
        "language_materialization_signature": (
            materialization_service._language_materialization_specs_signature(  # noqa: SLF001
                language_materialization_specs=(),
            )
        ),
        "code_package_package_name": "demo-ontology",
        "code_package_language": "aware",
        "code_package_surface": "structure",
        "code_package_manifest_kind": "aware_toml",
        "code_package_manifest_relative_path": "ontology/structure/aware.toml",
        "code_package_package_root": "ontology/structure",
        "code_package_sources_root": "ontology/structure/aware",
        "code_package_fqn_prefix": "aware_demo",
    }

    monkeypatch.setattr(
        materialization_service,
        "_read_reuse_cache_payload",
        lambda **_: payload,
    )

    phase_timings_s: dict[str, float] = {}
    result = await materialization_service._try_reuse_existing_object_config_graph_package_cache(  # noqa: SLF001
        index=SimpleNamespace(),
        branch_id=uuid4(),
        code_package_projection_hash="code-package-projection",
        object_config_graph_projection_hash="object-config-graph-projection",
        object_config_graph_package_projection_hash=(
            "object-config-graph-package-projection"
        ),
        aware_toml_path=Path("modules/demo/structure/ontology/aware.toml"),
        source_manifest_hash="current-source-hash",
        dependency_signature="dependency-signature",
        resolved_source_code_package_id=source_code_package_id,
        resolved_object_config_graph_id=object_config_graph_id,
        resolved_object_config_graph_package_id=object_config_graph_package_id,
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        function_impl_ownership="compiler",
        function_impl_parity_policy="error",
        implementation_policy_source="aware_toml",
        language_materialization_specs=(),
        language_materialization_package_root=Path("modules/demo/structure/ontology"),
        title=None,
        description=None,
        surface="structure",
        manifest_relative_path="modules/demo/structure/ontology/aware.toml",
        package_root_relative="modules/demo/structure/ontology",
        sources_root_relative="modules/demo/structure/ontology/aware",
        owned_file_paths=(
            "modules/demo/structure/ontology/aware/graph/config/demo.aware",
        ),
        phase_timings_s=phase_timings_s,
        package_started_at=0.0,
    )

    assert result is None
    assert (
        phase_timings_s[
            "reuse_existing_object_config_graph_package_cache."
            "miss.code_package_manifest_relative_path_mismatch"
        ]
        == 0.0
    )


@pytest.mark.asyncio
async def test_object_config_graph_package_reuse_cache_rejects_stale_lowering_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_code_package_id = uuid4()
    object_config_graph_id = uuid4()
    object_config_graph_package_id = uuid4()
    payload = {
        "v": materialization_service._PACKAGE_REUSE_CACHE_VERSION,  # noqa: SLF001
        "source_manifest_hash": "current-source-hash",
        "dependency_signature": "dependency-signature",
        "source_code_package_id": str(source_code_package_id),
        "object_config_graph_id": str(object_config_graph_id),
        "object_config_graph_package_id": str(object_config_graph_package_id),
        "function_impl_ownership": "compiler",
        "function_impl_parity_policy": "error",
        "implementation_policy_source": "aware_toml",
        "source_to_ocg_lowering_signature": "stale-lowering-signature",
    }

    monkeypatch.setattr(
        materialization_service,
        "_read_reuse_cache_payload",
        lambda **_: payload,
    )

    phase_timings_s: dict[str, float] = {}
    result = await materialization_service._try_reuse_existing_object_config_graph_package_cache(  # noqa: SLF001
        index=SimpleNamespace(),
        branch_id=uuid4(),
        code_package_projection_hash="code-package-projection",
        object_config_graph_projection_hash="object-config-graph-projection",
        object_config_graph_package_projection_hash=(
            "object-config-graph-package-projection"
        ),
        aware_toml_path=Path("modules/demo/structure/ontology/aware.toml"),
        source_manifest_hash="current-source-hash",
        dependency_signature="dependency-signature",
        resolved_source_code_package_id=source_code_package_id,
        resolved_object_config_graph_id=object_config_graph_id,
        resolved_object_config_graph_package_id=object_config_graph_package_id,
        package_name="demo-ontology",
        fqn_prefix="aware_demo",
        function_impl_ownership="compiler",
        function_impl_parity_policy="error",
        implementation_policy_source="aware_toml",
        language_materialization_specs=(),
        language_materialization_package_root=Path("modules/demo/structure/ontology"),
        title=None,
        description=None,
        surface="structure",
        manifest_relative_path="modules/demo/structure/ontology/aware.toml",
        package_root_relative="modules/demo/structure/ontology",
        sources_root_relative="modules/demo/structure/ontology/aware",
        owned_file_paths=(
            "modules/demo/structure/ontology/aware/graph/config/demo.aware",
        ),
        phase_timings_s=phase_timings_s,
        package_started_at=0.0,
    )

    assert result is None
    assert (
        phase_timings_s[
            "reuse_existing_object_config_graph_package_cache."
            "miss.source_to_ocg_lowering_signature_mismatch"
        ]
        == 0.0
    )


def test_existing_object_config_graph_head_summary_uses_cached_semantic_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    graph_id = uuid4()
    package_id = uuid4()
    head_commit_id = uuid4()
    projection_hash = "object-config-graph-projection"
    graph_hash = "sha256:semantic-ocg"
    graph = materialization_service.ObjectConfigGraph(
        id=graph_id,
        name="aware_demo",
        hash=graph_hash,
        fqn_prefix="aware_demo",
        language=materialization_service.CodeLanguage.aware,
    )
    payload = {
        "v": materialization_service._PACKAGE_REUSE_CACHE_VERSION,  # noqa: SLF001
        "cache_kind": materialization_service.OBJECT_CONFIG_GRAPH_PACKAGE_REUSE_CACHE_KIND_MATERIALIZED_PACKAGE,
        "object_config_graph_id": str(graph_id),
        "object_config_graph_package_id": str(package_id),
        "object_config_graph_head_commit_id": str(head_commit_id),
        "source_to_ocg_lowering_signature": (
            materialization_service.OBJECT_CONFIG_GRAPH_SOURCE_TO_RUNTIME_LOWERING_SIGNATURE
        ),
        "object_config_graph_hash": graph_hash,
    }

    monkeypatch.setattr(
        materialization_service,
        "_read_reuse_cache_payload",
        lambda **_: payload,
    )

    matched, reason = (
        materialization_service._existing_object_config_graph_head_summary_matches(  # noqa: SLF001
            branch_id=branch_id,
            object_config_graph_projection_hash=projection_hash,
            object_config_graph_package_id=package_id,
            object_config_graph_id=graph_id,
            existing_object_config_graph_head={
                "commit_id": str(head_commit_id),
                "root_object_id": str(graph_id),
                "projection_hash": projection_hash,
                "graph_hash_post": "oig-lane-hash-is-not-the-ocg-hash",
            },
            built_object_config_graph=graph,
        )
    )

    assert matched is True
    assert reason == "ok"


def test_object_config_graph_package_snapshot_root_preserves_package_policy() -> None:
    root, related_models = (
        materialization_service._build_object_config_graph_package_snapshot_root(  # noqa: SLF001
            object_config_graph_package_id=uuid4(),
            package_name="meta-ontology",
            fqn_prefix="aware_meta",
            source_code_package_id=uuid4(),
            object_config_graph_id=uuid4(),
            object_config_graph_object_instance_graph_commit_id=uuid4(),
            function_impl_ownership="compiler",
            function_impl_parity_policy="error",
            implementation_policy_source="aware_toml",
            title=None,
            description=None,
            language_materialization_specs=(),
            package_root=None,
            workspace_root=None,
        )
    )

    assert related_models == []
    assert (
        root.function_impl_ownership
        is materialization_service.ObjectConfigGraphPackageFunctionImplOwnership.compiler
    )
    assert (
        root.function_impl_parity_policy
        is materialization_service.ObjectConfigGraphPackageFunctionImplParityPolicy.error
    )
    assert root.implementation_policy_source == "aware_toml"


@pytest.mark.asyncio
async def test_current_index_identity_seed_lane_ensure_reuses_success_until_lane_revision_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with (
        materialization_service._CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE_LOCK
    ):  # noqa: SLF001
        materialization_service._CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE.clear()  # noqa: SLF001

    branch_id = uuid4()
    commit_id = uuid4()
    projection_hash = "identity-seed-projection-test"
    graph_hash_post = "identity-seed-graph-hash-post"
    graph = SimpleNamespace(id=uuid4(), hash="index-graph-hash")
    index = SimpleNamespace(ocg=graph)
    spec = materialization_service._GraphIdentityLaneSeedSpec(  # noqa: SLF001
        root_instance=SimpleNamespace(id=branch_id),
        branch_id=branch_id,
        opg_name="ObjectConfigGraphIdentity",
    )
    call_counts = {"preview": 0, "ensure": 0}

    def fake_iter_graph_identity_lane_seed_specs(
        *, graph: object
    ) -> tuple[object, ...]:
        assert graph is index.ocg
        return (spec,)

    async def fake_preview_graph_identity_seed_plan(**_: object) -> object:
        call_counts["preview"] += 1
        return SimpleNamespace(
            commit_id=commit_id,
            graph_hash_post=graph_hash_post,
            projection_hash=projection_hash,
        )

    def fake_read_single_root_runtime_lane_head(**_: object) -> dict[str, str]:
        return {
            "commit_id": str(commit_id),
            "graph_hash_post": graph_hash_post,
        }

    async def fake_ensure_graph_identity_seeded_lane(**_: object) -> None:
        call_counts["ensure"] += 1

    monkeypatch.setattr(
        materialization_service,
        "_iter_graph_identity_lane_seed_specs",
        fake_iter_graph_identity_lane_seed_specs,
    )
    monkeypatch.setattr(
        materialization_service,
        "preview_graph_identity_seed_plan",
        fake_preview_graph_identity_seed_plan,
    )
    monkeypatch.setattr(
        materialization_service,
        "_read_single_root_runtime_lane_head",
        fake_read_single_root_runtime_lane_head,
    )
    monkeypatch.setattr(
        materialization_service,
        "ensure_graph_identity_seeded_lane",
        fake_ensure_graph_identity_seeded_lane,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root_identity_seed_lane_cache", persistence_backend="fs"
    ):
        await materialization_service._ensure_current_index_identity_seed_lanes(
            index=index
        )  # noqa: SLF001
        await materialization_service._ensure_current_index_identity_seed_lanes(
            index=index
        )  # noqa: SLF001

        assert call_counts == {"preview": 1, "ensure": 1}

        materialization_service.get_shared_materialization_cache().invalidate_lane(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        await materialization_service._ensure_current_index_identity_seed_lanes(
            index=index
        )  # noqa: SLF001

        assert call_counts == {"preview": 2, "ensure": 2}

    with (
        materialization_service._CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE_LOCK
    ):  # noqa: SLF001
        materialization_service._CURRENT_INDEX_IDENTITY_SEED_LANE_ENSURE_CACHE.clear()  # noqa: SLF001


@pytest.mark.asyncio
async def test_ocg_seed_recovery_resets_nonempty_lane_missing_seed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    projection_hash = "object-config-graph-projection"
    missing_commit_id = uuid4()
    recovered_commit_id = uuid4()
    graph_id = uuid4()
    graph = materialization_service.ObjectConfigGraph(
        id=graph_id,
        name="aware_demo",
        hash="sha256:demo",
        fqn_prefix="aware_demo",
        language=materialization_service.CodeLanguage.aware,
    )

    def seed_plan(
        *, seeded: bool, commit_id: UUID
    ) -> materialization_service.OCGSeedPlan:
        return materialization_service.OCGSeedPlan(
            seeded=seeded,
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_id=graph_id,
            root_object_id=graph_id,
            graph_hash_pre="pre",
            graph_hash_post="post",
            commit_id=commit_id,
            changes=[],
            before_oig=None,
            after_oig=None,
            objects_by_id={},
        )

    plans = [
        seed_plan(seeded=False, commit_id=missing_commit_id),
        seed_plan(seeded=True, commit_id=recovered_commit_id),
    ]
    ensure_calls: list[dict[str, Any]] = []
    reset_calls: list[dict[str, Any]] = []
    snapshot_writes: list[UUID] = []
    progress_events: list[dict[str, object]] = []

    class FakeStore:
        aware_root = tmp_path

        async def get_commit(self, **kwargs: Any) -> object | None:
            return None

    async def fake_ensure_ocg_seeded_lane(
        **kwargs: Any,
    ) -> materialization_service.OCGSeedPlan:
        ensure_calls.append(kwargs)
        return plans.pop(0)

    async def fake_write_seed_snapshot_from_plan(
        *,
        plan: materialization_service.OCGSeedPlan,
        index: object,
    ) -> None:
        snapshot_writes.append(plan.commit_id)

    def fake_reset_generated_projection_lanes(**kwargs: Any) -> None:
        reset_calls.append(kwargs)

    def progress_callback(payload: Mapping[str, object]) -> None:
        progress_events.append(dict(payload))

    monkeypatch.setattr(
        materialization_service,
        "ensure_ocg_seeded_lane",
        fake_ensure_ocg_seeded_lane,
    )
    monkeypatch.setattr(
        materialization_service,
        "_write_seed_snapshot_from_plan",
        fake_write_seed_snapshot_from_plan,
    )
    monkeypatch.setattr(
        materialization_service,
        "_reset_generated_projection_lanes",
        fake_reset_generated_projection_lanes,
    )

    phase_timings_s: dict[str, float] = {}
    recovered_plan, snapshot_written, recovered_missing_seed = (
        await materialization_service._ensure_ocg_seeded_lane_with_missing_seed_recovery(  # noqa: SLF001
            ocg=graph,
            branch_id=branch_id,
            ocg_hash=str(graph.hash),
            external_graphs=(),
            projection_hash=projection_hash,
            index=object(),
            aware_toml_path=Path("modules/demo/structure/ontology/aware.toml"),
            phase_timings_s=phase_timings_s,
            store=FakeStore(),
            progress_callback=progress_callback,
            detail_payload={"package_name": "demo-ontology"},
        )
    )

    assert recovered_plan.commit_id == recovered_commit_id
    assert snapshot_written is True
    assert recovered_missing_seed is True
    assert snapshot_writes == [recovered_commit_id]
    assert len(ensure_calls) == 2
    assert reset_calls == [
        {
            "aware_root": tmp_path,
            "branch_id": branch_id,
            "projection_hashes": (projection_hash,),
        }
    ]
    assert phase_timings_s["reset_nonempty_missing_seed_projection_lane"] >= 0.0
    assert (
        phase_timings_s["write_seed_snapshot_from_plan_after_missing_seed_reset"] >= 0.0
    )
    emitted_subphases = {
        event["detail_payload"]["subphase_name"]
        for event in progress_events
        if isinstance(event.get("detail_payload"), Mapping)
    }
    assert "ensure_ocg_seeded_lane" in emitted_subphases
    assert "reset_nonempty_missing_seed_projection_lane" in emitted_subphases
    assert "ensure_ocg_seeded_lane_after_missing_seed_reset" in emitted_subphases
    assert "write_seed_snapshot_from_plan_after_missing_seed_reset" in emitted_subphases


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


async def _hydrate_projection_root(
    *,
    runtime: MetaGraphRuntime,
    branch_id: UUID,
    projection_hash: str,
    root_type: type[_TRoot],
    root_id: UUID,
) -> _TRoot | None:
    index = _meta_runtime_index(runtime)
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head is not None
    assert head.get("commit_id") is not None
    opg = index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_root_model(
        index=index,
        opg=opg,
        oig=oig,
        model_type=root_type,
        root_id=root_id,
        branch_id=branch_id,
    )


async def _assert_branch_has_committed_object_config_graph_topology(
    *,
    runtime: MetaGraphRuntime,
    branch_id: UUID,
    object_config_graph_id: UUID,
) -> None:
    from aware_meta_ontology.graph.config.object_config_graph import (  # noqa: WPS433
        ObjectConfigGraph,
    )

    index = _meta_runtime_index(runtime)
    projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="ObjectConfigGraph",
    )
    graph = await _hydrate_projection_root(
        runtime=runtime,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_type=ObjectConfigGraph,
        root_id=object_config_graph_id,
    )
    assert graph is not None
    assert graph.hash
    assert graph.hash != _EMPTY_OCG_HASH
    assert graph.object_config_graph_nodes
    assert any(
        node.class_config is not None and node.class_config.class_fqn
        for node in graph.object_config_graph_nodes
    )


async def _assert_replayable_oig_commit_ref(
    *,
    branch_id: UUID,
    projection_hash: str,
    domain_commit_id: UUID,
    object_instance_graph_commit_id: UUID,
) -> None:
    store = FSCommitStore()
    commit = await store.get_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=domain_commit_id,
    )
    assert commit is not None
    assert object_instance_graph_commit_id != commit.id
    assert (
        await store.domain_commit_id_for_object_instance_graph_commit_id(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        )
        == domain_commit_id
    )


def _write_package_fixture(
    *,
    workspace_root: Path,
    module_name: str = "demo",
    package_name: str = "demo-ontology",
    fqn_prefix: str = "aware_demo",
    title: str = "Demo Ontology",
    description: str = "Demo Meta package leaf materialization fixture",
    class_name: str = "DemoRoot",
    source_relpath: str = "graph/config/demo_root.aware",
    dependencies: tuple[str, ...] = (),
    source_text: str | None = None,
) -> Path:
    module_root = workspace_root / "modules" / module_name
    _write(
        module_root / "aware.module.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[module]",
                'stable_ids_ownership = "compiler"',
                'stable_ids_parity_policy = "error"',
                "",
                "[[packages]]",
                'aware_toml_path = "structure/ontology/aware.toml"',
            ]
        )
        + "\n",
    )
    aware_toml_path = module_root / "structure" / "ontology" / "aware.toml"
    _write(
        aware_toml_path,
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                f'package_name = "{package_name}"',
                f'fqn_prefix = "{fqn_prefix}"',
                'kind = "ontology"',
                f'title = "{title}"',
                f'description = "{description}"',
                "",
                "[build]",
                f'environment_slug = "{fqn_prefix}"',
                'sources_dir = "aware"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                *(
                    line
                    for dependency_package_name in dependencies
                    for line in (
                        "",
                        "[[dependencies]]",
                        f'package_name = "{dependency_package_name}"',
                    )
                ),
            ]
        )
        + "\n",
    )
    _write(
        module_root / "structure" / "ontology" / "aware" / Path(source_relpath),
        source_text or f"class {class_name} {{\n    name String\n}}\n",
    )
    return aware_toml_path


@pytest.mark.asyncio
async def test_materialize_object_config_graph_package_leaf_rejects_non_canonical_explicit_branch(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_explicit_branch"
    workspace_root.mkdir(parents=True, exist_ok=True)
    aware_toml_path = _write_package_fixture(workspace_root=workspace_root)

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_explicit_branch",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
            stable_object_config_graph_package_branch_id,
        )

        canonical_package_branch_id = stable_object_config_graph_package_branch_id(
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
            package_name="demo-ontology",
            fqn_prefix="aware_demo",
        )
        mismatched_package_branch_id = uuid4()
        assert mismatched_package_branch_id != canonical_package_branch_id

        with pytest.raises(RuntimeError, match="Meta-owned package lane identity"):
            await materialize_object_config_graph_package_leaf_from_manifest(
                runtime=runtime,
                index=index,
                actor_id=None,
                branch_id=uuid4(),
                workspace_root=workspace_root,
                aware_toml_path=aware_toml_path,
                package_branch_id=mismatched_package_branch_id,
            )


@pytest.mark.asyncio
async def test_materialize_home_story_fixture_materializes_full_meta_identity_plane(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    package_root = META_FIXTURES_ROOT / "home_story_ontology"
    aware_toml_path = package_root / "aware.toml"

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_home_story_fixture",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )

        result = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=package_root,
            aware_toml_path=aware_toml_path,
        )

        assert result.code_package.package_name == "home-ontology"
        assert result.code_package.fqn_prefix == "aware_home"
        assert result.code_package.surface == "structure"
        assert result.object_config_graph_package.package_name == "home-ontology"
        assert result.object_config_graph_package.fqn_prefix == "aware_home"
        assert result.object_config_graph_package.object_config_graph_id == (
            result.object_config_graph.id
        )
        assert result.object_config_graph.name == "aware_home"
        assert result.object_config_graph.fqn_prefix == "aware_home"
        assert result.object_config_graph.hash
        assert result.object_config_graph.hash != _EMPTY_OCG_HASH
        assert result.owned_file_paths == (
            "aware/home/door.aware",
            "aware/home/home.aware",
            "aware/home/tv.aware",
            "aware/home/tv_channel.aware",
            "aware/home_projection.aware",
        )

        assert result.code_package_head_commit_id is not None
        assert result.code_package_object_instance_graph_commit_id is not None
        assert result.object_config_graph_head_commit_id is not None
        assert result.object_config_graph_object_instance_graph_commit_id is not None
        assert result.object_config_graph_package_head_commit_id is not None
        assert (
            result.object_config_graph_package_object_instance_graph_commit_id
            is not None
        )

        ocgi = result.object_config_graph.object_config_graph_identity
        assert ocgi is not None
        assert result.object_config_graph.object_config_graph_identity_id == ocgi.id
        assert ocgi.key == "aware_home"
        assert len(ocgi.object_projection_graph_identities) == 1

        opgi = ocgi.object_projection_graph_identities[0]
        assert opgi.projection_name == "Home"
        assert opgi.is_branchable is True
        assert opgi.object_config_graph_identity_id == ocgi.id
        assert opgi.object_projection_graph_id == stable_object_projection_graph_id(
            object_config_graph_id=result.object_config_graph.id,
            name="Home",
        )

        observables = {
            observable.observable_key: observable
            for observable in opgi.object_projection_graph_observables
        }
        assert set(observables) == {"overview", "security", "entertainment"}
        assert observables["security"].is_default is True
        assert observables["security"].key == "Home:security"
        assert all(
            observable.key == f"Home:{observable.observable_key}"
            for observable in observables.values()
        )

        receipt = result.materialization_index_receipt
        assert receipt is not None
        assert (
            receipt["schema"]
            == "aware_meta.object_config_graph_package.materialization_index_receipt.v1"
        )
        assert (
            receipt["receipt_kind"]
            == "object_config_graph_package_materialization_index"
        )
        assert receipt["cache_status"] == "rebuilt"
        cache_key = receipt["cache_key"]
        assert isinstance(cache_key, dict)
        assert cache_key["package_name"] == "home-ontology"
        assert cache_key["fqn_prefix"] == "aware_home"
        assert cache_key["object_config_graph_hash"] == result.object_config_graph.hash
        assert cache_key["projection_hashes_complete"] is True
        assert len(cache_key["projection_hashes"]) == 1
        source = receipt["source"]
        assert isinstance(source, dict)
        assert source["code_package_id"] == str(result.code_package.id)
        assert source["code_package_object_instance_graph_commit_id"] == str(
            result.code_package_object_instance_graph_commit_id
        )
        semantic = receipt["semantic"]
        assert isinstance(semantic, dict)
        assert semantic["object_config_graph_id"] == str(result.object_config_graph.id)
        assert semantic["object_config_graph_package_id"] == str(
            result.object_config_graph_package.id
        )
        identity_plane = receipt["identity_plane"]
        assert isinstance(identity_plane, dict)
        assert identity_plane["object_config_graph_identity_id"] == str(ocgi.id)
        assert identity_plane["object_config_graph_identity_key"] == "aware_home"
        projection_receipts = identity_plane["projection_identities"]
        assert isinstance(projection_receipts, list)
        assert len(projection_receipts) == 1
        assert projection_receipts[0]["projection_name"] == "Home"
        assert projection_receipts[0]["object_projection_graph_id"] == str(
            opgi.object_projection_graph_id
        )
        assert projection_receipts[0]["observable_keys"] == [
            "entertainment",
            "overview",
            "security",
        ]
        observable_receipts = identity_plane["observables"]
        assert isinstance(observable_receipts, list)
        assert {
            item["observable_key"]
            for item in observable_receipts
            if isinstance(item, dict)
        } == {"overview", "security", "entertainment"}

        await _assert_branch_has_committed_object_config_graph_topology(
            runtime=runtime,
            branch_id=result.package_branch_id,
            object_config_graph_id=result.object_config_graph.id,
        )


async def _prepare_oigi_history_projector_fixture(
    *,
    tmp_path: Path,
    workspace_root: Path,
    aware_toml_path: Path,
    branch_id: UUID,
) -> dict[str, Any]:
    repo_root = REPO_ROOT
    base_aware_root = tmp_path / "aware_root_oigi_projector_base"
    handler_aware_root = tmp_path / "aware_root_oigi_projector_handler"
    direct_aware_root = tmp_path / "aware_root_oigi_projector_direct"

    with IsolatedAwareRoot(
        base_aware_root, persistence_backend="fs"
    ) as active_aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=active_aware_root)
        index = _meta_runtime_index(runtime)

        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )
        from aware_meta.runtime.commit.identity_lane import (  # noqa: WPS433
            _reset_invalid_object_instance_graph_identity_lane,
            ensure_object_instance_graph_identity_lane_head,
        )

        result = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )
        object_config_graph_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ObjectConfigGraph",
        )
        oigi_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ObjectInstanceGraphIdentity",
        )
        assert result.object_config_graph_commit_id is not None
        domain_commit = await FSCommitStore().get_commit(
            branch_id=result.package_branch_id,
            projection_hash=object_config_graph_projection_hash,
            commit_id=result.object_config_graph_commit_id,
        )
        assert domain_commit is not None

        _reset_invalid_object_instance_graph_identity_lane(
            aware_root=active_aware_root,
            branch_id=domain_commit.object_instance_graph_id,
            projection_hash=oigi_projection_hash,
        )
        await ensure_object_instance_graph_identity_lane_head(
            index=index,
            object_instance_graph_id=domain_commit.object_instance_graph_id,
            domain_projection_hash=object_config_graph_projection_hash,
            author_id=META_SYSTEM_ACTOR_ID,
        )

    shutil.copytree(base_aware_root, handler_aware_root)
    shutil.copytree(base_aware_root, direct_aware_root)
    return {
        "index": index,
        "handler_aware_root": handler_aware_root,
        "direct_aware_root": direct_aware_root,
        "package_branch_id": result.package_branch_id,
        "object_config_graph": result.object_config_graph,
        "object_config_graph_projection_hash": object_config_graph_projection_hash,
        "oigi_projection_hash": oigi_projection_hash,
        "domain_commit": domain_commit,
    }


async def _run_oigi_history_projector(
    *,
    fixture: Mapping[str, Any],
    projector_mode: str,
) -> dict[str, Any]:
    aware_root = fixture[f"{projector_mode}_aware_root"]
    index = fixture["index"]
    domain_commit = fixture["domain_commit"]
    object_config_graph_projection_hash = fixture["object_config_graph_projection_hash"]
    oigi_projection_hash = fixture["oigi_projection_hash"]

    with IsolatedAwareRoot(aware_root, persistence_backend="fs"):
        from aware_meta.graph.instance.commit.materialization_cache import (  # noqa: WPS433
            get_shared_materialization_cache,
        )
        from aware_meta.runtime.commit.identity_history import (  # noqa: WPS433
            upsert_object_instance_graph_identity_history_from_domain_commit,
        )

        get_shared_materialization_cache().invalidate_lane(
            branch_id=domain_commit.object_instance_graph_id,
            projection_hash=oigi_projection_hash,
        )
        perf_ms: dict[str, int] = {}
        oigi_id = (
            await upsert_object_instance_graph_identity_history_from_domain_commit(
                index=index,
                actor_id=META_SYSTEM_ACTOR_ID,
                domain_branch_id=fixture["package_branch_id"],
                domain_projection_hash=object_config_graph_projection_hash,
                domain_commit=domain_commit,
                perf_ms=perf_ms,
                projector_mode=projector_mode,
            )
        )
        oigi_head = await FSCommitStore().head(
            branch_id=domain_commit.object_instance_graph_id,
            projection_hash=oigi_projection_hash,
        )
        assert oigi_head is not None
        oig, _ = await OIGMaterializer().get(
            branch_id=domain_commit.object_instance_graph_id,
            ocg=index.ocg,
            opg=index.opg_by_hash[oigi_projection_hash],
            commit_id=None,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        function_call_class_instance_ids = {
            item.id
            for item in oig.class_instances
            if item.class_config_id == _FUNCTION_CALL_CLASS_CONFIG_ID
        }
        core_class_instances = tuple(
            sorted(
                (
                    str(item.class_config_id),
                    str(item.source_object_id),
                )
                for item in oig.class_instances
                if item.id not in function_call_class_instance_ids
            )
        )
        core_relationships = tuple(
            sorted(
                (
                    str(item.class_config_relationship_id),
                    str(item.source_class_instance_id),
                    str(item.target_class_instance_id),
                )
                for item in oig.class_instance_relationships
                if item.source_class_instance_id not in function_call_class_instance_ids
                and item.target_class_instance_id
                not in function_call_class_instance_ids
            )
        )
        return {
            "oigi_id": oigi_id,
            "oigi_head": dict(oigi_head),
            "oigi_hash": str(oig.hash),
            "oigi_core_summary": (core_class_instances, core_relationships),
            "oigi_class_instance_count": len(oig.class_instances),
            "function_call_count": len(function_call_class_instance_ids),
            "perf_ms": perf_ms,
        }


@pytest.mark.asyncio
async def test_oigi_history_direct_projector_matches_handler_projection(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace_oigi_projector_parity"
    workspace_root.mkdir(parents=True, exist_ok=True)
    aware_toml_path = _write_package_fixture(workspace_root=workspace_root)
    branch_id = uuid4()

    fixture = await _prepare_oigi_history_projector_fixture(
        tmp_path=tmp_path,
        workspace_root=workspace_root,
        aware_toml_path=aware_toml_path,
        branch_id=branch_id,
    )
    handler_projection = await _run_oigi_history_projector(
        fixture=fixture,
        projector_mode="handler",
    )
    direct_projection = await _run_oigi_history_projector(
        fixture=fixture,
        projector_mode="direct",
    )

    assert handler_projection["oigi_id"] == direct_projection["oigi_id"]
    assert (
        handler_projection["oigi_core_summary"]
        == direct_projection["oigi_core_summary"]
    )
    assert (
        handler_projection["oigi_class_instance_count"]
        == direct_projection["oigi_class_instance_count"]
    )
    assert handler_projection["function_call_count"] == 0
    assert direct_projection["function_call_count"] == 0
    assert handler_projection["oigi_head"]["object_instance_graph_id"] == (
        direct_projection["oigi_head"]["object_instance_graph_id"]
    )

    handler_perf = handler_projection["perf_ms"]
    direct_perf = direct_projection["perf_ms"]
    assert "run_commit_reaction_oigi_execute_history_handler_ms" in handler_perf
    assert "run_commit_reaction_oigi_project_history_direct_ms" not in handler_perf
    assert "run_commit_reaction_oigi_project_history_direct_ms" in direct_perf
    assert "run_commit_reaction_oigi_execute_history_handler_ms" not in direct_perf


def _write_workspace_api_package_fixture(
    *,
    workspace_root: Path,
    package_name: str = "home-api",
    fqn_prefix: str = "aware_home_api",
) -> Path:
    package_root = workspace_root / "apis" / "home_devices" / "packages" / "home_api"
    aware_toml_path = package_root / "aware.toml"
    _write(
        aware_toml_path,
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                f'package_name = "{package_name}"',
                f'fqn_prefix = "{fqn_prefix}"',
                'kind = "api"',
                'title = "Home API"',
                'description = "Workspace-root API DTO package fixture."',
                "",
                "[build]",
                f'environment_slug = "{fqn_prefix}"',
                'sources_dir = "aware"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
            ]
        )
        + "\n",
    )
    _write(
        package_root / "aware" / "door" / "request.aware",
        "class LockDoor {\n    door_id String key\n}\n",
    )
    return aware_toml_path


@pytest.mark.asyncio
async def test_materialize_object_config_graph_package_leaf_accepts_workspace_api_package_root(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_api_root"
    workspace_root.mkdir(parents=True, exist_ok=True)
    aware_toml_path = _write_workspace_api_package_fixture(
        workspace_root=workspace_root,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_api_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )

        result = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=uuid4(),
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )

        assert result.code_package.surface == "api"
        assert result.code_package.manifest_relative_path == (
            "apis/home_devices/packages/home_api/aware.toml"
        )
        assert result.code_package.package_root == "apis/home_devices/packages/home_api"
        assert result.object_config_graph.name == "aware_home_api"
        assert result.object_config_graph.fqn_prefix == "aware_home_api"
        await _assert_branch_has_committed_object_config_graph_topology(
            runtime=runtime,
            branch_id=result.package_branch_id,
            object_config_graph_id=result.object_config_graph.id,
        )


@pytest.mark.asyncio
async def test_materialize_object_config_graph_package_leaf_preserves_cross_ocg_relationships(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_cross_ocg"
    workspace_root.mkdir(parents=True, exist_ok=True)
    storage_toml_path = _write_package_fixture(
        workspace_root=workspace_root,
        module_name="storage",
        package_name="storage-ontology",
        fqn_prefix="aware_storage",
        title="Storage Ontology",
        class_name="StorageBlob",
        source_relpath="blob/storage_blob.aware",
        source_text="class StorageBlob {\n    sha String key\n}\n",
    )
    content_toml_path = _write_package_fixture(
        workspace_root=workspace_root,
        module_name="content",
        package_name="content-ontology",
        fqn_prefix="aware_content",
        title="Content Ontology",
        class_name="ContentPart",
        source_relpath="part/content_part.aware",
        dependencies=("storage-ontology",),
        source_text="\n".join(
            [
                "class ContentPart {",
                "    storage_blobs aware_storage.blob.StorageBlob? @ContentPartFile",
                "    type String key",
                "}",
                "",
                "edge ContentPartFile {",
                "    label String?",
                "}",
                "",
                "projection Content {",
                "    root aware_content.part.ContentPart",
                "    aware_content.part.ContentPart::storage_blobs",
                "}",
                "",
            ]
        ),
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_cross_ocg",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_meta.graph.config.handlers import (  # noqa: WPS433
            build_object_projection_graphs,
        )
        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )
        branch_id = uuid4()

        storage_result = (
            await materialize_object_config_graph_package_leaf_from_manifest(
                runtime=runtime,
                index=index,
                actor_id=None,
                branch_id=branch_id,
                workspace_root=workspace_root,
                aware_toml_path=storage_toml_path,
            )
        )
        content_result = (
            await materialize_object_config_graph_package_leaf_from_manifest(
                runtime=runtime,
                index=index,
                actor_id=None,
                branch_id=branch_id,
                workspace_root=workspace_root,
                aware_toml_path=content_toml_path,
                external_graphs=[storage_result.object_config_graph],
            )
        )

        cross_relationships = (
            content_result.object_config_graph.object_config_graph_relationships
        )
        assert len(cross_relationships) == 1
        assert (
            cross_relationships[0].target_object_config_graph_id
            == storage_result.object_config_graph.id
        )
        relationship_attribute_names = {
            rel_attr.attribute_config.name
            for rel in cross_relationships[0].class_config_relationships
            for rel_attr in rel.class_config_relationship_attributes
            if rel_attr.attribute_config is not None
        }
        assert "storage_blobs" in relationship_attribute_names

        runtime_content_graph = content_result.object_config_graph.model_copy(deep=True)
        runtime_content_graph.object_projection_graphs = build_object_projection_graphs(
            runtime_content_graph,
            external_graphs=[storage_result.object_config_graph],
        )
        assert {opg.name for opg in runtime_content_graph.object_projection_graphs} == {
            "Content"
        }


@pytest.mark.asyncio
async def test_materialize_object_config_graph_package_leaf_from_manifest_enriches_existing_package_shell(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_materialization"
    workspace_root.mkdir(parents=True, exist_ok=True)
    aware_toml_path = _write_package_fixture(workspace_root=workspace_root)

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_materialization", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )
        branch_id = uuid4()
        source_code_package_id = uuid4()
        object_config_graph_package_id = uuid4()

        code_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="CodePackage",
        )
        object_config_graph_package_projection_hash = (
            find_meta_graph_projection_hash_by_name(
                index=index,
                projection_name="ObjectConfigGraphPackage",
            )
        )

        result = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
            source_code_package_id=source_code_package_id,
            object_config_graph_package_id=object_config_graph_package_id,
        )

        assert result.aware_toml_path == aware_toml_path.resolve()
        assert result.code_package.id == source_code_package_id
        assert result.object_config_graph_package.id == object_config_graph_package_id
        assert (
            result.object_config_graph_package.object_config_graph_id
            == result.object_config_graph.id
        )
        assert (
            result.object_config_graph_package.object_config_graph_object_instance_graph_commit_id
            == result.object_config_graph_object_instance_graph_commit_id
        )
        assert result.object_config_graph_package.source_code_package_id == (
            source_code_package_id
        )
        assert result.object_config_graph_package.title == "Demo Ontology"
        assert (
            result.object_config_graph_package.description
            == "Demo Meta package leaf materialization fixture"
        )
        assert result.object_config_graph.fqn_prefix == "aware_demo"
        assert result.object_config_graph.name == "aware_demo"
        assert result.object_config_graph.hash
        assert result.object_config_graph.hash != _EMPTY_OCG_HASH
        assert result.object_config_graph.object_config_graph_nodes
        assert any(
            node.class_config is not None and node.class_config.class_fqn
            for node in result.object_config_graph.object_config_graph_nodes
        )
        assert result.owned_file_paths == (
            "modules/demo/structure/ontology/aware/graph/config/demo_root.aware",
        )
        assert result.code_package_commit_id is not None
        assert result.code_package_head_commit_id is not None
        assert result.code_package_object_instance_graph_commit_id is not None
        assert result.object_config_graph_commit_id is not None
        assert result.object_config_graph_head_commit_id is not None
        assert result.object_config_graph_object_instance_graph_commit_id is not None
        assert result.object_config_graph_package_commit_id is not None
        assert result.object_config_graph_package_head_commit_id is not None
        assert (
            result.object_config_graph_package_object_instance_graph_commit_id
            is not None
        )
        await _assert_replayable_oig_commit_ref(
            branch_id=result.package_branch_id,
            projection_hash=code_package_projection_hash,
            domain_commit_id=result.code_package_commit_id,
            object_instance_graph_commit_id=(
                result.code_package_object_instance_graph_commit_id
            ),
        )
        await _assert_replayable_oig_commit_ref(
            branch_id=result.package_branch_id,
            projection_hash=object_config_graph_package_projection_hash,
            domain_commit_id=result.object_config_graph_package_commit_id,
            object_instance_graph_commit_id=(
                result.object_config_graph_package_object_instance_graph_commit_id
            ),
        )
        await _assert_branch_has_committed_object_config_graph_topology(
            runtime=runtime,
            branch_id=result.package_branch_id,
            object_config_graph_id=result.object_config_graph.id,
        )

        rerun = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
            source_code_package_id=source_code_package_id,
            object_config_graph_package_id=object_config_graph_package_id,
        )
        assert rerun.object_config_graph.id == result.object_config_graph.id
        assert (
            rerun.object_config_graph_package.id
            == result.object_config_graph_package.id
        )
        assert (
            rerun.object_config_graph_object_instance_graph_commit_id
            == result.object_config_graph_object_instance_graph_commit_id
        )
        await _assert_branch_has_committed_object_config_graph_topology(
            runtime=runtime,
            branch_id=rerun.package_branch_id,
            object_config_graph_id=rerun.object_config_graph.id,
        )


@pytest.mark.asyncio
async def test_materialize_object_config_graph_package_leaf_from_manifest_is_idempotent_without_explicit_ids(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_manifest_rerun"
    workspace_root.mkdir(parents=True, exist_ok=True)
    aware_toml_path = _write_package_fixture(workspace_root=workspace_root)

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_manifest_rerun", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )
        from aware_meta.materialization.service import (  # noqa: WPS433
            _reset_invalid_package_branch_if_needed,
        )
        branch_id = uuid4()

        first_result = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )
        semantic_timings = first_result.semantic_commit_phase_timings_s
        assert first_result.semantic_commit_strategy == "seed"
        assert semantic_timings["write_seed_snapshot_from_plan"] >= 0.0
        assert (
            semantic_timings["validate_projection_lane_head.skipped_trusted_seed"]
            == 0.0
        )
        assert "validate_projection_lane_head" not in semantic_timings
        assert any(
            key.startswith("ensure_ocg_seeded_lane.ocg_seed.")
            for key in semantic_timings
        )
        assert (
            "run_required_runtime_commit_reactions."
            "ensure_object_instance_graph_identity_lane_head_total_s"
        ) in semantic_timings
        assert (
            "run_required_runtime_commit_reactions.read_domain_commit"
            in semantic_timings
        )
        assert (
            "run_required_runtime_commit_reactions.ensure_oigi_lane_head"
            in semantic_timings
        )
        assert (
            "run_required_runtime_commit_reactions.dispatch_required_reactions"
            in semantic_timings
        )
        assert (
            "run_required_runtime_commit_reactions."
            "required_reaction_aware_meta_object_instance_graph_identity_history_upsert_total_s"
        ) in semantic_timings
        assert (
            "run_required_runtime_commit_reactions."
            "required_reaction_oigi_history_contract_check_s"
        ) in semantic_timings
        assert (
            "run_required_runtime_commit_reactions."
            "run_commit_reaction_oigi_project_history_direct_s"
        ) in semantic_timings
        assert (
            "run_required_runtime_commit_reactions."
            "run_commit_reaction_oigi_execute_history_handler_s"
        ) not in semantic_timings
        code_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="CodePackage",
        )
        object_config_graph_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ObjectConfigGraph",
        )
        object_config_graph_package_projection_hash = (
            find_meta_graph_projection_hash_by_name(
                index=index,
                projection_name="ObjectConfigGraphPackage",
            )
        )
        heads_before_reset_check = {
            projection_hash: await FSCommitStore().head(
                branch_id=first_result.package_branch_id,
                projection_hash=projection_hash,
            )
            for projection_hash in (
                code_package_projection_hash,
                object_config_graph_projection_hash,
                object_config_graph_package_projection_hash,
            )
        }
        assert (
            await _reset_invalid_package_branch_if_needed(
                index=index,
                branch_id=first_result.package_branch_id,
                projection_hashes=(
                    code_package_projection_hash,
                    object_config_graph_projection_hash,
                    object_config_graph_package_projection_hash,
                ),
            )
            is False
        )
        heads_after_reset_check = {
            projection_hash: await FSCommitStore().head(
                branch_id=first_result.package_branch_id,
                projection_hash=projection_hash,
            )
            for projection_hash in (
                code_package_projection_hash,
                object_config_graph_projection_hash,
                object_config_graph_package_projection_hash,
            )
        }
        assert heads_after_reset_check == heads_before_reset_check
        rerun = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )

        assert rerun.code_package.id == first_result.code_package.id
        assert rerun.object_config_graph.id == first_result.object_config_graph.id
        assert (
            rerun.object_config_graph_package.id
            == first_result.object_config_graph_package.id
        )
        assert rerun.code_package_commit_id is None
        assert (
            rerun.code_package_head_commit_id
            == first_result.code_package_head_commit_id
        )
        assert rerun.object_config_graph_commit_id is None
        assert (
            rerun.object_config_graph_object_instance_graph_commit_id
            == first_result.object_config_graph_object_instance_graph_commit_id
        )
        assert rerun.semantic_commit_strategy == "unchanged"
        assert (
            rerun.phase_timings_s["reuse_existing_object_config_graph_package_cache"]
            >= 0.0
        )
        assert any(
            key.startswith("reset_invalid_package_branch_if_needed.")
            and key.endswith(".read_commit_health")
            for key in rerun.phase_timings_s
        )
        assert any(
            key.startswith("reset_invalid_package_branch_if_needed.")
            and key.endswith(".read_snapshot_health")
            for key in rerun.phase_timings_s
        )
        assert not any(
            key.startswith("reset_invalid_package_branch_if_needed.")
            and key.endswith(".read_commit")
            for key in rerun.phase_timings_s
        )
        assert not any(
            key.startswith("reset_invalid_package_branch_if_needed.")
            and key.endswith(".read_snapshot")
            for key in rerun.phase_timings_s
        )


@pytest.mark.asyncio
async def test_materialize_object_config_graph_package_leaf_reuses_ocg_head_summary_without_hydration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_ocg_head_summary"
    workspace_root.mkdir(parents=True, exist_ok=True)
    aware_toml_path = _write_package_fixture(
        workspace_root=workspace_root,
        source_text="\n".join(
            [
                "class DemoRoot {",
                "    name String",
                "}",
                "",
                "projection DemoRoot {",
                "    root aware_demo.graph.config.DemoRoot",
                "}",
                "",
            ]
        ),
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_ocg_head_summary",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )
        branch_id = uuid4()

        first_result = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )

        cache_path = (
            materialization_service.object_config_graph_package_reuse_cache_path(
                aware_root=FSCommitStore().aware_root,
                branch_id=first_result.package_branch_id,
                object_config_graph_package_id=(
                    first_result.object_config_graph_package.id
                ),
            )
        )
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        cached_graph = first_result.object_config_graph.model_copy(deep=True)
        cached_graph.object_projection_graphs.append(
            materialization_service.ObjectProjectionGraph(
                id=uuid4(),
                object_config_graph_id=cached_graph.id,
                language=materialization_service.CodeLanguage.aware,
                name="DemoRoot",
                projection_hash="sha256:test:demo-root",
            )
        )
        payload["object_config_graph"] = cached_graph.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        )
        cache_path.write_text(
            json.dumps(payload, separators=(",", ":"), sort_keys=True),
            encoding="utf-8",
        )

        fingerprint_rerun = (
            await materialize_object_config_graph_package_leaf_from_manifest(
                runtime=runtime,
                index=index,
                actor_id=None,
                branch_id=branch_id,
                workspace_root=workspace_root,
                aware_toml_path=aware_toml_path,
            )
        )
        assert fingerprint_rerun.semantic_commit_strategy == "unchanged"
        assert {
            opg.name
            for opg in fingerprint_rerun.object_config_graph.object_projection_graphs
        } == set()
        assert (
            fingerprint_rerun.phase_timings_s[
                "reuse_existing_object_config_graph_package_cache."
                "miss.object_config_graph_payload_missing_namespace_evidence"
            ]
            == 0.0
        )

        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        payload["code_package_head_commit_id"] = str(uuid4())
        cache_path.write_text(
            json.dumps(payload, separators=(",", ":"), sort_keys=True),
            encoding="utf-8",
        )

        hydrated_root_types: list[type[Any]] = []
        original_hydrate = (
            materialization_service._hydrate_lane_root_from_head
        )  # noqa: SLF001

        async def record_hydration(**kwargs: Any) -> object | None:
            root_type = kwargs["root_type"]
            hydrated_root_types.append(root_type)
            if root_type is materialization_service.ObjectConfigGraph:
                raise AssertionError(
                    "ObjectConfigGraph hydration should be skipped when the "
                    "Meta package head summary proves the semantic graph hash"
                )
            return await original_hydrate(**kwargs)

        monkeypatch.setattr(
            materialization_service,
            "_hydrate_lane_root_from_head",
            record_hydration,
        )

        rerun = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )

        assert rerun.semantic_commit_strategy == "unchanged"
        assert materialization_service.CodePackage in hydrated_root_types
        assert materialization_service.ObjectConfigGraph not in hydrated_root_types
        assert "hydrate_existing_object_config_graph_from_head" not in (
            rerun.phase_timings_s
        )
        assert (
            rerun.phase_timings_s[
                "reuse_existing_object_config_graph_package_cache."
                "miss.code_package_head_commit_id_mismatch"
            ]
            == 0.0
        )
        assert (
            rerun.phase_timings_s["match_existing_object_config_graph_head_summary.ok"]
            == 0.0
        )


@pytest.mark.asyncio
async def test_materialize_object_config_graph_package_leaf_reseeds_changed_code_package_lane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_changed_code_package"
    workspace_root.mkdir(parents=True, exist_ok=True)
    aware_toml_path = _write_package_fixture(workspace_root=workspace_root)

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_changed_code_package",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_code_ontology.package.code_package import CodePackage  # noqa: WPS433
        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )
        branch_id = uuid4()

        first_result = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )
        _write(
            aware_toml_path.parent / "aware" / "graph" / "config" / "demo_root.aware",
            "class DemoRoot {\n    name String\n    label String?\n}\n",
        )

        async def unexpected_upsert_codes_from_text(
            self, relative_paths, content_texts, language=None
        ):  # noqa: ANN001
            raise AssertionError(
                "Meta CodePackage source reseed must not use the legacy "
                "upsert_codes_from_text runtime handler"
            )

        monkeypatch.setattr(
            CodePackage,
            "upsert_codes_from_text",
            unexpected_upsert_codes_from_text,
        )

        rerun = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )

        assert rerun.code_package.id == first_result.code_package.id
        assert rerun.object_config_graph.id == first_result.object_config_graph.id
        assert (
            rerun.object_config_graph_package.id
            == first_result.object_config_graph_package.id
        )
        assert (
            rerun.code_package_head_commit_id
            != first_result.code_package_head_commit_id
        )
        assert (
            rerun.phase_timings_s[
                "reset_package_branch_for_code_package_source_snapshot"
            ]
            >= 0.0
        )
        assert rerun.phase_timings_s["seed_code_package_sources_from_manifest"] >= 0.0
        assert "reset_route_incomplete_package_branch" not in rerun.phase_timings_s


@pytest.mark.asyncio
async def test_materialization_service_preflight_avoids_full_lane_materialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_cached_lane_helpers"
    workspace_root.mkdir(parents=True, exist_ok=True)
    aware_toml_path = _write_package_fixture(workspace_root=workspace_root)

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_cached_lane_helpers", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )
        from aware_meta.materialization import (
            service as materialization_service,
        )  # noqa: WPS433
        from aware_meta_ontology.graph.config.object_config_graph import (  # noqa: WPS433
            ObjectConfigGraph,
        )
        branch_id = uuid4()

        first_result = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )
        code_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="CodePackage",
        )
        object_config_graph_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ObjectConfigGraph",
        )
        object_config_graph_package_projection_hash = (
            find_meta_graph_projection_hash_by_name(
                index=index,
                projection_name="ObjectConfigGraphPackage",
            )
        )

        recorded_projection_hashes: list[str] = []
        original_cached_lane_materializer = (
            materialization_service.CachedLaneMaterializer
        )

        class RecordingCachedLaneMaterializer:
            def __init__(self) -> None:
                self._delegate = original_cached_lane_materializer()

            async def get(self, **kwargs: Any) -> tuple[object, object]:
                projection_hash = getattr(kwargs["opg"], "projection_hash", None)
                if not isinstance(projection_hash, str):
                    raise AssertionError(
                        "Expected projection hash while recording cached lane materializer usage"
                    )
                recorded_projection_hashes.append(projection_hash)
                return await self._delegate.get(**kwargs)

        monkeypatch.setattr(
            materialization_service,
            "CachedLaneMaterializer",
            RecordingCachedLaneMaterializer,
        )

        assert (
            await materialization_service._reset_invalid_package_branch_if_needed(
                index=index,
                branch_id=first_result.package_branch_id,
                projection_hashes=(
                    code_package_projection_hash,
                    object_config_graph_projection_hash,
                    object_config_graph_package_projection_hash,
                ),
            )
            is False
        )
        assert recorded_projection_hashes == []

        recorded_projection_hashes.clear()
        hydrated_graph = await materialization_service._hydrate_lane_root_from_head(
            index=index,
            branch_id=first_result.package_branch_id,
            projection_hash=object_config_graph_projection_hash,
            root_id=first_result.object_config_graph.id,
            root_type=ObjectConfigGraph,
        )
        assert hydrated_graph is not None
        assert hydrated_graph.id == first_result.object_config_graph.id
        assert recorded_projection_hashes == [object_config_graph_projection_hash]

        recorded_projection_hashes.clear()
        await materialization_service._validate_projection_lane_head(
            index=index,
            branch_id=first_result.package_branch_id,
            projection_hash=object_config_graph_projection_hash,
        )
        assert recorded_projection_hashes == [object_config_graph_projection_hash]


@pytest.mark.asyncio
async def test_materialize_object_config_graph_package_leaf_uses_direct_code_package_source_snapshots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_batch_upsert"
    workspace_root.mkdir(parents=True, exist_ok=True)
    aware_toml_path = _write_package_fixture(workspace_root=workspace_root)
    _write(
        workspace_root
        / "modules"
        / "demo"
        / "structure"
        / "ontology"
        / "aware"
        / "graph"
        / "config"
        / "demo_extra.aware",
        "class DemoExtra {\n    value String\n}\n",
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_batch_upsert", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_code_ontology.package.code_package import CodePackage  # noqa: WPS433
        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )

        async def unexpected_upsert_codes_from_text(
            self, relative_paths, content_texts, language=None
        ):  # noqa: ANN001
            raise AssertionError(
                "Meta full materialization must not invoke "
                "CodePackage.upsert_codes_from_text"
            )

        monkeypatch.setattr(
            CodePackage, "upsert_codes_from_text", unexpected_upsert_codes_from_text
        )
        branch_id = uuid4()
        result = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )

        assert result.phase_timings_s["seed_code_package_sources_from_manifest"] >= 0.0
        assert (
            "invoke_code_package_upsert_codes_from_text" not in result.phase_timings_s
        )
        assert result.code_package.manifest_relative_path == (
            "modules/demo/structure/ontology/aware.toml"
        )
        assert result.code_package.package_root == "modules/demo/structure/ontology"
        assert (
            result.code_package.sources_root == "modules/demo/structure/ontology/aware"
        )
        assert result.owned_file_paths == (
            "modules/demo/structure/ontology/aware/graph/config/demo_extra.aware",
            "modules/demo/structure/ontology/aware/graph/config/demo_root.aware",
        )
        _write(
            workspace_root
            / "modules"
            / "demo"
            / "structure"
            / "ontology"
            / "aware"
            / "graph"
            / "config"
            / "demo_extra.aware",
            "class DemoExtra {\n    value String\n    label String?\n}\n",
        )

        rerun = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )

        assert (
            rerun.phase_timings_s[
                "reset_package_branch_for_code_package_source_snapshot"
            ]
            >= 0.0
        )
        assert rerun.phase_timings_s["seed_code_package_sources_from_manifest"] >= 0.0
        assert "invoke_code_package_upsert_codes_from_text" not in rerun.phase_timings_s
        assert rerun.code_package_head_commit_id != result.code_package_head_commit_id


@pytest.mark.asyncio
async def test_materialize_object_config_graph_package_leaf_reseeds_sources_without_legacy_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_clean_runtime_source_snapshot"
    workspace_root.mkdir(parents=True, exist_ok=True)
    aware_toml_path = _write_package_fixture(workspace_root=workspace_root)
    _write(
        workspace_root
        / "modules"
        / "demo"
        / "structure"
        / "ontology"
        / "aware"
        / "graph"
        / "config"
        / "demo_extra.aware",
        "class DemoExtra {\n    value String\n}\n",
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_clean_runtime_source_snapshot",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_code_ontology.package.code_package import CodePackage  # noqa: WPS433
        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )
        branch_id = uuid4()
        result = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )

        _write(
            workspace_root
            / "modules"
            / "demo"
            / "structure"
            / "ontology"
            / "aware"
            / "graph"
            / "config"
            / "demo_extra.aware",
            "class DemoExtra {\n    value String\n    label String?\n}\n",
        )

        async def unexpected_upsert_codes_from_text(
            self, relative_paths, content_texts, language=None
        ):  # noqa: ANN001
            raise AssertionError(
                "clean semantic materialization must not invoke "
                "CodePackage.upsert_codes_from_text"
            )

        monkeypatch.setattr(
            CodePackage,
            "upsert_codes_from_text",
            unexpected_upsert_codes_from_text,
        )

        rerun = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=object(),
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )

        assert (
            rerun.phase_timings_s[
                "reset_package_branch_for_code_package_source_snapshot"
            ]
            >= 0.0
        )
        assert rerun.phase_timings_s["seed_code_package_sources_from_manifest"] >= 0.0
        assert "invoke_code_package_upsert_codes_from_text" not in rerun.phase_timings_s
        assert rerun.code_package_head_commit_id != result.code_package_head_commit_id


@pytest.mark.asyncio
async def test_materialize_object_config_graph_package_leaf_supports_multiple_packages_on_shared_parent_branch(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_multiple_packages"
    workspace_root.mkdir(parents=True, exist_ok=True)
    first_aware_toml_path = _write_package_fixture(workspace_root=workspace_root)
    second_aware_toml_path = _write_package_fixture(
        workspace_root=workspace_root,
        module_name="demo_b",
        package_name="demo-b-ontology",
        fqn_prefix="aware_demo_b",
        title="Demo B Ontology",
        description="Second demo Meta package leaf materialization fixture",
        class_name="DemoBRoot",
        source_relpath="graph/config/demo_b_root.aware",
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_multiple_packages", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )
        branch_id = uuid4()

        first_result = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=first_aware_toml_path,
        )
        second_result = (
            await materialize_object_config_graph_package_leaf_from_manifest(
                runtime=runtime,
                index=index,
                actor_id=None,
                branch_id=branch_id,
                workspace_root=workspace_root,
                aware_toml_path=second_aware_toml_path,
            )
        )

        assert first_result.code_package.id != second_result.code_package.id
        assert (
            first_result.object_config_graph.id != second_result.object_config_graph.id
        )
        assert (
            first_result.object_config_graph_package.id
            != second_result.object_config_graph_package.id
        )


@pytest.mark.asyncio
async def test_materialize_object_config_graph_package_leaf_accepts_dependency_external_graphs(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_external_graphs"
    workspace_root.mkdir(parents=True, exist_ok=True)
    dependency_aware_toml_path = _write_package_fixture(
        workspace_root=workspace_root,
        module_name="economy",
        package_name="economy-ontology",
        fqn_prefix="aware_economy",
        title="Economy Ontology",
        description="Dependency package for external graph materialization proof",
        class_name="Service",
        source_relpath="service/service.aware",
        source_text="class Service {\n    name String\n}\n",
    )
    dependent_aware_toml_path = _write_package_fixture(
        workspace_root=workspace_root,
        module_name="agent",
        package_name="agent-ontology",
        fqn_prefix="aware_agent",
        title="Agent Ontology",
        description="Dependent package for external graph materialization proof",
        class_name="InferenceService",
        source_relpath="inference/inference_service.aware",
        dependencies=("economy-ontology",),
        source_text="class InferenceService {\n    service aware_economy.service.Service\n}\n",
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_external_graphs", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )
        branch_id = uuid4()

        dependency_result = (
            await materialize_object_config_graph_package_leaf_from_manifest(
                runtime=runtime,
                index=index,
                actor_id=None,
                branch_id=branch_id,
                workspace_root=workspace_root,
                aware_toml_path=dependency_aware_toml_path,
            )
        )
        dependent_result = (
            await materialize_object_config_graph_package_leaf_from_manifest(
                runtime=runtime,
                index=index,
                actor_id=None,
                branch_id=branch_id,
                workspace_root=workspace_root,
                aware_toml_path=dependent_aware_toml_path,
                external_graphs=[dependency_result.object_config_graph],
            )
        )

        assert (
            dependency_result.object_config_graph.id
            != dependent_result.object_config_graph.id
        )
        assert dependent_result.object_config_graph.hash != _EMPTY_OCG_HASH


@pytest.mark.asyncio
async def test_materialize_object_config_graph_package_leaf_resets_invalid_existing_package_branch(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_invalid_branch_reset"
    workspace_root.mkdir(parents=True, exist_ok=True)
    aware_toml_path = _write_package_fixture(workspace_root=workspace_root)

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_invalid_branch_reset", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_meta.graph.instance.commit.fs_store import (  # noqa: WPS433
            FSCommitStore,
            FSSnapshotStore,
        )
        from aware_meta.graph.instance.commit.materialization_cache import (  # noqa: WPS433
            CachedLaneMaterializer,
            get_shared_materialization_cache,
        )
        from aware_meta.graph.instance.validator_opg import (  # noqa: WPS433
            OigValidationError,
            validate_object_instance_graph_against_opg,
        )
        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
            stable_object_config_graph_package_branch_id,
        )
        branch_id = uuid4()

        code_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="CodePackage",
        )

        package_branch_id = stable_object_config_graph_package_branch_id(
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
            package_name="demo-ontology",
            fqn_prefix="aware_demo",
        )
        first_result = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
            package_branch_id=package_branch_id,
        )

        assert first_result.package_branch_id == package_branch_id
        head = await FSCommitStore().head(
            branch_id=package_branch_id,
            projection_hash=code_package_projection_hash,
        )
        if head is None:
            raise AssertionError(
                "Expected CodePackage HEAD after initial materialization"
            )
        head_commit_raw = head.get("commit_id")
        if not isinstance(head_commit_raw, str):
            raise AssertionError("Expected CodePackage HEAD commit id")
        head_commit_id = UUID(head_commit_raw)
        materialized_oig, _ = await CachedLaneMaterializer().get(
            branch_id=package_branch_id,
            ocg=index.ocg,
            opg=index.opg_by_hash[code_package_projection_hash],
            commit_id=head_commit_id,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        validate_object_instance_graph_against_opg(
            graph=materialized_oig,
            object_config_graph=index.ocg,
            object_projection_graph=index.opg_by_hash[code_package_projection_hash],
        )

        snapshots_root = (
            FSSnapshotStore().aware_root
            / ".aware"
            / "oig"
            / str(package_branch_id)
            / code_package_projection_hash
            / "snapshots"
        )
        snapshot_path = snapshots_root / f"{head_commit_id}.json"
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        payload["class_instance_relationships"] = []
        snapshot_path.write_text(
            json.dumps(payload, separators=(",", ":"), sort_keys=True),
            encoding="utf-8",
        )
        get_shared_materialization_cache().invalidate_lane(
            branch_id=package_branch_id,
            projection_hash=code_package_projection_hash,
        )

        with pytest.raises(OigValidationError):
            corrupted_oig, _ = await CachedLaneMaterializer().get(
                branch_id=package_branch_id,
                ocg=index.ocg,
                opg=index.opg_by_hash[code_package_projection_hash],
                commit_id=head_commit_id,
                attribute_configs_by_id=index.attribute_configs_by_id,
                class_configs_by_id=index.class_configs_by_id,
            )
            validate_object_instance_graph_against_opg(
                graph=corrupted_oig,
                object_config_graph=index.ocg,
                object_projection_graph=index.opg_by_hash[code_package_projection_hash],
            )

        rerun = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
            package_branch_id=package_branch_id,
        )

        assert rerun.code_package.id == first_result.code_package.id
        assert rerun.object_config_graph.id == first_result.object_config_graph.id
        assert (
            rerun.object_config_graph_package.id
            == first_result.object_config_graph_package.id
        )
        assert (
            rerun.code_package_head_commit_id
            != first_result.code_package_head_commit_id
        )

        rebuilt_head = await FSCommitStore().head(
            branch_id=package_branch_id,
            projection_hash=code_package_projection_hash,
        )
        if rebuilt_head is None:
            raise AssertionError(
                "Expected rebuilt CodePackage head after invalid branch reset"
            )
        rebuilt_commit_id = rebuilt_head.get("commit_id")
        if not isinstance(rebuilt_commit_id, str):
            raise AssertionError("Expected rebuilt CodePackage HEAD commit id")
        assert rebuilt_commit_id != str(head_commit_id)

        repaired_oig, _ = await CachedLaneMaterializer().get(
            branch_id=package_branch_id,
            ocg=index.ocg,
            opg=index.opg_by_hash[code_package_projection_hash],
            commit_id=UUID(rebuilt_commit_id),
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        validate_object_instance_graph_against_opg(
            graph=repaired_oig,
            object_config_graph=index.ocg,
            object_projection_graph=index.opg_by_hash[code_package_projection_hash],
        )


@pytest.mark.asyncio
async def test_materialize_object_config_graph_package_leaf_recovers_stale_compiler_owned_ocgi_lane(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "workspace_meta_leaf_stale_ocgi_lane"
    workspace_root.mkdir(parents=True, exist_ok=True)
    aware_toml_path = _write_package_fixture(workspace_root=workspace_root)

    with IsolatedAwareRoot(
        tmp_path / "aware_root_meta_leaf_stale_ocgi_lane", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        index = _meta_runtime_index(runtime)

        from aware_meta.graph.config.lane import (  # noqa: WPS433
            ensure_graph_identity_seeded_lane,
            preview_graph_identity_seed_plan,
        )
        from aware_meta.graph.instance.commit.materialization_cache import (  # noqa: WPS433
            get_shared_materialization_cache,
        )
        from aware_meta.materialization import (  # noqa: WPS433
            materialize_object_config_graph_package_leaf_from_manifest,
        )
        branch_id = uuid4()

        first_result = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )
        ocgi = index.ocg.object_config_graph_identity
        if ocgi is None:
            raise AssertionError("Expected runtime index ObjectConfigGraphIdentity")

        seed_plan = await preview_graph_identity_seed_plan(
            root_instance=ocgi,
            ocg=index.ocg,
            branch_id=ocgi.id,
            opg_name="ObjectConfigGraphIdentity",
        )
        if seed_plan.commit_id is None or not seed_plan.graph_hash_post:
            raise AssertionError(
                "Expected deterministic identity seed plan for ObjectConfigGraphIdentity"
            )
        _ = await ensure_graph_identity_seeded_lane(
            root_instance=ocgi,
            ocg=index.ocg,
            branch_id=ocgi.id,
            opg_name="ObjectConfigGraphIdentity",
        )

        lane_root = (
            FSCommitStore().aware_root
            / ".aware"
            / "oig"
            / str(ocgi.id)
            / str(seed_plan.projection_hash)
        )
        head_path = lane_root / "HEAD.json"
        commit_path = lane_root / "commits" / f"{seed_plan.commit_id}.json"
        corrupted_hash = "0" * 64

        head_payload = json.loads(head_path.read_text(encoding="utf-8"))
        head_payload["graph_hash_post"] = corrupted_hash
        head_path.write_text(
            json.dumps(head_payload, separators=(",", ":"), sort_keys=True),
            encoding="utf-8",
        )

        commit_payload = json.loads(commit_path.read_text(encoding="utf-8"))
        commit_payload["graph_hash_post"] = corrupted_hash
        commit_path.write_text(
            json.dumps(commit_payload, separators=(",", ":"), sort_keys=True),
            encoding="utf-8",
        )
        get_shared_materialization_cache().invalidate_lane(
            branch_id=ocgi.id,
            projection_hash=str(seed_plan.projection_hash),
        )

        corrupted_head = await FSCommitStore().head(
            branch_id=ocgi.id,
            projection_hash=str(seed_plan.projection_hash),
        )
        if corrupted_head is None:
            raise AssertionError(
                "Expected corrupted ObjectConfigGraphIdentity HEAD before rerun"
            )
        assert corrupted_head["graph_hash_post"] == corrupted_hash

        rerun = await materialize_object_config_graph_package_leaf_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            branch_id=branch_id,
            workspace_root=workspace_root,
            aware_toml_path=aware_toml_path,
        )

        repaired_head = await FSCommitStore().head(
            branch_id=ocgi.id,
            projection_hash=str(seed_plan.projection_hash),
        )
        if repaired_head is None:
            raise AssertionError(
                "Expected repaired ObjectConfigGraphIdentity HEAD after rerun"
            )
        assert repaired_head["commit_id"] == str(seed_plan.commit_id)
        assert repaired_head["graph_hash_post"] == seed_plan.graph_hash_post
        assert rerun.object_config_graph.id == first_result.object_config_graph.id
        assert (
            rerun.object_config_graph_package.id
            == first_result.object_config_graph_package.id
        )
