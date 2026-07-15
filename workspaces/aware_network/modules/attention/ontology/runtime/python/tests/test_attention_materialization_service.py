from __future__ import annotations

import ast
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from aware_attention_ontology.attention.attention_package import AttentionPackage
from aware_attention_ontology.layout.layout import Layout
from aware_attention_ontology.layout.layout_config import LayoutConfig
from aware_attention_ontology.section.section import Section
from aware_attention_ontology.stable_ids import (
    stable_attention_package_id,
    stable_layout_config_id,
    stable_layout_config_section_config_id,
    stable_layout_id,
    stable_layout_section_id,
    stable_section_config_id,
    stable_section_id,
)
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
)
from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)

_RUNTIME_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _RUNTIME_ROOT.parents[6]
for _path in (_REPO_ROOT, _RUNTIME_ROOT):
    _path_str = str(_path)
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_attention.materialization import service as attention_materialization_service

_TEST_NS = uuid5(NAMESPACE_URL, "aware:test:attention-materialization-service")


class _NoOpRuntime:
    manifest_path: Path = Path(".")

    @property
    def invoker(self) -> "_RecordingInvoker":
        raise AssertionError("No-op runtime invoker should not be used")


class _RecordingInvoker:
    def __init__(self) -> None:
        self.requests: list[MetaGraphInvokeFunctionRequest] = []

    async def invoke_function_with_index(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse:
        _ = index
        self.requests.append(request)
        sequence = len(self.requests)
        commit_id = _uid(f"commit:{sequence}")
        return MetaGraphInvokeFunctionResponse(
            actor_id=request.actor_id,
            domain_branch_id=request.domain_branch_id,
            domain_projection_hash=request.domain_projection_hash,
            status="succeeded",
            root_object_id=request.target_object_id or _uid(f"root:{sequence}"),
            graph_hash_pre=request.expected_graph_hash_pre,
            graph_hash_post=f"graph-hash-{sequence}",
            domain_commit_id=commit_id,
            object_instance_graph_commit_id=commit_id,
        )


class _RecordingRuntime:
    manifest_path: Path = Path(".")

    def __init__(self) -> None:
        self.invoker = _RecordingInvoker()


class _ExistingPackageInvoker(_RecordingInvoker):
    async def invoke_function_with_index(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse:
        if request.call_target is MetaGraphFunctionCallTarget.instance:
            _ = index
            self.requests.append(request)
            return MetaGraphInvokeFunctionResponse(
                actor_id=request.actor_id,
                domain_branch_id=request.domain_branch_id,
                domain_projection_hash=request.domain_projection_hash,
                status="succeeded",
                root_object_id=request.target_object_id,
                graph_hash_pre=request.expected_graph_hash_pre,
                graph_hash_post=request.expected_graph_hash_pre,
            )
        return await super().invoke_function_with_index(index=index, request=request)


class _ExistingPackageRuntime:
    manifest_path: Path = Path(".")

    def __init__(self) -> None:
        self.invoker = _ExistingPackageInvoker()


def _index_stub() -> MetaGraphRuntimeIndex:
    return cast(MetaGraphRuntimeIndex, object())


def _uid(name: str) -> UUID:
    return uuid5(_TEST_NS, name)


@pytest.mark.asyncio
async def test_attention_lane_replay_failure_resets_exact_generated_lane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = _uid("stale-attention-lane")
    projection_hash = "projection:AttentionPackage"
    lane_dir = tmp_path / ".aware" / "oig" / str(branch_id) / projection_hash
    lane_dir.mkdir(parents=True)
    (lane_dir / "HEAD.json").write_text("{}", encoding="utf-8")
    invalidated: list[tuple[UUID, str]] = []

    class _Cache:
        def invalidate_lane(self, *, branch_id: UUID, projection_hash: str) -> None:
            invalidated.append((branch_id, projection_hash))

    async def _raise_replay_error(**_: object) -> object:
        raise ValueError("OIG commit envelope branch mismatch")

    monkeypatch.setattr(
        attention_materialization_service,
        "_load_attention_root_lane_head",
        _raise_replay_error,
    )
    monkeypatch.setattr(
        attention_materialization_service,
        "get_shared_materialization_cache",
        lambda: _Cache(),
    )

    result = await attention_materialization_service._load_attention_root_lane_head_with_recovery(
        index=_index_stub(),
        target=attention_materialization_service._ProjectionInvokeTarget(
            object_projection_graph_id=_uid("attention-package-opg"),
            projection_hash=projection_hash,
            constructor_function_id=_uid("attention-package-constructor"),
        ),
        branch_id=branch_id,
        root_type=AttentionPackage,
        aware_root=tmp_path,
    )

    assert result is None
    assert not lane_dir.exists()
    assert invalidated == [(branch_id, projection_hash)]


def _attention_index() -> MetaGraphRuntimeIndex:
    nodes = []
    opgs = []

    def add_projection(
        *,
        projection_name: str,
        class_name: str,
        constructor_name: str,
        instance_function_names: tuple[str, ...] = (),
    ) -> None:
        constructor_function = SimpleNamespace(
            id=_uid(f"function:{projection_name}:{constructor_name}"),
            name=constructor_name,
        )
        constructor_link = SimpleNamespace(
            id=_uid(f"link:{projection_name}:{constructor_name}"),
            function_config_id=constructor_function.id,
            function_config=constructor_function,
            is_public=True,
        )
        function_links = [constructor_link]
        nodes.append(
            SimpleNamespace(
                type=ObjectConfigGraphNodeType.function,
                function_config=constructor_function,
                class_config=None,
            )
        )
        for function_name in instance_function_names:
            function = SimpleNamespace(
                id=_uid(f"function:{projection_name}:{function_name}"),
                name=function_name,
            )
            function_links.append(
                SimpleNamespace(
                    id=_uid(f"link:{projection_name}:{function_name}"),
                    function_config_id=function.id,
                    function_config=function,
                    is_public=True,
                )
            )
            nodes.append(
                SimpleNamespace(
                    type=ObjectConfigGraphNodeType.function,
                    function_config=function,
                    class_config=None,
                )
            )
        nodes.append(
            SimpleNamespace(
                type=ObjectConfigGraphNodeType.class_,
                function_config=None,
                class_config=SimpleNamespace(
                    id=_uid(f"class:{projection_name}"),
                    name=class_name,
                    class_config_function_configs=function_links,
                ),
            )
        )
        opgs.append(
            SimpleNamespace(
                id=_uid(f"opg:{projection_name}"),
                name=projection_name,
                projection_hash=f"projection:{projection_name}",
                object_projection_graph_constructors=[
                    SimpleNamespace(function_constructor_id=constructor_link.id)
                ],
            )
        )

    add_projection(
        projection_name="AttentionPackage",
        class_name="aware_attention_ontology.attention.attention_package.AttentionPackage",
        constructor_name="build",
        instance_function_names=("attach_layout_config",),
    )
    add_projection(
        projection_name="LayoutConfig",
        class_name="aware_attention_ontology.layout.layout_config.LayoutConfig",
        constructor_name="build",
        instance_function_names=("add_section_config",),
    )
    add_projection(
        projection_name="LayoutConfigSectionConfig",
        class_name=(
            "aware_attention_ontology.layout.layout_config_section_config."
            "LayoutConfigSectionConfig"
        ),
        constructor_name="create_via_layout_config",
        instance_function_names=("set_geometry", "set_visibility"),
    )
    add_projection(
        projection_name="Layout",
        class_name="aware_attention_ontology.layout.layout.Layout",
        constructor_name="build",
        instance_function_names=("add_section",),
    )
    add_projection(
        projection_name="Section",
        class_name="aware_attention_ontology.section.section.Section",
        constructor_name="build",
    )
    add_projection(
        projection_name="LayoutSection",
        class_name="aware_attention_ontology.layout.layout_section.LayoutSection",
        constructor_name="create_via_layout",
        instance_function_names=("set_geometry", "set_visibility"),
    )
    return cast(
        MetaGraphRuntimeIndex,
        cast(
            object,
            SimpleNamespace(
                ocg=SimpleNamespace(
                    object_projection_graphs=opgs,
                    object_config_graph_nodes=nodes,
                )
            ),
        ),
    )


def _lane() -> MaterializationLaneContext:
    return MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash="attention_projection_hash",
    )


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def test_attention_materialization_service_uses_meta_runtime_contracts() -> None:
    service_path = Path(attention_materialization_service.__file__).resolve()

    assert "aware_runtime" not in _import_roots(service_path)
    assert "aware_environment_service_dto" not in _import_roots(service_path)


def test_load_attention_compile_plan_payloads_reads_runtime_artifacts(
    tmp_path: Path,
) -> None:
    compile_plan_path = (
        tmp_path
        / ".aware"
        / "attention"
        / "runtime"
        / "attention_layout_workspace"
        / "attention.compile_plan.json"
    )
    compile_plan_path.parent.mkdir(parents=True, exist_ok=True)
    _ = compile_plan_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "layout_ontology": [],
            }
        ),
        encoding="utf-8",
    )

    payloads = attention_materialization_service.load_attention_compile_plan_payloads(
        repo_root=tmp_path
    )

    assert len(payloads) == 1
    assert payloads[0]["schema_version"] == 1


@pytest.mark.asyncio
async def test_materialize_attention_compile_plan_ontology_returns_none_without_payloads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        attention_materialization_service, "_find_repo_root", lambda *, start: tmp_path
    )

    receipt = await attention_materialization_service.materialize_attention_compile_plan_ontology(
        runtime=_NoOpRuntime(),
        index=_index_stub(),
        actor_id=None,
        lane=_lane(),
    )

    assert receipt is None


@pytest.mark.asyncio
async def test_materialize_attention_compile_plan_ontology_materializes_layout_sections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout_key = "coordination_center"
    conversation_key = "conversation"
    work_item_key = "work_item"
    layout_config_id = stable_layout_config_id(key=layout_key)
    conversation_layout_config_section_config_id = (
        stable_layout_config_section_config_id(
            layout_config_id=layout_config_id,
            section_key=conversation_key,
        )
    )
    work_item_layout_config_section_config_id = stable_layout_config_section_config_id(
        layout_config_id=layout_config_id,
        section_key=work_item_key,
    )
    compile_plan_path = (
        tmp_path
        / ".aware"
        / "attention"
        / "runtime"
        / "attention_layout_workspace"
        / "attention.compile_plan.json"
    )
    compile_plan_path.parent.mkdir(parents=True, exist_ok=True)
    _ = compile_plan_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package_name": "attention_layout_workspace",
                "attention_package_id": str(
                    stable_attention_package_id(name="attention_layout_workspace")
                ),
                "source_files": ["aware_workspace_shell.aware"],
                "layout_ontology": [
                    {
                        "layout_config_id": str(layout_config_id),
                        "layout_key": layout_key,
                        "title": "Coordination Center",
                        "description": None,
                        "frame_mode": "default",
                        "sections": [
                            {
                                "layout_config_section_config_id": str(
                                    conversation_layout_config_section_config_id
                                ),
                                "section_config_id": str(
                                    stable_section_config_id(
                                        layout_config_section_config_id=(
                                            conversation_layout_config_section_config_id
                                        ),
                                        key=conversation_key,
                                    )
                                ),
                                "section_key": conversation_key,
                                "title": "Conversation",
                                "description": None,
                                "order": 0,
                                "flex": 0.9,
                                "is_visible": True,
                            },
                            {
                                "layout_config_section_config_id": str(
                                    work_item_layout_config_section_config_id
                                ),
                                "section_config_id": str(
                                    stable_section_config_id(
                                        layout_config_section_config_id=(
                                            work_item_layout_config_section_config_id
                                        ),
                                        key=work_item_key,
                                    )
                                ),
                                "section_key": work_item_key,
                                "title": "Work Item",
                                "description": "Selected issue work unit",
                                "order": 2,
                                "flex": 1.2,
                                "is_visible": False,
                            },
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        attention_materialization_service, "_find_repo_root", lambda *, start: tmp_path
    )

    async def _missing_package_head(**_: object):
        return None

    monkeypatch.setattr(
        attention_materialization_service,
        "_load_attention_package_lane_head",
        _missing_package_head,
    )
    monkeypatch.setattr(
        attention_materialization_service,
        "_load_attention_root_lane_head",
        _missing_package_head,
    )
    runtime = _RecordingRuntime()

    receipt = await attention_materialization_service.materialize_attention_compile_plan_ontology(
        runtime=runtime,
        index=_attention_index(),
        actor_id=None,
        lane=_lane(),
    )

    assert receipt is not None
    assert receipt.status == "succeeded"
    assert (
        receipt.pipeline_id
        == "attention.compile_plan.layout_section.materialization.v0"
    )
    assert len(receipt.steps) == 1
    assert receipt.steps[0].details["layout_key"] == layout_key
    assert receipt.steps[0].details["sections_materialized"] == 2
    assert receipt.steps[0].details["invoke_count"] == 18

    requests = runtime.invoker.requests
    assert len(requests) == 18
    package_build = requests[0]
    assert package_build.call_target == MetaGraphFunctionCallTarget.opg_constructor
    assert package_build.domain_projection_hash == "projection:AttentionPackage"
    assert package_build.domain_branch_id == stable_attention_package_id(
        name="attention_layout_workspace"
    )
    assert package_build.kwargs["name"] == "attention_layout_workspace"
    layout_config_build = requests[1]
    assert layout_config_build.domain_projection_hash == "projection:LayoutConfig"
    assert layout_config_build.domain_branch_id == layout_config_id
    package_attach = next(
        request
        for request in requests
        if request.call_target is MetaGraphFunctionCallTarget.instance
        and request.domain_projection_hash == "projection:AttentionPackage"
        and request.kwargs.get("layout_config_id") == str(layout_config_id)
    )
    assert package_attach.domain_branch_id == stable_attention_package_id(
        name="attention_layout_workspace"
    )
    assert package_attach.expected_head_commit_id is not None
    layout_config_section_config = next(
        request
        for request in requests
        if request.call_target is MetaGraphFunctionCallTarget.instance
        and request.domain_projection_hash == "projection:LayoutConfig"
        and request.target_object_id == layout_config_id
        and request.kwargs.get("section_key") == conversation_key
    )
    assert layout_config_section_config.domain_branch_id == layout_config_id
    layout_section_adds = [
        request
        for request in requests
        if request.call_target == MetaGraphFunctionCallTarget.instance
        and request.domain_projection_hash == "projection:Layout"
        and request.target_object_id == stable_layout_id(key=layout_key)
        and "section_id" in request.kwargs
    ]
    layout_section_matches = [
        request
        for request in layout_section_adds
        if request.kwargs.get("section_id") == str(stable_section_id(key=work_item_key))
    ]
    assert layout_section_matches, [
        dict(request.kwargs) for request in layout_section_adds
    ]
    layout_section_add = layout_section_matches[0]
    assert layout_section_add.domain_branch_id == stable_layout_id(key=layout_key)
    assert layout_section_add.kwargs["title"] == "Work Item"
    work_item_section_build = next(
        request
        for request in requests
        if request.call_target == MetaGraphFunctionCallTarget.opg_constructor
        and request.domain_projection_hash == "projection:Section"
        and request.kwargs.get("key") == work_item_key
    )
    assert work_item_section_build.domain_branch_id == stable_section_id(
        key=work_item_key
    )

    work_item_layout_section_id = stable_layout_section_id(
        layout_id=stable_layout_id(key=layout_key),
        section_id=stable_section_id(key=work_item_key),
    )
    layout_section_geometry = next(
        request
        for request in requests
        if request.call_target is MetaGraphFunctionCallTarget.instance
        and request.domain_projection_hash == "projection:Layout"
        and request.target_object_id == work_item_layout_section_id
        and "order" in request.kwargs
    )
    assert layout_section_geometry.kwargs["order"] == 2
    assert layout_section_geometry.kwargs["flex"] == 1.2
    layout_section_visibility = next(
        request
        for request in requests
        if request.call_target is MetaGraphFunctionCallTarget.instance
        and request.domain_projection_hash == "projection:Layout"
        and request.target_object_id == work_item_layout_section_id
        and "is_visible" in request.kwargs
    )
    assert layout_section_visibility.kwargs["is_visible"] is False
    assert layout_section_visibility.expected_head_commit_id is not None


@pytest.mark.asyncio
async def test_materialize_attention_layout_spec_reuses_existing_package_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_name = "attention_layout_workspace"
    package_id = stable_attention_package_id(name=package_name)
    layout_key = "coordination_center"
    layout_config_id = stable_layout_config_id(key=layout_key)
    section_key = "conversation"
    section_config_id = stable_layout_config_section_config_id(
        layout_config_id=layout_config_id,
        section_key=section_key,
    )
    spec = attention_materialization_service._AttentionLayoutSpec(
        package_name=package_name,
        attention_package_id=package_id,
        layout_config_id=layout_config_id,
        layout_id=stable_layout_id(key=layout_key),
        layout_key=layout_key,
        title="Coordination Center",
        description=None,
        sections=(
            attention_materialization_service._AttentionLayoutSectionSpec(
                layout_config_section_config_id=section_config_id,
                section_config_id=stable_section_config_id(
                    layout_config_section_config_id=section_config_id,
                    key=section_key,
                ),
                section_id=stable_section_id(key=section_key),
                section_key=section_key,
                title="Conversation",
                description=None,
                order=0,
                flex=1.0,
                is_visible=True,
            ),
        ),
    )
    existing_commit_id = _uid("existing-package-head")
    existing_graph_hash = "existing-package-graph-hash"

    async def _existing_package_head(**_: object):
        return attention_materialization_service._AttentionPackageLaneHead(
            commit_id=existing_commit_id,
            graph_hash_post=existing_graph_hash,
            root=AttentionPackage(id=package_id, name=package_name),
        )

    async def _existing_root_head(
        *,
        branch_id: UUID,
        root_type: type,
        **_: object,
    ):
        if root_type is LayoutConfig:
            root = LayoutConfig(
                id=branch_id,
                key=layout_key,
                title="Coordination Center",
                description=None,
            )
        elif root_type is Layout:
            root = Layout(
                id=branch_id,
                key=layout_key,
                title="Coordination Center",
                description=None,
            )
        elif root_type is Section:
            root = Section(
                id=branch_id,
                key=section_key,
                title="Conversation",
                description=None,
            )
        else:  # pragma: no cover - focused test guard
            raise AssertionError(f"Unexpected root type: {root_type}")
        return attention_materialization_service._AttentionRootLaneHead(
            commit_id=_uid(f"existing-root:{branch_id}"),
            graph_hash_post=f"existing-root-graph-hash:{branch_id}",
            root=root,
        )

    monkeypatch.setattr(
        attention_materialization_service,
        "_load_attention_package_lane_head",
        _existing_package_head,
    )
    monkeypatch.setattr(
        attention_materialization_service,
        "_load_attention_root_lane_head",
        _existing_root_head,
    )
    index = _attention_index()
    runtime = _ExistingPackageRuntime()

    receipt = await attention_materialization_service._materialize_attention_layout_spec(
        runtime=runtime,
        index=index,
        actor_id=None,
        lane=_lane(),
        lane_state={},
        targets=attention_materialization_service._resolve_attention_runtime_targets(
            index=index
        ),
        spec=spec,
        materialize_package=True,
    )

    requests = runtime.invoker.requests
    assert not any(
        request.call_target is MetaGraphFunctionCallTarget.opg_constructor
        for request in requests
    )
    package_attach = next(
        request
        for request in requests
        if request.call_target is MetaGraphFunctionCallTarget.instance
        and request.domain_projection_hash == "projection:AttentionPackage"
    )
    assert package_attach.expected_head_commit_id == existing_commit_id
    assert package_attach.expected_graph_hash_pre == existing_graph_hash
    assert receipt.details["attention_package_materialized"] is False
    assert receipt.details["attention_package_reused"] is True
    assert receipt.details["attention_package_head_commit_id"] == str(
        existing_commit_id
    )
    assert receipt.details["attention_package_graph_hash"] == existing_graph_hash
    assert receipt.details["layout_config_reused"] is True
    assert receipt.details["layout_reused"] is True
    assert receipt.details["section_roots_reused"] == 1
    assert receipt.details["invoke_count"] == 7


@pytest.mark.asyncio
async def test_materialize_attention_compile_plan_ontology_filters_package_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    compile_plan_path = (
        tmp_path
        / ".aware"
        / "attention"
        / "runtime"
        / "attention_layout_workspace"
        / "attention.compile_plan.json"
    )
    compile_plan_path.parent.mkdir(parents=True, exist_ok=True)
    _ = compile_plan_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package_name": "attention_layout_workspace",
                "attention_package_id": str(
                    stable_attention_package_id(name="attention_layout_workspace")
                ),
                "source_files": ["aware_workspace_shell.aware"],
                "layout_ontology": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        attention_materialization_service, "_find_repo_root", lambda *, start: tmp_path
    )

    receipt = await attention_materialization_service.materialize_attention_compile_plan_ontology(
        runtime=_RecordingRuntime(),
        index=_attention_index(),
        actor_id=None,
        lane=_lane(),
        package_name="different_package",
    )

    assert receipt is None


@pytest.mark.asyncio
async def test_materialize_attention_compile_plan_ontology_fails_on_incomplete_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    compile_plan_path = (
        tmp_path
        / ".aware"
        / "attention"
        / "runtime"
        / "attention_layout_workspace"
        / "attention.compile_plan.json"
    )
    compile_plan_path.parent.mkdir(parents=True, exist_ok=True)
    _ = compile_plan_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package_name": "attention_layout_workspace",
                "attention_package_id": str(
                    stable_attention_package_id(name="attention_layout_workspace")
                ),
                "layout_ontology": [],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        attention_materialization_service, "_find_repo_root", lambda *, start: tmp_path
    )

    with pytest.raises(RuntimeError, match="layout_ontology must contain"):
        _ = await attention_materialization_service.materialize_attention_compile_plan_ontology(
            runtime=_RecordingRuntime(),
            index=_attention_index(),
            actor_id=None,
            lane=_lane(),
        )
