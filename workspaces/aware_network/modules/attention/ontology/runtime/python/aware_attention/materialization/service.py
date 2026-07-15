from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
from typing import Any, Protocol, cast
from uuid import UUID

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
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    get_shared_materialization_cache,
)
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
)
from aware_meta_service_dto.graph.instance.function_call_target import (
    MetaGraphFunctionCallTarget,
)
from aware_meta.materialization import (
    MaterializationLaneContext,
    MaterializationRunReceipt,
    MaterializationStepReceipt,
)
from aware_meta.materialization.receipts import utc_now_iso
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_orm.models.orm_model import ORMModel
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_types import JsonArray, JsonObject
from aware_utils.logging import logger


@dataclass(frozen=True, slots=True)
class _AttentionLayoutSectionSpec:
    layout_config_section_config_id: UUID
    section_config_id: UUID
    section_id: UUID
    section_key: str
    title: str
    description: str | None
    order: int
    flex: float
    is_visible: bool


@dataclass(frozen=True, slots=True)
class _AttentionLayoutSpec:
    package_name: str
    attention_package_id: UUID
    layout_config_id: UUID
    layout_id: UUID
    layout_key: str
    title: str
    description: str | None
    sections: tuple[_AttentionLayoutSectionSpec, ...]


@dataclass(frozen=True, slots=True)
class _ProjectionInvokeTarget:
    object_projection_graph_id: UUID
    projection_hash: str
    constructor_function_id: UUID


@dataclass(frozen=True, slots=True)
class _AttentionPackageLaneHead:
    commit_id: UUID
    graph_hash_post: str
    root: AttentionPackage


@dataclass(frozen=True, slots=True)
class _AttentionRootLaneHead:
    commit_id: UUID
    graph_hash_post: str
    root: ORMModel


@dataclass(frozen=True, slots=True)
class _AttentionRuntimeTargets:
    attention_package: _ProjectionInvokeTarget
    attention_package_attach_layout_config_function_id: UUID
    layout_config: _ProjectionInvokeTarget
    layout_config_add_section_config_function_id: UUID
    layout_config_section_config_set_geometry_function_id: UUID
    layout_config_section_config_set_visibility_function_id: UUID
    layout: _ProjectionInvokeTarget
    layout_add_section_function_id: UUID
    section: _ProjectionInvokeTarget
    layout_section_set_geometry_function_id: UUID
    layout_section_set_visibility_function_id: UUID


class _RuntimeInvokerProtocol(Protocol):
    async def invoke_function_with_index(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        request: MetaGraphInvokeFunctionRequest,
    ) -> MetaGraphInvokeFunctionResponse: ...


class _RuntimeProtocol(Protocol):
    @property
    def manifest_path(self) -> Path: ...

    @property
    def invoker(self) -> _RuntimeInvokerProtocol: ...


def load_attention_compile_plan_payloads(*, repo_root: Path) -> list[dict[str, object]]:
    runtime_root = (repo_root / ".aware" / "attention" / "runtime").resolve()
    if not runtime_root.exists() or not runtime_root.is_dir():
        return []

    payloads: list[dict[str, object]] = []
    for compile_plan_path in sorted(runtime_root.glob("*/attention.compile_plan.json")):
        if not compile_plan_path.is_file():
            continue
        try:
            payload_obj = cast(
                object,
                json.loads(compile_plan_path.read_text(encoding="utf-8") or "{}"),
            )
        except Exception as exc:  # pragma: no cover - defensive adapter
            raise RuntimeError(
                f"Invalid attention compile plan at {compile_plan_path}: {exc}"
            ) from exc
        payload_map = _expect_mapping(
            payload_obj, field_name=f"{compile_plan_path}:root"
        )
        payloads.append(dict(payload_map))
    return payloads


async def materialize_attention_compile_plan_ontology(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    aware_root: Path | None = None,
    lane: MaterializationLaneContext,
    package_name: str | None = None,
) -> MaterializationRunReceipt | None:
    repo_root = _find_repo_root(start=runtime.manifest_path.parent)
    compile_plan_payloads = load_attention_compile_plan_payloads(repo_root=repo_root)
    if package_name is not None and package_name.strip():
        package_name_filter = package_name.strip()
        compile_plan_payloads = [
            payload
            for payload in compile_plan_payloads
            if str(payload.get("package_name") or "").strip() == package_name_filter
        ]
    if not compile_plan_payloads:
        return None

    specs = _resolve_attention_layout_specs(compile_plan_payloads)
    if not specs:
        return None

    started_at = utc_now_iso()
    targets = _resolve_attention_runtime_targets(index=index)
    lane_state: dict[tuple[str, UUID], tuple[UUID | None, str | None]] = {}
    step_receipts: list[MaterializationStepReceipt] = []
    materialized_package_names: set[str] = set()
    for spec in specs:
        materialize_package = spec.package_name not in materialized_package_names
        step_receipts.append(
            await _materialize_attention_layout_spec(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                aware_root=aware_root,
                lane=lane,
                lane_state=lane_state,
                targets=targets,
                spec=spec,
                materialize_package=materialize_package,
            )
        )
        materialized_package_names.add(spec.package_name)

    return MaterializationRunReceipt(
        module_id="attention",
        pipeline_id="attention.compile_plan.layout_section.materialization.v0",
        lane=lane,
        status="succeeded",
        started_at_utc=started_at,
        finished_at_utc=utc_now_iso(),
        steps=tuple(step_receipts),
    )


async def _materialize_attention_layout_spec(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    aware_root: Path | None = None,
    lane: MaterializationLaneContext,
    lane_state: dict[tuple[str, UUID], tuple[UUID | None, str | None]],
    targets: _AttentionRuntimeTargets,
    spec: _AttentionLayoutSpec,
    materialize_package: bool,
) -> MaterializationStepReceipt:
    started_at = utc_now_iso()
    responses: list[MetaGraphInvokeFunctionResponse] = []
    attention_package_reused = False

    if materialize_package:
        package_response = await _ensure_attention_package(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            aware_root=aware_root,
            lane_state=lane_state,
            target=targets.attention_package,
            spec=spec,
        )
        attention_package_reused = package_response is None
        if package_response is not None:
            responses.append(package_response)
    layout_config_response = await _ensure_attention_root(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        aware_root=aware_root,
        lane_state=lane_state,
        target=targets.layout_config,
        branch_id=spec.layout_config_id,
        root_type=LayoutConfig,
        label=f"LayoutConfig.build({spec.layout_key})",
        kwargs={
            "key": spec.layout_key,
            "title": spec.title,
            "description": spec.description,
        },
        expected_fields={
            "id": spec.layout_config_id,
            "key": spec.layout_key,
            "title": spec.title,
            "description": spec.description,
        },
    )
    layout_config_reused = layout_config_response is None
    if layout_config_response is not None:
        responses.append(layout_config_response)
    responses.append(
        await _invoke_instance(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            lane_state=lane_state,
            projection_hash=targets.attention_package.projection_hash,
            branch_id=spec.attention_package_id,
            object_id=spec.attention_package_id,
            function_id=targets.attention_package_attach_layout_config_function_id,
            label=(
                "AttentionPackage.attach_layout_config"
                f"({spec.package_name}.{spec.layout_key})"
            ),
            kwargs={
                "layout_config_id": spec.layout_config_id,
            },
        )
    )
    attention_package_head_commit_id, attention_package_graph_hash = lane_state[
        (targets.attention_package.projection_hash, spec.attention_package_id)
    ]
    layout_response = await _ensure_attention_root(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        aware_root=aware_root,
        lane_state=lane_state,
        target=targets.layout,
        branch_id=spec.layout_id,
        root_type=Layout,
        label=f"Layout.build({spec.layout_key})",
        kwargs={
            "key": spec.layout_key,
            "title": spec.title,
            "description": spec.description,
        },
        expected_fields={
            "id": spec.layout_id,
            "key": spec.layout_key,
            "title": spec.title,
            "description": spec.description,
        },
    )
    layout_reused = layout_response is None
    if layout_response is not None:
        responses.append(layout_response)

    layout_section_ids: list[str] = []
    section_roots_reused = 0
    for section in spec.sections:
        layout_section_id = stable_layout_section_id(
            layout_id=spec.layout_id,
            section_id=section.section_id,
        )
        layout_section_ids.append(str(layout_section_id))
        responses.append(
            await _invoke_instance(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                lane_state=lane_state,
                projection_hash=targets.layout_config.projection_hash,
                branch_id=spec.layout_config_id,
                object_id=spec.layout_config_id,
                function_id=targets.layout_config_add_section_config_function_id,
                label=(
                    "LayoutConfig.add_section_config"
                    f"({spec.layout_key}.{section.section_key})"
                ),
                kwargs={
                    "section_key": section.section_key,
                    "title": section.title,
                    "description": section.description,
                    "order": section.order,
                    "flex": section.flex,
                    "is_visible": section.is_visible,
                },
            )
        )
        responses.append(
            await _invoke_instance(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                lane_state=lane_state,
                projection_hash=targets.layout_config.projection_hash,
                branch_id=spec.layout_config_id,
                object_id=section.layout_config_section_config_id,
                function_id=(
                    targets.layout_config_section_config_set_geometry_function_id
                ),
                label=(
                    "LayoutConfigSectionConfig.set_geometry"
                    f"({spec.layout_key}.{section.section_key})"
                ),
                kwargs={
                    "order": section.order,
                    "flex": section.flex,
                },
            )
        )
        responses.append(
            await _invoke_instance(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                lane_state=lane_state,
                projection_hash=targets.layout_config.projection_hash,
                branch_id=spec.layout_config_id,
                object_id=section.layout_config_section_config_id,
                function_id=(
                    targets.layout_config_section_config_set_visibility_function_id
                ),
                label=(
                    "LayoutConfigSectionConfig.set_visibility"
                    f"({spec.layout_key}.{section.section_key})"
                ),
                kwargs={
                    "is_visible": section.is_visible,
                },
            )
        )
        section_response = await _ensure_attention_root(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            aware_root=aware_root,
            lane_state=lane_state,
            target=targets.section,
            branch_id=section.section_id,
            root_type=Section,
            label=f"Section.build({section.section_key})",
            kwargs={
                "key": section.section_key,
                "title": section.title,
                "description": section.description,
            },
            expected_fields={
                "id": section.section_id,
                "key": section.section_key,
                "title": section.title,
                "description": section.description,
            },
        )
        if section_response is None:
            section_roots_reused += 1
        else:
            responses.append(section_response)
        responses.append(
            await _invoke_instance(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                lane_state=lane_state,
                projection_hash=targets.layout.projection_hash,
                branch_id=spec.layout_id,
                object_id=spec.layout_id,
                function_id=targets.layout_add_section_function_id,
                label=(
                    "Layout.add_section" f"({spec.layout_key}.{section.section_key})"
                ),
                kwargs={
                    "section_id": section.section_id,
                    "title": section.title,
                    "description": section.description,
                },
            )
        )
        responses.append(
            await _invoke_instance(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                lane_state=lane_state,
                projection_hash=targets.layout.projection_hash,
                branch_id=spec.layout_id,
                object_id=layout_section_id,
                function_id=targets.layout_section_set_geometry_function_id,
                label=(
                    "LayoutSection.set_geometry"
                    f"({spec.layout_key}.{section.section_key})"
                ),
                kwargs={
                    "order": section.order,
                    "flex": section.flex,
                },
            )
        )
        responses.append(
            await _invoke_instance(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                lane_state=lane_state,
                projection_hash=targets.layout.projection_hash,
                branch_id=spec.layout_id,
                object_id=layout_section_id,
                function_id=targets.layout_section_set_visibility_function_id,
                label=(
                    "LayoutSection.set_visibility"
                    f"({spec.layout_key}.{section.section_key})"
                ),
                kwargs={
                    "is_visible": section.is_visible,
                },
            )
        )

    return MaterializationStepReceipt(
        step_id=f"layout:{spec.package_name}:{spec.layout_key}",
        step_kind="attention_layout_config_runtime_layout_section",
        status="succeeded",
        commit_requested=True,
        commit_id=_last_commit_id(responses),
        head_commit_id=_last_commit_id(responses),
        started_at_utc=started_at,
        finished_at_utc=utc_now_iso(),
        details={
            "package_name": spec.package_name,
            "attention_package_id": str(spec.attention_package_id),
            "attention_package_materialized": (
                materialize_package and not attention_package_reused
            ),
            "attention_package_reused": attention_package_reused,
            "attention_package_head_commit_id": (
                str(attention_package_head_commit_id)
                if attention_package_head_commit_id is not None
                else None
            ),
            "attention_package_graph_hash": attention_package_graph_hash,
            "layout_config_reused": layout_config_reused,
            "layout_reused": layout_reused,
            "section_roots_reused": section_roots_reused,
            "layout_key": spec.layout_key,
            "layout_config_id": str(spec.layout_config_id),
            "layout_id": str(spec.layout_id),
            "section_keys": [section.section_key for section in spec.sections],
            "layout_section_ids": layout_section_ids,
            "sections_materialized": len(spec.sections),
            "invoke_count": len(responses),
            "commit_ids": [
                str(commit_id)
                for commit_id in (
                    response.domain_commit_id
                    or response.object_instance_graph_commit_id
                    for response in responses
                )
                if commit_id is not None
            ],
        },
        error=None,
    )


async def _ensure_attention_root(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    aware_root: Path | None,
    lane_state: dict[tuple[str, UUID], tuple[UUID | None, str | None]],
    target: _ProjectionInvokeTarget,
    branch_id: UUID,
    root_type: type[ORMModel],
    label: str,
    kwargs: Mapping[str, object],
    expected_fields: Mapping[str, object],
) -> MetaGraphInvokeFunctionResponse | None:
    existing_head = await _load_attention_root_lane_head_with_recovery(
        index=index,
        target=target,
        branch_id=branch_id,
        root_type=root_type,
        aware_root=aware_root,
    )
    if existing_head is None:
        return await _invoke_constructor(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            lane_state=lane_state,
            target=target,
            branch_id=branch_id,
            label=label,
            kwargs=kwargs,
        )

    for field_name, expected in expected_fields.items():
        actual = getattr(existing_head.root, field_name, None)
        if actual != expected:
            raise RuntimeError(
                "Attention materialization existing root does not match source: "
                f"label={label!r} branch_id={branch_id} field={field_name!r} "
                f"expected={expected!r} actual={actual!r}"
            )
    lane_state[(target.projection_hash, branch_id)] = (
        existing_head.commit_id,
        existing_head.graph_hash_post,
    )
    return None


async def _ensure_attention_package(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    aware_root: Path | None,
    lane_state: dict[tuple[str, UUID], tuple[UUID | None, str | None]],
    target: _ProjectionInvokeTarget,
    spec: _AttentionLayoutSpec,
) -> MetaGraphInvokeFunctionResponse | None:
    existing_head = await _load_attention_package_lane_head(
        index=index,
        target=target,
        attention_package_id=spec.attention_package_id,
        aware_root=aware_root,
    )
    if existing_head is None:
        return await _invoke_constructor(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            lane_state=lane_state,
            target=target,
            branch_id=spec.attention_package_id,
            label=f"AttentionPackage.build({spec.package_name})",
            kwargs={
                "name": spec.package_name,
                "source_code_package_id": None,
            },
        )

    existing_name = (existing_head.root.name or "").strip()
    if existing_head.root.id != spec.attention_package_id:
        raise RuntimeError(
            "Attention package lane root id does not match its stable package id: "
            f"package={spec.package_name!r} expected={spec.attention_package_id} "
            f"actual={existing_head.root.id}"
        )
    if existing_name != spec.package_name:
        raise RuntimeError(
            "Attention package lane root name does not match source package: "
            f"attention_package_id={spec.attention_package_id} "
            f"expected={spec.package_name!r} actual={existing_name!r}"
        )

    lane_state[(target.projection_hash, spec.attention_package_id)] = (
        existing_head.commit_id,
        existing_head.graph_hash_post,
    )
    return None


async def _load_attention_package_lane_head(
    *,
    index: MetaGraphRuntimeIndex,
    target: _ProjectionInvokeTarget,
    attention_package_id: UUID,
    aware_root: Path | None = None,
) -> _AttentionPackageLaneHead | None:
    lane_head = await _load_attention_root_lane_head_with_recovery(
        index=index,
        target=target,
        branch_id=attention_package_id,
        root_type=AttentionPackage,
        aware_root=aware_root,
    )
    if lane_head is None:
        return None
    if not isinstance(lane_head.root, AttentionPackage):
        raise RuntimeError(
            "Attention package lane HEAD resolved the wrong root type: "
            f"attention_package_id={attention_package_id} "
            f"root_type={type(lane_head.root).__name__}"
        )
    return _AttentionPackageLaneHead(
        commit_id=lane_head.commit_id,
        graph_hash_post=lane_head.graph_hash_post,
        root=lane_head.root,
    )


async def _load_attention_root_lane_head_with_recovery(
    *,
    index: MetaGraphRuntimeIndex,
    target: _ProjectionInvokeTarget,
    branch_id: UUID,
    root_type: type[ORMModel],
    aware_root: Path | None = None,
) -> _AttentionRootLaneHead | None:
    try:
        return await _load_attention_root_lane_head(
            index=index,
            target=target,
            branch_id=branch_id,
            root_type=root_type,
            aware_root=aware_root,
        )
    except Exception as exc:
        _reset_invalid_attention_lane(
            branch_id=branch_id,
            projection_hash=target.projection_hash,
            aware_root=aware_root,
        )
        logger.warning(
            "Attention materialization reset an unreplayable generated lane: "
            "branch_id=%s projection_hash=%s root_type=%s error=%s",
            branch_id,
            target.projection_hash,
            root_type.__name__,
            exc,
        )
        return None


def _reset_invalid_attention_lane(
    *,
    branch_id: UUID,
    projection_hash: str,
    aware_root: Path | None,
) -> None:
    store = (
        FSCommitStore(root_dir=aware_root)
        if aware_root is not None
        else FSCommitStore()
    )
    branch_dir = store.aware_root / ".aware" / "oig" / str(branch_id)
    lane_dir = branch_dir / projection_hash
    if lane_dir.exists():
        shutil.rmtree(lane_dir)
    get_shared_materialization_cache().invalidate_lane(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if branch_dir.exists() and not any(branch_dir.iterdir()):
        shutil.rmtree(branch_dir)


async def _load_attention_root_lane_head(
    *,
    index: MetaGraphRuntimeIndex,
    target: _ProjectionInvokeTarget,
    branch_id: UUID,
    root_type: type[ORMModel],
    aware_root: Path | None = None,
) -> _AttentionRootLaneHead | None:
    store = (
        FSCommitStore(root_dir=aware_root)
        if aware_root is not None
        else FSCommitStore()
    )
    head = await store.head(
        branch_id=branch_id,
        projection_hash=target.projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None

    raw_commit_id = head.get("commit_id")
    commit_id = (
        raw_commit_id if isinstance(raw_commit_id, UUID) else UUID(str(raw_commit_id))
    )
    graph_hash_post = str(head.get("graph_hash_post") or "").strip()
    if not graph_hash_post:
        raise RuntimeError(
            "Attention root lane HEAD is missing graph_hash_post: "
            f"branch_id={branch_id} "
            f"projection_hash={target.projection_hash}"
        )
    raw_root_object_id = head.get("root_object_id")
    if raw_root_object_id is not None and UUID(str(raw_root_object_id)) != branch_id:
        raise RuntimeError(
            "Attention root lane HEAD root does not match its branch identity: "
            f"branch_id={branch_id} "
            f"root_object_id={raw_root_object_id}"
        )

    opg = index.opg_by_hash.get(target.projection_hash)
    if opg is None:
        raise RuntimeError(
            "Attention materialization cannot hydrate an unknown projection: "
            f"projection_hash={target.projection_hash}"
        )
    oig, _ = await OIGMaterializer(commits=store).get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=commit_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    if oig.hash != graph_hash_post:
        raise RuntimeError(
            "Attention materialized graph hash does not match lane HEAD: "
            f"branch_id={branch_id} "
            f"head={graph_hash_post} materialized={oig.hash}"
        )
    session = reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )
    root = session.imap_get(root_type, branch_id)
    if root is None:
        raise RuntimeError(
            "Attention lane HEAD does not contain its stable root: "
            f"branch_id={branch_id} root_type={root_type.__name__} "
            f"projection_hash={target.projection_hash}"
        )
    return _AttentionRootLaneHead(
        commit_id=commit_id,
        graph_hash_post=graph_hash_post,
        root=root,
    )


async def _invoke_constructor(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane_state: dict[tuple[str, UUID], tuple[UUID | None, str | None]],
    target: _ProjectionInvokeTarget,
    branch_id: UUID,
    label: str,
    kwargs: Mapping[str, object],
) -> MetaGraphInvokeFunctionResponse:
    expected_head_commit_id, expected_graph_hash_pre = lane_state.get(
        (target.projection_hash, branch_id), (None, None)
    )
    request = MetaGraphInvokeFunctionRequest(
        actor_id=actor_id or UUID(int=0),
        domain_branch_id=branch_id,
        domain_projection_hash=target.projection_hash,
        call_target=MetaGraphFunctionCallTarget.opg_constructor,
        target_object_id=None,
        object_projection_graph_id=target.object_projection_graph_id,
        function_id=target.constructor_function_id,
        args=JsonArray(),
        kwargs=JsonObject(cast(Any, dict(kwargs))),
        expected_graph_hash_pre=expected_graph_hash_pre,
        expected_head_commit_id=expected_head_commit_id,
        commit=True,
        publish=False,
    )
    try:
        response = await runtime.invoker.invoke_function_with_index(
            index=index,
            request=request,
        )
    except Exception as exc:
        raise RuntimeError(f"{label} invocation failed: {exc}") from exc
    _ensure_invoke_succeeded(response=response, label=label)
    _record_lane_state(
        lane_state=lane_state,
        projection_hash=target.projection_hash,
        branch_id=branch_id,
        response=response,
    )
    return response


async def _invoke_instance(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    lane_state: dict[tuple[str, UUID], tuple[UUID | None, str | None]],
    projection_hash: str,
    branch_id: UUID,
    object_id: UUID,
    function_id: UUID,
    label: str,
    kwargs: Mapping[str, object],
) -> MetaGraphInvokeFunctionResponse:
    expected_head_commit_id, expected_graph_hash_pre = lane_state.get(
        (projection_hash, branch_id), (None, None)
    )
    request = MetaGraphInvokeFunctionRequest(
        actor_id=actor_id or UUID(int=0),
        domain_branch_id=branch_id,
        domain_projection_hash=projection_hash,
        call_target=MetaGraphFunctionCallTarget.instance,
        target_object_id=object_id,
        object_projection_graph_id=None,
        function_id=function_id,
        args=JsonArray(),
        kwargs=JsonObject(cast(Any, dict(kwargs))),
        expected_graph_hash_pre=expected_graph_hash_pre,
        expected_head_commit_id=expected_head_commit_id,
        commit=True,
        publish=False,
    )
    try:
        response = await runtime.invoker.invoke_function_with_index(
            index=index,
            request=request,
        )
    except Exception as exc:
        raise RuntimeError(f"{label} invocation failed: {exc}") from exc
    _ensure_invoke_succeeded(response=response, label=label)
    _record_lane_state(
        lane_state=lane_state,
        projection_hash=projection_hash,
        branch_id=branch_id,
        response=response,
    )
    return response


def _record_lane_state(
    *,
    lane_state: dict[tuple[str, UUID], tuple[UUID | None, str | None]],
    projection_hash: str,
    branch_id: UUID,
    response: MetaGraphInvokeFunctionResponse,
) -> None:
    previous_commit_id, previous_graph_hash = lane_state.get(
        (projection_hash, branch_id), (None, None)
    )
    commit_id = (
        response.domain_commit_id
        or response.object_instance_graph_commit_id
        or previous_commit_id
    )
    lane_state[(projection_hash, branch_id)] = (
        commit_id,
        response.graph_hash_post or previous_graph_hash,
    )


def _ensure_invoke_succeeded(
    *,
    response: MetaGraphInvokeFunctionResponse,
    label: str,
) -> None:
    if (response.status or "").strip().casefold() == "succeeded":
        return
    raise RuntimeError(f"{label} failed: {response.error or response.status}")


def _last_commit_id(
    responses: Sequence[MetaGraphInvokeFunctionResponse],
) -> UUID | None:
    for response in reversed(responses):
        commit_id = (
            response.domain_commit_id or response.object_instance_graph_commit_id
        )
        if commit_id is not None:
            return commit_id
    return None


def _resolve_attention_layout_specs(
    payloads: Sequence[Mapping[str, object]],
) -> tuple[_AttentionLayoutSpec, ...]:
    specs: list[_AttentionLayoutSpec] = []
    seen_layout_keys: set[str] = set()
    for payload_index, payload in enumerate(payloads):
        field_prefix = f"payload[{payload_index}]"
        schema_version = _expect_int(
            payload.get("schema_version"),
            field_name=f"{field_prefix}.schema_version",
        )
        if schema_version != 1:
            raise RuntimeError(
                "Invalid attention compile plan payload: "
                f"{field_prefix}.schema_version must be 1"
            )
        package_name = _expect_text(
            payload.get("package_name"),
            field_name=f"{field_prefix}.package_name",
        )
        attention_package_id = _expect_uuid(
            payload.get("attention_package_id"),
            field_name=f"{field_prefix}.attention_package_id",
        )
        expected_attention_package_id = stable_attention_package_id(name=package_name)
        if attention_package_id != expected_attention_package_id:
            raise RuntimeError(
                "Invalid attention compile plan payload: "
                f"{field_prefix}.attention_package_id does not match stable id "
                f"for package_name={package_name!r}"
            )
        layout_items = _expect_sequence(
            payload.get("layout_ontology"),
            field_name=f"{field_prefix}.layout_ontology",
        )
        if not layout_items:
            raise RuntimeError(
                "Invalid attention compile plan payload: "
                f"{field_prefix}.layout_ontology must contain at least one layout"
            )
        for layout_index, layout_value in enumerate(layout_items):
            layout = _expect_mapping(
                layout_value,
                field_name=f"{field_prefix}.layout_ontology[{layout_index}]",
            )
            spec = _resolve_layout_spec(
                package_name=package_name,
                attention_package_id=attention_package_id,
                layout=layout,
                field_prefix=f"{field_prefix}.layout_ontology[{layout_index}]",
            )
            layout_unique_key = f"{package_name}:{spec.layout_key}"
            if layout_unique_key in seen_layout_keys:
                raise RuntimeError(
                    "Invalid attention compile plan payload: duplicate layout_key "
                    f"{spec.layout_key!r} in package {package_name!r}"
                )
            seen_layout_keys.add(layout_unique_key)
            specs.append(spec)
    return tuple(specs)


def _resolve_layout_spec(
    *,
    package_name: str,
    attention_package_id: UUID,
    layout: Mapping[str, object],
    field_prefix: str,
) -> _AttentionLayoutSpec:
    layout_key = _expect_text(
        layout.get("layout_key"),
        field_name=f"{field_prefix}.layout_key",
    )
    title = _expect_text(layout.get("title"), field_name=f"{field_prefix}.title")
    description = _optional_text(
        layout.get("description"),
        field_name=f"{field_prefix}.description",
    )
    layout_config_id = _expect_uuid(
        layout.get("layout_config_id"),
        field_name=f"{field_prefix}.layout_config_id",
    )
    expected_layout_config_id = stable_layout_config_id(key=layout_key)
    if layout_config_id != expected_layout_config_id:
        raise RuntimeError(
            "Invalid attention compile plan payload: "
            f"{field_prefix}.layout_config_id does not match stable id for "
            f"layout_key={layout_key!r}"
        )
    layout_id = stable_layout_id(key=layout_key)
    section_items = _expect_sequence(
        layout.get("sections"),
        field_name=f"{field_prefix}.sections",
    )
    if not section_items:
        raise RuntimeError(
            "Invalid attention compile plan payload: "
            f"{field_prefix}.sections must contain at least one section"
        )
    sections: list[_AttentionLayoutSectionSpec] = []
    seen_section_keys: set[str] = set()
    for section_index, section_value in enumerate(section_items):
        section = _expect_mapping(
            section_value,
            field_name=f"{field_prefix}.sections[{section_index}]",
        )
        section_spec = _resolve_layout_section_spec(
            layout_config_id=layout_config_id,
            section=section,
            field_prefix=f"{field_prefix}.sections[{section_index}]",
        )
        if section_spec.section_key in seen_section_keys:
            raise RuntimeError(
                "Invalid attention compile plan payload: duplicate section_key "
                f"{section_spec.section_key!r} in layout {layout_key!r}"
            )
        seen_section_keys.add(section_spec.section_key)
        sections.append(section_spec)
    return _AttentionLayoutSpec(
        package_name=package_name,
        attention_package_id=attention_package_id,
        layout_config_id=layout_config_id,
        layout_id=layout_id,
        layout_key=layout_key,
        title=title,
        description=description,
        sections=tuple(sections),
    )


def _resolve_layout_section_spec(
    *,
    layout_config_id: UUID,
    section: Mapping[str, object],
    field_prefix: str,
) -> _AttentionLayoutSectionSpec:
    section_key = _expect_text(
        section.get("section_key"),
        field_name=f"{field_prefix}.section_key",
    )
    title = _expect_text(section.get("title"), field_name=f"{field_prefix}.title")
    description = _optional_text(
        section.get("description"),
        field_name=f"{field_prefix}.description",
    )
    order = _expect_int(section.get("order"), field_name=f"{field_prefix}.order")
    flex = _expect_float(section.get("flex"), field_name=f"{field_prefix}.flex")
    is_visible = _expect_bool(
        section.get("is_visible"),
        field_name=f"{field_prefix}.is_visible",
    )
    layout_config_section_config_id = _expect_uuid(
        section.get("layout_config_section_config_id"),
        field_name=f"{field_prefix}.layout_config_section_config_id",
    )
    expected_layout_config_section_config_id = stable_layout_config_section_config_id(
        layout_config_id=layout_config_id,
        section_key=section_key,
    )
    if layout_config_section_config_id != expected_layout_config_section_config_id:
        raise RuntimeError(
            "Invalid attention compile plan payload: "
            f"{field_prefix}.layout_config_section_config_id does not match "
            f"stable id for section_key={section_key!r}"
        )
    section_config_id = _expect_uuid(
        section.get("section_config_id"),
        field_name=f"{field_prefix}.section_config_id",
    )
    expected_section_config_id = stable_section_config_id(
        layout_config_section_config_id=layout_config_section_config_id,
        key=section_key,
    )
    if section_config_id != expected_section_config_id:
        raise RuntimeError(
            "Invalid attention compile plan payload: "
            f"{field_prefix}.section_config_id does not match stable id for "
            f"section_key={section_key!r}"
        )
    return _AttentionLayoutSectionSpec(
        layout_config_section_config_id=layout_config_section_config_id,
        section_config_id=section_config_id,
        section_id=stable_section_id(key=section_key),
        section_key=section_key,
        title=title,
        description=description,
        order=order,
        flex=flex,
        is_visible=is_visible,
    )


def _resolve_attention_runtime_targets(
    *,
    index: MetaGraphRuntimeIndex,
) -> _AttentionRuntimeTargets:
    return _AttentionRuntimeTargets(
        attention_package=_resolve_projection_invoke_target(
            index=index,
            projection_name="AttentionPackage",
        ),
        attention_package_attach_layout_config_function_id=_resolve_public_function_id(
            index=index,
            class_name_suffix="AttentionPackage",
            function_name="attach_layout_config",
        ),
        layout_config=_resolve_projection_invoke_target(
            index=index,
            projection_name="LayoutConfig",
        ),
        layout_config_add_section_config_function_id=_resolve_public_function_id(
            index=index,
            class_name_suffix="LayoutConfig",
            function_name="add_section_config",
        ),
        layout_config_section_config_set_geometry_function_id=(
            _resolve_public_function_id(
                index=index,
                class_name_suffix="LayoutConfigSectionConfig",
                function_name="set_geometry",
            )
        ),
        layout_config_section_config_set_visibility_function_id=(
            _resolve_public_function_id(
                index=index,
                class_name_suffix="LayoutConfigSectionConfig",
                function_name="set_visibility",
            )
        ),
        layout=_resolve_projection_invoke_target(
            index=index,
            projection_name="Layout",
        ),
        layout_add_section_function_id=_resolve_public_function_id(
            index=index,
            class_name_suffix="Layout",
            function_name="add_section",
        ),
        section=_resolve_projection_invoke_target(
            index=index,
            projection_name="Section",
        ),
        layout_section_set_geometry_function_id=_resolve_public_function_id(
            index=index,
            class_name_suffix="LayoutSection",
            function_name="set_geometry",
        ),
        layout_section_set_visibility_function_id=_resolve_public_function_id(
            index=index,
            class_name_suffix="LayoutSection",
            function_name="set_visibility",
        ),
    )


def _resolve_projection_invoke_target(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> _ProjectionInvokeTarget:
    target = (projection_name or "").strip()
    if not target:
        raise ValueError("projection_name is required")
    opg = next(
        (
            item
            for item in index.ocg.object_projection_graphs
            if (item.name or "").strip() == target
        ),
        None,
    )
    if opg is None:
        raise RuntimeError(f"Attention projection {projection_name!r} was not found")
    return _ProjectionInvokeTarget(
        object_projection_graph_id=opg.id,
        projection_hash=opg.projection_hash,
        constructor_function_id=_resolve_single_opg_constructor_function_id(
            index=index,
            object_projection_graph_id=opg.id,
        ),
    )


def _resolve_single_opg_constructor_function_id(
    *,
    index: MetaGraphRuntimeIndex,
    object_projection_graph_id: UUID,
) -> UUID:
    opg = next(
        (
            item
            for item in index.ocg.object_projection_graphs
            if item.id == object_projection_graph_id
        ),
        None,
    )
    if opg is None:
        raise RuntimeError(
            "ObjectProjectionGraph not found: "
            f"object_projection_graph_id={object_projection_graph_id}"
        )

    constructors = list(opg.object_projection_graph_constructors or [])
    if len(constructors) != 1:
        raise RuntimeError(
            "Expected exactly one OPG constructor for Attention materialization: "
            f"object_projection_graph_id={object_projection_graph_id} "
            f"count={len(constructors)}"
        )

    constructor_link_id = constructors[0].function_constructor_id
    for node in index.ocg.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        for link in node.class_config.class_config_function_configs:
            if link.id != constructor_link_id:
                continue
            function_config_id = getattr(link, "function_config_id", None)
            if not isinstance(function_config_id, UUID):
                raise RuntimeError(
                    "OPG constructor link missing function_config_id: "
                    f"object_projection_graph_id={object_projection_graph_id} "
                    f"function_constructor_id={constructor_link_id}"
                )
            return function_config_id

    raise RuntimeError(
        "OPG constructor link not found in OCG class-function edges: "
        f"object_projection_graph_id={object_projection_graph_id} "
        f"function_constructor_id={constructor_link_id}"
    )


def _resolve_public_function_id(
    *,
    index: MetaGraphRuntimeIndex,
    class_name_suffix: str,
    function_name: str,
) -> UUID:
    normalized_suffix = (class_name_suffix or "").strip()
    normalized_fn_name = (function_name or "").strip()
    if not normalized_suffix:
        raise ValueError("class_name_suffix is required")
    if not normalized_fn_name:
        raise ValueError("function_name is required")

    suffix_leaf = normalized_suffix.rsplit(".", 1)[-1]
    function_by_id: dict[UUID, Any] = {}
    for node in index.ocg.object_config_graph_nodes:
        node_obj = cast(Any, node)
        if (
            node_obj.type == ObjectConfigGraphNodeType.function
            and node_obj.function_config is not None
        ):
            function_by_id[node_obj.function_config.id] = node_obj.function_config

    matches: set[UUID] = set()
    for node in index.ocg.object_config_graph_nodes:
        node_obj = cast(Any, node)
        if (
            node_obj.type != ObjectConfigGraphNodeType.class_
            or node_obj.class_config is None
        ):
            continue
        class_name = (node_obj.class_config.name or "").strip()
        class_match = class_name.endswith(normalized_suffix)
        if not class_match and "." in normalized_suffix:
            class_match = class_name == suffix_leaf or class_name.endswith(
                f".{suffix_leaf}"
            )
        if not class_match:
            continue
        for link in node_obj.class_config.class_config_function_configs:
            if not link.is_public:
                continue
            fn_cfg = link.function_config
            function_config_id = getattr(link, "function_config_id", None)
            if function_config_id is not None:
                fn_cfg = function_by_id.get(function_config_id) or fn_cfg
            if fn_cfg is None:
                continue
            if (fn_cfg.name or "").strip() == normalized_fn_name:
                matches.add(fn_cfg.id)

    if not matches:
        raise RuntimeError(
            "Could not resolve function "
            f"{normalized_fn_name!r} for class suffix {normalized_suffix!r}"
        )
    if len(matches) > 1:
        raise RuntimeError(
            "Ambiguous function "
            f"{normalized_fn_name!r} for class suffix {normalized_suffix!r}"
        )
    return next(iter(matches))


def _expect_mapping(value: object, *, field_name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise RuntimeError(
        f"Invalid attention compile plan payload: {field_name} must be an object"
    )


def _expect_sequence(value: object, *, field_name: str) -> Sequence[object]:
    if isinstance(value, (list, tuple)):
        return value
    raise RuntimeError(
        f"Invalid attention compile plan payload: {field_name} must be an array"
    )


def _expect_text(value: object, *, field_name: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise RuntimeError(
        f"Invalid attention compile plan payload: {field_name} must be a non-empty string"
    )


def _optional_text(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    raise RuntimeError(
        f"Invalid attention compile plan payload: {field_name} must be a string or null"
    )


def _expect_int(value: object, *, field_name: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise RuntimeError(
        f"Invalid attention compile plan payload: {field_name} must be an integer"
    )


def _expect_float(value: object, *, field_name: str) -> float:
    if isinstance(value, bool):
        raise RuntimeError(
            f"Invalid attention compile plan payload: {field_name} must be a number"
        )
    if isinstance(value, (int, float)):
        return float(value)
    raise RuntimeError(
        f"Invalid attention compile plan payload: {field_name} must be a number"
    )


def _expect_bool(value: object, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise RuntimeError(
        f"Invalid attention compile plan payload: {field_name} must be a boolean"
    )


def _expect_uuid(value: object, *, field_name: str) -> UUID:
    text = _expect_text(value, field_name=field_name)
    try:
        return UUID(text)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid attention compile plan payload: {field_name} must be a UUID"
        ) from exc


def _find_repo_root(*, start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    while current.parent != current:
        if (current / "aware.workspace.toml").exists() or (
            current / "aware.environment.toml"
        ).exists():
            return current
        current = current.parent
    if (current / "aware.workspace.toml").exists() or (
        current / "aware.environment.toml"
    ).exists():
        return current
    return (start or Path.cwd()).resolve()


__all__ = [
    "load_attention_compile_plan_payloads",
    "materialize_attention_compile_plan_ontology",
]
