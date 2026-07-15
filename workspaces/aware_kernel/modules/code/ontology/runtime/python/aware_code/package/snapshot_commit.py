from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.types import Json, JsonValue
from aware_code.package.snapshot_artifacts import (
    code_package_artifact_state_index_from_refs as _code_package_artifact_state_index_from_refs,
)
from aware_code.package.snapshot_artifacts import (
    code_package_artifact_state_index_from_refs_delta as _code_package_artifact_state_index_from_refs_delta,
)
from aware_code.package.snapshot_contract import (
    CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA,
    CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_OVERLAY_SCHEMA,
    CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_SCHEMA,
    CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION as _CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION,
)
from aware_code.package.snapshot_index import (
    code_package_text_snapshot_index_hit as _code_package_text_snapshot_index_hit,
)
from aware_code.package.snapshot_index import (
    code_package_text_snapshot_index_payload_hit as _code_package_text_snapshot_index_payload_hit,
)
from aware_code.package.snapshot_index import (
    load_code_package_text_snapshot_source_object_state_index_selected as _load_code_package_text_snapshot_source_object_state_index_selected,
)
from aware_code.package.snapshot_index import (
    load_current_code_package_text_snapshot_index_payload as _load_current_code_package_text_snapshot_index_payload,
)
from aware_code.package.snapshot_index import (
    load_current_code_package_text_snapshot_index_payload_with_head as _load_current_code_package_text_snapshot_index_payload_with_head,
)
from aware_code.package.snapshot_index import (
    write_code_package_text_snapshot_index as _write_code_package_text_snapshot_index,
)
from aware_code.package.snapshot_json import head_string as _head_string
from aware_code.package.snapshot_json import head_uuid as _head_uuid
from aware_code.package.snapshot_json import optional_text as _optional_text
from aware_code.package.snapshot_json import payload_int as _payload_int
from aware_code.package.snapshot_json import stable_json_hash as _stable_json_hash
from aware_code.package.snapshot_source_text import (  # noqa: F401
    code_package_text_source_snapshot_fingerprint,
)
from aware_code.package.snapshot_source_text import (
    code_package_text_source_snapshot_fingerprint_result as _code_package_text_source_snapshot_fingerprint_result,
)
from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_delta import ChangeDelta
from aware_history_ontology.change.change_enums import ChangeDeltaKind, ChangeType
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_change import AttributeChange
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.attribute.attribute_value_change import AttributeValueChange
from aware_meta_ontology.attribute.attribute_value_link import AttributeValueLink
from aware_meta_ontology.attribute.attribute_value_link_change import (
    AttributeValueLinkChange,
)
from aware_meta.attribute.instance.value import AttributeValueTreeValidationError
from aware_meta.attribute.instance.value.stable_ids import (
    stable_attribute_value_id,
    stable_attribute_value_link_id,
)
from aware_meta.attribute.instance.value.builder import fingerprint_attribute_value
from aware_code.language import normalize_code_language
from aware_code.package.text_upsert import build_code_content_plan_copy_from_text
from aware_code_ontology.code.code_plan import CodeContentPlan
from aware_code_ontology.code.code_plan import CodePackagePathRole
from aware_code.stable_ids import (
    stable_code_id,
    stable_code_package_artifact_id,
    stable_code_package_code_id,
    stable_code_package_id,
    stable_code_section_id,
)
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_artifact import (
    CodePackageArtifact,
    CodePackageArtifactRef,
)
from aware_code_ontology.package.code_package_code import CodePackageCode
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_content_ontology.stable_ids import stable_content_part_text_segment_id
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.class_.instance.stable_ids import stable_class_instance_relationship_id
from aware_meta.graph.config.stable_ids import stable_class_instance_id
from aware_meta.graph.config.stable_ids import stable_attribute_id
from aware_meta.graph.instance.builder import (
    build_include_relationship_attribute_config_ids_by_class_config_id,
    build_object_instance_graph,
    build_object_instance_graph_from_class_instances,
    build_relationship_attribute_config_ids_by_class_config_id,
)
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.contract import CommitActionDescriptor
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.graph.instance.commit.perf_trace import (
    commit_perf_span,
    record_commit_perf_elapsed,
)
from aware_meta.graph.instance.commit.materialization_cache import (
    get_shared_materialization_cache,
)
from aware_meta.graph.instance.commit.state_snapshot_segments import (
    ObjectInstanceGraphSnapshotStateRawClassSegmentCursorSelection,
    ObjectInstanceGraphSnapshotStateRawClassSegment,
    ObjectInstanceGraphSnapshotStateRawClassSegmentIndexSelection,
    ObjectInstanceGraphSnapshotStateRawClassSegmentSelection,
    ObjectInstanceGraphSnapshotStateSegmentIndexMetadata,
    commit_state_witness_cursor_summary_from_payload,
)
from aware_meta.graph.instance.commit.snapshot_state_rows import (
    ObjectInstanceGraphSnapshotStateSelection,
)
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.commit.builder import (
    extract_object_instance_graph_commit_root_metadata,
)
from aware_meta.graph.instance.commit.contract import (
    ObjectInstanceGraphCommitGraphHashSource,
    ObjectInstanceGraphCommitPreStateEvidence,
    ObjectInstanceGraphCommitRootMetadata,
)
from aware_meta.graph.instance.diff import (
    build_object_instance_graph_identity_snapshot_changes,
)
from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    CommitStateRow,
    CommitStateRowKind,
    CommitStateRowMaps,
    build_commit_state_index,
    compute_commit_state_rows_hash,
)
from aware_meta.graph.instance.commit.state_witness import (
    CommitStateWitnessCursorChunk,
    CommitStateWitnessCursorSummary,
    CommitStateSegmentRef,
    CommitStateWitnessRef,
    build_commit_state_witness_cursor,
    build_commit_state_witness_ref,
    compute_commit_state_segment_digest,
    replace_commit_state_witness_cursor_chunk_segments,
    replace_existing_commit_state_witness_cursor_summary_chunks,
    replace_existing_commit_state_witness_ref_segments,
)
from aware_meta_ontology.stable_ids import (
    stable_class_instance_attribute_id,
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
)
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.class_.class_instance_relationship_change import (
    ClassInstanceRelationshipChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)
from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_orm.models.base_model import BaseORMModel
from aware_orm.models.introspection import ModelIntrospection
from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import disable_change_tracking_hooks


@dataclass(frozen=True, slots=True)
class CodePackageTextSnapshotCommitResult:
    code_package: CodePackage
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class _CodePackageDesiredState:
    object_instance_graph_id: UUID
    graph_hash: str
    state_index: CommitStateIndex
    root_metadata: ObjectInstanceGraphCommitRootMetadata
    root_class_instance: ClassInstance
    class_instances: tuple[ClassInstance, ...]
    class_instance_payloads: tuple[Mapping[str, object], ...]
    class_instances_by_id: Mapping[UUID, ClassInstance]
    class_instance_relationships: tuple[ClassInstanceRelationship, ...]
    relationships_by_key: Mapping[tuple[UUID, UUID, UUID], ClassInstanceRelationship]
    graph_meta: Mapping[str, object]
    source_object_state_index: Mapping[str, object]
    previous_snapshot_payload: Mapping[str, object] | None = None
    previous_snapshot_state_rows: tuple[CommitStateRow, ...] | None = None
    previous_snapshot_state_maps: CommitStateRowMaps | None = None
    graph_hash_source: ObjectInstanceGraphCommitGraphHashSource = "state_hash"
    previous_commit_id: UUID | None = None
    pre_witness_ref: CommitStateWitnessRef | None = None
    post_witness_ref: CommitStateWitnessRef | None = None
    pre_witness_cursor_summary: CommitStateWitnessCursorSummary | None = None
    post_witness_cursor_summary: CommitStateWitnessCursorSummary | None = None
    post_witness_cursor_chunks: tuple[CommitStateWitnessCursorChunk, ...] = ()
    replacement_class_segments: tuple[
        ObjectInstanceGraphSnapshotStateRawClassSegment,
        ...,
    ] = ()
    precomputed_change_result: _CodePackageSnapshotChangeResult | None = None


@dataclass(frozen=True, slots=True)
class _CodePackageSourceObjectState:
    source_object_id: UUID
    class_config_id: UUID
    class_instance_id: UUID
    signature_hash: str


@dataclass(frozen=True, slots=True)
class _CodePackageSourceObjectStateBuild:
    states_by_id: Mapping[UUID, _CodePackageSourceObjectState]
    path_source_object_ids: Mapping[str, tuple[UUID, ...]]


@dataclass(frozen=True, slots=True)
class _CodePackageSourceObjectIndexView:
    object_rows_by_source_id: Mapping[UUID, Mapping[str, object]]
    path_source_object_ids: Mapping[str, tuple[UUID, ...]]

    @property
    def object_count(self) -> int:
        return len(self.object_rows_by_source_id)


@dataclass(frozen=True, slots=True)
class _CodePackageSourceObjectRawIndexView:
    object_rows: tuple[Mapping[str, object], ...]
    path_source_object_ids: Mapping[str, tuple[UUID, ...]]
    declared_object_count: int | None = None
    partial: bool = False

    @property
    def object_count(self) -> int:
        if self.declared_object_count is not None:
            return self.declared_object_count
        return len(self.object_rows)


@dataclass(frozen=True, slots=True)
class _CodePackageChangedPathSourceState:
    changed_source_states_by_id: Mapping[UUID, _CodePackageSourceObjectState]
    root_source_state: _CodePackageSourceObjectState
    changed_source_object_ids: frozenset[UUID]
    source_object_path_index: Mapping[str, tuple[UUID, ...]]
    source_object_state_index: Mapping[str, object]
    source_object_count: int
    build_relationship_topology: bool


@dataclass(frozen=True, slots=True)
class _CodePackageSnapshotChangeResult:
    changes: list[ObjectInstanceGraphChange]
    pre_state_index: CommitStateIndex | None
    pre_state_evidence: ObjectInstanceGraphCommitPreStateEvidence


@dataclass(frozen=True, slots=True)
class _CodePackageDirectClassState:
    class_instance_id: UUID
    class_config_id: UUID
    source_object_id: UUID
    state_rows: tuple[CommitStateRow, ...]
    snapshot_payload: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class _CodePackageDirectRelationshipContext:
    relationships_by_id: Mapping[UUID, object]
    relationship_attribute_ids_by_cc_id: Mapping[UUID, set[UUID]]
    include_relationship_attr_ids_by_cc_id: Mapping[UUID, set[UUID]]
    relationship_configs_by_key: Mapping[tuple[str, str, str], UUID]
    relationship_count: int
    cache_hit: bool = False


_CODE_PACKAGE_DIRECT_RELATIONSHIP_CONTEXT_CACHE: dict[
    tuple[int, int, str, str, int],
    _CodePackageDirectRelationshipContext,
] = {}
_CODE_PACKAGE_DIRECT_RELATIONSHIP_CONTEXT_CACHE_MAX = 16
_CODE_PACKAGE_STATE_ROW_MAP_MIN_ROW_COUNT = 25_000
_CODE_PACKAGE_STATE_ROW_MAP_MIN_SOURCE_OBJECT_COUNT = 500
_CODE_PACKAGE_STATE_CLASS_SEGMENTS_ENV = "AWARE_CODE_PACKAGE_WRITE_STATE_CLASS_SEGMENTS"
_CODE_PACKAGE_PARTIAL_SOURCE_REUSE_MIN_SOURCE_OBJECT_COUNT = 500


def _code_package_state_class_segments_enabled(*, node_count: int) -> bool:
    return (
        os.getenv(_CODE_PACKAGE_STATE_CLASS_SEGMENTS_ENV) == "1"
        and node_count >= _CODE_PACKAGE_STATE_ROW_MAP_MIN_SOURCE_OBJECT_COUNT
    )


@dataclass(frozen=True, slots=True)
class _ModelIntrospectionOverlay(ModelIntrospection):
    source: ModelIntrospection
    values_by_name: Mapping[str, object]

    @property
    def id(self) -> UUID:
        return self.source.id

    def field_is_declared(self, name: str) -> bool:
        return name in self.values_by_name or self.source.field_is_declared(name)

    def field_is_set(self, name: str) -> bool:
        return name in self.values_by_name or self.source.field_is_set(name)

    def try_field_value(
        self,
        name: str,
        *,
        include_unset: bool = False,
    ) -> tuple[bool, object]:
        if name in self.values_by_name:
            return True, self.values_by_name[name]
        found, value = self.source.try_field_value(
            name,
            include_unset=include_unset,
        )
        if found:
            return True, value
        return False, None

    def try_virtual_value(self, attribute_config: object) -> tuple[bool, object]:
        return self.source.try_virtual_value(attribute_config)  # type: ignore[arg-type]

    def try_attribute_value(self, attribute_config: object) -> tuple[bool, object]:
        name = getattr(attribute_config, "name", None)
        if name in self.values_by_name:
            return True, self.values_by_name[str(name)]
        found, value = self.source.try_attribute_value(attribute_config)  # type: ignore[arg-type]
        if found:
            return True, value
        return False, None

    def try_class_config_id(self) -> UUID | None:
        return self.source.try_class_config_id()


_CODE_PACKAGE_TEXT_CONTENT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://code/package/text-content/v1",
)
_CODE_PACKAGE_TEXT_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://code/package/text-snapshot-commit/v1",
)


async def _code_package_text_snapshot_head_commit_record_readable(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    head: Mapping[str, object] | None,
) -> bool:
    head_commit_id = _head_uuid(head, "commit_id")
    if head_commit_id is None:
        return False
    return (
        await store.get_commit_record(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
        )
        is not None
    )


async def commit_code_package_text_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    code_package_config_id: UUID,
    package_name: str,
    language: CodeLanguage,
    surface: str,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
    source_texts_by_relative_path: Mapping[str, str],
    source_plans_by_relative_path: Mapping[str, CodeContentPlan] | None = None,
    unparsed_texts_by_relative_path: Mapping[str, str] | None = None,
    path_roles_by_relative_path: Mapping[str, CodePackagePathRole] | None = None,
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...] = (),
    changed_relative_paths: Iterable[str] | None = None,
) -> CodePackageTextSnapshotCommitResult:
    wall_started = time.perf_counter()

    def _record_wall_phase(phase: str, **metadata: object) -> None:
        nonlocal wall_started
        ended = time.perf_counter()
        record_commit_perf_elapsed(
            phase=f"code_package.snapshot_commit.wall.{phase}",
            started=wall_started,
            ended=ended,
            category="code_package.snapshot_commit.wall",
            metadata=metadata,
        )
        wall_started = time.perf_counter()

    language = normalize_code_language(language)
    changed_relative_path_set = _normalize_code_package_changed_relative_paths(
        changed_relative_paths,
    )
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "CodePackage text snapshot commit missing projection hash: "
            f"{projection_hash}"
        )

    code_package_id = stable_code_package_id(
        code_package_config_id=code_package_config_id,
        package_name=package_name,
        language=language,
    )
    store = FSCommitStore()
    domain_oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    _record_wall_phase(
        "setup",
        changed_path_count=len(changed_relative_path_set),
        source_text_count=len(source_texts_by_relative_path),
        unparsed_text_count=len(unparsed_texts_by_relative_path or {}),
        artifact_count=len(code_package_artifact_refs),
    )
    with commit_perf_span(
        phase="code_package.snapshot_commit.head_snapshot_index",
        category="code_package.snapshot_commit",
    ):
        head, previous_snapshot_index_payload = (
            await _load_current_code_package_text_snapshot_index_payload_with_head(
                store=store,
                branch_id=branch_id,
                projection_hash=projection_hash,
                code_package_id=code_package_id,
                include_sections=bool(changed_relative_path_set),
                include_source_object_index=False,
            )
        )
        stale_head_reset = False
        if _head_uuid(head, "commit_id") is not None and not (
            await _code_package_text_snapshot_head_commit_record_readable(
                store=store,
                branch_id=branch_id,
                projection_hash=projection_hash,
                head=cast(Mapping[str, object] | None, head),
            )
        ):
            _reset_code_package_text_snapshot_lane(
                store=store,
                branch_id=branch_id,
                projection_hash=projection_hash,
            )
            head = None
            previous_snapshot_index_payload = None
            stale_head_reset = True
    _record_wall_phase(
        "head_snapshot_index",
        previous_snapshot_index=previous_snapshot_index_payload is not None,
        stale_head_reset=stale_head_reset,
    )
    with commit_perf_span(
        phase="code_package.snapshot_commit.fingerprint",
        category="code_package.snapshot_commit",
        metadata={
            "source_text_count": len(source_texts_by_relative_path),
            "unparsed_text_count": len(unparsed_texts_by_relative_path or {}),
            "artifact_count": len(code_package_artifact_refs),
            "changed_path_count": len(changed_relative_path_set),
            "previous_snapshot_index": previous_snapshot_index_payload is not None,
        },
    ):
        source_fingerprint = _code_package_text_source_snapshot_fingerprint_result(
            code_package_config_id=code_package_config_id,
            package_name=package_name,
            language=language,
            surface=surface,
            manifest_kind=manifest_kind,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root,
            sources_root=sources_root,
            fqn_prefix=fqn_prefix,
            source_texts_by_relative_path=source_texts_by_relative_path,
            source_plans_by_relative_path=source_plans_by_relative_path or {},
            unparsed_texts_by_relative_path=unparsed_texts_by_relative_path or {},
            path_roles_by_relative_path=path_roles_by_relative_path or {},
            previous_snapshot_index_payload=previous_snapshot_index_payload,
            changed_relative_paths=changed_relative_path_set,
        )
        source_snapshot_fingerprint = source_fingerprint.source_snapshot_fingerprint
        source_text_hash_index = source_fingerprint.source_text_hash_index
        snapshot_fingerprint = _code_package_text_snapshot_fingerprint(
            source_snapshot_fingerprint=source_snapshot_fingerprint,
            code_package_artifact_refs=code_package_artifact_refs,
        )
    with commit_perf_span(
        phase=(
            "code_package.snapshot_commit.source_fingerprint_delta_hit"
            if source_fingerprint.delta_hit
            else "code_package.snapshot_commit.source_fingerprint_full_hash"
        ),
        category="code_package.snapshot_commit",
        metadata={
            "changed_path_count": len(changed_relative_path_set),
            "source_text_count": len(source_texts_by_relative_path),
            "unparsed_text_count": len(unparsed_texts_by_relative_path or {}),
        },
    ):
        pass
    _record_wall_phase(
        "fingerprint",
        source_fingerprint_delta_hit=source_fingerprint.delta_hit,
    )
    with commit_perf_span(
        phase="code_package.snapshot_commit.fast_noop_lookup",
        category="code_package.snapshot_commit",
    ):
        fast_noop = await _code_package_text_snapshot_index_noop_result(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name=package_name,
            language=language,
            surface=surface,
            manifest_kind=manifest_kind,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root,
            sources_root=sources_root,
            fqn_prefix=fqn_prefix,
            domain_oig_id=domain_oig_id,
            snapshot_fingerprint=snapshot_fingerprint,
            snapshot_index_payload=previous_snapshot_index_payload,
        )
    if fast_noop is not None:
        _record_wall_phase("fast_noop_return")
        return fast_noop
    _record_wall_phase("fast_noop_lookup")
    if (
        previous_snapshot_index_payload is not None
        and not _code_package_snapshot_index_payload_has_reuse_sections(
            previous_snapshot_index_payload,
        )
    ):
        with commit_perf_span(
            phase="code_package.snapshot_commit.load_snapshot_index_sections",
            category="code_package.snapshot_commit",
        ):
            _head, previous_snapshot_index_payload = (
                await _load_current_code_package_text_snapshot_index_payload_with_head(
                    store=store,
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    code_package_id=code_package_id,
                    include_sections=True,
                    include_source_object_index=False,
                )
            )
        _record_wall_phase(
            "load_snapshot_index_sections",
            previous_snapshot_index=previous_snapshot_index_payload is not None,
        )

    with commit_perf_span(
        phase="code_package.snapshot_commit.input_plan_index",
        category="code_package.snapshot_commit",
        metadata={
            "source_text_count": len(source_texts_by_relative_path),
            "unparsed_text_count": len(unparsed_texts_by_relative_path or {}),
            "artifact_count": len(code_package_artifact_refs),
            "changed_path_count": len(changed_relative_path_set),
        },
    ):
        partial_plan_paths = (
            changed_relative_path_set
            if changed_relative_path_set and previous_snapshot_index_payload is not None
            else frozenset()
        )
        plans_are_partial = bool(partial_plan_paths)
        plans_by_relative_path = _code_package_snapshot_plans_by_relative_path(
            language=language,
            source_texts_by_relative_path=source_texts_by_relative_path,
            source_plans_by_relative_path=source_plans_by_relative_path or {},
            unparsed_texts_by_relative_path=unparsed_texts_by_relative_path or {},
            include_relative_paths=partial_plan_paths or None,
        )
        source_object_path_index: Mapping[str, tuple[UUID, ...]] | None = (
            None
            if plans_are_partial
            else _code_package_source_object_path_index_from_snapshot_inputs(
                code_package_id=code_package_id,
                plans_by_relative_path=plans_by_relative_path,
                code_package_artifact_refs=code_package_artifact_refs,
            )
        )
    _record_wall_phase(
        "input_plan_index",
        plan_count=len(plans_by_relative_path),
        partial_plan_index=plans_are_partial,
    )

    def _ensure_full_plan_index() -> None:
        nonlocal plans_are_partial
        nonlocal plans_by_relative_path
        nonlocal source_object_path_index
        if not plans_are_partial:
            return
        with commit_perf_span(
            phase="code_package.snapshot_commit.input_plan_index.full_fallback",
            category="code_package.snapshot_commit",
            metadata={
                "source_text_count": len(source_texts_by_relative_path),
                "unparsed_text_count": len(unparsed_texts_by_relative_path or {}),
                "artifact_count": len(code_package_artifact_refs),
            },
        ):
            plans_by_relative_path = _code_package_snapshot_plans_by_relative_path(
                language=language,
                source_texts_by_relative_path=source_texts_by_relative_path,
                source_plans_by_relative_path=source_plans_by_relative_path or {},
                unparsed_texts_by_relative_path=unparsed_texts_by_relative_path or {},
            )
            source_object_path_index = (
                _code_package_source_object_path_index_from_snapshot_inputs(
                    code_package_id=code_package_id,
                    plans_by_relative_path=plans_by_relative_path,
                    code_package_artifact_refs=code_package_artifact_refs,
                )
            )
            plans_are_partial = False

    with commit_perf_span(
        phase="code_package.snapshot_commit.identity_head_index",
        category="code_package.snapshot_commit",
    ):
        _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
            index=index,
            projection_hash=projection_hash,
        )
        if opgi is None:
            raise RuntimeError(
                "CodePackage text snapshot commit missing "
                "ObjectProjectionGraphIdentity: "
                f"projection_hash={projection_hash}"
            )
        oigi_id = stable_object_instance_graph_identity_id(
            object_projection_graph_identity_id=opgi.id,
            object_instance_graph_id=domain_oig_id,
        )
    with commit_perf_span(
        phase="_code_package_artifact_state_index_from_refs_delta",
        category="code_package.artifact_state_index",
        metadata={
            "artifact_count": len(code_package_artifact_refs),
            "changed_path_count": len(changed_relative_path_set),
        },
    ):
        artifact_state_index = _code_package_artifact_state_index_from_refs_delta(
            code_package_id=code_package_id,
            code_package_artifact_refs=code_package_artifact_refs,
            previous_snapshot_index_payload=previous_snapshot_index_payload,
            changed_relative_paths=changed_relative_path_set,
        )
    if artifact_state_index is None:
        artifact_state_index = _code_package_artifact_state_index_from_refs(
            code_package_id=code_package_id,
            code_package_artifact_refs=code_package_artifact_refs,
        )
    _record_wall_phase(
        "identity_and_artifact_index",
        artifact_count=len(code_package_artifact_refs),
    )
    current_source_states_by_id: dict[UUID, _CodePackageSourceObjectState] | None = None
    full_source_object_ids: frozenset[UUID] | None = None
    build_relationship_topology = True
    current_source_object_path_index = source_object_path_index
    changed_path_source_state: _CodePackageChangedPathSourceState | None = None
    previous_source_states_by_id: dict[UUID, _CodePackageSourceObjectState] | None = (
        None
    )
    if (
        changed_relative_path_set
        and previous_snapshot_index_payload is not None
        and not isinstance(
            previous_snapshot_index_payload.get("source_object_state_index"),
            Mapping,
        )
        and isinstance(
            previous_snapshot_index_payload.get("source_object_state_index_ref"),
            Mapping,
        )
    ):
        with commit_perf_span(
            phase="code_package.reused_state.selected_source_index_view",
            category="code_package.reused_state",
            metadata={"changed_path_count": len(changed_relative_path_set)},
        ):
            selected_source_object_index = (
                _load_code_package_text_snapshot_source_object_state_index_selected(
                    store=store,
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    code_package_id=code_package_id,
                    snapshot_index_payload=previous_snapshot_index_payload,
                    relative_paths=changed_relative_path_set,
                )
            )
        if selected_source_object_index is not None:
            previous_snapshot_index_payload = {
                **previous_snapshot_index_payload,
                "source_object_state_index": selected_source_object_index,
            }
    with commit_perf_span(
        phase="code_package.reused_state.raw_source_index_view",
        category="code_package.reused_state",
    ):
        previous_source_raw_index_view = (
            _code_package_source_object_raw_index_view_from_index_payload(
                previous_snapshot_index_payload,
            )
        )
    previous_source_index_view: _CodePackageSourceObjectIndexView | None = None
    if (
        head is not None
        and previous_source_raw_index_view is not None
        and previous_source_raw_index_view.object_count
        >= _CODE_PACKAGE_PARTIAL_SOURCE_REUSE_MIN_SOURCE_OBJECT_COUNT
    ):
        with commit_perf_span(
            phase="code_package.reused_state.prebuild_source_signatures",
            category="code_package.reused_state",
            metadata={
                "previous_object_count": previous_source_raw_index_view.object_count,
                "changed_path_count": len(changed_relative_path_set),
            },
        ):
            changed_path_source_state = (
                _code_package_changed_path_source_state_from_snapshot_inputs(
                    domain_oig_id=domain_oig_id,
                    code_package_id=code_package_id,
                    code_package_config_id=code_package_config_id,
                    package_name=package_name,
                    language=language,
                    surface=surface,
                    manifest_kind=manifest_kind,
                    manifest_relative_path=manifest_relative_path,
                    package_root=package_root,
                    sources_root=sources_root,
                    fqn_prefix=fqn_prefix,
                    plans_by_relative_path=plans_by_relative_path,
                    path_roles_by_relative_path=path_roles_by_relative_path or {},
                    code_package_artifact_refs=code_package_artifact_refs,
                    changed_relative_paths=changed_relative_path_set,
                    previous_source_index_view=previous_source_raw_index_view,
                )
            )
            if changed_path_source_state is not None:
                full_source_object_ids = (
                    changed_path_source_state.changed_source_object_ids
                )
                current_source_object_path_index = (
                    changed_path_source_state.source_object_path_index
                )
                build_relationship_topology = (
                    changed_path_source_state.build_relationship_topology
                )
            else:
                previous_source_index_view = (
                    _code_package_source_object_index_view_from_index_payload(
                        previous_snapshot_index_payload,
                    )
                )
                if previous_source_index_view is None:
                    previous_source_states_by_id = None
                else:
                    previous_source_states_by_id = (
                        _code_package_source_object_states_from_index_view(
                            previous_source_index_view,
                        )
                    )
                if previous_source_states_by_id is None:
                    _ensure_full_plan_index()
                    previous_source_index_view = None
                else:
                    current_source_build = (
                        _code_package_source_object_state_build_from_snapshot_inputs(
                            domain_oig_id=domain_oig_id,
                            code_package_id=code_package_id,
                            code_package_config_id=code_package_config_id,
                            package_name=package_name,
                            language=language,
                            surface=surface,
                            manifest_kind=manifest_kind,
                            manifest_relative_path=manifest_relative_path,
                            package_root=package_root,
                            sources_root=sources_root,
                            fqn_prefix=fqn_prefix,
                            plans_by_relative_path=plans_by_relative_path,
                            path_roles_by_relative_path=path_roles_by_relative_path
                            or {},
                            code_package_artifact_refs=code_package_artifact_refs,
                        )
                    )
                    current_source_states_by_id = dict(
                        current_source_build.states_by_id,
                    )
                    current_source_object_path_index = (
                        current_source_build.path_source_object_ids
                    )
                    changed_source_object_ids = {
                        source_object_id
                        for source_object_id, source_state in (
                            current_source_states_by_id.items()
                        )
                        if previous_source_states_by_id.get(source_object_id)
                        != source_state
                    }
                    changed_source_object_ids.add(code_package_id)
                    full_source_object_ids = frozenset(changed_source_object_ids)
                    build_relationship_topology = set(
                        previous_source_states_by_id,
                    ) != set(
                        current_source_states_by_id,
                    )
    elif previous_source_raw_index_view is not None:
        previous_source_index_view = (
            _code_package_source_object_index_view_from_index_payload(
                previous_snapshot_index_payload,
            )
        )
        if previous_source_index_view is not None:
            previous_source_states_by_id = (
                _code_package_source_object_states_from_index_view(
                    previous_source_index_view,
                )
            )
    if full_source_object_ids is None or build_relationship_topology:
        _ensure_full_plan_index()
    _record_wall_phase(
        "source_state_reuse",
        reused_source_states=current_source_states_by_id is not None,
        full_source_object_filter=full_source_object_ids is not None,
        partial_plan_index=plans_are_partial,
    )

    with commit_perf_span(
        phase="code_package.snapshot_commit.build_objects",
        category="code_package.snapshot_commit",
        metadata={
            "full_source_object_filter": full_source_object_ids is not None,
            "build_relationship_topology": build_relationship_topology,
        },
    ):
        code_package, objects_by_id = await _build_code_package_text_snapshot_objects(
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name=package_name,
            language=language,
            surface=surface,
            manifest_kind=manifest_kind,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root,
            sources_root=sources_root,
            fqn_prefix=fqn_prefix,
            source_texts_by_relative_path=source_texts_by_relative_path,
            source_plans_by_relative_path=source_plans_by_relative_path or {},
            unparsed_texts_by_relative_path=unparsed_texts_by_relative_path or {},
            path_roles_by_relative_path=path_roles_by_relative_path or {},
            code_package_artifact_refs=code_package_artifact_refs,
            plans_by_relative_path=plans_by_relative_path,
            full_source_object_ids=full_source_object_ids,
            build_relationship_topology=build_relationship_topology,
        )
    _record_wall_phase(
        "build_objects",
        object_count=len(objects_by_id),
        full_source_object_filter=full_source_object_ids is not None,
    )
    with commit_perf_span(
        phase="code_package.snapshot_commit.reused_witness_desired_state",
        category="code_package.snapshot_commit",
        metadata={"object_count": len(objects_by_id)},
    ):
        desired_state = (
            await _try_build_code_package_reused_witness_segment_desired_state(
                index=index,
                opg=opg,
                branch_id=branch_id,
                projection_hash=projection_hash,
                head=head,
                previous_snapshot_index_payload=previous_snapshot_index_payload,
                domain_oig_id=domain_oig_id,
                code_package=code_package,
                code_package_config_id=code_package_config_id,
                manifest_kind=manifest_kind,
                surface=surface,
                objects_by_id=objects_by_id,
                current_source_states_by_id=current_source_states_by_id,
                changed_path_source_state=changed_path_source_state,
                current_source_object_path_index=current_source_object_path_index,
                previous_source_states_by_id=previous_source_states_by_id,
                oigi_id=oigi_id,
            )
        )
    if desired_state is None:
        with commit_perf_span(
            phase="code_package.snapshot_commit.reused_direct_desired_state",
            category="code_package.snapshot_commit",
            metadata={"object_count": len(objects_by_id)},
        ):
            desired_state = await _try_build_code_package_reused_direct_desired_state(
                index=index,
                opg=opg,
                branch_id=branch_id,
                projection_hash=projection_hash,
                head=head,
                previous_snapshot_index_payload=previous_snapshot_index_payload,
                domain_oig_id=domain_oig_id,
                code_package=code_package,
                code_package_config_id=code_package_config_id,
                manifest_kind=manifest_kind,
                surface=surface,
                objects_by_id=objects_by_id,
                current_source_states_by_id=current_source_states_by_id,
                current_source_object_path_index=current_source_object_path_index,
            )
    if desired_state is None and full_source_object_ids is not None:
        _ensure_full_plan_index()
        code_package, objects_by_id = await _build_code_package_text_snapshot_objects(
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name=package_name,
            language=language,
            surface=surface,
            manifest_kind=manifest_kind,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root,
            sources_root=sources_root,
            fqn_prefix=fqn_prefix,
            source_texts_by_relative_path=source_texts_by_relative_path,
            source_plans_by_relative_path=source_plans_by_relative_path or {},
            unparsed_texts_by_relative_path=unparsed_texts_by_relative_path or {},
            path_roles_by_relative_path=path_roles_by_relative_path or {},
            code_package_artifact_refs=code_package_artifact_refs,
            plans_by_relative_path=plans_by_relative_path,
        )
        current_source_states_by_id = None
        full_source_object_ids = None
        desired_state = (
            await _try_build_code_package_reused_witness_segment_desired_state(
                index=index,
                opg=opg,
                branch_id=branch_id,
                projection_hash=projection_hash,
                head=head,
                previous_snapshot_index_payload=previous_snapshot_index_payload,
                domain_oig_id=domain_oig_id,
                code_package=code_package,
                code_package_config_id=code_package_config_id,
                manifest_kind=manifest_kind,
                surface=surface,
                objects_by_id=objects_by_id,
                current_source_states_by_id=current_source_states_by_id,
                changed_path_source_state=None,
                current_source_object_path_index=current_source_object_path_index,
                previous_source_states_by_id=previous_source_states_by_id,
                oigi_id=oigi_id,
            )
        )
        if desired_state is None:
            desired_state = await _try_build_code_package_reused_direct_desired_state(
                index=index,
                opg=opg,
                branch_id=branch_id,
                projection_hash=projection_hash,
                head=head,
                previous_snapshot_index_payload=previous_snapshot_index_payload,
                domain_oig_id=domain_oig_id,
                code_package=code_package,
                code_package_config_id=code_package_config_id,
                manifest_kind=manifest_kind,
                surface=surface,
                objects_by_id=objects_by_id,
                current_source_object_path_index=current_source_object_path_index,
            )
    if desired_state is None:
        desired_state = _build_code_package_direct_desired_state(
            index=index,
            opg=opg,
            branch_id=branch_id,
            domain_oig_id=domain_oig_id,
            code_package=code_package,
            code_package_config_id=code_package_config_id,
            manifest_kind=manifest_kind,
            surface=surface,
            objects_by_id=objects_by_id,
            materialize_class_instances=False,
            source_object_path_index=current_source_object_path_index,
        )
    if _head_uuid(head, "commit_id") is None:
        desired_state = _code_package_seed_witness_desired_state_if_enabled(
            desired_state,
        )
    _record_wall_phase(
        "desired_state",
        graph_hash_source=desired_state.graph_hash_source,
        has_precomputed_change_result=desired_state.precomputed_change_result
        is not None,
    )
    desired_state_index = desired_state.state_index
    graph_hash_post = desired_state.graph_hash
    object_count = _code_package_source_object_count_from_index(
        desired_state.source_object_state_index,
        fallback=len(objects_by_id),
    )
    head_commit_id = _head_uuid(head, "commit_id")
    head_oig_id = _head_uuid(head, "object_instance_graph_id")
    head_root_object_id = _head_uuid(head, "root_object_id")
    head_oig_commit_id = _head_uuid(head, "object_instance_graph_commit_id")
    head_graph_hash_post = _head_string(head, "graph_hash_post")
    timeline_parent_commit_id = head_commit_id
    if head_commit_id is None:
        commit_id = _code_package_text_snapshot_commit_id(
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package.id,
            parent_commit_id=None,
            graph_hash_pre=graph_hash_post,
            graph_hash_post=graph_hash_post,
        )
        record = await FSLaneCommitter().commit_record_seed(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=domain_oig_id,
            pre_state_index=desired_state_index,
            root_metadata=desired_state.root_metadata,
            root_object_id=code_package.id,
            graph_hash_pre=graph_hash_post,
            graph_hash_post=graph_hash_post,
            author_id=resolve_meta_author_id(actor_id),
            commit_id=commit_id,
            commit_action=CommitActionDescriptor(
                operation_label="CodePackage.materialize_text_snapshot",
                call_target="generated_materialization",
                object_id=code_package.id,
            ),
            graph_hash_source=desired_state.graph_hash_source,
        )
        state_snapshot_metadata = (
            await _ensure_code_package_text_snapshot_state_snapshot_from_state(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=record.commit_id,
                desired_state=desired_state,
            )
        )
        _write_code_package_text_snapshot_index(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package.id,
            snapshot_fingerprint=snapshot_fingerprint,
            source_snapshot_fingerprint=source_snapshot_fingerprint,
            commit_id=record.commit_id,
            head_commit_id=record.commit_id,
            object_instance_graph_commit_id=record.object_instance_graph_commit_id,
            object_instance_graph_id=domain_oig_id,
            graph_hash_post=graph_hash_post,
            object_count=object_count,
            change_count=0,
            artifact_state_index=artifact_state_index,
            state_snapshot_metadata=state_snapshot_metadata,
            source_object_state_index=desired_state.source_object_state_index,
            source_text_hash_index=source_text_hash_index,
        )
        _record_wall_phase(
            "seed_append_snapshot",
            object_count=object_count,
            graph_hash_source=desired_state.graph_hash_source,
        )
        return CodePackageTextSnapshotCommitResult(
            code_package=code_package,
            commit_id=record.commit_id,
            head_commit_id=record.commit_id,
            object_instance_graph_commit_id=record.object_instance_graph_commit_id,
            object_count=object_count,
            change_count=0,
        )
    if (
        head_commit_id is not None
        and head_oig_commit_id is not None
        and head_oig_id == domain_oig_id
        and head_root_object_id == code_package.id
        and head_graph_hash_post == graph_hash_post
    ):
        state_snapshot_metadata = (
            await _ensure_code_package_text_snapshot_state_snapshot_from_state(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=head_commit_id,
                desired_state=desired_state,
            )
        )
        _write_code_package_text_snapshot_index(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package.id,
            snapshot_fingerprint=snapshot_fingerprint,
            source_snapshot_fingerprint=source_snapshot_fingerprint,
            commit_id=head_commit_id,
            head_commit_id=head_commit_id,
            object_instance_graph_commit_id=head_oig_commit_id,
            object_instance_graph_id=domain_oig_id,
            graph_hash_post=graph_hash_post,
            object_count=object_count,
            change_count=0,
            artifact_state_index=artifact_state_index,
            state_snapshot_metadata=state_snapshot_metadata,
            source_object_state_index=desired_state.source_object_state_index,
            source_text_hash_index=source_text_hash_index,
        )
        _record_wall_phase(
            "same_hash_snapshot_refresh",
            object_count=object_count,
            graph_hash_source=desired_state.graph_hash_source,
        )
        return CodePackageTextSnapshotCommitResult(
            code_package=code_package,
            commit_id=head_commit_id,
            head_commit_id=head_commit_id,
            object_instance_graph_commit_id=head_oig_commit_id,
            object_count=object_count,
            change_count=0,
        )
    sidecar_change_result = desired_state.precomputed_change_result
    if sidecar_change_result is None:
        sidecar_change_result = (
            await _build_code_package_text_snapshot_changes_from_snapshot_state(
                branch_id=branch_id,
                projection_hash=projection_hash,
                head=head,
                previous_snapshot_index_payload=previous_snapshot_index_payload,
                domain_oig_id=domain_oig_id,
                root_object_id=code_package.id,
                desired_state=desired_state,
                desired_state_index=desired_state_index,
                oigi_id=oigi_id,
                previous_snapshot_payload=desired_state.previous_snapshot_payload,
                previous_snapshot_state_rows=desired_state.previous_snapshot_state_rows,
                previous_snapshot_state_maps=desired_state.previous_snapshot_state_maps,
            )
        )
    pre_state_evidence: ObjectInstanceGraphCommitPreStateEvidence | None = None
    if sidecar_change_result is not None:
        changes = sidecar_change_result.changes
        pre_state_index = sidecar_change_result.pre_state_index
        pre_state_evidence = sidecar_change_result.pre_state_evidence
        graph_hash_pre = _code_package_pre_state_evidence_graph_hash(
            pre_state_evidence,
        )
        root_metadata_for_commit = desired_state.root_metadata
    else:
        if desired_state.class_instance_payloads:
            if full_source_object_ids is not None and len(objects_by_id) < object_count:
                _ensure_full_plan_index()
                code_package, objects_by_id = (
                    await _build_code_package_text_snapshot_objects(
                        code_package_id=code_package_id,
                        code_package_config_id=code_package_config_id,
                        package_name=package_name,
                        language=language,
                        surface=surface,
                        manifest_kind=manifest_kind,
                        manifest_relative_path=manifest_relative_path,
                        package_root=package_root,
                        sources_root=sources_root,
                        fqn_prefix=fqn_prefix,
                        source_texts_by_relative_path=source_texts_by_relative_path,
                        source_plans_by_relative_path=(
                            source_plans_by_relative_path or {}
                        ),
                        unparsed_texts_by_relative_path=(
                            unparsed_texts_by_relative_path or {}
                        ),
                        path_roles_by_relative_path=(path_roles_by_relative_path or {}),
                        code_package_artifact_refs=code_package_artifact_refs,
                        plans_by_relative_path=plans_by_relative_path,
                    )
                )
                full_source_object_ids = None
            desired_state = _build_code_package_direct_desired_state(
                index=index,
                opg=opg,
                branch_id=branch_id,
                domain_oig_id=domain_oig_id,
                code_package=code_package,
                code_package_config_id=code_package_config_id,
                manifest_kind=manifest_kind,
                surface=surface,
                objects_by_id=objects_by_id,
                source_object_path_index=current_source_object_path_index,
            )
            desired_state_index = desired_state.state_index
            graph_hash_post = desired_state.graph_hash
            object_count = _code_package_source_object_count_from_index(
                desired_state.source_object_state_index,
                fallback=len(objects_by_id),
            )
        desired_oig = _build_code_package_oig_from_desired_state(
            index=index,
            opg=opg,
            branch_id=branch_id,
            domain_oig_id=domain_oig_id,
            desired_state=desired_state,
        )
        desired_oig.hash = graph_hash_post
        try:
            before_oig = await _load_code_package_before_oig(
                index=index,
                branch_id=branch_id,
                projection_hash=projection_hash,
                domain_oig_id=domain_oig_id,
                root_object_id=code_package.id,
            )
        except AttributeValueTreeValidationError:
            _reset_code_package_text_snapshot_lane(
                store=store,
                branch_id=branch_id,
                projection_hash=projection_hash,
            )
            before_oig = _build_code_package_rooted_base(
                index=index,
                opg=opg,
                branch_id=branch_id,
                domain_oig_id=domain_oig_id,
                root_object_id=code_package.id,
            )
            head_commit_id = None

        if _root_source_object_id(before_oig) != code_package.id:
            _reset_code_package_text_snapshot_lane(
                store=store,
                branch_id=branch_id,
                projection_hash=projection_hash,
            )
            before_oig = _build_code_package_rooted_base(
                index=index,
                opg=opg,
                branch_id=branch_id,
                domain_oig_id=domain_oig_id,
                root_object_id=code_package.id,
            )
            head = None
            head_commit_id = None

        pre_state_index = build_commit_state_index(before_oig)
        graph_hash_pre = pre_state_index.compute_hash()
        before_oig.hash = graph_hash_pre
        root_metadata_for_commit = extract_object_instance_graph_commit_root_metadata(
            graph=before_oig,
        )

        changes = _build_code_package_text_snapshot_changes(
            before_oig=before_oig,
            desired_oig=desired_oig,
            oigi_id=oigi_id,
        )

    _record_wall_phase(
        "change_plan",
        change_count=len(changes),
        pre_state_evidence=pre_state_evidence is not None,
        full_source_object_filter=full_source_object_ids is not None,
    )
    if not changes:
        raw_head_commit_id = _head_uuid(head, "commit_id")
        raw_head_oig_commit_id = _head_uuid(head, "object_instance_graph_commit_id")
        raw_head_graph_hash_post = _head_string(head, "graph_hash_post")
        if raw_head_commit_id is None or raw_head_oig_commit_id is None:
            raise RuntimeError(
                "CodePackage text snapshot commit produced no OIG changes and no "
                f"existing lane head: package_name={package_name!r}"
            )
        head_commit_id = raw_head_commit_id
        state_snapshot_metadata = (
            await _ensure_code_package_text_snapshot_state_snapshot_from_state(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=head_commit_id,
                desired_state=desired_state,
            )
        )
        _write_code_package_text_snapshot_index(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package.id,
            snapshot_fingerprint=snapshot_fingerprint,
            source_snapshot_fingerprint=source_snapshot_fingerprint,
            commit_id=head_commit_id,
            head_commit_id=head_commit_id,
            object_instance_graph_commit_id=raw_head_oig_commit_id,
            object_instance_graph_id=domain_oig_id,
            graph_hash_post=raw_head_graph_hash_post or graph_hash_pre,
            object_count=object_count,
            change_count=0,
            artifact_state_index=artifact_state_index,
            state_snapshot_metadata=state_snapshot_metadata,
            source_object_state_index=desired_state.source_object_state_index,
            source_text_hash_index=source_text_hash_index,
        )
        _record_wall_phase(
            "no_change_snapshot_refresh",
            object_count=object_count,
            graph_hash_source=desired_state.graph_hash_source,
        )
        return CodePackageTextSnapshotCommitResult(
            code_package=code_package,
            commit_id=head_commit_id,
            head_commit_id=head_commit_id,
            object_instance_graph_commit_id=raw_head_oig_commit_id,
            object_count=object_count,
            change_count=0,
        )
    commit_id = _code_package_text_snapshot_commit_id(
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package.id,
        parent_commit_id=timeline_parent_commit_id,
        graph_hash_pre=graph_hash_pre,
        graph_hash_post=graph_hash_post,
    )
    committer = FSLaneCommitter()
    commit_action = CommitActionDescriptor(
        operation_label="CodePackage.materialize_text_snapshot",
        call_target="generated_materialization",
        object_id=code_package.id,
    )
    if pre_state_evidence is not None:
        with commit_perf_span(
            phase="code_package.snapshot_commit.append_pre_state_evidence",
            category="code_package.snapshot_commit",
            metadata={"change_count": len(changes)},
        ):
            record = await committer.commit_record_shallow_from_pre_state_evidence(
                branch_id=branch_id,
                projection_hash=projection_hash,
                object_instance_graph_identity_id=oigi_id,
                object_instance_graph_id=domain_oig_id,
                pre_state_evidence=pre_state_evidence,
                root_metadata=root_metadata_for_commit,
                root_object_id=code_package.id,
                changes=changes,
                graph_hash_pre=graph_hash_pre,
                graph_hash_post=graph_hash_post,
                author_id=resolve_meta_author_id(actor_id),
                commit_id=commit_id,
                commit_action=commit_action,
            )
        appended_commit_id = record.commit_id
        object_instance_graph_commit_id = record.object_instance_graph_commit_id
    else:
        if pre_state_index is None:
            raise RuntimeError(
                "CodePackage legacy shallow commit missing pre-state index"
            )
        with commit_perf_span(
            phase="code_package.snapshot_commit.append_legacy_shallow",
            category="code_package.snapshot_commit",
            metadata={"change_count": len(changes)},
        ):
            commit = await committer.commit_shallow(
                branch_id=branch_id,
                projection_hash=projection_hash,
                object_instance_graph_identity_id=oigi_id,
                object_instance_graph_id=domain_oig_id,
                pre_state_index=pre_state_index,
                root_metadata=root_metadata_for_commit,
                root_object_id=code_package.id,
                changes=changes,
                graph_hash_pre=graph_hash_pre,
                graph_hash_post=graph_hash_post,
                author_id=resolve_meta_author_id(actor_id),
                commit_id=commit_id,
                commit_action=commit_action,
            )
        if commit is None or commit.commit is None:
            raise RuntimeError(
                "CodePackage text snapshot commit did not append a lane commit: "
                f"package_name={package_name!r}"
            )
        appended_commit_id = commit.commit.id
        object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        )
    _record_wall_phase(
        "append",
        change_count=len(changes),
        pre_state_evidence=pre_state_evidence is not None,
    )
    state_snapshot_metadata = (
        await _ensure_code_package_text_snapshot_state_snapshot_from_state(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=appended_commit_id,
            desired_state=desired_state,
        )
    )
    _record_wall_phase(
        "state_snapshot",
        object_count=object_count,
        graph_hash_source=desired_state.graph_hash_source,
    )
    _write_code_package_text_snapshot_index(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package.id,
        snapshot_fingerprint=snapshot_fingerprint,
        source_snapshot_fingerprint=source_snapshot_fingerprint,
        commit_id=appended_commit_id,
        head_commit_id=appended_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        object_instance_graph_id=domain_oig_id,
        graph_hash_post=graph_hash_post,
        object_count=object_count,
        change_count=len(changes),
        artifact_state_index=artifact_state_index,
        state_snapshot_metadata=state_snapshot_metadata,
        source_object_state_index=desired_state.source_object_state_index,
        source_text_hash_index=source_text_hash_index,
    )
    _record_wall_phase("write_snapshot_index", change_count=len(changes))
    return CodePackageTextSnapshotCommitResult(
        code_package=code_package,
        commit_id=appended_commit_id,
        head_commit_id=appended_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        object_count=object_count,
        change_count=len(changes),
    )


async def _build_code_package_text_snapshot_objects(
    *,
    code_package_id: UUID,
    code_package_config_id: UUID,
    package_name: str,
    language: CodeLanguage,
    surface: str,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
    source_texts_by_relative_path: Mapping[str, str],
    source_plans_by_relative_path: Mapping[str, CodeContentPlan],
    unparsed_texts_by_relative_path: Mapping[str, str],
    path_roles_by_relative_path: Mapping[str, CodePackagePathRole],
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
    plans_by_relative_path: Mapping[str, CodeContentPlan] | None = None,
    full_source_object_ids: frozenset[UUID] | None = None,
    build_relationship_topology: bool = True,
) -> tuple[CodePackage, dict[UUID, BaseORMModel]]:
    normalized_package_name = (package_name or "").strip()
    normalized_manifest_relative_path = (manifest_relative_path or "").strip()
    normalized_package_root = (package_root or "").strip()
    if not normalized_package_name:
        raise RuntimeError("CodePackage snapshot requires non-empty package_name")
    if not normalized_manifest_relative_path:
        raise RuntimeError(
            "CodePackage snapshot requires non-empty manifest_relative_path"
        )
    if not normalized_package_root:
        raise RuntimeError("CodePackage snapshot requires non-empty package_root")
    if plans_by_relative_path is None:
        plans_by_relative_path = _code_package_snapshot_plans_by_relative_path(
            language=language,
            source_texts_by_relative_path=source_texts_by_relative_path,
            source_plans_by_relative_path=source_plans_by_relative_path,
            unparsed_texts_by_relative_path=unparsed_texts_by_relative_path,
        )
    if full_source_object_ids is None:
        return _build_code_package_text_snapshot_objects_full(
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name=normalized_package_name,
            language=language,
            surface=surface,
            manifest_kind=manifest_kind,
            manifest_relative_path=normalized_manifest_relative_path,
            package_root=normalized_package_root,
            sources_root=sources_root,
            fqn_prefix=fqn_prefix,
            plans_by_relative_path=plans_by_relative_path,
            path_roles_by_relative_path=path_roles_by_relative_path,
            code_package_artifact_refs=code_package_artifact_refs,
        )
    objects_by_id: dict[UUID, BaseORMModel] = {}
    selected_full_source_object_ids = frozenset(
        (*full_source_object_ids, code_package_id)
    )

    def _needs_full_object(source_object_id: UUID) -> bool:
        return source_object_id in selected_full_source_object_ids

    def _remember_if_full(obj: BaseORMModel) -> BaseORMModel:
        obj_id = getattr(obj, "id", None)
        if isinstance(obj_id, UUID) and _needs_full_object(obj_id):
            return _remember(objects_by_id, obj)
        return obj

    code_package = _remember(
        objects_by_id,
        _build_code_package_identity(
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name=normalized_package_name,
            language=language,
            surface=surface,
            manifest_kind=manifest_kind,
            manifest_relative_path=normalized_manifest_relative_path,
            package_root=normalized_package_root,
            sources_root=sources_root,
            fqn_prefix=fqn_prefix,
        ),
    )
    for relative_path, plan in sorted(plans_by_relative_path.items()):
        code_package_code_id = stable_code_package_code_id(
            code_package_id=code_package.id,
            relative_path=relative_path,
        )
        code_id = stable_code_id(
            code_package_code_id=code_package_code_id,
            relative_path=relative_path,
        )
        content_part_text_id = _stable_code_content_part_text_id(code_id=code_id)
        section_items: list[tuple[object, CodeSectionType, UUID, UUID]] = []
        for descriptor in plan.section_plans:
            section_type = CodeSectionType(descriptor.section_type.value)
            section_id = stable_code_section_id(
                code_id=code_id,
                section_key=descriptor.section_key,
                type=section_type.value,
            )
            segment_id = stable_content_part_text_segment_id(
                content_part_text_id=content_part_text_id,
                key=f"code-section:{section_id}",
            )
            section_items.append((descriptor, section_type, section_id, segment_id))
        path_source_object_ids = {
            code_package_code_id,
            code_id,
            content_part_text_id,
            *(section_id for _descriptor, _type, section_id, _segment in section_items),
            *(segment_id for _descriptor, _type, _section, segment_id in section_items),
        }
        if (
            selected_full_source_object_ids is not None
            and not build_relationship_topology
            and path_source_object_ids.isdisjoint(selected_full_source_object_ids)
        ):
            continue
        if _needs_full_object(content_part_text_id):
            content_part_text = _remember(
                objects_by_id,
                ContentPartText(
                    id=content_part_text_id,
                    key="default",
                    inline_text=plan.content_text,
                ),
            )
        else:
            content_part_text = ContentPartText.model_construct(
                id=content_part_text_id,
                key="default",
                inline_text=plan.content_text,
                segments=[],
            )
        if _needs_full_object(code_id):
            code = _remember(
                objects_by_id,
                Code(
                    id=code_id,
                    code_package_code_id=code_package_code_id,
                    relative_path=relative_path,
                    content_part_text=content_part_text,
                    content_part_text_id=content_part_text.id,
                    language=_enum_value(plan.language),
                ),
            )
        else:
            code = Code.model_construct(
                id=code_id,
                code_package_code_id=code_package_code_id,
                relative_path=relative_path,
                content_part_text=content_part_text,
                content_part_text_id=content_part_text.id,
                language=_enum_value(plan.language),
                code_sections=[],
                tests=[],
            )
        if _needs_full_object(code_package_code_id):
            package_code = _remember(
                objects_by_id,
                CodePackageCode(
                    id=code_package_code_id,
                    code_package_id=code_package.id,
                    code=code,
                    relative_path=relative_path,
                    path_role=_enum_value(
                        path_roles_by_relative_path.get(
                            relative_path,
                            CodePackagePathRole.authored_source,
                        )
                    ),
                ),
            )
        else:
            package_code = CodePackageCode.model_construct(
                id=code_package_code_id,
                code_package_id=code_package.id,
                code=code,
                relative_path=relative_path,
                path_role=_enum_value(
                    path_roles_by_relative_path.get(
                        relative_path,
                        CodePackagePathRole.authored_source,
                    )
                ),
            )
        code_package.code_package_codes.append(package_code)
        for descriptor, section_type, section_id, segment_id in section_items:
            if _needs_full_object(segment_id):
                segment = _remember(
                    objects_by_id,
                    ContentPartTextSegment(
                        id=segment_id,
                        content_part_text_id=content_part_text.id,
                        content_part_text=content_part_text,
                        byte_start=descriptor.byte_start,
                        byte_end=descriptor.byte_end,
                    ),
                )
            else:
                segment = ContentPartTextSegment.model_construct(
                    id=segment_id,
                    content_part_text_id=content_part_text.id,
                    content_part_text=content_part_text,
                    byte_start=descriptor.byte_start,
                    byte_end=descriptor.byte_end,
                    content_part_text_segment_translations=[],
                    key="default",
                    parent=None,
                    parent_id=None,
                    style=None,
                )
            if _needs_full_object(section_id):
                section = _remember(
                    objects_by_id,
                    CodeSection(
                        id=section_id,
                        code_id=code.id,
                        section_key=descriptor.section_key,
                        qualname=descriptor.qualname,
                        type=_enum_value(section_type),
                        identity_hash=descriptor.identity_hash,
                        metadata=descriptor.metadata,
                        content_part_text_segment=segment,
                        content_part_text_segment_id=segment.id,
                    ),
                )
            else:
                section = CodeSection.model_construct(
                    id=section_id,
                    code_id=code.id,
                    section_key=descriptor.section_key,
                    qualname=descriptor.qualname,
                    type=_enum_value(section_type),
                    identity_hash=descriptor.identity_hash,
                    metadata=descriptor.metadata,
                    content_part_text_segment=segment,
                    content_part_text_segment_id=segment.id,
                )
            content_part_text.segments.append(segment)
            code.code_sections.append(section)
    for artifact_ref in sorted(
        code_package_artifact_refs,
        key=lambda item: (item.output_key, item.artifact_key),
    ):
        artifact_id = stable_code_package_artifact_id(
            code_package_id=code_package.id,
            output_key=(artifact_ref.output_key or "").strip(),
            artifact_key=(artifact_ref.artifact_key or "").strip(),
        )
        if (
            selected_full_source_object_ids is not None
            and not build_relationship_topology
            and artifact_id not in selected_full_source_object_ids
        ):
            continue
        artifact = _remember_if_full(
            (
                _build_code_package_artifact_from_ref(
                    code_package_id=code_package.id,
                    artifact_ref=artifact_ref,
                )
                if _needs_full_object(artifact_id)
                else CodePackageArtifact.model_construct(
                    id=artifact_id,
                    code_package_id=code_package.id,
                    output_key=(artifact_ref.output_key or "").strip(),
                    artifact_key=(artifact_ref.artifact_key or "").strip(),
                )
            ),
        )
        code_package.artifacts.append(artifact)
    return code_package, objects_by_id


def _build_code_package_text_snapshot_objects_full(
    *,
    code_package_id: UUID,
    code_package_config_id: UUID,
    package_name: str,
    language: CodeLanguage,
    surface: str,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
    plans_by_relative_path: Mapping[str, CodeContentPlan],
    path_roles_by_relative_path: Mapping[str, CodePackagePathRole],
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
) -> tuple[CodePackage, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    code_package = _remember(
        objects_by_id,
        _build_code_package_identity(
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name=package_name,
            language=language,
            surface=surface,
            manifest_kind=manifest_kind,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root,
            sources_root=sources_root,
            fqn_prefix=fqn_prefix,
        ),
    )
    for relative_path, plan in sorted(plans_by_relative_path.items()):
        code_package_code_id = stable_code_package_code_id(
            code_package_id=code_package.id,
            relative_path=relative_path,
        )
        code_id = stable_code_id(
            code_package_code_id=code_package_code_id,
            relative_path=relative_path,
        )
        content_part_text = _remember(
            objects_by_id,
            ContentPartText(
                id=_stable_code_content_part_text_id(code_id=code_id),
                key="default",
                inline_text=plan.content_text,
            ),
        )
        code = _remember(
            objects_by_id,
            Code(
                id=code_id,
                code_package_code_id=code_package_code_id,
                relative_path=relative_path,
                content_part_text=content_part_text,
                content_part_text_id=content_part_text.id,
                language=_enum_value(plan.language),
            ),
        )
        package_code = _remember(
            objects_by_id,
            CodePackageCode(
                id=code_package_code_id,
                code_package_id=code_package.id,
                code=code,
                relative_path=relative_path,
                path_role=_enum_value(
                    path_roles_by_relative_path.get(
                        relative_path,
                        CodePackagePathRole.authored_source,
                    )
                ),
            ),
        )
        code_package.code_package_codes.append(package_code)
        for descriptor in plan.section_plans:
            section_type = CodeSectionType(descriptor.section_type.value)
            section_id = stable_code_section_id(
                code_id=code.id,
                section_key=descriptor.section_key,
                type=section_type.value,
            )
            segment = _remember(
                objects_by_id,
                ContentPartTextSegment(
                    id=stable_content_part_text_segment_id(
                        content_part_text_id=content_part_text.id,
                        key=f"code-section:{section_id}",
                    ),
                    content_part_text_id=content_part_text.id,
                    content_part_text=content_part_text,
                    byte_start=descriptor.byte_start,
                    byte_end=descriptor.byte_end,
                ),
            )
            section = _remember(
                objects_by_id,
                CodeSection(
                    id=section_id,
                    code_id=code.id,
                    section_key=descriptor.section_key,
                    qualname=descriptor.qualname,
                    type=_enum_value(section_type),
                    identity_hash=descriptor.identity_hash,
                    metadata=descriptor.metadata,
                    content_part_text_segment=segment,
                    content_part_text_segment_id=segment.id,
                ),
            )
            content_part_text.segments.append(segment)
            code.code_sections.append(section)
    for artifact_ref in sorted(
        code_package_artifact_refs,
        key=lambda item: (item.output_key, item.artifact_key),
    ):
        artifact = _remember(
            objects_by_id,
            _build_code_package_artifact_from_ref(
                code_package_id=code_package.id,
                artifact_ref=artifact_ref,
            ),
        )
        code_package.artifacts.append(artifact)
    return code_package, objects_by_id


def _code_package_snapshot_plans_by_relative_path(
    *,
    language: CodeLanguage,
    source_texts_by_relative_path: Mapping[str, str],
    source_plans_by_relative_path: Mapping[str, CodeContentPlan],
    unparsed_texts_by_relative_path: Mapping[str, str],
    include_relative_paths: frozenset[str] | None = None,
) -> dict[str, CodeContentPlan]:
    plans_by_relative_path: dict[str, CodeContentPlan] = {}
    seen_relative_paths: set[str] = set()

    def _should_include(relative_path: str) -> bool:
        return include_relative_paths is None or relative_path in include_relative_paths

    for relative_path, content_text in source_texts_by_relative_path.items():
        seen_relative_paths.add(relative_path)
        if _should_include(relative_path):
            plans_by_relative_path[relative_path] = (
                build_code_content_plan_copy_from_text(
                    content_text=content_text,
                    language=language,
                )
            )
    for relative_path, content_plan in source_plans_by_relative_path.items():
        if relative_path in seen_relative_paths:
            raise RuntimeError(
                "CodePackage snapshot received duplicate text/plan path: "
                f"{relative_path}"
            )
        seen_relative_paths.add(relative_path)
        if _should_include(relative_path):
            plans_by_relative_path[relative_path] = content_plan
    for relative_path, content_text in unparsed_texts_by_relative_path.items():
        if relative_path in seen_relative_paths:
            raise RuntimeError(
                "CodePackage snapshot received duplicate parsed/unparsed path: "
                f"{relative_path}"
            )
        seen_relative_paths.add(relative_path)
        if _should_include(relative_path):
            plans_by_relative_path[relative_path] = CodeContentPlan(
                language=_enum_value(language),
                content_text=content_text,
                section_plans=[],
            )
    return plans_by_relative_path


def _build_code_package_artifact_from_ref(
    *,
    code_package_id: UUID,
    artifact_ref: CodePackageArtifactRef,
) -> CodePackageArtifact:
    if artifact_ref.code_package_id != code_package_id:
        raise RuntimeError(
            "CodePackage snapshot artifact ref targets a different CodePackage: "
            f"expected={code_package_id} actual={artifact_ref.code_package_id}"
        )
    output_key = (artifact_ref.output_key or "").strip()
    artifact_key = (artifact_ref.artifact_key or "").strip()
    if not output_key:
        raise RuntimeError("CodePackage snapshot artifact ref missing output_key")
    if not artifact_key:
        raise RuntimeError("CodePackage snapshot artifact ref missing artifact_key")
    artifact_id = stable_code_package_artifact_id(
        code_package_id=code_package_id,
        output_key=output_key,
        artifact_key=artifact_key,
    )
    return CodePackageArtifact(
        id=artifact_id,
        code_package_id=code_package_id,
        output_key=output_key,
        artifact_key=artifact_key,
        status=_enum_value(artifact_ref.status),
        artifact_family=_optional_text(artifact_ref.artifact_family),
        artifact_role=_optional_text(artifact_ref.artifact_role),
        required_for=list(artifact_ref.required_for or []),
        producer_key=_optional_text(artifact_ref.producer_key),
        producer_kind=_optional_text(artifact_ref.producer_kind),
        materialization_index=artifact_ref.materialization_index,
        source_code_package_id=artifact_ref.source_code_package_id,
        source_object_instance_graph_commit_id=(
            artifact_ref.source_object_instance_graph_commit_id
        ),
        input_code_package_id=artifact_ref.input_code_package_id,
        input_object_instance_graph_commit_id=(
            artifact_ref.input_object_instance_graph_commit_id
        ),
        digest=_optional_text(artifact_ref.digest),
        relative_path=_optional_text(artifact_ref.relative_path),
        uri=_optional_text(artifact_ref.uri),
        media_type=_optional_text(artifact_ref.media_type),
        runtime_contract_version=_optional_text(artifact_ref.runtime_contract_version),
        provider_payload=artifact_ref.provider_payload,
        receipt_payload=artifact_ref.receipt_payload,
        error=_optional_text(artifact_ref.error),
    )


def _build_code_package_identity(
    *,
    code_package_id: UUID,
    code_package_config_id: UUID,
    package_name: str,
    language: CodeLanguage,
    surface: str,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
) -> CodePackage:
    code_package = CodePackage(
        id=code_package_id,
        code_package_config_id=code_package_config_id,
        package_name=(package_name or "").strip(),
        language=_enum_value(language),
        surface=surface,
        manifest_relative_path=(manifest_relative_path or "").strip(),
        package_root=(package_root or "").strip(),
        sources_root=(sources_root or "").strip() or None,
        fqn_prefix=(fqn_prefix or "").strip() or None,
    )
    if getattr(code_package, "code_package_config_id", None) != code_package_config_id:
        object.__setattr__(
            code_package,
            "code_package_config_id",
            code_package_config_id,
        )
    return code_package


def _build_code_package_direct_desired_oig(
    *,
    index: MetaGraphRuntimeIndex,
    opg,
    branch_id: UUID,
    domain_oig_id: UUID,
    code_package: CodePackage,
    code_package_config_id: UUID,
    manifest_kind: str,
    surface: str,
    objects_by_id: Mapping[UUID, BaseORMModel],
):
    desired_state = _build_code_package_direct_desired_state(
        index=index,
        opg=opg,
        branch_id=branch_id,
        domain_oig_id=domain_oig_id,
        code_package=code_package,
        code_package_config_id=code_package_config_id,
        manifest_kind=manifest_kind,
        surface=surface,
        objects_by_id=objects_by_id,
        materialize_class_instances=True,
    )
    oig = _build_code_package_oig_from_desired_state(
        index=index,
        opg=opg,
        branch_id=branch_id,
        domain_oig_id=domain_oig_id,
        desired_state=desired_state,
    )
    oig.hash = desired_state.graph_hash
    return oig


def _build_code_package_direct_desired_state(
    *,
    index: MetaGraphRuntimeIndex,
    opg,
    branch_id: UUID,
    domain_oig_id: UUID,
    code_package: CodePackage,
    code_package_config_id: UUID,
    manifest_kind: str,
    surface: str,
    objects_by_id: Mapping[UUID, BaseORMModel],
    materialize_class_instances: bool = True,
    source_object_path_index: Mapping[str, tuple[UUID, ...]] | None = None,
) -> _CodePackageDesiredState:
    with commit_perf_span(
        phase="code_package.direct_state.relationship_indexes",
        category="code_package.direct_state",
        metadata={"object_count": len(objects_by_id)},
    ):
        relationship_context = _code_package_direct_relationship_context(
            index=index,
            opg=opg,
        )
        relationship_attribute_ids_by_cc_id = (
            relationship_context.relationship_attribute_ids_by_cc_id
        )
        include_relationship_attr_ids_by_cc_id = (
            relationship_context.include_relationship_attr_ids_by_cc_id
        )
    with commit_perf_span(
        phase="code_package.direct_state.class_instances",
        category="code_package.direct_state",
        metadata={"object_count": len(objects_by_id)},
    ):
        class_configs_by_id = dict(index.class_configs_by_id)
        class_instances_by_source_id: dict[UUID, object] = {}
        class_instances: list[ClassInstance] = []
        class_instance_payloads: list[Mapping[str, object]] = []
        class_state_rows_by_id: dict[UUID, tuple[CommitStateRow, ...]] = {}
        for source_object_id, source_object in sorted(
            objects_by_id.items(),
            key=lambda item: str(item[0]),
        ):
            class_config_id = source_object.try_class_config_id()
            if class_config_id is None:
                raise RuntimeError(
                    "CodePackage direct snapshot object missing class config id: "
                    f"source_object_id={source_object_id}"
                )
            class_config = index.class_configs_by_id.get(class_config_id)
            if class_config is None:
                raise RuntimeError(
                    "CodePackage direct snapshot class config not found: "
                    f"class_config_id={class_config_id}"
                )
            source = (
                _code_package_config_overlay(
                    code_package=code_package,
                    code_package_config_id=code_package_config_id,
                    surface=surface,
                )
                if source_object_id == code_package.id
                else source_object
            )
            if not materialize_class_instances:
                direct_class_state = _try_build_code_package_direct_class_state(
                    object_instance_graph_id=domain_oig_id,
                    class_config=class_config,
                    source=source,
                    relationship_attribute_config_ids=(
                        relationship_attribute_ids_by_cc_id.get(class_config_id)
                    ),
                    include_relationship_attribute_config_ids=(
                        include_relationship_attr_ids_by_cc_id.get(class_config_id)
                    ),
                )
                if direct_class_state is not None:
                    if source_object_id == code_package.id:
                        try:
                            class_instance = ClassInstance.model_validate(
                                direct_class_state.snapshot_payload
                            )
                        except Exception:
                            class_instance = None
                        if (
                            class_instance is None
                            or class_instance.id != direct_class_state.class_instance_id
                        ):
                            raise RuntimeError(
                                "CodePackage direct root snapshot did not validate "
                                "as a ClassInstance"
                            )
                        class_instances_by_source_id[source_object_id] = class_instance
                        class_instances.append(class_instance)
                    else:
                        class_instances_by_source_id[source_object_id] = (
                            direct_class_state.class_instance_id
                        )
                        class_instance_payloads.append(
                            direct_class_state.snapshot_payload
                        )
                    class_state_rows_by_id[direct_class_state.class_instance_id] = (
                        direct_class_state.state_rows
                    )
                    continue
            class_instance = build_class_instance(
                object_instance_graph_id=domain_oig_id,
                class_config=class_config,
                class_configs_by_id=class_configs_by_id,
                source=source,
                enum_option_resolver=default_meta_enum_option_resolver,
                relationship_attribute_config_ids=(
                    relationship_attribute_ids_by_cc_id.get(class_config_id)
                ),
                include_relationship_attribute_config_ids=(
                    include_relationship_attr_ids_by_cc_id.get(class_config_id)
                ),
                attach_class_config=False,
            )
            class_instances_by_source_id[source_object_id] = class_instance
            class_instances.append(class_instance)
            if class_instance.id is not None:
                class_state_rows_by_id[class_instance.id] = (
                    _code_package_class_instance_state_rows(class_instance)
                )

    with commit_perf_span(
        phase="code_package.direct_state.relationship_configs",
        category="code_package.direct_state",
        metadata={
            "relationship_count": relationship_context.relationship_count,
            "cache_hit": relationship_context.cache_hit,
        },
    ):
        relationship_configs_by_key = relationship_context.relationship_configs_by_key
    with commit_perf_span(
        phase="code_package.direct_state.relationships",
        category="code_package.direct_state",
        metadata={"class_instance_count": len(class_instances_by_source_id)},
    ):
        relationships = _build_code_package_direct_relationships(
            domain_oig_id=domain_oig_id,
            code_package=code_package,
            class_instances_by_source_id=class_instances_by_source_id,
            relationship_configs_by_key=relationship_configs_by_key,
        )
    root_class_instance = class_instances_by_source_id.get(code_package.id)
    if root_class_instance is None:
        raise RuntimeError(
            "CodePackage direct snapshot missing root class instance: "
            f"code_package_id={code_package.id}"
        )
    if root_class_instance.id is None or root_class_instance.class_config_id is None:
        raise RuntimeError(
            "CodePackage direct snapshot root ClassInstance missing id/config"
        )
    with commit_perf_span(
        phase="code_package.direct_state.indexes",
        category="code_package.direct_state",
        metadata={
            "class_instance_count": len(class_instances),
            "relationship_count": len(relationships),
        },
    ):
        class_instances_by_id = _class_instances_by_id_from_iterable(class_instances)
        relationships_by_key = _relationships_by_key_from_relationships(relationships)
        state_index = _code_package_desired_state_index_from_state_rows(
            class_state_rows_by_id=class_state_rows_by_id,
            class_instance_relationships=tuple(relationships),
        )
        graph_hash = state_index.compute_hash()
    graph_meta = {
        "id": domain_oig_id,
        "key": str(branch_id),
        "name": f"OIG_{branch_id.hex[:8]}",
        "description": "CodePackage text snapshot",
        "object_projection_graph_id": opg.id,
        "root_class_instance_id": root_class_instance.id,
        "root_source_object_id": root_class_instance.source_object_id,
        "hash": graph_hash,
    }
    source_object_state_index = _code_package_source_object_state_index(
        domain_oig_id=domain_oig_id,
        objects_by_id=objects_by_id,
        source_object_path_index=source_object_path_index,
    )
    return _CodePackageDesiredState(
        object_instance_graph_id=domain_oig_id,
        graph_hash=graph_hash,
        state_index=state_index,
        root_metadata=ObjectInstanceGraphCommitRootMetadata(
            object_instance_graph_key=str(branch_id),
            object_instance_graph_name=f"OIG_{branch_id.hex[:8]}",
            object_instance_graph_description="CodePackage text snapshot",
            root_class_config_id=root_class_instance.class_config_id,
            root_source_object_id=root_class_instance.source_object_id,
        ),
        root_class_instance=root_class_instance,
        class_instances=tuple(class_instances),
        class_instance_payloads=tuple(class_instance_payloads),
        class_instances_by_id=class_instances_by_id,
        class_instance_relationships=tuple(relationships),
        relationships_by_key=relationships_by_key,
        graph_meta=graph_meta,
        source_object_state_index=source_object_state_index,
    )


def _code_package_seed_witness_desired_state_if_enabled(
    desired_state: _CodePackageDesiredState,
) -> _CodePackageDesiredState:
    if not _code_package_state_class_segments_enabled(
        node_count=desired_state.state_index.node_count,
    ):
        return desired_state
    post_witness_ref = build_commit_state_witness_ref(desired_state.state_index)
    post_witness_cursor = build_commit_state_witness_cursor(post_witness_ref)
    graph_meta = dict(desired_state.graph_meta)
    graph_meta["hash"] = post_witness_cursor.cursor_hash
    return replace(
        desired_state,
        graph_hash=post_witness_cursor.cursor_hash,
        graph_hash_source="witness_cursor_hash",
        graph_meta=graph_meta,
        post_witness_ref=post_witness_ref,
        post_witness_cursor_summary=post_witness_cursor.summary(),
        post_witness_cursor_chunks=post_witness_cursor.chunks,
    )


async def _try_build_code_package_reused_witness_segment_desired_state(
    *,
    index: MetaGraphRuntimeIndex,
    opg,
    branch_id: UUID,
    projection_hash: str,
    head: Mapping[str, object] | None,
    previous_snapshot_index_payload: Mapping[str, object] | None,
    domain_oig_id: UUID,
    code_package: CodePackage,
    code_package_config_id: UUID,
    manifest_kind: str,
    surface: str,
    objects_by_id: Mapping[UUID, BaseORMModel],
    current_source_states_by_id: Mapping[UUID, _CodePackageSourceObjectState] | None,
    changed_path_source_state: _CodePackageChangedPathSourceState | None,
    current_source_object_path_index: Mapping[str, tuple[UUID, ...]] | None,
    previous_source_states_by_id: Mapping[UUID, _CodePackageSourceObjectState] | None,
    oigi_id: UUID,
) -> _CodePackageDesiredState | None:
    head_commit_id = _head_uuid(head, "commit_id")
    head_graph_hash_post = _head_string(head, "graph_hash_post")
    head_graph_hash_source = _head_string(head, "graph_hash_source") or "state_hash"
    fatal_miss = head_graph_hash_source in {"witness_hash", "witness_cursor_hash"}
    if current_source_states_by_id is None and changed_path_source_state is None:
        return _code_package_witness_segment_reuse_miss(
            "missing_current_source_states",
            fatal=fatal_miss,
        )
    if head_commit_id is None or not head_graph_hash_post:
        return _code_package_witness_segment_reuse_miss(
            "missing_head",
            fatal=fatal_miss,
        )
    source_object_count = (
        changed_path_source_state.source_object_count
        if changed_path_source_state is not None
        else len(current_source_states_by_id or ())
    )
    with commit_perf_span(
        phase="code_package.witness_desired_state.source_reuse_check",
        category="code_package.witness_desired_state",
        metadata={
            "current_source_count": source_object_count,
            "changed_path_raw_index": changed_path_source_state is not None,
        },
    ):
        previous_source_states = None
        if changed_path_source_state is None:
            previous_source_states = previous_source_states_by_id or (
                _code_package_source_object_states_from_index_payload(
                    previous_snapshot_index_payload,
                )
            )
            source_set_not_reusable = (
                previous_source_states is None
                or len(previous_source_states)
                < _CODE_PACKAGE_PARTIAL_SOURCE_REUSE_MIN_SOURCE_OBJECT_COUNT
                or set(previous_source_states) != set(current_source_states_by_id or ())
            )
        else:
            source_set_not_reusable = (
                source_object_count
                < _CODE_PACKAGE_PARTIAL_SOURCE_REUSE_MIN_SOURCE_OBJECT_COUNT
            )
    if source_set_not_reusable:
        return _code_package_witness_segment_reuse_miss(
            "source_set_not_reusable",
            fatal=fatal_miss,
            previous_count=(
                0 if previous_source_states is None else len(previous_source_states)
            ),
            current_count=source_object_count,
        )
    if previous_source_states is None and changed_path_source_state is None:
        return _code_package_witness_segment_reuse_miss(
            "missing_previous_source_states",
            fatal=fatal_miss,
        )
    snapshot_store = FSSnapshotStore()
    segment_metadata: ObjectInstanceGraphSnapshotStateSegmentIndexMetadata | None = None
    previous_cursor_summary: CommitStateWitnessCursorSummary | None = None
    if head_graph_hash_source == "witness_cursor_hash":
        with commit_perf_span(
            phase="code_package.witness_desired_state.load_cursor_summary",
            category="code_package.witness_desired_state",
        ):
            previous_cursor_summary = (
                _code_package_text_snapshot_state_snapshot_witness_cursor(
                    previous_snapshot_index_payload,
                )
            )
        if (
            previous_cursor_summary is None
            or previous_cursor_summary.cursor_hash != head_graph_hash_post
        ):
            return _code_package_witness_segment_reuse_miss(
                "missing_cursor_summary",
                fatal=fatal_miss,
                cursor_found=previous_cursor_summary is not None,
            )
    else:
        with commit_perf_span(
            phase="code_package.witness_desired_state.load_segment_metadata",
            category="code_package.witness_desired_state",
        ):
            segment_metadata = (
                snapshot_store.snapshot_state_class_segment_index_metadata(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    commit_id=head_commit_id,
                    expected_object_instance_graph_id=domain_oig_id,
                    expected_graph_hash=head_graph_hash_post,
                )
            )
        if (
            segment_metadata is None
            or segment_metadata.witness_hash != head_graph_hash_post
        ):
            return _code_package_witness_segment_reuse_miss(
                "missing_segment_metadata",
                fatal=fatal_miss,
                metadata_found=segment_metadata is not None,
            )
    with commit_perf_span(
        phase="code_package.witness_desired_state.changed_source_scan",
        category="code_package.witness_desired_state",
        metadata={
            "source_count": source_object_count,
            "changed_path_raw_index": changed_path_source_state is not None,
        },
    ):
        if changed_path_source_state is not None:
            changed_source_object_ids = set(
                changed_path_source_state.changed_source_object_ids,
            )
            current_changed_source_states_by_id = dict(
                changed_path_source_state.changed_source_states_by_id,
            )
            current_changed_source_states_by_id[code_package.id] = (
                changed_path_source_state.root_source_state
            )
        else:
            if current_source_states_by_id is None or previous_source_states is None:
                return _code_package_witness_segment_reuse_miss(
                    "missing_source_state_scan_inputs",
                    fatal=fatal_miss,
                )
            changed_source_object_ids = {
                source_object_id
                for source_object_id, source_state in current_source_states_by_id.items()
                if previous_source_states.get(source_object_id) != source_state
            }
            changed_source_object_ids.add(code_package.id)
            current_changed_source_states_by_id = current_source_states_by_id
        changed_class_instance_ids = tuple(
            sorted(
                {
                    current_changed_source_states_by_id[
                        source_object_id
                    ].class_instance_id
                    for source_object_id in changed_source_object_ids
                },
                key=str,
            )
        )
    previous_selection = (
        await _get_code_package_text_snapshot_indexed_raw_class_segments(
            snapshot_store=snapshot_store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
            class_instance_ids=changed_class_instance_ids,
            previous_snapshot_index_payload=previous_snapshot_index_payload,
            segment_metadata=segment_metadata,
            previous_cursor_summary=previous_cursor_summary,
            expected_object_instance_graph_id=domain_oig_id,
            expected_graph_hash=head_graph_hash_post,
        )
    )
    if previous_selection is None:
        return _code_package_witness_segment_reuse_miss(
            "missing_previous_segments",
            fatal=fatal_miss,
            selected_count=len(changed_class_instance_ids),
        )

    with commit_perf_span(
        phase="code_package.witness_desired_state.relationship_context",
        category="code_package.witness_desired_state",
    ):
        relationship_context = _code_package_direct_relationship_context(
            index=index,
            opg=opg,
        )
        class_configs_by_id = dict(index.class_configs_by_id)
    desired_class_instances_by_id: dict[UUID, ClassInstance] = {}
    replacement_class_segments: list[
        ObjectInstanceGraphSnapshotStateRawClassSegment
    ] = []
    replacement_segment_refs: dict[str, CommitStateSegmentRef] = {}
    with commit_perf_span(
        phase="code_package.witness_desired_state.build_replacement_segments",
        category="code_package.witness_desired_state",
        metadata={"changed_source_count": len(changed_source_object_ids)},
    ):
        for source_object_id in sorted(changed_source_object_ids, key=str):
            source_state = current_changed_source_states_by_id.get(source_object_id)
            source_object = objects_by_id.get(source_object_id)
            if source_state is None or source_object is None:
                return _code_package_witness_segment_reuse_miss(
                    "missing_changed_source_object",
                    fatal=fatal_miss,
                )
            class_config = class_configs_by_id.get(source_state.class_config_id)
            if class_config is None:
                return _code_package_witness_segment_reuse_miss(
                    "missing_class_config",
                    fatal=fatal_miss,
                )
            source = (
                _code_package_config_overlay(
                    code_package=code_package,
                    code_package_config_id=code_package_config_id,
                    surface=surface,
                )
                if source_object_id == code_package.id
                else source_object
            )
            try:
                class_instance, rows, snapshot_payload = (
                    _build_code_package_changed_class_segment_state(
                        object_instance_graph_id=domain_oig_id,
                        class_config=class_config,
                        class_configs_by_id=class_configs_by_id,
                        source=source,
                        source_state=source_state,
                        relationship_attribute_ids_by_cc_id=(
                            relationship_context.relationship_attribute_ids_by_cc_id
                        ),
                        include_relationship_attr_ids_by_cc_id=(
                            relationship_context.include_relationship_attr_ids_by_cc_id
                        ),
                    )
                )
            except ValueError:
                return _code_package_witness_segment_reuse_miss(
                    "changed_class_segment_build_failed",
                    fatal=fatal_miss,
                )
            if class_instance.id is None or class_instance.class_config_id is None:
                return _code_package_witness_segment_reuse_miss(
                    "changed_class_instance_missing_id",
                    fatal=fatal_miss,
                )
            segment_ref = _code_package_class_state_segment_ref(
                class_instance_id=class_instance.id,
                rows=rows,
            )
            replacement_segment_refs[segment_ref.key] = segment_ref
            desired_class_instances_by_id[class_instance.id] = class_instance
            replacement_class_segments.append(
                ObjectInstanceGraphSnapshotStateRawClassSegment(
                    class_instance_id=class_instance.id,
                    class_config_id=class_instance.class_config_id,
                    source_object_id=class_instance.source_object_id,
                    rows_text=_code_package_state_rows_text(rows),
                    row_count=len(rows),
                    row_hash=segment_ref.row_hash,
                    snapshot_payload=dict(snapshot_payload),
                    segment_ref=segment_ref,
                )
            )

    old_class_instances_by_id: dict[UUID, ClassInstance] = {}
    old_class_config_ids_by_id: dict[UUID, UUID] = {}
    old_class_state_rows: dict[str, tuple[CommitStateRow, ...]] = {}
    with commit_perf_span(
        phase="code_package.witness_desired_state.validate_old_segments",
        category="code_package.witness_desired_state",
        metadata={
            "selected_count": len(previous_selection.class_segments_by_id),
        },
    ):
        for (
            class_instance_id,
            segment,
        ) in previous_selection.class_segments_by_id.items():
            old_rows = _code_package_state_rows_from_text(segment.rows_text)
            if old_rows is None:
                return _code_package_witness_segment_reuse_miss(
                    "invalid_old_rows_text",
                    fatal=fatal_miss,
                )
            try:
                old_class_instance = ClassInstance.model_validate(
                    segment.snapshot_payload,
                )
            except Exception:
                return _code_package_witness_segment_reuse_miss(
                    "old_class_instance_validate_failed",
                    fatal=fatal_miss,
                )
            old_class_instances_by_id[class_instance_id] = old_class_instance
            old_class_config_ids_by_id[class_instance_id] = segment.class_config_id
            old_class_state_rows[str(class_instance_id)] = old_rows

    with commit_perf_span(
        phase="code_package.witness_desired_state.build_changes",
        category="code_package.witness_desired_state",
        metadata={"replacement_segment_count": len(replacement_class_segments)},
    ):
        new_class_config_ids_by_id = {
            segment.class_instance_id: segment.class_config_id
            for segment in replacement_class_segments
        }
        new_class_state_rows = {
            str(segment.class_instance_id): _code_package_state_rows_from_text(
                segment.rows_text,
            )
            for segment in replacement_class_segments
        }
        if any(rows is None for rows in new_class_state_rows.values()):
            return _code_package_witness_segment_reuse_miss(
                "invalid_new_rows_text",
                fatal=fatal_miss,
            )
        changes = _build_code_package_direct_state_row_changes_from_indexes(
            old_graph_id=domain_oig_id,
            old_class_config_ids_by_id=old_class_config_ids_by_id,
            new_class_config_ids_by_id=new_class_config_ids_by_id,
            old_class_state_rows=old_class_state_rows,
            new_class_state_rows={
                key: rows
                for key, rows in new_class_state_rows.items()
                if rows is not None
            },
            old_relationship_keys=set(),
            old_class_instances_by_id=old_class_instances_by_id,
            desired_class_instances_by_id=desired_class_instances_by_id,
            desired_relationships_by_key={},
            object_instance_graph_identity_id=oigi_id,
            created_at=datetime.now(timezone.utc),
        )
    if changes is None:
        return _code_package_witness_segment_reuse_miss(
            "change_build_failed",
            fatal=fatal_miss,
        )
    with commit_perf_span(
        phase="code_package.witness_desired_state.replace_witness",
        category="code_package.witness_desired_state",
        metadata={"replacement_segment_count": len(replacement_segment_refs)},
    ):
        post_witness_ref: CommitStateWitnessRef | None = None
        post_witness_cursor_summary: CommitStateWitnessCursorSummary | None = None
        post_witness_cursor_chunks: tuple[CommitStateWitnessCursorChunk, ...] = ()
        if previous_cursor_summary is not None:
            if not isinstance(
                previous_selection,
                ObjectInstanceGraphSnapshotStateRawClassSegmentCursorSelection,
            ):
                return _code_package_witness_segment_reuse_miss(
                    "missing_cursor_selection",
                    fatal=fatal_miss,
                )
            replacement_chunks_by_index: dict[int, CommitStateWitnessCursorChunk] = {}
            covered_replacement_keys: set[str] = set()
            for chunk_index, chunk in previous_selection.cursor_chunks_by_index.items():
                replacements_for_chunk = {
                    key: segment
                    for key, segment in replacement_segment_refs.items()
                    if key in chunk.segment_keys
                }
                if not replacements_for_chunk:
                    continue
                replacement_chunks_by_index[chunk_index] = (
                    replace_commit_state_witness_cursor_chunk_segments(
                        chunk=chunk,
                        replacement_segments_by_key=replacements_for_chunk,
                    )
                )
                covered_replacement_keys.update(replacements_for_chunk)
            if covered_replacement_keys != set(replacement_segment_refs):
                return _code_package_witness_segment_reuse_miss(
                    "missing_cursor_replacement_chunk",
                    fatal=fatal_miss,
                )
            post_witness_cursor_summary = (
                replace_existing_commit_state_witness_cursor_summary_chunks(
                    summary=previous_cursor_summary,
                    replacement_chunks_by_index=replacement_chunks_by_index,
                )
            )
            post_witness_cursor_chunks = tuple(replacement_chunks_by_index.values())
        elif segment_metadata is not None:
            post_witness_ref = replace_existing_commit_state_witness_ref_segments(
                pre_witness_ref=segment_metadata.witness_ref,
                replacement_segments_by_key=replacement_segment_refs,
            )
        else:
            return _code_package_witness_segment_reuse_miss(
                "missing_witness_replacement_source",
                fatal=fatal_miss,
            )
    graph_hash = (
        post_witness_cursor_summary.cursor_hash
        if post_witness_cursor_summary is not None
        else (post_witness_ref.witness_hash if post_witness_ref is not None else None)
    )
    if graph_hash is None:
        return _code_package_witness_segment_reuse_miss(
            "missing_post_graph_hash",
            fatal=fatal_miss,
        )
    root_source_state = (
        changed_path_source_state.root_source_state
        if changed_path_source_state is not None
        else (
            current_source_states_by_id[code_package.id]
            if current_source_states_by_id is not None
            else None
        )
    )
    if root_source_state is None:
        return _code_package_witness_segment_reuse_miss(
            "missing_root_source_state",
            fatal=fatal_miss,
        )
    root_class_instance = desired_class_instances_by_id.get(
        root_source_state.class_instance_id,
    )
    if (
        root_class_instance is None
        or root_class_instance.class_config_id is None
        or root_class_instance.source_object_id is None
    ):
        return _code_package_witness_segment_reuse_miss(
            "missing_root_class_instance",
            fatal=fatal_miss,
        )
    graph_meta = {
        "id": domain_oig_id,
        "key": str(branch_id),
        "name": f"OIG_{branch_id.hex[:8]}",
        "description": "CodePackage text snapshot",
        "object_projection_graph_id": opg.id,
        "root_class_instance_id": root_class_instance.id,
        "root_source_object_id": root_class_instance.source_object_id,
        "hash": graph_hash,
    }
    with commit_perf_span(
        phase="code_package.witness_desired_state.source_index",
        category="code_package.witness_desired_state",
        metadata={
            "source_count": source_object_count,
            "changed_path_raw_index": changed_path_source_state is not None,
        },
    ):
        if changed_path_source_state is not None:
            source_object_state_index = (
                changed_path_source_state.source_object_state_index
            )
        else:
            if current_source_states_by_id is None:
                return _code_package_witness_segment_reuse_miss(
                    "missing_source_index_states",
                    fatal=fatal_miss,
                )
            source_object_state_index = (
                _code_package_source_object_state_index_from_states(
                    current_source_states_by_id.values(),
                    source_object_path_index=current_source_object_path_index,
                )
            )
    pre_state_row_count = (
        previous_cursor_summary.row_count
        if previous_cursor_summary is not None
        else (segment_metadata.row_count if segment_metadata is not None else 0)
    )
    pre_state_source_contract = (
        "aware.oig.snapshot_state_class_segment_cursor"
        if previous_cursor_summary is not None
        else (
            str(segment_metadata.payload.get("schema"))
            if segment_metadata is not None
            else ""
        )
    )
    return _CodePackageDesiredState(
        object_instance_graph_id=domain_oig_id,
        graph_hash=graph_hash,
        state_index=CommitStateIndex(
            rows=tuple(
                row
                for segment in replacement_class_segments
                for row in (_code_package_state_rows_from_text(segment.rows_text) or ())
            ),
        ),
        root_metadata=ObjectInstanceGraphCommitRootMetadata(
            object_instance_graph_key=str(branch_id),
            object_instance_graph_name=f"OIG_{branch_id.hex[:8]}",
            object_instance_graph_description="CodePackage text snapshot",
            root_class_config_id=root_class_instance.class_config_id,
            root_source_object_id=root_class_instance.source_object_id,
        ),
        root_class_instance=root_class_instance,
        class_instances=tuple(desired_class_instances_by_id.values()),
        class_instance_payloads=tuple(
            segment.snapshot_payload for segment in replacement_class_segments
        ),
        class_instances_by_id=desired_class_instances_by_id,
        class_instance_relationships=(),
        relationships_by_key={},
        graph_meta=graph_meta,
        source_object_state_index=source_object_state_index,
        graph_hash_source=(
            "witness_cursor_hash"
            if post_witness_cursor_summary is not None
            else "witness_hash"
        ),
        previous_commit_id=head_commit_id,
        pre_witness_ref=(
            segment_metadata.witness_ref if segment_metadata is not None else None
        ),
        post_witness_ref=post_witness_ref,
        pre_witness_cursor_summary=previous_cursor_summary,
        post_witness_cursor_summary=post_witness_cursor_summary,
        post_witness_cursor_chunks=post_witness_cursor_chunks,
        replacement_class_segments=tuple(replacement_class_segments),
        precomputed_change_result=_CodePackageSnapshotChangeResult(
            changes=changes,
            pre_state_index=None,
            pre_state_evidence=ObjectInstanceGraphCommitPreStateEvidence(
                graph_hash_source=(
                    "witness_cursor_hash"
                    if previous_cursor_summary is not None
                    else "witness_hash"
                ),
                witness_hash=(
                    segment_metadata.witness_hash
                    if segment_metadata is not None
                    else None
                ),
                witness_cursor_hash=(
                    previous_cursor_summary.cursor_hash
                    if previous_cursor_summary is not None
                    else None
                ),
                row_count=pre_state_row_count,
                source_contract=pre_state_source_contract,
                source_ref=f"{head_commit_id}.segments.jsonl",
            ),
        ),
    )


def _code_package_witness_segment_reuse_miss(
    reason: str,
    *,
    fatal: bool = False,
    **metadata: object,
) -> None:
    with commit_perf_span(
        phase="code_package.reused_state.witness_segment_miss",
        category="code_package.reused_state",
        metadata={"reason": reason, **metadata},
    ):
        pass
    if fatal:
        detail = " ".join(f"{key}={value}" for key, value in sorted(metadata.items()))
        raise RuntimeError(
            "CodePackage witness segment reuse miss on witness-hash lane: "
            f"reason={reason}" + (f" {detail}" if detail else "")
        )
    return None


async def _get_code_package_text_snapshot_indexed_raw_class_segments(
    *,
    snapshot_store: FSSnapshotStore,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    class_instance_ids: Iterable[UUID],
    previous_snapshot_index_payload: Mapping[str, object] | None,
    segment_metadata: ObjectInstanceGraphSnapshotStateSegmentIndexMetadata | None,
    previous_cursor_summary: CommitStateWitnessCursorSummary | None,
    expected_object_instance_graph_id: UUID,
    expected_graph_hash: str,
) -> (
    ObjectInstanceGraphSnapshotStateRawClassSegmentIndexSelection
    | ObjectInstanceGraphSnapshotStateRawClassSegmentSelection
    | ObjectInstanceGraphSnapshotStateRawClassSegmentCursorSelection
    | None
):
    if previous_cursor_summary is not None:
        return await snapshot_store.get_snapshot_state_indexed_raw_class_segments_by_witness_cursor(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=class_instance_ids,
            expected_witness_cursor_summary=previous_cursor_summary,
            expected_object_instance_graph_id=expected_object_instance_graph_id,
            expected_graph_hash=expected_graph_hash,
        )
    if segment_metadata is None:
        return None
    if (
        segment_metadata.state_hash is None
        or segment_metadata.payload.get("graph_hash_source") == "witness_hash"
    ):
        return await snapshot_store.get_snapshot_state_indexed_raw_class_segments_by_witness_ref(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=class_instance_ids,
            expected_witness_ref=segment_metadata.witness_ref,
            expected_object_instance_graph_id=expected_object_instance_graph_id,
            expected_graph_hash=expected_graph_hash,
        )
    witness = _code_package_text_snapshot_state_snapshot_witness(
        previous_snapshot_index_payload,
    )
    if witness is None:
        return None
    return await snapshot_store.get_snapshot_state_indexed_raw_class_segments_by_file_witness(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        class_instance_ids=class_instance_ids,
        expected_state_rows_file_size=int(str(witness["file_size"])),
        expected_state_rows_file_mtime_ns=int(str(witness["file_mtime_ns"])),
        expected_state_rows_file_ctime_ns=int(str(witness["file_ctime_ns"])),
        expected_state_rows_payload_sha256=str(witness["payload_sha256"]),
        expected_state_hash=str(witness["state_hash"]),
        expected_object_instance_graph_id=expected_object_instance_graph_id,
        expected_graph_hash=expected_graph_hash,
    )


def _build_code_package_changed_class_segment_state(
    *,
    object_instance_graph_id: UUID,
    class_config: object,
    class_configs_by_id: Mapping[UUID, object],
    source: ModelIntrospection,
    source_state: _CodePackageSourceObjectState,
    relationship_attribute_ids_by_cc_id: Mapping[UUID, set[UUID]],
    include_relationship_attr_ids_by_cc_id: Mapping[UUID, set[UUID]],
) -> tuple[ClassInstance, tuple[CommitStateRow, ...], Mapping[str, object]]:
    direct_class_state = _try_build_code_package_direct_class_state(
        object_instance_graph_id=object_instance_graph_id,
        class_config=class_config,
        source=source,
        relationship_attribute_config_ids=relationship_attribute_ids_by_cc_id.get(
            source_state.class_config_id,
        ),
        include_relationship_attribute_config_ids=(
            include_relationship_attr_ids_by_cc_id.get(source_state.class_config_id)
        ),
    )
    if direct_class_state is not None:
        try:
            class_instance = ClassInstance.model_validate(
                direct_class_state.snapshot_payload,
            )
        except Exception:
            class_instance = None
        if (
            class_instance is not None
            and class_instance.id == direct_class_state.class_instance_id
        ):
            return (
                class_instance,
                direct_class_state.state_rows,
                direct_class_state.snapshot_payload,
            )
    class_instance = build_class_instance(
        object_instance_graph_id=object_instance_graph_id,
        class_config=class_config,  # type: ignore[arg-type]
        class_configs_by_id=dict(class_configs_by_id),  # type: ignore[arg-type]
        source=source,
        enum_option_resolver=default_meta_enum_option_resolver,
        relationship_attribute_config_ids=relationship_attribute_ids_by_cc_id.get(
            source_state.class_config_id,
        ),
        include_relationship_attribute_config_ids=(
            include_relationship_attr_ids_by_cc_id.get(source_state.class_config_id)
        ),
        attach_class_config=False,
    )
    if class_instance.id != source_state.class_instance_id:
        raise ValueError(
            "CodePackage witness segment state produced unexpected ClassInstance id: "
            f"expected={source_state.class_instance_id} actual={class_instance.id}"
        )
    return (
        class_instance,
        _code_package_class_instance_state_rows(class_instance),
        class_instance.model_dump(mode="json", exclude_none=True),
    )


def _code_package_class_state_segment_ref(
    *,
    class_instance_id: UUID,
    rows: tuple[CommitStateRow, ...],
) -> CommitStateSegmentRef:
    row_hash = compute_commit_state_rows_hash(rows)
    key = f"class:{class_instance_id}"
    return CommitStateSegmentRef(
        kind="CLASS",
        key=key,
        row_count=len(rows),
        row_hash=row_hash,
        digest=compute_commit_state_segment_digest(
            kind="CLASS",
            key=key,
            row_count=len(rows),
            row_hash=row_hash,
        ),
    )


def _code_package_state_rows_text(rows: Iterable[CommitStateRow]) -> str:
    return "".join(f"{row.kind}\t{row.key}\t{row.value}\n" for row in rows)


def _code_package_state_rows_from_text(
    rows_text: str,
) -> tuple[CommitStateRow, ...] | None:
    rows: list[CommitStateRow] = []
    try:
        for line in rows_text.splitlines():
            if not line:
                continue
            kind, key, value = line.split("\t", 2)
            if kind not in {"NODE", "ATTR", "EDGE"}:
                return None
            rows.append(
                CommitStateRow(
                    kind=cast(CommitStateRowKind, kind), key=key, value=value
                )
            )
    except Exception:
        return None
    return tuple(rows)


def _code_package_pre_state_evidence_graph_hash(
    evidence: ObjectInstanceGraphCommitPreStateEvidence,
) -> str:
    if evidence.graph_hash_source == "witness_hash":
        if not evidence.witness_hash:
            raise RuntimeError("CodePackage witness pre-state evidence missing hash")
        return evidence.witness_hash
    if evidence.graph_hash_source == "witness_cursor_hash":
        if not evidence.witness_cursor_hash:
            raise RuntimeError(
                "CodePackage witness cursor pre-state evidence missing hash"
            )
        return evidence.witness_cursor_hash
    if not evidence.state_hash:
        raise RuntimeError("CodePackage row pre-state evidence missing hash")
    return evidence.state_hash


def _try_build_code_package_direct_class_state(
    *,
    object_instance_graph_id: UUID,
    class_config: object,
    source: ModelIntrospection,
    relationship_attribute_config_ids: Iterable[UUID] | None,
    include_relationship_attribute_config_ids: Iterable[UUID] | None,
) -> _CodePackageDirectClassState | None:
    class_config_id = getattr(class_config, "id", None)
    if not isinstance(class_config_id, UUID):
        return None
    class_instance_id = stable_class_instance_id(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config_id,
        source_object_id=source.id,
    )
    relationship_attribute_ids = _code_package_relationship_attribute_config_ids(
        class_config,
    )
    relationship_attribute_ids |= set(relationship_attribute_config_ids or ())
    relationship_attribute_ids -= set(include_relationship_attribute_config_ids or ())
    required_fk_attribute_ids = _code_package_required_fk_attribute_config_ids(
        class_config,
    )

    class_instance_attributes: list[Mapping[str, object]] = []
    attribute_rows: set[tuple[str, str]] = set()
    for link in _code_package_deduped_attribute_links(
        getattr(class_config, "class_config_attribute_configs", None) or (),
    ):
        attr_cfg = getattr(link, "attribute_config", None)
        attr_cfg_id = getattr(attr_cfg, "id", None)
        if not isinstance(attr_cfg_id, UUID):
            continue
        if bool(getattr(attr_cfg, "is_virtual", False)):
            continue
        if attr_cfg_id in relationship_attribute_ids:
            continue

        found, raw_value = source.try_attribute_value(attr_cfg)
        if not found:
            default_value = getattr(attr_cfg, "default_value", None)
            if default_value is not None:
                try:
                    raw_value = json.loads(default_value)
                except Exception:
                    return None
            elif bool(getattr(attr_cfg, "is_required", False)) or (
                attr_cfg_id in required_fk_attribute_ids
            ):
                return None
            else:
                continue

        attr_state = _try_build_code_package_direct_attribute_state(
            object_instance_graph_id=object_instance_graph_id,
            owner_key=source.id,
            class_instance_id=class_instance_id,
            attribute_config=attr_cfg,
            value=raw_value,
        )
        if attr_state is None:
            return None
        class_instance_attributes.append(attr_state["class_instance_attribute"])
        attribute_rows.add(
            (
                str(attr_cfg_id),
                str(attr_state["value_fingerprint"]),
            )
        )

    rows: list[CommitStateRow] = [
        CommitStateRow(
            kind="NODE",
            key=str(class_config_id),
            value=str(class_instance_id),
        )
    ]
    for attribute_config_id, value_fingerprint in sorted(attribute_rows):
        rows.append(
            CommitStateRow(
                kind="ATTR",
                key=str(class_instance_id),
                value=f"{attribute_config_id}:{value_fingerprint}",
            )
        )
    return _CodePackageDirectClassState(
        class_instance_id=class_instance_id,
        class_config_id=class_config_id,
        source_object_id=source.id,
        state_rows=tuple(rows),
        snapshot_payload={
            "id": str(class_instance_id),
            "source_object_id": str(source.id),
            "object_instance_graph_id": str(object_instance_graph_id),
            "class_config_id": str(class_config_id),
            "class_instance_attributes": class_instance_attributes,
        },
    )


def _try_build_code_package_direct_attribute_state(
    *,
    object_instance_graph_id: UUID,
    owner_key: UUID,
    class_instance_id: UUID,
    attribute_config: object,
    value: object,
) -> Mapping[str, object] | None:
    attribute_config_id = getattr(attribute_config, "id", None)
    type_descriptor = getattr(attribute_config, "type_descriptor", None)
    if not isinstance(attribute_config_id, UUID) or type_descriptor is None:
        return None
    attribute_id = stable_attribute_id(
        owner_key=owner_key,
        attribute_config_id=attribute_config_id,
    )
    value_state = _try_build_code_package_direct_attribute_value_state(
        object_instance_graph_id=object_instance_graph_id,
        type_descriptor=type_descriptor,
        value=value,
        value_id=stable_attribute_value_id(
            parent_value_id=attribute_id,
            role="member",
            position=0,
            identity_key="root",
        ),
    )
    if value_state is None:
        return None
    value_root_id = value_state["value_id"]
    value_root_payload = dict(value_state["payload"])
    value_root_payload["id"] = str(value_root_id)
    attribute_payload = {
        "id": str(attribute_id),
        "value_root": value_root_payload,
        "owner_key": str(owner_key),
        "attribute_config_id": str(attribute_config_id),
        "value_root_id": str(value_root_id),
    }
    edge_id = stable_class_instance_attribute_id(
        class_instance_id=class_instance_id,
        attribute_id=attribute_id,
    )
    return {
        "class_instance_attribute": {
            "id": str(edge_id),
            "attribute": attribute_payload,
            "attribute_id": str(attribute_id),
            "class_instance_id": str(class_instance_id),
        },
        "value_fingerprint": value_state["fingerprint"],
    }


def _try_build_code_package_direct_attribute_value_state(
    *,
    object_instance_graph_id: UUID,
    type_descriptor: object,
    value: object,
    value_id: UUID,
) -> Mapping[str, object] | None:
    type_descriptor_id = getattr(type_descriptor, "id", None)
    if not isinstance(type_descriptor_id, UUID):
        return None
    kind = _enum_value(getattr(type_descriptor, "kind", None))
    primitive_value: JsonValue | None = None
    enum_option_id: UUID | None = None
    class_instance_id: UUID | None = None
    child_links: list[Mapping[str, object]] = []
    fingerprint_children: list[Mapping[str, object]] = []
    if kind == "primitive":
        primitive_value = _code_package_direct_primitive_value(value)
    elif kind == "enum":
        try:
            enum_option_id = default_meta_enum_option_resolver(type_descriptor, value)
        except Exception:
            return None
    elif kind == "class":
        if isinstance(value, UUID):
            class_instance_id = value
        else:
            source_object_id = getattr(value, "id", None)
            try_class_config_id = getattr(value, "try_class_config_id", None)
            value_class_config_id = (
                try_class_config_id() if callable(try_class_config_id) else None
            )
            if not isinstance(source_object_id, UUID) or not isinstance(
                value_class_config_id,
                UUID,
            ):
                return None
            class_instance_id = stable_class_instance_id(
                object_instance_graph_id=object_instance_graph_id,
                class_config_id=value_class_config_id,
                source_object_id=source_object_id,
            )
        if class_instance_id is None:
            return None
    elif kind == "collection":
        collection_kind = _enum_value(getattr(type_descriptor, "collection_kind", None))
        if collection_kind == "list" and isinstance(value, (list, tuple)):
            element_descriptor = _code_package_element_descriptor(type_descriptor)
            if value and element_descriptor is None:
                return None
            for position, item in enumerate(value):
                if element_descriptor is None:
                    return None
                child_value_id = stable_attribute_value_id(
                    parent_value_id=value_id,
                    role="element",
                    position=position,
                    identity_key=None,
                )
                child_state = _try_build_code_package_direct_attribute_value_state(
                    object_instance_graph_id=object_instance_graph_id,
                    type_descriptor=element_descriptor,
                    value=item,
                    value_id=child_value_id,
                )
                if child_state is None:
                    return None
                link_id = stable_attribute_value_link_id(
                    parent_value_id=value_id,
                    role="element",
                    position=position,
                    identity_key=None,
                )
                child_links.append(
                    {
                        "id": str(link_id),
                        "child": child_state["payload"],
                        "role": "element",
                        "position": position,
                        "attribute_value_id": str(value_id),
                        "child_id": str(child_value_id),
                    }
                )
                fingerprint_children.append(
                    {
                        "role": "element",
                        "position": position,
                        "child": child_state["fingerprint_payload"],
                    }
                )
        else:
            return None
    elif kind == "union":
        selected = _code_package_direct_union_selection(
            type_descriptor=type_descriptor,
            value=value,
        )
        if selected is None:
            return None
        selected_pos, selected_value, selected_descriptor = selected
        child_value_id = stable_attribute_value_id(
            parent_value_id=value_id,
            role="member",
            position=selected_pos,
            identity_key=None,
        )
        child_state = _try_build_code_package_direct_attribute_value_state(
            object_instance_graph_id=object_instance_graph_id,
            type_descriptor=selected_descriptor,
            value=selected_value,
            value_id=child_value_id,
        )
        if child_state is None:
            return None
        link_id = stable_attribute_value_link_id(
            parent_value_id=value_id,
            role="member",
            position=selected_pos,
            identity_key=None,
        )
        child_links.append(
            {
                "id": str(link_id),
                "child": child_state["payload"],
                "role": "member",
                "position": selected_pos,
                "attribute_value_id": str(value_id),
                "child_id": str(child_value_id),
            }
        )
        fingerprint_children.append(
            {
                "role": "member",
                "position": selected_pos,
                "child": child_state["fingerprint_payload"],
            }
        )
    else:
        return None

    descriptor_payload = _code_package_direct_type_descriptor_payload(type_descriptor)
    fingerprint_payload = {
        "descriptor_id": str(type_descriptor_id),
        "kind": kind,
        "collection_kind": _enum_value(
            getattr(type_descriptor, "collection_kind", None),
        ),
        "primitive_value": primitive_value,
        "enum_option_id": None if enum_option_id is None else str(enum_option_id),
        "class_instance_id": (
            None if class_instance_id is None else str(class_instance_id)
        ),
        "inline_value_instance_id": None,
        "children": sorted(
            fingerprint_children,
            key=lambda item: (
                str(item["role"]),
                int(item["position"]) if item.get("position") is not None else -1,
                json.dumps(item["child"], sort_keys=True),
            ),
        ),
    }
    fingerprint = hashlib.sha256(
        json.dumps(
            fingerprint_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    payload: dict[str, object] = {
        "id": str(value_id),
        "type_descriptor": descriptor_payload,
        "type_descriptor_id": str(type_descriptor_id),
        "child_links": child_links,
    }
    if primitive_value is not None:
        payload["primitive_value"] = primitive_value
    if enum_option_id is not None:
        payload["enum_option_id"] = str(enum_option_id)
    if class_instance_id is not None:
        payload["class_instance_id"] = str(class_instance_id)
    return {
        "value_id": value_id,
        "payload": payload,
        "fingerprint": fingerprint,
        "fingerprint_payload": fingerprint_payload,
    }


def _code_package_direct_union_selection(
    *,
    type_descriptor: object,
    value: object,
) -> tuple[int, object, object] | None:
    members = _code_package_member_descriptors(type_descriptor)
    if not members:
        return None
    if value is None:
        null_members = [
            (position, descriptor)
            for position, descriptor in members.items()
            if _code_package_is_null_descriptor(descriptor)
        ]
        if len(null_members) != 1:
            return None
        selected_pos, selected_descriptor = null_members[0]
        return selected_pos, None, selected_descriptor
    non_null_members = [
        (position, descriptor)
        for position, descriptor in members.items()
        if not _code_package_is_null_descriptor(descriptor)
    ]
    if len(non_null_members) != 1:
        return None
    selected_pos, selected_descriptor = non_null_members[0]
    return selected_pos, value, selected_descriptor


def _code_package_element_descriptor(type_descriptor: object) -> object | None:
    elements = _code_package_child_descriptors(
        type_descriptor=type_descriptor,
        role="element",
    )
    if len(elements) != 1:
        return None
    return next(iter(elements.values()))


def _code_package_member_descriptors(type_descriptor: object) -> dict[int, object]:
    return _code_package_child_descriptors(
        type_descriptor=type_descriptor,
        role="member",
    )


def _code_package_child_descriptors(
    *,
    type_descriptor: object,
    role: str,
) -> dict[int, object]:
    members: dict[int, object] = {}
    for link in getattr(type_descriptor, "child_links", None) or []:
        if _enum_value(getattr(link, "role", None)) != role:
            continue
        position = getattr(link, "position", None)
        child = getattr(link, "child", None)
        if not isinstance(position, int) or child is None:
            continue
        members[position] = child
    return dict(sorted(members.items(), key=lambda item: item[0]))


def _code_package_is_null_descriptor(type_descriptor: object) -> bool:
    if _enum_value(getattr(type_descriptor, "kind", None)) != "primitive":
        return False
    primitive_config = getattr(type_descriptor, "primitive_config", None)
    primitive_type = getattr(primitive_config, "primitive_type", None)
    return _enum_value(getattr(primitive_type, "base_type", None)) == "null"


def _code_package_direct_type_descriptor_payload(
    type_descriptor: object,
) -> Mapping[str, object]:
    payload: dict[str, object] = {
        "kind": _enum_value(getattr(type_descriptor, "kind", None)),
    }
    for field_name in (
        "id",
        "class_config_id",
        "enum_config_id",
        "primitive_config_id",
    ):
        value = getattr(type_descriptor, field_name, None)
        if isinstance(value, UUID):
            payload[field_name] = str(value)
    collection_kind = getattr(type_descriptor, "collection_kind", None)
    if collection_kind is not None:
        payload["collection_kind"] = _enum_value(collection_kind)
    return payload


def _code_package_direct_primitive_value(value: object) -> JsonValue | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return {
            str(key): _code_package_direct_json_value(item)
            for key, item in value.items()
        }
    return {"value": _code_package_direct_json_value(value)}


def _code_package_direct_json_value(value: object) -> JsonValue:
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if hasattr(value, "value"):
        return _code_package_direct_json_value(getattr(value, "value"))
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_code_package_direct_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [_code_package_direct_json_value(item) for item in value]
    if isinstance(value, Mapping):
        return {
            str(key): _code_package_direct_json_value(item)
            for key, item in value.items()
        }
    return str(value)


def _code_package_deduped_attribute_links(
    class_config_attribute_configs: Iterable[object],
) -> list[object]:
    links: list[object] = []
    seen_attribute_config_ids: set[UUID] = set()
    for link in class_config_attribute_configs:
        attr_cfg = getattr(link, "attribute_config", None)
        attr_cfg_id = getattr(attr_cfg, "id", None) or getattr(
            link,
            "attribute_config_id",
            None,
        )
        if not isinstance(attr_cfg_id, UUID):
            links.append(link)
            continue
        if attr_cfg_id in seen_attribute_config_ids:
            continue
        seen_attribute_config_ids.add(attr_cfg_id)
        links.append(link)
    return sorted(
        links,
        key=lambda item: (
            (
                -1
                if getattr(item, "position", None) is None
                else getattr(item, "position", None)
            ),
            getattr(getattr(item, "attribute_config", None), "name", ""),
        ),
    )


def _code_package_relationship_attribute_config_ids(class_config: object) -> set[UUID]:
    ids: set[UUID] = set()
    for rel in getattr(class_config, "class_config_relationships", None) or []:
        for rel_attr in (
            getattr(rel, "class_config_relationship_attributes", None) or []
        ):
            attr_id = getattr(rel_attr, "attribute_config_id", None)
            if isinstance(attr_id, UUID):
                ids.add(attr_id)
    return ids


def _code_package_required_fk_attribute_config_ids(class_config: object) -> set[UUID]:
    owned_attr_ids = {
        link.attribute_config.id
        for link in getattr(class_config, "class_config_attribute_configs", None) or []
        if getattr(link, "attribute_config", None) is not None
        and isinstance(getattr(link.attribute_config, "id", None), UUID)
    }
    required_ids: set[UUID] = set()
    for rel in getattr(class_config, "class_config_relationships", None) or []:
        is_association = (
            getattr(rel, "class_config_relationship_association_edge", None) is not None
        )
        for rel_attr in (
            getattr(rel, "class_config_relationship_attributes", None) or []
        ):
            if _enum_value(getattr(rel_attr, "role", None)) != "foreign_key":
                continue
            attr_id = getattr(rel_attr, "attribute_config_id", None)
            if not isinstance(attr_id, UUID) or attr_id not in owned_attr_ids:
                continue
            if is_association or bool(getattr(rel, "forward_required", False)):
                required_ids.add(attr_id)
    return required_ids


async def _try_build_code_package_reused_direct_desired_state(
    *,
    index: MetaGraphRuntimeIndex,
    opg,
    branch_id: UUID,
    projection_hash: str,
    head: Mapping[str, object] | None,
    previous_snapshot_index_payload: Mapping[str, object] | None,
    domain_oig_id: UUID,
    code_package: CodePackage,
    code_package_config_id: UUID,
    manifest_kind: str,
    surface: str,
    objects_by_id: Mapping[UUID, BaseORMModel],
    current_source_states_by_id: (
        Mapping[UUID, _CodePackageSourceObjectState] | None
    ) = None,
    current_source_object_path_index: Mapping[str, tuple[UUID, ...]] | None = None,
) -> _CodePackageDesiredState | None:
    head_commit_id = _head_uuid(head, "commit_id")
    if head_commit_id is None:
        return None
    with commit_perf_span(
        phase="code_package.reused_state.previous_source_index",
        category="code_package.reused_state",
    ):
        previous_source_states_by_id = (
            _code_package_source_object_states_from_index_payload(
                previous_snapshot_index_payload,
            )
        )
    if previous_source_states_by_id is None:
        return None
    include_state_row_maps = (
        len(previous_source_states_by_id)
        >= _CODE_PACKAGE_STATE_ROW_MAP_MIN_SOURCE_OBJECT_COUNT
    )
    with commit_perf_span(
        phase="code_package.reused_state.state_selection",
        category="code_package.reused_state",
        metadata={"previous_source_object_count": len(previous_source_states_by_id)},
    ):
        state_selection = await _get_code_package_text_snapshot_state_selection(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
            class_instance_ids=(),
            previous_snapshot_index_payload=previous_snapshot_index_payload,
            expected_object_instance_graph_id=domain_oig_id,
            expected_graph_hash=_head_string(head, "graph_hash_post"),
            include_state_row_maps=include_state_row_maps,
        )
    if state_selection is None:
        return None
    if (
        _snapshot_state_root_source_object_id(state_selection.payload)
        != code_package.id
    ):
        return None
    with commit_perf_span(
        phase="code_package.reused_state.previous_state_rows_index",
        category="code_package.reused_state",
        metadata={
            "state_row_count": len(state_selection.state_rows),
            "state_row_maps_reused": state_selection.state_row_maps is not None,
        },
    ):
        old_class_state_rows_by_id = (
            state_selection.state_row_maps.class_state_rows_by_raw_id
            if state_selection.state_row_maps is not None
            else _class_instance_state_rows_by_raw_id(
                state_selection.state_rows,
            )
        )
    with commit_perf_span(
        phase="code_package.reused_state.previous_payload_index",
        category="code_package.reused_state",
    ):
        old_class_payloads_by_id = _snapshot_state_class_instance_payloads_by_raw_id(
            state_selection.payload,
        )
    if old_class_payloads_by_id is None:
        return None
    with commit_perf_span(
        phase="code_package.reused_state.current_source_signatures",
        category="code_package.reused_state",
        metadata={"object_count": len(objects_by_id)},
    ):
        if current_source_states_by_id is None:
            current_source_states_by_id = (
                _code_package_source_object_states_by_source_id(
                    domain_oig_id=domain_oig_id,
                    objects_by_id=objects_by_id,
                )
            )
        else:
            current_source_states_by_id = dict(current_source_states_by_id)
    with commit_perf_span(
        phase="code_package.reused_state.changed_source_scan",
        category="code_package.reused_state",
        metadata={"object_count": len(current_source_states_by_id)},
    ):
        changed_source_object_ids = {
            source_object_id
            for source_object_id, source_state in current_source_states_by_id.items()
            if previous_source_states_by_id.get(source_object_id) != source_state
        }
        changed_source_object_ids.add(code_package.id)
        relationship_topology_reused = len(
            previous_source_states_by_id
        ) >= _CODE_PACKAGE_PARTIAL_SOURCE_REUSE_MIN_SOURCE_OBJECT_COUNT and set(
            previous_source_states_by_id
        ) == set(
            current_source_states_by_id
        )
        old_relationship_keys: set[tuple[UUID, UUID, UUID]] = set()
        if relationship_topology_reused:
            old_relationship_keys = (
                set(state_selection.state_row_maps.relationship_keys)
                if state_selection.state_row_maps is not None
                else _relationship_keys_from_state_rows(state_selection.state_rows)
            )

    with commit_perf_span(
        phase="code_package.direct_state.relationship_indexes",
        category="code_package.direct_state",
        metadata={"object_count": len(objects_by_id), "reuse": True},
    ):
        relationship_context = _code_package_direct_relationship_context(
            index=index,
            opg=opg,
        )
        relationship_attribute_ids_by_cc_id = (
            relationship_context.relationship_attribute_ids_by_cc_id
        )
        include_relationship_attr_ids_by_cc_id = (
            relationship_context.include_relationship_attr_ids_by_cc_id
        )

    with commit_perf_span(
        phase="code_package.direct_state.class_instances",
        category="code_package.direct_state",
        metadata={
            "object_count": len(objects_by_id),
            "changed_object_count": len(changed_source_object_ids),
            "reuse": True,
        },
    ):
        class_configs_by_id = dict(index.class_configs_by_id)
        class_instances_by_source_id: dict[UUID, object] = {}
        materialized_class_instances: list[ClassInstance] = []
        reused_class_instance_payloads: list[Mapping[str, object]] = []
        class_state_rows_by_id: dict[UUID, tuple[CommitStateRow, ...]] = {}
        for source_object_id, source_state in sorted(
            current_source_states_by_id.items(),
            key=lambda item: str(item[0]),
        ):
            if source_object_id not in changed_source_object_ids:
                raw_class_instance_id = str(source_state.class_instance_id)
                old_rows = old_class_state_rows_by_id.get(
                    raw_class_instance_id,
                )
                old_payload = old_class_payloads_by_id.get(
                    raw_class_instance_id,
                )
                if old_rows is None or old_payload is None:
                    return None
                class_state_rows_by_id[source_state.class_instance_id] = old_rows
                reused_class_instance_payloads.append(old_payload)
                class_instances_by_source_id[source_object_id] = (
                    source_state.class_instance_id
                )
                continue

            source_object = objects_by_id.get(source_object_id)
            if source_object is None:
                return None
            class_config = class_configs_by_id.get(source_state.class_config_id)
            if class_config is None:
                raise RuntimeError(
                    "CodePackage direct snapshot class config not found: "
                    f"class_config_id={source_state.class_config_id}"
                )
            source = (
                _code_package_config_overlay(
                    code_package=code_package,
                    code_package_config_id=code_package_config_id,
                    surface=surface,
                )
                if source_object_id == code_package.id
                else source_object
            )
            if source_object_id != code_package.id:
                direct_class_state = _try_build_code_package_direct_class_state(
                    object_instance_graph_id=domain_oig_id,
                    class_config=class_config,
                    source=source,
                    relationship_attribute_config_ids=(
                        relationship_attribute_ids_by_cc_id.get(
                            source_state.class_config_id
                        )
                    ),
                    include_relationship_attribute_config_ids=(
                        include_relationship_attr_ids_by_cc_id.get(
                            source_state.class_config_id,
                        )
                    ),
                )
                if direct_class_state is not None:
                    if direct_class_state.class_instance_id != (
                        source_state.class_instance_id
                    ):
                        return None
                    try:
                        class_instance = ClassInstance.model_validate(
                            direct_class_state.snapshot_payload
                        )
                    except Exception:
                        class_instance = None
                    if (
                        class_instance is not None
                        and class_instance.id == direct_class_state.class_instance_id
                    ):
                        materialized_class_instances.append(class_instance)
                        class_state_rows_by_id[direct_class_state.class_instance_id] = (
                            direct_class_state.state_rows
                        )
                        reused_class_instance_payloads.append(
                            direct_class_state.snapshot_payload
                        )
                        class_instances_by_source_id[source_object_id] = (
                            direct_class_state.class_instance_id
                        )
                        continue
            class_instance = build_class_instance(
                object_instance_graph_id=domain_oig_id,
                class_config=class_config,
                class_configs_by_id=class_configs_by_id,
                source=source,
                enum_option_resolver=default_meta_enum_option_resolver,
                relationship_attribute_config_ids=(
                    relationship_attribute_ids_by_cc_id.get(
                        source_state.class_config_id
                    )
                ),
                include_relationship_attribute_config_ids=(
                    include_relationship_attr_ids_by_cc_id.get(
                        source_state.class_config_id,
                    )
                ),
                attach_class_config=False,
            )
            if class_instance.id != source_state.class_instance_id:
                return None
            materialized_class_instances.append(class_instance)
            class_state_rows_by_id[class_instance.id] = (
                _code_package_class_instance_state_rows(class_instance)
            )
            class_instances_by_source_id[source_object_id] = class_instance

    with commit_perf_span(
        phase="code_package.direct_state.relationship_configs",
        category="code_package.direct_state",
        metadata={
            "relationship_count": relationship_context.relationship_count,
            "cache_hit": relationship_context.cache_hit,
            "reuse": True,
        },
    ):
        relationship_configs_by_key = relationship_context.relationship_configs_by_key
    with commit_perf_span(
        phase="code_package.direct_state.relationships",
        category="code_package.direct_state",
        metadata={
            "class_instance_count": len(class_instances_by_source_id),
            "topology_reused": relationship_topology_reused,
            "reuse": True,
        },
    ):
        if relationship_topology_reused:
            relationships = [
                _relationship_from_key(
                    key,
                    object_instance_graph_id=domain_oig_id,
                )
                for key in sorted(
                    old_relationship_keys,
                    key=lambda item: tuple(str(value) for value in item),
                )
            ]
        else:
            relationships = _build_code_package_direct_relationships(
                domain_oig_id=domain_oig_id,
                code_package=code_package,
                class_instances_by_source_id=class_instances_by_source_id,
                relationship_configs_by_key=relationship_configs_by_key,
            )
    root_class_instance = next(
        (
            class_instance
            for class_instance in materialized_class_instances
            if class_instance.source_object_id == code_package.id
        ),
        None,
    )
    if root_class_instance is None:
        return None
    if root_class_instance.id is None or root_class_instance.class_config_id is None:
        raise RuntimeError(
            "CodePackage direct snapshot root ClassInstance missing id/config"
        )
    with commit_perf_span(
        phase="code_package.direct_state.indexes",
        category="code_package.direct_state",
        metadata={
            "class_instance_count": len(class_state_rows_by_id),
            "materialized_class_instance_count": len(materialized_class_instances),
            "relationship_count": len(relationships),
            "reuse": True,
        },
    ):
        class_instances_by_id = _class_instances_by_id_from_iterable(
            materialized_class_instances,
        )
        relationships_by_key = _relationships_by_key_from_relationships(relationships)
        state_index = _code_package_desired_state_index_from_state_rows(
            class_state_rows_by_id=class_state_rows_by_id,
            class_instance_relationships=tuple(relationships),
        )
        graph_hash = state_index.compute_hash()
    graph_meta = {
        "id": domain_oig_id,
        "key": str(branch_id),
        "name": f"OIG_{branch_id.hex[:8]}",
        "description": "CodePackage text snapshot",
        "object_projection_graph_id": opg.id,
        "root_class_instance_id": root_class_instance.id,
        "root_source_object_id": root_class_instance.source_object_id,
        "hash": graph_hash,
    }
    with commit_perf_span(
        phase="code_package.reused_state.source_index_serialize",
        category="code_package.reused_state",
        metadata={"object_count": len(current_source_states_by_id)},
    ):
        source_object_state_index = _code_package_source_object_state_index_from_states(
            current_source_states_by_id.values(),
            source_object_path_index=current_source_object_path_index,
        )
    return _CodePackageDesiredState(
        object_instance_graph_id=domain_oig_id,
        graph_hash=graph_hash,
        state_index=state_index,
        root_metadata=ObjectInstanceGraphCommitRootMetadata(
            object_instance_graph_key=str(branch_id),
            object_instance_graph_name=f"OIG_{branch_id.hex[:8]}",
            object_instance_graph_description="CodePackage text snapshot",
            root_class_config_id=root_class_instance.class_config_id,
            root_source_object_id=root_class_instance.source_object_id,
        ),
        root_class_instance=root_class_instance,
        class_instances=tuple(materialized_class_instances),
        class_instance_payloads=tuple(reused_class_instance_payloads),
        class_instances_by_id=class_instances_by_id,
        class_instance_relationships=tuple(relationships),
        relationships_by_key=relationships_by_key,
        graph_meta=graph_meta,
        source_object_state_index=source_object_state_index,
        previous_snapshot_payload=state_selection.payload,
        previous_snapshot_state_rows=state_selection.state_rows,
        previous_snapshot_state_maps=state_selection.state_row_maps,
    )


def _build_code_package_oig_from_desired_state(
    *,
    index: MetaGraphRuntimeIndex,
    opg,
    branch_id: UUID,
    domain_oig_id: UUID,
    desired_state: _CodePackageDesiredState,
) -> ObjectInstanceGraph:
    return build_object_instance_graph_from_class_instances(
        key=str(branch_id),
        name=f"OIG_{branch_id.hex[:8]}",
        description="CodePackage text snapshot",
        object_config_graph_id=index.ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=desired_state.root_class_instance,
        class_instances=list(desired_state.class_instances),
        class_instance_relationships=list(desired_state.class_instance_relationships),
        oig_id=domain_oig_id,
    )


def _build_code_package_generic_desired_oig(
    *,
    index: MetaGraphRuntimeIndex,
    opg,
    branch_id: UUID,
    domain_oig_id: UUID,
    code_package: CodePackage,
    code_package_config_id: UUID,
    manifest_kind: str,
    surface: str,
    objects_by_id: Mapping[UUID, BaseORMModel],
):
    return build_object_instance_graph(
        root_instance=_code_package_config_overlay(
            code_package=code_package,
            code_package_config_id=code_package_config_id,
            surface=surface,
        ),
        object_config_graph=index.ocg,
        object_projection_graph=opg,
        key=str(branch_id),
        name=f"OIG_{branch_id.hex[:8]}",
        description="CodePackage text snapshot",
        oig_id=domain_oig_id,
        instance_registry=tuple(
            obj for obj_id, obj in objects_by_id.items() if obj_id != code_package.id
        ),
        enum_option_resolver=default_meta_enum_option_resolver,
    )


def _relationships_by_id(*, index: MetaGraphRuntimeIndex) -> dict[UUID, object]:
    relationships = {}
    for class_config in index.class_configs_by_id.values():
        for relationship in class_config.class_config_relationships or []:
            relationships[relationship.id] = relationship
    return relationships


def _clear_code_package_direct_relationship_context_cache_for_tests() -> None:
    _CODE_PACKAGE_DIRECT_RELATIONSHIP_CONTEXT_CACHE.clear()


def _code_package_direct_relationship_context(
    *,
    index: MetaGraphRuntimeIndex,
    opg,
) -> _CodePackageDirectRelationshipContext:
    cache_key = _code_package_direct_relationship_context_cache_key(
        index=index,
        opg=opg,
    )
    cached = _CODE_PACKAGE_DIRECT_RELATIONSHIP_CONTEXT_CACHE.get(cache_key)
    if cached is not None:
        return _CodePackageDirectRelationshipContext(
            relationships_by_id=cached.relationships_by_id,
            relationship_attribute_ids_by_cc_id=(
                cached.relationship_attribute_ids_by_cc_id
            ),
            include_relationship_attr_ids_by_cc_id=(
                cached.include_relationship_attr_ids_by_cc_id
            ),
            relationship_configs_by_key=cached.relationship_configs_by_key,
            relationship_count=cached.relationship_count,
            cache_hit=True,
        )

    relationships_by_id = _relationships_by_id(index=index)
    context = _CodePackageDirectRelationshipContext(
        relationships_by_id=relationships_by_id,
        relationship_attribute_ids_by_cc_id=(
            build_relationship_attribute_config_ids_by_class_config_id(
                class_configs_by_id=index.class_configs_by_id,
                relationships_by_id=relationships_by_id,
            )
        ),
        include_relationship_attr_ids_by_cc_id=(
            build_include_relationship_attribute_config_ids_by_class_config_id(
                object_projection_graph=opg,
                class_configs_by_id=index.class_configs_by_id,
                relationships_by_id=relationships_by_id,
            )
        ),
        relationship_configs_by_key=_code_package_relationship_configs_by_key(
            index=index,
            relationships_by_id=relationships_by_id,
        ),
        relationship_count=len(relationships_by_id),
    )
    if (
        len(_CODE_PACKAGE_DIRECT_RELATIONSHIP_CONTEXT_CACHE)
        >= _CODE_PACKAGE_DIRECT_RELATIONSHIP_CONTEXT_CACHE_MAX
    ):
        oldest_key = next(iter(_CODE_PACKAGE_DIRECT_RELATIONSHIP_CONTEXT_CACHE))
        _CODE_PACKAGE_DIRECT_RELATIONSHIP_CONTEXT_CACHE.pop(oldest_key, None)
    _CODE_PACKAGE_DIRECT_RELATIONSHIP_CONTEXT_CACHE[cache_key] = context
    return context


def _code_package_direct_relationship_context_cache_key(
    *,
    index: MetaGraphRuntimeIndex,
    opg,
) -> tuple[int, int, str, str, int]:
    return (
        id(index),
        id(opg),
        str(getattr(index.ocg, "id", "")),
        str(getattr(opg, "id", "")),
        len(index.class_configs_by_id),
    )


def _code_package_relationship_configs_by_key(
    *,
    index: MetaGraphRuntimeIndex,
    relationships_by_id: Mapping[UUID, object],
) -> dict[tuple[str, str, str], UUID]:
    configs_by_key: dict[tuple[str, str, str], UUID] = {}
    seen_ids_by_key: dict[tuple[str, str, str], set[UUID]] = {}
    for relationship in relationships_by_id.values():
        source_class_config_id = getattr(relationship, "class_config_id", None)
        target_class_config_id = getattr(relationship, "target_class_config_id", None)
        relationship_key = getattr(relationship, "relationship_key", None)
        if (
            source_class_config_id is None
            or target_class_config_id is None
            or not isinstance(relationship_key, str)
        ):
            continue
        source_class = index.class_configs_by_id.get(source_class_config_id)
        target_class = index.class_configs_by_id.get(target_class_config_id)
        if source_class is None or target_class is None:
            continue
        key = (str(source_class.name), str(target_class.name), relationship_key)
        relationship_ids = seen_ids_by_key.setdefault(key, set())
        relationship_ids.add(relationship.id)
        if len(relationship_ids) > 1:
            raise RuntimeError(
                "CodePackage direct snapshot relationship key is ambiguous: " f"{key}"
            )
        configs_by_key[key] = relationship.id
    return configs_by_key


def _build_code_package_direct_relationships(
    *,
    domain_oig_id: UUID,
    code_package: CodePackage,
    class_instances_by_source_id: Mapping[UUID, object],
    relationship_configs_by_key: Mapping[tuple[str, str, str], UUID],
) -> list[ClassInstanceRelationship]:
    relationships_by_key: dict[
        tuple[UUID, UUID, UUID],
        ClassInstanceRelationship,
    ] = {}

    def _add_relationship(
        *,
        source_object: BaseORMModel | None,
        target_object: BaseORMModel | None,
        source_class_name: str,
        target_class_name: str,
        relationship_key: str,
    ) -> None:
        if source_object is None or target_object is None:
            return
        source_ci = class_instances_by_source_id.get(source_object.id)
        target_ci = class_instances_by_source_id.get(target_object.id)
        if source_ci is None or target_ci is None:
            raise RuntimeError(
                "CodePackage direct snapshot relationship target missing "
                "ClassInstance: "
                f"{source_class_name}.{relationship_key} "
                f"{getattr(source_object, 'id', None)} -> "
                f"{getattr(target_object, 'id', None)}"
            )
        source_class_instance_id = (
            source_ci if isinstance(source_ci, UUID) else getattr(source_ci, "id", None)
        )
        target_class_instance_id = (
            target_ci if isinstance(target_ci, UUID) else getattr(target_ci, "id", None)
        )
        class_config_relationship_id = relationship_configs_by_key.get(
            (source_class_name, target_class_name, relationship_key),
        )
        if class_config_relationship_id is None:
            raise RuntimeError(
                "CodePackage direct snapshot relationship config not found: "
                f"{source_class_name}.{relationship_key}->{target_class_name}"
            )
        if not isinstance(source_class_instance_id, UUID) or not isinstance(
            target_class_instance_id,
            UUID,
        ):
            raise RuntimeError(
                "CodePackage direct snapshot relationship endpoint missing "
                "ClassInstance id"
            )
        key = (
            class_config_relationship_id,
            source_class_instance_id,
            target_class_instance_id,
        )
        if key in relationships_by_key:
            return
        with disable_change_tracking_hooks():
            with disable_autobind():
                relationships_by_key[key] = ClassInstanceRelationship(
                    id=stable_class_instance_relationship_id(
                        class_config_relationship_id=class_config_relationship_id,
                        source_class_instance_id=source_class_instance_id,
                        target_class_instance_id=target_class_instance_id,
                    ),
                    object_instance_graph_id=domain_oig_id,
                    class_config_relationship_id=class_config_relationship_id,
                    source_class_instance_id=source_class_instance_id,
                    target_class_instance_id=target_class_instance_id,
                )

    for package_code in code_package.code_package_codes:
        _add_relationship(
            source_object=code_package,
            target_object=package_code,
            source_class_name="CodePackage",
            target_class_name="CodePackageCode",
            relationship_key="code_package_codes",
        )
        _add_relationship(
            source_object=package_code,
            target_object=package_code.code,
            source_class_name="CodePackageCode",
            target_class_name="Code",
            relationship_key="code",
        )
        code = package_code.code
        if code is None:
            continue
        _add_relationship(
            source_object=code,
            target_object=code.content_part_text,
            source_class_name="Code",
            target_class_name="ContentPartText",
            relationship_key="content_part_text",
        )
        for section in code.code_sections:
            _add_relationship(
                source_object=code,
                target_object=section,
                source_class_name="Code",
                target_class_name="CodeSection",
                relationship_key="code_sections",
            )
            _add_relationship(
                source_object=section,
                target_object=section.content_part_text_segment,
                source_class_name="CodeSection",
                target_class_name="ContentPartTextSegment",
                relationship_key="content_part_text_segment",
            )
        content_part_text = code.content_part_text
        if content_part_text is None:
            continue
        for segment in content_part_text.segments:
            _add_relationship(
                source_object=content_part_text,
                target_object=segment,
                source_class_name="ContentPartText",
                target_class_name="ContentPartTextSegment",
                relationship_key="segments",
            )

    for artifact in code_package.artifacts:
        _add_relationship(
            source_object=code_package,
            target_object=artifact,
            source_class_name="CodePackage",
            target_class_name="CodePackageArtifact",
            relationship_key="artifacts",
        )

    return [
        relationship
        for _key, relationship in sorted(
            relationships_by_key.items(),
            key=lambda item: tuple(str(part) for part in item[0]),
        )
    ]


def _code_package_config_overlay(
    *,
    code_package: CodePackage,
    code_package_config_id: UUID,
    surface: str,
) -> ModelIntrospection:
    return _ModelIntrospectionOverlay(
        source=code_package,
        values_by_name={
            "code_package_config_id": code_package_config_id,
            "surface": surface,
        },
    )


def _build_code_package_text_snapshot_changes(
    *,
    before_oig,
    desired_oig,
    oigi_id: UUID,
):
    return build_object_instance_graph_identity_snapshot_changes(
        old=before_oig,
        new=desired_oig,
        object_instance_graph_identity_id=oigi_id,
    )


async def _ensure_code_package_text_snapshot_state_snapshot(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    oig: ObjectInstanceGraph,
) -> dict[str, object]:
    snapshot_store = FSSnapshotStore()
    state_payload = await snapshot_store.get_snapshot_state_rows(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=oig.id,
        expected_graph_hash=str(oig.hash or ""),
    )
    if state_payload is None:
        state_payload = await snapshot_store.put_state_snapshot(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            oig=oig,
        )
    file_metadata = snapshot_store.snapshot_state_rows_file_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    if state_payload is None or file_metadata is None:
        raise RuntimeError(
            "CodePackage text snapshot could not write state snapshot: "
            f"commit_id={commit_id}"
        )
    return {
        "state_snapshot_payload_sha256": state_payload.get("payload_sha256"),
        "state_snapshot_state_hash": state_payload.get("state_hash"),
        **file_metadata,
    }


async def _ensure_code_package_text_snapshot_state_snapshot_from_state(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    desired_state: _CodePackageDesiredState,
) -> dict[str, object]:
    with commit_perf_span(
        phase="code_package.snapshot_commit.ensure_state_snapshot_from_state",
        category="code_package.snapshot_commit",
        metadata={
            "graph_hash_source": desired_state.graph_hash_source,
            "has_previous_commit": desired_state.previous_commit_id is not None,
            "replacement_segment_count": len(desired_state.replacement_class_segments),
        },
    ):
        return await _ensure_code_package_text_snapshot_state_snapshot_from_state_inner(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            desired_state=desired_state,
        )


async def _ensure_code_package_text_snapshot_state_snapshot_from_state_inner(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    desired_state: _CodePackageDesiredState,
) -> dict[str, object]:
    snapshot_store = FSSnapshotStore()
    if desired_state.graph_hash_source in {"witness_hash", "witness_cursor_hash"} and (
        desired_state.post_witness_ref is not None
        or desired_state.post_witness_cursor_summary is not None
    ):
        if (
            desired_state.previous_commit_id is not None
            and desired_state.replacement_class_segments
        ):
            state_payload = await snapshot_store.put_state_snapshot_class_segment_index_from_previous(
                branch_id=branch_id,
                projection_hash=projection_hash,
                previous_commit_id=desired_state.previous_commit_id,
                commit_id=commit_id,
                object_instance_graph_id=desired_state.object_instance_graph_id,
                graph_hash=desired_state.graph_hash,
                post_witness_ref=(
                    desired_state.post_witness_ref
                    if desired_state.graph_hash_source != "witness_cursor_hash"
                    else None
                ),
                replacement_class_segments=desired_state.replacement_class_segments,
                graph_meta=desired_state.graph_meta,
                graph_hash_source=desired_state.graph_hash_source,
                state_witness_cursor_summary=(
                    desired_state.post_witness_cursor_summary
                ),
                state_witness_cursor_chunks=desired_state.post_witness_cursor_chunks,
            )
        else:
            if desired_state.post_witness_ref is None:
                raise RuntimeError(
                    "CodePackage full witness snapshot missing post witness ref"
                )
            state_payload = await snapshot_store.put_state_snapshot_class_segment_index(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_id=desired_state.object_instance_graph_id,
                graph_hash=desired_state.graph_hash,
                post_witness_ref=desired_state.post_witness_ref,
                class_segments=_code_package_raw_class_segments_from_desired_state(
                    desired_state,
                ),
                graph_meta=desired_state.graph_meta,
                graph_hash_source=desired_state.graph_hash_source,
                state_witness_cursor_summary=(
                    desired_state.post_witness_cursor_summary
                ),
                state_witness_cursor_chunks=desired_state.post_witness_cursor_chunks,
            )
        if state_payload is not None:
            return _code_package_state_segment_index_metadata_payload(state_payload)
    state_payload = await snapshot_store.get_snapshot_state_rows(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_object_instance_graph_id=desired_state.object_instance_graph_id,
        expected_graph_hash=desired_state.graph_hash,
    )
    if state_payload is None:
        write_state_class_segment_index = _code_package_state_class_segments_enabled(
            node_count=desired_state.state_index.node_count,
        )
        if desired_state.class_instance_payloads:
            state_payload = await snapshot_store.put_state_snapshot_rows_from_payloads(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_id=desired_state.object_instance_graph_id,
                graph_hash=desired_state.graph_hash,
                graph_meta=desired_state.graph_meta,
                class_instance_payloads=desired_state.class_instance_payloads,
                class_instances=desired_state.class_instances,
                class_instance_relationships=desired_state.class_instance_relationships,
                state_index=desired_state.state_index,
                write_state_class_segment_index=write_state_class_segment_index,
            )
        else:
            state_payload = await snapshot_store.put_state_snapshot_rows(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                object_instance_graph_id=desired_state.object_instance_graph_id,
                graph_hash=desired_state.graph_hash,
                graph_meta=desired_state.graph_meta,
                class_instances=desired_state.class_instances,
                class_instance_relationships=desired_state.class_instance_relationships,
                state_index=desired_state.state_index,
                write_state_class_segment_index=write_state_class_segment_index,
            )
    file_metadata = snapshot_store.snapshot_state_rows_file_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    if state_payload is None or file_metadata is None:
        raise RuntimeError(
            "CodePackage text snapshot could not write state snapshot: "
            f"commit_id={commit_id}"
        )
    return {
        "state_snapshot_payload_sha256": state_payload.get("payload_sha256"),
        "state_snapshot_state_hash": state_payload.get("state_hash"),
        **file_metadata,
    }


def _code_package_state_segment_index_metadata_payload(
    payload: Mapping[str, object],
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "state_snapshot_kind": "class_segment_index",
        "state_snapshot_schema": str(payload.get("schema") or ""),
        "state_snapshot_graph_hash": str(payload.get("graph_hash") or ""),
        "state_snapshot_graph_hash_source": str(
            payload.get("graph_hash_source") or "state_hash",
        ),
        "state_snapshot_witness_hash": str(payload.get("witness_hash") or ""),
        "state_snapshot_row_count": _payload_int(payload, "row_count") or 0,
        "state_snapshot_segment_count": _payload_int(payload, "segment_count") or 0,
    }
    state_hash = payload.get("state_hash")
    if isinstance(state_hash, str) and state_hash:
        metadata["state_snapshot_state_hash"] = state_hash
    witness_cursor = payload.get("state_witness_cursor")
    if isinstance(witness_cursor, Mapping):
        metadata["state_snapshot_witness_cursor"] = {
            str(key): value
            for key, value in witness_cursor.items()
            if isinstance(key, str)
        }
    return metadata


def _code_package_raw_class_segments_from_desired_state(
    desired_state: _CodePackageDesiredState,
) -> tuple[ObjectInstanceGraphSnapshotStateRawClassSegment, ...]:
    if desired_state.post_witness_ref is None:
        raise RuntimeError("CodePackage witness snapshot missing post witness ref")
    class_payloads_by_id: dict[UUID, Mapping[str, object]] = {}
    for class_instance in desired_state.class_instances:
        if class_instance.id is None:
            continue
        class_payloads_by_id[class_instance.id] = class_instance.model_dump(
            mode="json",
            exclude_none=True,
        )
    for payload in desired_state.class_instance_payloads:
        raw_id = payload.get("id")
        if not isinstance(raw_id, str):
            continue
        class_payloads_by_id[UUID(raw_id)] = payload

    rows_by_id = desired_state.state_index.row_maps(
        include_relationship_keys=False,
    ).class_state_rows_by_id
    segment_refs_by_key = {
        segment.key: segment
        for segment in desired_state.post_witness_ref.segments
        if segment.kind == "CLASS"
    }
    segments: list[ObjectInstanceGraphSnapshotStateRawClassSegment] = []
    for class_instance_id, rows in sorted(
        rows_by_id.items(), key=lambda item: str(item[0])
    ):
        node_rows = [row for row in rows if row.kind == "NODE"]
        if len(node_rows) != 1:
            raise RuntimeError(
                "CodePackage witness snapshot class rows require one NODE row: "
                f"{class_instance_id}"
            )
        payload = class_payloads_by_id.get(class_instance_id)
        if payload is None:
            raise RuntimeError(
                "CodePackage witness snapshot missing class payload: "
                f"{class_instance_id}"
            )
        segment_ref = segment_refs_by_key.get(f"class:{class_instance_id}")
        if segment_ref is None:
            raise RuntimeError(
                "CodePackage witness snapshot missing class segment ref: "
                f"{class_instance_id}"
            )
        source_object_id = None
        raw_source_object_id = payload.get("source_object_id")
        if isinstance(raw_source_object_id, str):
            source_object_id = UUID(raw_source_object_id)
        segments.append(
            ObjectInstanceGraphSnapshotStateRawClassSegment(
                class_instance_id=class_instance_id,
                class_config_id=UUID(node_rows[0].key),
                source_object_id=source_object_id,
                rows_text=_code_package_state_rows_text(rows),
                row_count=len(rows),
                row_hash=segment_ref.row_hash,
                snapshot_payload=dict(payload),
                segment_ref=segment_ref,
            )
        )
    return tuple(segments)


def _build_code_package_rooted_base(
    *,
    index: MetaGraphRuntimeIndex,
    opg,
    branch_id: UUID,
    domain_oig_id: UUID,
    root_object_id: UUID,
):
    return build_rooted_object_instance_graph_base(
        key=str(branch_id),
        name=f"OIG_{branch_id.hex[:8]}",
        description="ROOTED_BASE",
        object_config_graph=index.ocg,
        object_projection_graph=opg,
        root_source_object_id=root_object_id,
        oig_id=domain_oig_id,
    )


def _root_source_object_id(oig: object) -> UUID | None:
    value = getattr(oig, "root_source_object_id", None)
    if isinstance(value, UUID):
        return value
    root_class_instance = getattr(oig, "root_class_instance", None)
    root_value = getattr(root_class_instance, "source_object_id", None)
    return root_value if isinstance(root_value, UUID) else None


async def _build_code_package_text_snapshot_changes_from_snapshot_state(
    *,
    branch_id: UUID,
    projection_hash: str,
    head: Mapping[str, object] | None,
    previous_snapshot_index_payload: Mapping[str, object] | None,
    domain_oig_id: UUID,
    root_object_id: UUID,
    desired_state: _CodePackageDesiredState,
    desired_state_index: CommitStateIndex,
    oigi_id: UUID,
    previous_snapshot_payload: Mapping[str, object] | None = None,
    previous_snapshot_state_rows: tuple[CommitStateRow, ...] | None = None,
    previous_snapshot_state_maps: CommitStateRowMaps | None = None,
) -> _CodePackageSnapshotChangeResult | None:
    head_commit_id = _head_uuid(head, "commit_id")
    if head_commit_id is None:
        return None
    if (
        previous_snapshot_payload is not None
        and previous_snapshot_state_rows is not None
    ):
        state_payload = previous_snapshot_payload
        state_rows = previous_snapshot_state_rows
        state_maps = previous_snapshot_state_maps
    else:
        state_selection = await _get_code_package_text_snapshot_state_selection(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
            class_instance_ids=(),
            previous_snapshot_index_payload=previous_snapshot_index_payload,
            expected_object_instance_graph_id=domain_oig_id,
            expected_graph_hash=_head_string(head, "graph_hash_post"),
        )
        if state_selection is None:
            return None
        state_payload = state_selection.payload
        state_rows = state_selection.state_rows
        state_maps = state_selection.state_row_maps
    if _snapshot_state_root_source_object_id(state_payload) != root_object_id:
        return None
    raw_state_hash = state_payload.get("state_hash")
    if not isinstance(raw_state_hash, str) or not raw_state_hash:
        return None
    use_state_row_maps = (
        _should_use_code_package_state_row_maps(
            old_rows=state_rows,
            desired_rows=desired_state_index.rows,
        )
        or state_maps is not None
    )
    if use_state_row_maps:
        pre_state_index = CommitStateIndex(rows=state_rows)
        pre_state_maps = (
            state_maps if state_maps is not None else pre_state_index.row_maps()
        )
        desired_state_maps = desired_state_index.row_maps(
            include_relationship_keys=False,
        )
        changed_class_instance_ids = _class_instance_ids_with_state_row_changes(
            old_maps=pre_state_maps,
            desired_maps=desired_state_maps,
        )
    else:
        pre_state_index = CommitStateIndex(rows=state_rows)
        pre_state_maps = None
        desired_state_maps = None
        changed_class_instance_ids = (
            _class_instance_ids_with_state_row_changes_from_rows(
                old_rows=state_rows,
                desired_state_index=desired_state_index,
            )
        )
    old_class_instances_by_id: Mapping[UUID, ClassInstance] = {}
    if changed_class_instance_ids:
        selected_class_instances = _snapshot_state_selected_class_instances(
            payload=state_payload,
            class_instance_ids=changed_class_instance_ids,
        )
        if selected_class_instances is None:
            return None
        old_class_instances_by_id = selected_class_instances
    try:
        if pre_state_maps is not None and desired_state_maps is not None:
            changes = _build_code_package_direct_state_row_changes_from_maps(
                old_graph_id=domain_oig_id,
                old_state_maps=pre_state_maps,
                old_class_instances_by_id=old_class_instances_by_id,
                desired_object_instance_graph_id=(
                    desired_state.object_instance_graph_id
                ),
                desired_class_instances_by_id=desired_state.class_instances_by_id,
                desired_relationships_by_key=desired_state.relationships_by_key,
                desired_state_maps=desired_state_maps,
                object_instance_graph_identity_id=oigi_id,
            )
        else:
            changes = _build_code_package_direct_state_row_changes_from_rows(
                old_graph_id=domain_oig_id,
                old_state_rows=state_rows,
                old_class_instances_by_id=old_class_instances_by_id,
                desired_object_instance_graph_id=(
                    desired_state.object_instance_graph_id
                ),
                desired_class_instances_by_id=desired_state.class_instances_by_id,
                desired_relationships_by_key=desired_state.relationships_by_key,
                desired_state_index=desired_state_index,
                object_instance_graph_identity_id=oigi_id,
            )
    except ValueError:
        return None
    if changes is None:
        return None
    return _CodePackageSnapshotChangeResult(
        changes=changes,
        pre_state_index=pre_state_index,
        pre_state_evidence=ObjectInstanceGraphCommitPreStateEvidence(
            state_hash=raw_state_hash,
            row_count=len(state_rows),
            source_contract="aware.oig.snapshot_state_rows.v2",
            source_ref=f"{head_commit_id}.json",
        ),
    )


def _should_use_code_package_state_row_maps(
    *,
    old_rows: tuple[CommitStateRow, ...],
    desired_rows: tuple[CommitStateRow, ...],
) -> bool:
    return (
        max(len(old_rows), len(desired_rows))
        >= _CODE_PACKAGE_STATE_ROW_MAP_MIN_ROW_COUNT
    )


def _build_code_package_direct_state_row_changes(
    *,
    old_graph_id: UUID,
    old_state_rows: tuple[CommitStateRow, ...],
    old_class_instances_by_id: Mapping[UUID, ClassInstance],
    desired_object_instance_graph_id: UUID,
    desired_class_instances_by_id: Mapping[UUID, ClassInstance],
    desired_relationships_by_key: Mapping[
        tuple[UUID, UUID, UUID],
        ClassInstanceRelationship,
    ],
    desired_state_index: CommitStateIndex,
    object_instance_graph_identity_id: UUID,
) -> list[ObjectInstanceGraphChange] | None:
    if old_graph_id != desired_object_instance_graph_id:
        return None
    created_at = datetime.now(timezone.utc)
    old_class_config_ids_by_id = _class_config_ids_by_class_instance_id_from_rows(
        old_state_rows,
    )
    new_class_config_ids_by_id = _class_config_ids_by_class_instance_id_from_rows(
        desired_state_index.rows,
    )
    old_class_state_rows = _class_instance_state_rows_by_raw_id(old_state_rows)
    new_class_state_rows = _class_instance_state_rows_by_raw_id(
        desired_state_index.rows,
    )
    return _build_code_package_direct_state_row_changes_from_indexes(
        old_graph_id=old_graph_id,
        old_class_config_ids_by_id=old_class_config_ids_by_id,
        new_class_config_ids_by_id=new_class_config_ids_by_id,
        old_class_state_rows=old_class_state_rows,
        new_class_state_rows=new_class_state_rows,
        old_relationship_keys=_relationship_keys_from_state_rows(old_state_rows),
        old_class_instances_by_id=old_class_instances_by_id,
        desired_class_instances_by_id=desired_class_instances_by_id,
        desired_relationships_by_key=desired_relationships_by_key,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        created_at=created_at,
    )


def _build_code_package_direct_state_row_changes_from_rows(
    *,
    old_graph_id: UUID,
    old_state_rows: tuple[CommitStateRow, ...],
    old_class_instances_by_id: Mapping[UUID, ClassInstance],
    desired_object_instance_graph_id: UUID,
    desired_class_instances_by_id: Mapping[UUID, ClassInstance],
    desired_relationships_by_key: Mapping[
        tuple[UUID, UUID, UUID],
        ClassInstanceRelationship,
    ],
    desired_state_index: CommitStateIndex,
    object_instance_graph_identity_id: UUID,
) -> list[ObjectInstanceGraphChange] | None:
    return _build_code_package_direct_state_row_changes(
        old_graph_id=old_graph_id,
        old_state_rows=old_state_rows,
        old_class_instances_by_id=old_class_instances_by_id,
        desired_object_instance_graph_id=desired_object_instance_graph_id,
        desired_class_instances_by_id=desired_class_instances_by_id,
        desired_relationships_by_key=desired_relationships_by_key,
        desired_state_index=desired_state_index,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
    )


def _build_code_package_direct_state_row_changes_from_maps(
    *,
    old_graph_id: UUID,
    old_state_maps: CommitStateRowMaps,
    old_class_instances_by_id: Mapping[UUID, ClassInstance],
    desired_object_instance_graph_id: UUID,
    desired_class_instances_by_id: Mapping[UUID, ClassInstance],
    desired_relationships_by_key: Mapping[
        tuple[UUID, UUID, UUID],
        ClassInstanceRelationship,
    ],
    desired_state_maps: CommitStateRowMaps,
    object_instance_graph_identity_id: UUID,
) -> list[ObjectInstanceGraphChange] | None:
    if old_graph_id != desired_object_instance_graph_id:
        return None
    created_at = datetime.now(timezone.utc)
    old_class_config_ids_by_id = old_state_maps.class_config_ids_by_class_instance_id
    new_class_config_ids_by_id = (
        desired_state_maps.class_config_ids_by_class_instance_id
    )
    old_class_state_rows = old_state_maps.class_state_rows_by_raw_id
    new_class_state_rows = desired_state_maps.class_state_rows_by_raw_id
    return _build_code_package_direct_state_row_changes_from_indexes(
        old_graph_id=old_graph_id,
        old_class_config_ids_by_id=old_class_config_ids_by_id,
        new_class_config_ids_by_id=new_class_config_ids_by_id,
        old_class_state_rows=old_class_state_rows,
        new_class_state_rows=new_class_state_rows,
        old_relationship_keys=set(old_state_maps.relationship_keys),
        old_class_instances_by_id=old_class_instances_by_id,
        desired_class_instances_by_id=desired_class_instances_by_id,
        desired_relationships_by_key=desired_relationships_by_key,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        created_at=created_at,
    )


def _build_code_package_direct_state_row_changes_from_indexes(
    *,
    old_graph_id: UUID,
    old_class_config_ids_by_id: Mapping[UUID, UUID],
    new_class_config_ids_by_id: Mapping[UUID, UUID],
    old_class_state_rows: Mapping[str, tuple[CommitStateRow, ...]],
    new_class_state_rows: Mapping[str, tuple[CommitStateRow, ...]],
    old_relationship_keys: set[tuple[UUID, UUID, UUID]],
    old_class_instances_by_id: Mapping[UUID, ClassInstance],
    desired_class_instances_by_id: Mapping[UUID, ClassInstance],
    desired_relationships_by_key: Mapping[
        tuple[UUID, UUID, UUID],
        ClassInstanceRelationship,
    ],
    object_instance_graph_identity_id: UUID,
    created_at: datetime,
) -> list[ObjectInstanceGraphChange] | None:
    class_instance_changes: list[ClassInstanceChange] = []
    for class_instance_id in sorted(
        set(old_class_config_ids_by_id) | set(new_class_config_ids_by_id),
        key=str,
    ):
        old_exists = class_instance_id in old_class_config_ids_by_id
        new_exists = class_instance_id in new_class_config_ids_by_id
        new_class_instance = desired_class_instances_by_id.get(class_instance_id)
        if not old_exists:
            if new_class_instance is None:
                return None
            class_instance_changes.append(
                _code_package_class_instance_create_change(
                    class_instance=new_class_instance,
                    created_at=created_at,
                )
            )
            continue
        if not new_exists:
            class_instance_changes.append(
                _code_package_class_instance_delete_change(
                    class_instance_id=class_instance_id,
                    class_config_id=old_class_config_ids_by_id[class_instance_id],
                    created_at=created_at,
                )
            )
            continue
        raw_class_instance_id = str(class_instance_id)
        if old_class_state_rows.get(raw_class_instance_id) == new_class_state_rows.get(
            raw_class_instance_id,
        ):
            continue
        if new_class_instance is None:
            return None
        old_class_instance = old_class_instances_by_id.get(class_instance_id)
        if old_class_instance is None:
            return None
        class_instance_change = _code_package_class_instance_update_change(
            old_class_instance=old_class_instance,
            new_class_instance=new_class_instance,
            created_at=created_at,
        )
        if class_instance_change is not None:
            class_instance_changes.append(class_instance_change)

    desired_relationship_keys = set(desired_relationships_by_key)
    relationship_changes: list[ClassInstanceRelationshipChange] = []
    for relationship_key in sorted(
        old_relationship_keys - desired_relationship_keys,
        key=lambda item: tuple(str(value) for value in item),
    ):
        relationship_changes.append(
            _code_package_relationship_delete_change(
                relationship=_relationship_from_key(relationship_key),
                created_at=created_at,
            )
        )
    for relationship_key in sorted(
        desired_relationship_keys - old_relationship_keys,
        key=lambda item: tuple(str(value) for value in item),
    ):
        relationship_changes.append(
            _code_package_relationship_create_change(
                relationship=desired_relationships_by_key[relationship_key],
                created_at=created_at,
            )
        )

    changes: list[ObjectInstanceGraphChange] = []
    if class_instance_changes:
        root_change = _code_package_change(
            key="root:object_instance:update",
            change_type=ChangeType.update,
            field_deltas=(),
            created_at=created_at,
        )
        changes.append(
            ObjectInstanceGraphChange(
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=old_graph_id,
                type=ObjectInstanceGraphChangeType.object_instance,
                change=root_change,
                change_id=root_change.id,
                class_instance_changes=class_instance_changes,
                class_instance_relationship_changes=[],
            )
        )
    if relationship_changes:
        root_change = _code_package_change(
            key="root:object_instance_relationship:update",
            change_type=ChangeType.update,
            field_deltas=(),
            created_at=created_at,
        )
        changes.append(
            ObjectInstanceGraphChange(
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                object_instance_graph_id=old_graph_id,
                type=ObjectInstanceGraphChangeType.object_instance_relationship,
                change=root_change,
                change_id=root_change.id,
                class_instance_changes=[],
                class_instance_relationship_changes=relationship_changes,
            )
        )
    return changes


def _class_instance_ids_with_state_row_changes(
    *,
    old_maps: CommitStateRowMaps,
    desired_maps: CommitStateRowMaps,
) -> tuple[UUID, ...]:
    old_rows_by_id = old_maps.class_state_rows_by_raw_id
    new_rows_by_id = desired_maps.class_state_rows_by_raw_id
    changed_ids = [
        UUID(raw_class_instance_id)
        for raw_class_instance_id in set(old_rows_by_id) | set(new_rows_by_id)
        if old_rows_by_id.get(raw_class_instance_id)
        != new_rows_by_id.get(raw_class_instance_id)
    ]
    return tuple(sorted(changed_ids, key=str))


def _class_instance_ids_with_state_row_changes_from_rows(
    *,
    old_rows: tuple[CommitStateRow, ...],
    desired_state_index: CommitStateIndex,
) -> tuple[UUID, ...]:
    old_rows_by_id = _class_instance_state_rows_by_raw_id(old_rows)
    new_rows_by_id = _class_instance_state_rows_by_raw_id(desired_state_index.rows)
    changed_ids = [
        UUID(raw_class_instance_id)
        for raw_class_instance_id in set(old_rows_by_id) | set(new_rows_by_id)
        if old_rows_by_id.get(raw_class_instance_id)
        != new_rows_by_id.get(raw_class_instance_id)
    ]
    return tuple(sorted(changed_ids, key=str))


def _class_instance_state_rows_by_id(
    rows: tuple[CommitStateRow, ...],
) -> dict[UUID, tuple[CommitStateRow, ...]]:
    return {
        UUID(class_instance_id): member_rows
        for class_instance_id, member_rows in _class_instance_state_rows_by_raw_id(
            rows
        ).items()
    }


def _class_instance_state_rows_by_raw_id(
    rows: tuple[CommitStateRow, ...],
) -> dict[str, tuple[CommitStateRow, ...]]:
    rows_by_id: dict[str, list[CommitStateRow]] = {}
    for row in rows:
        if row.kind == "NODE":
            rows_by_id.setdefault(row.value, []).append(row)
        elif row.kind == "ATTR":
            rows_by_id.setdefault(row.key, []).append(row)
    return {
        class_instance_id: tuple(member_rows)
        for class_instance_id, member_rows in rows_by_id.items()
    }


def _snapshot_state_selected_class_instances(
    *,
    payload: Mapping[str, object],
    class_instance_ids: Iterable[UUID],
) -> dict[UUID, ClassInstance] | None:
    selected_ids = {str(class_instance_id) for class_instance_id in class_instance_ids}
    if not selected_ids:
        return {}
    class_instances = payload.get("class_instances")
    if not isinstance(class_instances, list):
        return None
    selected: dict[UUID, ClassInstance] = {}
    try:
        for item in class_instances:
            if not isinstance(item, dict):
                continue
            raw_id = item.get("id")
            if not isinstance(raw_id, str) or raw_id not in selected_ids:
                continue
            class_instance = ClassInstance.model_validate(item)
            if class_instance.id is None:
                return None
            selected[class_instance.id] = class_instance
    except Exception:
        return None
    return selected


def _class_config_ids_by_class_instance_id_from_rows(
    rows: Iterable[CommitStateRow],
) -> dict[UUID, UUID]:
    out: dict[UUID, UUID] = {}
    for row in rows:
        if row.kind != "NODE":
            continue
        class_config_id = UUID(row.key)
        class_instance_id = UUID(row.value)
        previous = out.get(class_instance_id)
        if previous is not None and previous != class_config_id:
            raise ValueError(
                "CodePackage state rows contain conflicting NODE rows for "
                f"ClassInstance {class_instance_id}"
            )
        out[class_instance_id] = class_config_id
    return out


def _class_instances_by_id(
    graph: ObjectInstanceGraph,
) -> dict[UUID, ClassInstance]:
    out: dict[UUID, ClassInstance] = {}
    for class_instance in graph.class_instances:
        class_instance_id = class_instance.id
        if class_instance_id is None:
            raise ValueError(
                "CodePackage desired OIG contains ClassInstance without id"
            )
        if class_instance_id in out:
            raise ValueError(
                "CodePackage desired OIG contains duplicate ClassInstance id: "
                f"{class_instance_id}"
            )
        out[class_instance_id] = class_instance
    return out


def _relationships_by_key_from_state_rows(
    rows: Iterable[CommitStateRow],
) -> dict[tuple[UUID, UUID, UUID], ClassInstanceRelationship]:
    out: dict[tuple[UUID, UUID, UUID], ClassInstanceRelationship] = {}
    for key in _relationship_keys_from_state_rows(rows):
        out[key] = _relationship_from_key(key)
    return out


def _relationship_keys_from_state_rows(
    rows: Iterable[CommitStateRow],
) -> set[tuple[UUID, UUID, UUID]]:
    out: set[tuple[UUID, UUID, UUID]] = set()
    for row in rows:
        if row.kind != "EDGE":
            continue
        raw_source_id, separator, raw_target_id = row.value.partition("->")
        if not separator:
            raise ValueError(f"Malformed relationship state row: {row.value!r}")
        out.add((UUID(row.key), UUID(raw_source_id), UUID(raw_target_id)))
    return out


def _relationship_from_key(
    key: tuple[UUID, UUID, UUID],
    *,
    object_instance_graph_id: UUID | None = None,
) -> ClassInstanceRelationship:
    return ClassInstanceRelationship.model_construct(
        object_instance_graph_id=object_instance_graph_id,
        class_config_relationship_id=key[0],
        source_class_instance_id=key[1],
        target_class_instance_id=key[2],
    )


def _relationships_by_key_from_relationships(
    relationships: Iterable[ClassInstanceRelationship],
) -> dict[tuple[UUID, UUID, UUID], ClassInstanceRelationship]:
    out: dict[tuple[UUID, UUID, UUID], ClassInstanceRelationship] = {}
    for relationship in relationships:
        relationship_id = relationship.class_config_relationship_id
        source_id = relationship.source_class_instance_id
        target_id = relationship.target_class_instance_id
        if relationship_id is None or source_id is None or target_id is None:
            raise ValueError(
                "CodePackage desired relationship missing "
                "class_config_relationship_id/source/target"
            )
        key = (relationship_id, source_id, target_id)
        if key in out:
            raise ValueError(
                "CodePackage desired relationships contain duplicate key: " f"{key}"
            )
        out[key] = relationship
    return out


def _relationships_by_key_from_oig(
    graph: ObjectInstanceGraph,
) -> dict[tuple[UUID, UUID, UUID], ClassInstanceRelationship]:
    return _relationships_by_key_from_relationships(graph.class_instance_relationships)


def _class_instances_by_id_from_iterable(
    class_instances: Iterable[ClassInstance],
) -> dict[UUID, ClassInstance]:
    out: dict[UUID, ClassInstance] = {}
    for class_instance in class_instances:
        class_instance_id = class_instance.id
        if class_instance_id is None:
            raise ValueError(
                "CodePackage desired state contains ClassInstance without id"
            )
        if class_instance_id in out:
            raise ValueError(
                "CodePackage desired state contains duplicate ClassInstance id: "
                f"{class_instance_id}"
            )
        out[class_instance_id] = class_instance
    return out


def _code_package_desired_state_index_from_parts(
    *,
    class_instances: tuple[ClassInstance, ...],
    class_instance_relationships: tuple[ClassInstanceRelationship, ...],
) -> CommitStateIndex:
    rows: list[CommitStateRow] = []
    for class_instance in sorted(
        class_instances,
        key=lambda item: (str(item.class_config_id), str(item.id)),
    ):
        rows.extend(_code_package_class_instance_state_rows(class_instance))

    relationship_rows: set[tuple[str, str, str]] = set()
    for relationship in class_instance_relationships:
        if relationship.class_config_relationship_id is None:
            continue
        if (
            relationship.source_class_instance_id is None
            or relationship.target_class_instance_id is None
        ):
            continue
        relationship_rows.add(
            (
                str(relationship.class_config_relationship_id),
                str(relationship.source_class_instance_id),
                str(relationship.target_class_instance_id),
            )
        )
    for relationship_id, source_id, target_id in sorted(relationship_rows):
        rows.append(
            CommitStateRow(
                kind="EDGE",
                key=relationship_id,
                value=f"{source_id}->{target_id}",
            )
        )
    return CommitStateIndex(rows=tuple(rows))


def _code_package_desired_state_index_from_state_rows(
    *,
    class_state_rows_by_id: Mapping[UUID, tuple[CommitStateRow, ...]],
    class_instance_relationships: tuple[ClassInstanceRelationship, ...],
) -> CommitStateIndex:
    rows: list[CommitStateRow] = []
    ordered_class_rows: list[tuple[str, str, tuple[CommitStateRow, ...]]] = []
    for class_instance_id, class_rows in class_state_rows_by_id.items():
        node_rows = [row for row in class_rows if row.kind == "NODE"]
        if len(node_rows) != 1:
            raise ValueError(
                "CodePackage desired state rows require exactly one NODE row for "
                f"ClassInstance {class_instance_id}"
            )
        node_row = node_rows[0]
        ordered_class_rows.append((node_row.key, node_row.value, class_rows))
    for _class_config_id, _class_instance_id, class_rows in sorted(
        ordered_class_rows,
        key=lambda item: (item[0], item[1]),
    ):
        node_rows = [row for row in class_rows if row.kind == "NODE"]
        attr_rows = sorted(
            (row for row in class_rows if row.kind == "ATTR"),
            key=lambda row: (row.key, row.value),
        )
        rows.extend(node_rows)
        rows.extend(attr_rows)

    relationship_rows: set[tuple[str, str, str]] = set()
    for relationship in class_instance_relationships:
        if relationship.class_config_relationship_id is None:
            continue
        if (
            relationship.source_class_instance_id is None
            or relationship.target_class_instance_id is None
        ):
            continue
        relationship_rows.add(
            (
                str(relationship.class_config_relationship_id),
                str(relationship.source_class_instance_id),
                str(relationship.target_class_instance_id),
            )
        )
    for relationship_id, source_id, target_id in sorted(relationship_rows):
        rows.append(
            CommitStateRow(
                kind="EDGE",
                key=relationship_id,
                value=f"{source_id}->{target_id}",
            )
        )
    return CommitStateIndex(rows=tuple(rows))


def _code_package_class_instance_state_rows(
    class_instance: ClassInstance,
) -> tuple[CommitStateRow, ...]:
    if class_instance.class_config_id is None or class_instance.id is None:
        return ()
    rows: list[CommitStateRow] = [
        CommitStateRow(
            kind="NODE",
            key=str(class_instance.class_config_id),
            value=str(class_instance.id),
        )
    ]
    attribute_rows: set[tuple[str, str]] = set()
    for attribute in class_instance.attributes:
        if attribute is None or attribute.attribute_config_id is None:
            continue
        root = attribute.value_root
        value_fingerprint = (
            fingerprint_attribute_value(root) if root is not None else "missing"
        )
        attribute_rows.add((str(attribute.attribute_config_id), value_fingerprint))
    for attribute_config_id, value_fingerprint in sorted(attribute_rows):
        rows.append(
            CommitStateRow(
                kind="ATTR",
                key=str(class_instance.id),
                value=f"{attribute_config_id}:{value_fingerprint}",
            )
        )
    return tuple(rows)


def _code_package_class_instance_create_change(
    *,
    class_instance: ClassInstance,
    created_at: datetime,
) -> ClassInstanceChange:
    change = _code_package_change(
        key=(
            f"class_instance:{class_instance.class_config_id}:"
            f"{class_instance.id}:create"
        ),
        change_type=ChangeType.create,
        field_deltas=(
            ("class_config_id", class_instance.class_config_id),
            ("source_object_id", class_instance.source_object_id),
        ),
        created_at=created_at,
    )
    class_instance_change = ClassInstanceChange(
        class_instance_id=class_instance.id,
        change=change,
        change_id=change.id,
        attribute_changes=[],
    )
    for attribute in _sorted_unique_attributes(class_instance.attributes):
        class_instance_change.attribute_changes.append(
            _code_package_attribute_create_change(
                attribute=attribute,
                parent=class_instance_change,
                created_at=created_at,
            )
        )
    return class_instance_change


def _code_package_class_instance_delete_change(
    *,
    class_instance_id: UUID,
    class_config_id: UUID,
    created_at: datetime,
) -> ClassInstanceChange:
    change = _code_package_change(
        key=f"class_instance:{class_config_id}:{class_instance_id}:delete",
        change_type=ChangeType.delete,
        field_deltas=(),
        created_at=created_at,
    )
    return ClassInstanceChange(
        class_instance_id=class_instance_id,
        change=change,
        change_id=change.id,
        attribute_changes=[],
    )


def _code_package_class_instance_update_change(
    *,
    old_class_instance: ClassInstance,
    new_class_instance: ClassInstance,
    created_at: datetime,
) -> ClassInstanceChange | None:
    field_deltas: list[tuple[str, object]] = []
    if old_class_instance.class_config_id != new_class_instance.class_config_id:
        field_deltas.append(("class_config_id", new_class_instance.class_config_id))
    if old_class_instance.source_object_id != new_class_instance.source_object_id:
        field_deltas.append(("source_object_id", new_class_instance.source_object_id))

    change = _code_package_change(
        key=(
            f"class_instance:{new_class_instance.class_config_id}:"
            f"{new_class_instance.id}:update"
        ),
        change_type=ChangeType.update,
        field_deltas=tuple(field_deltas),
        created_at=created_at,
    )
    class_instance_change = ClassInstanceChange(
        class_instance_id=new_class_instance.id,
        change=change,
        change_id=change.id,
        attribute_changes=[],
    )

    old_attrs_by_id = _attributes_by_id(old_class_instance.attributes)
    new_attrs_by_id = _attributes_by_id(new_class_instance.attributes)
    for attribute_id in sorted(set(old_attrs_by_id) | set(new_attrs_by_id), key=str):
        old_attribute = old_attrs_by_id.get(attribute_id)
        new_attribute = new_attrs_by_id.get(attribute_id)
        if old_attribute is None:
            if new_attribute is None:
                continue
            class_instance_change.attribute_changes.append(
                _code_package_attribute_create_change(
                    attribute=new_attribute,
                    parent=class_instance_change,
                    created_at=created_at,
                )
            )
            continue
        if new_attribute is None:
            class_instance_change.attribute_changes.append(
                _code_package_attribute_delete_change(
                    attribute=old_attribute,
                    parent=class_instance_change,
                    created_at=created_at,
                )
            )
            continue
        if (
            old_attribute.attribute_config_id == new_attribute.attribute_config_id
            and _attribute_value_fingerprint(old_attribute)
            == _attribute_value_fingerprint(new_attribute)
        ):
            continue
        class_instance_change.attribute_changes.append(
            _code_package_attribute_update_change(
                old_attribute=old_attribute,
                new_attribute=new_attribute,
                parent=class_instance_change,
                created_at=created_at,
            )
        )

    if not field_deltas and not class_instance_change.attribute_changes:
        return None
    return class_instance_change


def _attributes_by_id(
    attributes: Iterable[Attribute],
) -> dict[UUID, Attribute]:
    out: dict[UUID, Attribute] = {}
    for attribute in attributes:
        attribute_id = attribute.id
        if attribute_id is None:
            raise ValueError("CodePackage ClassInstance contains Attribute without id")
        previous = out.get(attribute_id)
        if previous is not None:
            if (
                previous.attribute_config_id != attribute.attribute_config_id
                or previous.value_root_id != attribute.value_root_id
            ):
                raise ValueError(
                    "CodePackage ClassInstance contains conflicting duplicate "
                    f"Attribute id: {attribute_id}"
                )
            continue
        out[attribute_id] = attribute
    return out


def _sorted_unique_attributes(
    attributes: Iterable[Attribute],
) -> tuple[Attribute, ...]:
    return tuple(
        sorted(
            _attributes_by_id(attributes).values(),
            key=lambda item: (str(item.attribute_config_id), str(item.id)),
        )
    )


def _attribute_value_fingerprint(attribute: Attribute) -> str:
    root = attribute.value_root
    return fingerprint_attribute_value(root) if root is not None else "missing"


def _code_package_attribute_create_change(
    *,
    attribute: Attribute,
    parent: ClassInstanceChange,
    created_at: datetime,
) -> AttributeChange:
    change = _code_package_change(
        key=f"attribute:attr:{attribute.attribute_config_id}:create",
        change_type=ChangeType.create,
        field_deltas=(("attribute_config_id", attribute.attribute_config_id),),
        created_at=created_at,
    )
    value_root_change = (
        None
        if attribute.value_root is None
        else _code_package_attribute_value_create_change(
            value=attribute.value_root,
            created_at=created_at,
        )
    )
    return AttributeChange(
        attribute_id=attribute.id,
        class_instance_change_id=parent.id,
        change=change,
        change_id=change.id,
        value_root_change=value_root_change,
        value_root_change_id=(
            None if value_root_change is None else value_root_change.id
        ),
    )


def _code_package_attribute_delete_change(
    *,
    attribute: Attribute,
    parent: ClassInstanceChange,
    created_at: datetime,
) -> AttributeChange:
    change = _code_package_change(
        key=f"attribute:attr:{attribute.attribute_config_id}:delete",
        change_type=ChangeType.delete,
        field_deltas=(),
        created_at=created_at,
    )
    return AttributeChange(
        attribute_id=attribute.id,
        class_instance_change_id=parent.id,
        change=change,
        change_id=change.id,
        value_root_change=None,
        value_root_change_id=None,
    )


def _code_package_attribute_update_change(
    *,
    old_attribute: Attribute,
    new_attribute: Attribute,
    parent: ClassInstanceChange,
    created_at: datetime,
) -> AttributeChange:
    field_deltas: list[tuple[str, object]] = []
    if old_attribute.attribute_config_id != new_attribute.attribute_config_id:
        field_deltas.append(("attribute_config_id", new_attribute.attribute_config_id))
    value_root_change = None
    if _attribute_value_fingerprint(old_attribute) != _attribute_value_fingerprint(
        new_attribute,
    ):
        if old_attribute.value_root is None or new_attribute.value_root is None:
            raise ValueError("CodePackage Attribute update missing value_root")
        value_root_change = _code_package_attribute_value_update_change(
            old_value=old_attribute.value_root,
            new_value=new_attribute.value_root,
            created_at=created_at,
        )
        if value_root_change is None:
            raise ValueError("CodePackage Attribute update produced no value change")
    change = _code_package_change(
        key=f"attribute:attr:{new_attribute.attribute_config_id}:update",
        change_type=ChangeType.update,
        field_deltas=tuple(field_deltas),
        created_at=created_at,
    )
    return AttributeChange(
        attribute_id=new_attribute.id,
        class_instance_change_id=parent.id,
        change=change,
        change_id=change.id,
        value_root_change=value_root_change,
        value_root_change_id=(
            None if value_root_change is None else value_root_change.id
        ),
    )


def _code_package_attribute_value_create_change(
    *,
    value: AttributeValue,
    created_at: datetime,
) -> AttributeValueChange:
    field_deltas: list[tuple[str, object]] = []
    primitive_value = _attribute_value_primitive_payload(value)
    if primitive_value is not None:
        field_deltas.append(("primitive_value", primitive_value))
    if value.enum_option_id is not None:
        field_deltas.append(("enum_option_id", value.enum_option_id))
    if value.inline_value_instance_id is not None:
        field_deltas.append(
            ("inline_value_instance_id", value.inline_value_instance_id)
        )
    elif value.inline_value_instance is not None:
        field_deltas.append(
            ("inline_value_instance_id", value.inline_value_instance.id)
        )
    elif value.class_instance_id is not None:
        field_deltas.append(("class_instance_id", value.class_instance_id))

    change = _code_package_change(
        key="attribute_value:value:create",
        change_type=ChangeType.create,
        field_deltas=tuple(field_deltas),
        created_at=created_at,
    )
    value_change = AttributeValueChange(
        attribute_value_id=value.id,
        change=change,
        change_id=change.id,
        attribute_value_link_changes=[],
    )
    for link in sorted(
        value.child_links,
        key=lambda item: (
            item.role.value,
            item.position if item.position is not None else -1,
            item.identity_key or "",
            str(item.id),
        ),
    ):
        value_change.attribute_value_link_changes.append(
            _code_package_attribute_value_link_create_change(
                link=link,
                parent=value_change,
                created_at=created_at,
            )
        )
    return value_change


def _code_package_attribute_value_update_change(
    *,
    old_value: AttributeValue,
    new_value: AttributeValue,
    created_at: datetime,
) -> AttributeValueChange | None:
    if old_value.id != new_value.id:
        raise ValueError(
            "CodePackage AttributeValue direct update requires stable value id: "
            f"old={old_value.id} new={new_value.id}"
        )
    field_deltas: list[tuple[str, object]] = []
    old_primitive = _attribute_value_primitive_payload(old_value)
    new_primitive = _attribute_value_primitive_payload(new_value)
    if old_primitive != new_primitive:
        field_deltas.append(("primitive_value", new_primitive))
    if old_value.enum_option_id != new_value.enum_option_id:
        field_deltas.append(("enum_option_id", new_value.enum_option_id))
    old_inline_value_instance_id = old_value.inline_value_instance_id
    if (
        old_inline_value_instance_id is None
        and old_value.inline_value_instance is not None
    ):
        old_inline_value_instance_id = old_value.inline_value_instance.id
    new_inline_value_instance_id = new_value.inline_value_instance_id
    if (
        new_inline_value_instance_id is None
        and new_value.inline_value_instance is not None
    ):
        new_inline_value_instance_id = new_value.inline_value_instance.id
    if old_inline_value_instance_id != new_inline_value_instance_id:
        field_deltas.append(("inline_value_instance_id", new_inline_value_instance_id))
    if old_value.class_instance_id != new_value.class_instance_id:
        field_deltas.append(("class_instance_id", new_value.class_instance_id))

    old_links_by_id = _attribute_value_links_by_id(old_value.child_links)
    new_links_by_id = _attribute_value_links_by_id(new_value.child_links)
    link_changes: list[AttributeValueLinkChange] = []
    change = _code_package_change(
        key="attribute_value:value:update",
        change_type=ChangeType.update,
        field_deltas=tuple(field_deltas),
        created_at=created_at,
    )
    value_change = AttributeValueChange(
        attribute_value_id=new_value.id,
        change=change,
        change_id=change.id,
        attribute_value_link_changes=link_changes,
    )
    for link_id in sorted(set(old_links_by_id) | set(new_links_by_id), key=str):
        old_link = old_links_by_id.get(link_id)
        new_link = new_links_by_id.get(link_id)
        if old_link is None:
            if new_link is None:
                continue
            link_changes.append(
                _code_package_attribute_value_link_create_change(
                    link=new_link,
                    parent=value_change,
                    created_at=created_at,
                )
            )
            continue
        if new_link is None:
            link_changes.append(
                _code_package_attribute_value_link_delete_change(
                    link=old_link,
                    parent=value_change,
                    created_at=created_at,
                )
            )
            continue
        link_change = _code_package_attribute_value_link_update_change(
            old_link=old_link,
            new_link=new_link,
            parent=value_change,
            created_at=created_at,
        )
        if link_change is not None:
            link_changes.append(link_change)

    if not field_deltas and not link_changes:
        return None
    return value_change


def _attribute_value_links_by_id(
    links: Iterable[AttributeValueLink],
) -> dict[UUID, AttributeValueLink]:
    out: dict[UUID, AttributeValueLink] = {}
    for link in links:
        link_id = link.id
        if link_id is None:
            raise ValueError("CodePackage AttributeValueLink missing id")
        if link_id in out:
            raise ValueError(
                "CodePackage AttributeValue contains duplicate link id: " f"{link_id}"
            )
        out[link_id] = link
    return out


def _code_package_attribute_value_link_create_change(
    *,
    link: AttributeValueLink,
    parent: AttributeValueChange,
    created_at: datetime,
) -> AttributeValueLinkChange:
    field_deltas: list[tuple[str, object]] = [("role", link.role.value)]
    if link.position is not None:
        field_deltas.append(("position", link.position))
    if link.identity_key is not None:
        field_deltas.append(("identity_key", link.identity_key))
    change = _code_package_change(
        key=f"attribute_value_link:{_attribute_value_link_path_key(link)}:create",
        change_type=ChangeType.create,
        field_deltas=tuple(field_deltas),
        created_at=created_at,
    )
    child_change = (
        None
        if link.child is None
        else _code_package_attribute_value_create_change(
            value=link.child,
            created_at=created_at,
        )
    )
    return AttributeValueLinkChange(
        attribute_value_change_id=parent.id,
        attribute_value_link_id=link.id,
        change=change,
        change_id=change.id,
        child_attribute_value_change=child_change,
        child_attribute_value_change_id=(
            None if child_change is None else child_change.id
        ),
    )


def _code_package_attribute_value_link_update_change(
    *,
    old_link: AttributeValueLink,
    new_link: AttributeValueLink,
    parent: AttributeValueChange,
    created_at: datetime,
) -> AttributeValueLinkChange | None:
    if (
        old_link.role != new_link.role
        or old_link.position != new_link.position
        or old_link.identity_key != new_link.identity_key
    ):
        raise ValueError(
            "CodePackage AttributeValueLink direct update requires stable slot "
            f"metadata: link_id={new_link.id}"
        )
    old_child = old_link.child
    new_child = new_link.child
    if old_child is None or new_child is None:
        if old_child is new_child:
            return None
        raise ValueError(
            "CodePackage AttributeValueLink direct update requires both child "
            f"values: link_id={new_link.id}"
        )
    child_change = _code_package_attribute_value_update_change(
        old_value=old_child,
        new_value=new_child,
        created_at=created_at,
    )
    if child_change is None:
        return None
    change = _code_package_change(
        key=f"attribute_value_link:{_attribute_value_link_path_key(new_link)}:update",
        change_type=ChangeType.update,
        field_deltas=(),
        created_at=created_at,
    )
    return AttributeValueLinkChange(
        attribute_value_change_id=parent.id,
        attribute_value_link_id=new_link.id,
        change=change,
        change_id=change.id,
        child_attribute_value_change=child_change,
        child_attribute_value_change_id=child_change.id,
    )


def _code_package_attribute_value_link_delete_change(
    *,
    link: AttributeValueLink,
    parent: AttributeValueChange,
    created_at: datetime,
) -> AttributeValueLinkChange:
    change = _code_package_change(
        key=f"attribute_value_link:{_attribute_value_link_path_key(link)}:delete",
        change_type=ChangeType.delete,
        field_deltas=(),
        created_at=created_at,
    )
    return AttributeValueLinkChange(
        attribute_value_change_id=parent.id,
        attribute_value_link_id=link.id,
        change=change,
        change_id=change.id,
        child_attribute_value_change=None,
        child_attribute_value_change_id=None,
    )


def _code_package_relationship_create_change(
    *,
    relationship: ClassInstanceRelationship,
    created_at: datetime,
) -> ClassInstanceRelationshipChange:
    change = _code_package_change(
        key=(
            "relationship:"
            f"{relationship.source_class_instance_id}->"
            f"{relationship.target_class_instance_id}:"
            f"{relationship.class_config_relationship_id}:create"
        ),
        change_type=ChangeType.create,
        field_deltas=(),
        created_at=created_at,
    )
    return ClassInstanceRelationshipChange(
        change=change,
        change_id=change.id,
        class_config_relationship_id=relationship.class_config_relationship_id,
        source_class_instance_id=relationship.source_class_instance_id,
        target_class_instance_id=relationship.target_class_instance_id,
    )


def _code_package_relationship_delete_change(
    *,
    relationship: ClassInstanceRelationship,
    created_at: datetime,
) -> ClassInstanceRelationshipChange:
    change = _code_package_change(
        key=(
            "relationship:"
            f"{relationship.source_class_instance_id}->"
            f"{relationship.target_class_instance_id}:"
            f"{relationship.class_config_relationship_id}:delete"
        ),
        change_type=ChangeType.delete,
        field_deltas=(),
        created_at=created_at,
    )
    return ClassInstanceRelationshipChange(
        change=change,
        change_id=change.id,
        class_config_relationship_id=relationship.class_config_relationship_id,
        source_class_instance_id=relationship.source_class_instance_id,
        target_class_instance_id=relationship.target_class_instance_id,
    )


def _code_package_change(
    *,
    key: str,
    change_type: ChangeType,
    field_deltas: tuple[tuple[str, object], ...],
    created_at: datetime,
) -> Change:
    change = Change(
        key=key,
        type=change_type,
        change_deltas=[],
        created_at=created_at,
    )
    if not field_deltas:
        return change
    deltas: list[ChangeDelta] = []
    for position, (property_name, value) in enumerate(field_deltas):
        deltas.append(
            ChangeDelta(
                change_id=change.id,
                position=position,
                property=property_name,
                kind=ChangeDeltaKind.scalar_set,
                payload=Json({"value": _field_delta_payload_value(value)}),
            )
        )
    change.change_deltas = deltas
    return change


def _field_delta_payload_value(value: object) -> JsonValue:
    if isinstance(value, UUID):
        return str(value)
    return _coerce_json_value(value)


def _coerce_json_value(value: object) -> JsonValue:
    if value is None:
        return None
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [_coerce_json_value(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(
                    "Field delta JSON object keys must be strings, got "
                    f"{type(key).__name__}"
                )
            normalized[key] = _coerce_json_value(item)
        return normalized
    raise TypeError(f"Unsupported field delta value type: {type(value).__name__}")


def _attribute_value_primitive_payload(value: AttributeValue) -> JsonValue | None:
    raw = value.primitive_value
    if isinstance(raw, dict) and set(raw.keys()) == {"value"}:
        return _coerce_json_value(raw.get("value"))
    return _coerce_json_value(raw)


def _attribute_value_link_path_key(link: AttributeValueLink) -> str:
    role = link.role.value
    if link.identity_key is not None:
        return f"link:{role}:{link.identity_key}"
    if link.position is not None:
        return f"link:{role}:{link.position}"
    return f"link:{role}"


def _snapshot_state_root_source_object_id(payload: Mapping[str, object]) -> UUID | None:
    graph = payload.get("graph")
    if not isinstance(graph, Mapping):
        return None
    raw_value = graph.get("root_source_object_id")
    if not isinstance(raw_value, str) or not raw_value:
        return None
    try:
        return UUID(raw_value)
    except ValueError:
        return None


async def _load_code_package_before_oig(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    domain_oig_id: UUID,
    root_object_id: UUID,
):
    opg = index.opg_by_hash[projection_hash]
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    head_commit_id = _head_uuid(head, "commit_id")
    if head_commit_id is not None:
        snapshot_store = FSSnapshotStore()
        snapshot = await snapshot_store.get(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=head_commit_id,
        )
        if snapshot is not None:
            oig, _indexes = snapshot
            if oig.id != domain_oig_id:
                raise RuntimeError(
                    "CodePackage text snapshot head targets unexpected OIG: "
                    f"branch_id={branch_id} projection_hash={projection_hash} "
                    f"head_commit_id={head_commit_id} "
                    f"snapshot_oig_id={oig.id} expected_oig_id={domain_oig_id}"
                )
            return oig
        oig, _ = await OIGMaterializer().get(
            branch_id=branch_id,
            ocg=index.ocg,
            opg=opg,
            commit_id=None,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        return oig
    return _build_code_package_rooted_base(
        index=index,
        opg=opg,
        branch_id=branch_id,
        domain_oig_id=domain_oig_id,
        root_object_id=root_object_id,
    )


def _reset_code_package_text_snapshot_lane(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
) -> None:
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


def _remember(
    objects_by_id: dict[UUID, BaseORMModel],
    obj: BaseORMModel,
) -> BaseORMModel:
    obj_id = getattr(obj, "id", None)
    if not isinstance(obj_id, UUID):
        raise RuntimeError(f"CodePackage snapshot object missing UUID id: {obj!r}")
    previous = objects_by_id.get(obj_id)
    if previous is not None and previous is not obj:
        raise RuntimeError(f"CodePackage snapshot duplicate object id: {obj_id}")
    objects_by_id[obj_id] = obj
    return obj


_SOURCE_SIGNATURE_SKIP = object()
_CODE_PACKAGE_SOURCE_SIGNATURE_FIELD_NAMES_BY_CLASS = {
    CodePackage: (
        "artifacts",
        "code_package_codes",
        "code_package_config_id",
        "code_package_test_frameworks",
        "delta_producers",
        "fqn_prefix",
        "language",
        "manifest_relative_path",
        "package_name",
        "package_root",
        "sources_root",
        "surface",
        "tests",
    ),
    CodePackageCode: (
        "code",
        "code_package_id",
        "path_role",
        "relative_path",
    ),
    Code: (
        "code_package_code_id",
        "code_sections",
        "content_part_text",
        "content_part_text_id",
        "language",
        "relative_path",
        "tests",
    ),
    ContentPartText: (
        "blob",
        "blob_id",
        "content_part_id",
        "index",
        "inline_text",
        "key",
        "segments",
    ),
    ContentPartTextSegment: (
        "byte_end",
        "byte_start",
        "content_part_text",
        "content_part_text_id",
        "content_part_text_segment_translations",
        "key",
        "parent",
        "parent_id",
        "style",
    ),
    CodeSection: (
        "code_id",
        "code_section_annotation",
        "code_section_attribute",
        "code_section_binding",
        "code_section_class",
        "code_section_comment",
        "code_section_decorator",
        "code_section_enum",
        "code_section_enum_value",
        "code_section_expression",
        "code_section_function",
        "code_section_import",
        "code_section_mirror",
        "code_section_projection",
        "content_part_text_segment",
        "content_part_text_segment_id",
        "identity_hash",
        "metadata",
        "qualname",
        "section_key",
        "type",
    ),
    CodePackageArtifact: (
        "artifact_family",
        "artifact_key",
        "artifact_role",
        "code_package_id",
        "digest",
        "error",
        "input_code_package_id",
        "input_object_instance_graph_commit_id",
        "materialization_index",
        "media_type",
        "output_key",
        "producer_key",
        "producer_kind",
        "provider_payload",
        "receipt_payload",
        "relative_path",
        "required_for",
        "runtime_contract_version",
        "source_code_package_id",
        "source_object_instance_graph_commit_id",
        "status",
        "uri",
    ),
}


def _code_package_source_object_state_index(
    *,
    domain_oig_id: UUID,
    objects_by_id: Mapping[UUID, BaseORMModel],
    source_object_path_index: Mapping[str, tuple[UUID, ...]] | None = None,
) -> dict[str, object]:
    return _code_package_source_object_state_index_from_states(
        _code_package_source_object_states_by_source_id(
            domain_oig_id=domain_oig_id,
            objects_by_id=objects_by_id,
        ).values(),
        source_object_path_index=source_object_path_index,
    )


def _code_package_source_object_state_index_from_states(
    states: Iterable[_CodePackageSourceObjectState],
    source_object_path_index: Mapping[str, tuple[UUID, ...]] | None = None,
) -> dict[str, object]:
    return _code_package_source_object_state_index_from_raw_rows(
        (
            _code_package_source_object_state_index_row(source_state=state)
            for state in states
        ),
        source_object_path_index=source_object_path_index,
    )


def _code_package_source_object_state_index_from_raw_rows(
    rows: Iterable[Mapping[str, object]],
    source_object_path_index: Mapping[str, tuple[UUID, ...]] | None = None,
) -> dict[str, object]:
    objects = sorted(
        (dict(row) for row in rows),
        key=lambda item: str(item["source_object_id"]),
    )
    payload: dict[str, object] = {
        "schema": CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_SCHEMA,
        "object_count": len(objects),
        "objects": objects,
    }
    if source_object_path_index:
        payload["path_source_object_index"] = (
            _code_package_source_object_path_index_rows(source_object_path_index)
        )
    return payload


def _code_package_source_object_state_index_from_index_view_delta(
    *,
    previous_source_index_view: (
        _CodePackageSourceObjectIndexView | _CodePackageSourceObjectRawIndexView
    ),
    changed_rows_by_source_id: Mapping[UUID, Mapping[str, object]],
    source_object_path_index: Mapping[str, tuple[UUID, ...]],
    changed_relative_paths: frozenset[str] = frozenset(),
) -> dict[str, object] | None:
    if not changed_rows_by_source_id:
        return None
    changed_rows_by_source_id_text = {
        str(source_object_id): row
        for source_object_id, row in changed_rows_by_source_id.items()
    }
    changed_paths = {
        relative_path
        for relative_path in changed_relative_paths
        if relative_path in source_object_path_index
    }
    changed_source_object_ids = set(changed_rows_by_source_id)
    for relative_path, source_object_ids in source_object_path_index.items():
        if changed_paths and relative_path not in changed_paths:
            continue
        if any(
            source_object_id in changed_source_object_ids
            for source_object_id in source_object_ids
        ):
            changed_paths.add(relative_path)
    path_source_object_index = {
        relative_path: source_object_path_index[relative_path]
        for relative_path in sorted(changed_paths)
    }
    overlay_source_object_ids = {
        str(source_object_id)
        for source_object_ids in path_source_object_index.values()
        for source_object_id in source_object_ids
    }
    overlay_source_object_ids.update(changed_rows_by_source_id_text)
    seen_changed_source_object_ids: set[str] = set()
    previous_object_rows: Iterable[Mapping[str, object]]
    if isinstance(previous_source_index_view, _CodePackageSourceObjectRawIndexView):
        previous_object_rows = previous_source_index_view.object_rows
    else:
        previous_object_rows = (
            previous_source_index_view.object_rows_by_source_id.values()
        )
    objects_by_source_id_text: dict[str, Mapping[str, object]] = {}
    for previous_row in previous_object_rows:
        source_object_id_text = str(previous_row.get("source_object_id"))
        if source_object_id_text not in overlay_source_object_ids:
            continue
        if source_object_id_text in objects_by_source_id_text:
            return None
        changed_row = changed_rows_by_source_id_text.get(source_object_id_text)
        if changed_row is not None:
            seen_changed_source_object_ids.add(source_object_id_text)
            objects_by_source_id_text[source_object_id_text] = changed_row
        else:
            objects_by_source_id_text[source_object_id_text] = previous_row
        if len(objects_by_source_id_text) == len(overlay_source_object_ids):
            break
    if set(objects_by_source_id_text) != overlay_source_object_ids:
        return None
    if seen_changed_source_object_ids != set(changed_rows_by_source_id_text):
        return None
    payload: dict[str, object] = {
        "schema": CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_OVERLAY_SCHEMA,
        "base_schema": CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_SCHEMA,
        "object_count": previous_source_index_view.object_count,
        "changed_object_count": len(changed_rows_by_source_id_text),
        "changed_path_count": len(path_source_object_index),
        "objects": [
            dict(row)
            for _source_object_id_text, row in sorted(
                objects_by_source_id_text.items(),
                key=lambda item: item[0],
            )
        ],
    }
    if path_source_object_index:
        payload["path_source_object_index"] = (
            _code_package_source_object_path_index_rows(path_source_object_index)
        )
    return payload


def _code_package_source_object_state_index_row(
    *,
    source_state: _CodePackageSourceObjectState,
) -> dict[str, object]:
    return {
        "source_object_id": str(source_state.source_object_id),
        "class_config_id": str(source_state.class_config_id),
        "class_instance_id": str(source_state.class_instance_id),
        "signature_hash": source_state.signature_hash,
    }


def _code_package_source_object_path_index_rows(
    source_object_path_index: Mapping[str, tuple[UUID, ...]],
) -> list[dict[str, object]]:
    return [
        {
            "relative_path": relative_path,
            "source_object_ids": [
                str(source_object_id)
                for source_object_id in sorted(source_object_ids, key=str)
            ],
        }
        for relative_path, source_object_ids in sorted(
            source_object_path_index.items(),
        )
    ]


def _code_package_source_object_count_from_index(
    payload: Mapping[str, object],
    *,
    fallback: int,
) -> int:
    raw_count = payload.get("object_count")
    if isinstance(raw_count, int):
        return raw_count
    raw_objects = payload.get("objects")
    if isinstance(raw_objects, list):
        return len(raw_objects)
    return fallback


def _code_package_source_object_states_by_source_id(
    *,
    domain_oig_id: UUID,
    objects_by_id: Mapping[UUID, BaseORMModel],
) -> dict[UUID, _CodePackageSourceObjectState]:
    states: dict[UUID, _CodePackageSourceObjectState] = {}
    for source_object_id, source_object in objects_by_id.items():
        class_config_id = source_object.try_class_config_id()
        if class_config_id is None:
            raise RuntimeError(
                "CodePackage source object missing class config id: "
                f"source_object_id={source_object_id}"
            )
        states[source_object_id] = _CodePackageSourceObjectState(
            source_object_id=source_object_id,
            class_config_id=class_config_id,
            class_instance_id=stable_class_instance_id(
                object_instance_graph_id=domain_oig_id,
                class_config_id=class_config_id,
                source_object_id=source_object_id,
            ),
            signature_hash=_code_package_source_object_signature_hash(source_object),
        )
    return states


def _code_package_source_object_states_from_snapshot_inputs(
    *,
    domain_oig_id: UUID,
    code_package_id: UUID,
    code_package_config_id: UUID,
    package_name: str,
    language: CodeLanguage,
    surface: str,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
    plans_by_relative_path: Mapping[str, CodeContentPlan],
    path_roles_by_relative_path: Mapping[str, CodePackagePathRole],
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
    include_relative_paths: frozenset[str] | None = None,
) -> dict[UUID, _CodePackageSourceObjectState]:
    return dict(
        _code_package_source_object_state_build_from_snapshot_inputs(
            domain_oig_id=domain_oig_id,
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name=package_name,
            language=language,
            surface=surface,
            manifest_kind=manifest_kind,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root,
            sources_root=sources_root,
            fqn_prefix=fqn_prefix,
            plans_by_relative_path=plans_by_relative_path,
            path_roles_by_relative_path=path_roles_by_relative_path,
            code_package_artifact_refs=code_package_artifact_refs,
            include_relative_paths=include_relative_paths,
        ).states_by_id,
    )


def _code_package_source_object_state_build_from_snapshot_inputs(
    *,
    domain_oig_id: UUID,
    code_package_id: UUID,
    code_package_config_id: UUID,
    package_name: str,
    language: CodeLanguage,
    surface: str,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
    plans_by_relative_path: Mapping[str, CodeContentPlan],
    path_roles_by_relative_path: Mapping[str, CodePackagePathRole],
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
    include_relative_paths: frozenset[str] | None = None,
) -> _CodePackageSourceObjectStateBuild:
    states: dict[UUID, _CodePackageSourceObjectState] = {}
    path_source_object_ids: dict[str, set[UUID]] = {}

    def _add(
        *,
        model_cls: type[BaseORMModel],
        source_object_id: UUID,
        raw_fields: Mapping[str, object],
        skip_fields: frozenset[str] = frozenset(),
        relative_path: str | None = None,
    ) -> None:
        states[source_object_id] = _code_package_source_object_state_from_raw_fields(
            domain_oig_id=domain_oig_id,
            model_cls=model_cls,
            source_object_id=source_object_id,
            raw_fields=raw_fields,
            skip_fields=skip_fields,
        )
        if relative_path is not None:
            path_source_object_ids.setdefault(relative_path, set()).add(
                source_object_id,
            )

    _add(
        model_cls=CodePackage,
        source_object_id=code_package_id,
        raw_fields={
            "artifacts": [],
            "code_package_codes": [],
            "code_package_config_id": code_package_config_id,
            "code_package_test_frameworks": [],
            "delta_producers": [],
            "fqn_prefix": (fqn_prefix or "").strip() or None,
            "language": _enum_value(language),
            "manifest_relative_path": (manifest_relative_path or "").strip(),
            "package_name": (package_name or "").strip(),
            "package_root": (package_root or "").strip(),
            "sources_root": (sources_root or "").strip() or None,
            "surface": surface,
            "tests": [],
        },
        skip_fields=frozenset(
            (
                *(("code_package_codes",) if plans_by_relative_path else ()),
                *(("artifacts",) if code_package_artifact_refs else ()),
            )
        ),
    )

    for relative_path, plan in sorted(plans_by_relative_path.items()):
        if include_relative_paths is not None and relative_path not in (
            include_relative_paths
        ):
            continue
        code_package_code_id = stable_code_package_code_id(
            code_package_id=code_package_id,
            relative_path=relative_path,
        )
        code_id = stable_code_id(
            code_package_code_id=code_package_code_id,
            relative_path=relative_path,
        )
        content_part_text_id = _stable_code_content_part_text_id(code_id=code_id)
        section_plans = tuple(plan.section_plans or ())
        _add(
            model_cls=CodePackageCode,
            source_object_id=code_package_code_id,
            raw_fields={
                "code_package_id": code_package_id,
                "path_role": _enum_value(
                    path_roles_by_relative_path.get(
                        relative_path,
                        CodePackagePathRole.authored_source,
                    )
                ),
                "relative_path": relative_path,
            },
            skip_fields=frozenset(("code",)),
            relative_path=relative_path,
        )
        _add(
            model_cls=Code,
            source_object_id=code_id,
            raw_fields={
                "code_package_code_id": code_package_code_id,
                "code_sections": [],
                "content_part_text_id": content_part_text_id,
                "language": _enum_value(plan.language),
                "relative_path": relative_path,
                "tests": [],
            },
            skip_fields=frozenset(
                (
                    "content_part_text",
                    *(("code_sections",) if section_plans else ()),
                )
            ),
            relative_path=relative_path,
        )
        _add(
            model_cls=ContentPartText,
            source_object_id=content_part_text_id,
            raw_fields={
                "blob": None,
                "blob_id": None,
                "content_part_id": None,
                "index": None,
                "inline_text": plan.content_text,
                "key": "default",
                "segments": [],
            },
            skip_fields=frozenset(("segments",) if section_plans else ()),
            relative_path=relative_path,
        )
        for descriptor in section_plans:
            section_type = CodeSectionType(descriptor.section_type.value)
            section_id = stable_code_section_id(
                code_id=code_id,
                section_key=descriptor.section_key,
                type=section_type.value,
            )
            segment_id = stable_content_part_text_segment_id(
                content_part_text_id=content_part_text_id,
                key=f"code-section:{section_id}",
            )
            _add(
                model_cls=ContentPartTextSegment,
                source_object_id=segment_id,
                raw_fields={
                    "byte_end": descriptor.byte_end,
                    "byte_start": descriptor.byte_start,
                    "content_part_text_id": content_part_text_id,
                    "content_part_text_segment_translations": [],
                    "key": "default",
                    "parent": None,
                    "parent_id": None,
                    "style": None,
                },
                skip_fields=frozenset(("content_part_text",)),
                relative_path=relative_path,
            )
            _add(
                model_cls=CodeSection,
                source_object_id=section_id,
                raw_fields={
                    "code_id": code_id,
                    "content_part_text_segment_id": segment_id,
                    "identity_hash": descriptor.identity_hash,
                    "metadata": descriptor.metadata,
                    "qualname": descriptor.qualname,
                    "section_key": descriptor.section_key,
                    "type": _enum_value(section_type),
                },
                skip_fields=frozenset(("content_part_text_segment",)),
                relative_path=relative_path,
            )

    for artifact_ref in sorted(
        code_package_artifact_refs,
        key=lambda item: (item.output_key, item.artifact_key),
    ):
        artifact_relative_path = _optional_text(artifact_ref.relative_path)
        if include_relative_paths is not None and (
            artifact_relative_path is None
            or artifact_relative_path not in include_relative_paths
        ):
            continue
        artifact_id = stable_code_package_artifact_id(
            code_package_id=code_package_id,
            output_key=(artifact_ref.output_key or "").strip(),
            artifact_key=(artifact_ref.artifact_key or "").strip(),
        )
        _add(
            model_cls=CodePackageArtifact,
            source_object_id=artifact_id,
            raw_fields=_code_package_artifact_signature_raw_fields(
                code_package_id=code_package_id,
                artifact_ref=artifact_ref,
            ),
            relative_path=artifact_relative_path,
        )
    return _CodePackageSourceObjectStateBuild(
        states_by_id=states,
        path_source_object_ids={
            relative_path: tuple(sorted(source_object_ids, key=str))
            for relative_path, source_object_ids in sorted(
                path_source_object_ids.items(),
            )
        },
    )


def _code_package_source_object_path_index_from_snapshot_inputs(
    *,
    code_package_id: UUID,
    plans_by_relative_path: Mapping[str, CodeContentPlan],
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
) -> Mapping[str, tuple[UUID, ...]]:
    path_source_object_ids: dict[str, set[UUID]] = {}

    def _add(relative_path: str, source_object_id: UUID) -> None:
        path_source_object_ids.setdefault(relative_path, set()).add(source_object_id)

    for relative_path, plan in sorted(plans_by_relative_path.items()):
        code_package_code_id = stable_code_package_code_id(
            code_package_id=code_package_id,
            relative_path=relative_path,
        )
        code_id = stable_code_id(
            code_package_code_id=code_package_code_id,
            relative_path=relative_path,
        )
        content_part_text_id = _stable_code_content_part_text_id(code_id=code_id)
        _add(relative_path, code_package_code_id)
        _add(relative_path, code_id)
        _add(relative_path, content_part_text_id)
        for descriptor in tuple(plan.section_plans or ()):
            section_type = CodeSectionType(descriptor.section_type.value)
            section_id = stable_code_section_id(
                code_id=code_id,
                section_key=descriptor.section_key,
                type=section_type.value,
            )
            segment_id = stable_content_part_text_segment_id(
                content_part_text_id=content_part_text_id,
                key=f"code-section:{section_id}",
            )
            _add(relative_path, segment_id)
            _add(relative_path, section_id)

    for artifact_ref in sorted(
        code_package_artifact_refs,
        key=lambda item: (item.output_key, item.artifact_key),
    ):
        artifact_relative_path = _optional_text(artifact_ref.relative_path)
        if artifact_relative_path is None:
            continue
        artifact_id = stable_code_package_artifact_id(
            code_package_id=code_package_id,
            output_key=(artifact_ref.output_key or "").strip(),
            artifact_key=(artifact_ref.artifact_key or "").strip(),
        )
        _add(artifact_relative_path, artifact_id)

    return {
        relative_path: tuple(sorted(source_object_ids, key=str))
        for relative_path, source_object_ids in sorted(path_source_object_ids.items())
    }


def _code_package_source_object_state_from_raw_fields(
    *,
    domain_oig_id: UUID,
    model_cls: type[BaseORMModel],
    source_object_id: UUID,
    raw_fields: Mapping[str, object],
    skip_fields: frozenset[str] = frozenset(),
) -> _CodePackageSourceObjectState:
    class_config_id = _code_package_model_class_config_id(model_cls)
    return _CodePackageSourceObjectState(
        source_object_id=source_object_id,
        class_config_id=class_config_id,
        class_instance_id=stable_class_instance_id(
            object_instance_graph_id=domain_oig_id,
            class_config_id=class_config_id,
            source_object_id=source_object_id,
        ),
        signature_hash=_code_package_source_object_signature_hash_from_fields(
            model_cls=model_cls,
            source_object_id=source_object_id,
            raw_fields=raw_fields,
            skip_fields=skip_fields,
        ),
    )


def _code_package_model_class_config_id(model_cls: type[BaseORMModel]) -> UUID:
    class_config = model_cls.get_class_config()
    class_config_id = getattr(class_config, "id", None)
    if not isinstance(class_config_id, UUID):
        raise RuntimeError(
            "CodePackage source model missing bound class config: "
            f"model={model_cls.__module__}.{model_cls.__qualname__}"
        )
    return class_config_id


def _code_package_source_object_signature_hash_from_fields(
    *,
    model_cls: type[BaseORMModel],
    source_object_id: UUID,
    raw_fields: Mapping[str, object],
    skip_fields: frozenset[str] = frozenset(),
) -> str:
    fields = _code_package_source_object_signature_fields_from_raw_values(
        model_cls=model_cls,
        raw_fields=raw_fields,
        skip_fields=skip_fields,
    )
    payload = {
        "model": f"{model_cls.__module__}.{model_cls.__qualname__}",
        "id": str(source_object_id),
        "fields": fields,
    }
    return _stable_json_hash(payload)


def _code_package_source_object_signature_fields_from_raw_values(
    *,
    model_cls: type[BaseORMModel],
    raw_fields: Mapping[str, object],
    skip_fields: frozenset[str] = frozenset(),
) -> dict[str, object]:
    field_names = _CODE_PACKAGE_SOURCE_SIGNATURE_FIELD_NAMES_BY_CLASS.get(model_cls)
    if field_names is None:
        field_names = tuple(
            name
            for name in sorted(str(item) for item in model_cls.model_fields)
            if name != "id"
        )
    fields: dict[str, object] = {}
    for field_name in field_names:
        if field_name in skip_fields:
            continue
        encoded = _code_package_source_signature_value(
            raw_fields.get(field_name),
        )
        if encoded is _SOURCE_SIGNATURE_SKIP:
            continue
        fields[field_name] = encoded
    return fields


def _code_package_artifact_signature_raw_fields(
    *,
    code_package_id: UUID,
    artifact_ref: CodePackageArtifactRef,
) -> Mapping[str, object]:
    return {
        "artifact_family": _optional_text(artifact_ref.artifact_family),
        "artifact_key": (artifact_ref.artifact_key or "").strip(),
        "artifact_role": _optional_text(artifact_ref.artifact_role),
        "code_package_id": code_package_id,
        "digest": _optional_text(artifact_ref.digest),
        "error": _optional_text(artifact_ref.error),
        "input_code_package_id": artifact_ref.input_code_package_id,
        "input_object_instance_graph_commit_id": (
            artifact_ref.input_object_instance_graph_commit_id
        ),
        "materialization_index": artifact_ref.materialization_index,
        "media_type": _optional_text(artifact_ref.media_type),
        "output_key": (artifact_ref.output_key or "").strip(),
        "producer_key": _optional_text(artifact_ref.producer_key),
        "producer_kind": _optional_text(artifact_ref.producer_kind),
        "provider_payload": artifact_ref.provider_payload,
        "receipt_payload": artifact_ref.receipt_payload,
        "relative_path": _optional_text(artifact_ref.relative_path),
        "required_for": list(artifact_ref.required_for or []),
        "runtime_contract_version": _optional_text(
            artifact_ref.runtime_contract_version
        ),
        "source_code_package_id": artifact_ref.source_code_package_id,
        "source_object_instance_graph_commit_id": (
            artifact_ref.source_object_instance_graph_commit_id
        ),
        "status": _enum_value(artifact_ref.status),
        "uri": _optional_text(artifact_ref.uri),
    }


def _code_package_source_object_states_from_index_payload(
    payload: Mapping[str, object] | None,
) -> dict[UUID, _CodePackageSourceObjectState] | None:
    view = _code_package_source_object_index_view_from_index_payload(payload)
    if view is None:
        return None
    return _code_package_source_object_states_from_index_view(view)


def _code_package_source_object_states_from_index_view(
    view: _CodePackageSourceObjectIndexView,
) -> dict[UUID, _CodePackageSourceObjectState]:
    return {
        source_object_id: _code_package_source_object_state_from_index_row(
            raw_item,
        )
        for source_object_id, raw_item in view.object_rows_by_source_id.items()
    }


def _code_package_source_object_index_view_from_index_payload(
    payload: Mapping[str, object] | None,
) -> _CodePackageSourceObjectIndexView | None:
    raw_view = _code_package_source_object_raw_index_view_from_index_payload(payload)
    if raw_view is None:
        return None
    if raw_view.partial:
        return None
    object_rows_by_source_id: dict[UUID, Mapping[str, object]] = {}
    try:
        for raw_item in raw_view.object_rows:
            row = _validated_code_package_source_object_state_row(raw_item)
            if row is None:
                return None
            source_object_id = UUID(str(row["source_object_id"]))
            if source_object_id in object_rows_by_source_id:
                return None
            object_rows_by_source_id[source_object_id] = row
    except Exception:
        return None
    return _CodePackageSourceObjectIndexView(
        object_rows_by_source_id=object_rows_by_source_id,
        path_source_object_ids=raw_view.path_source_object_ids,
    )


def _code_package_source_object_raw_index_view_from_index_payload(
    payload: Mapping[str, object] | None,
) -> _CodePackageSourceObjectRawIndexView | None:
    if payload is None:
        return None
    with commit_perf_span(
        phase="code_package.source_object_state_index.raw_view_header",
        category="code_package.source_object_state_index",
    ):
        raw_index = payload.get("source_object_state_index")
        if not isinstance(raw_index, Mapping):
            return None
        source_index = {
            str(key): value for key, value in raw_index.items() if isinstance(key, str)
        }
        source_index_schema = source_index.get("schema")
        partial = (
            source_index_schema == CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_OVERLAY_SCHEMA
        )
        if source_index_schema not in {
            CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_SCHEMA,
            CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_OVERLAY_SCHEMA,
        }:
            return None
        declared_object_count: int | None = None
        if partial:
            if (
                source_index.get("base_schema")
                != CODE_PACKAGE_SOURCE_OBJECT_STATE_INDEX_SCHEMA
            ):
                return None
            raw_object_count = source_index.get("object_count")
            if not isinstance(raw_object_count, int) or raw_object_count < 0:
                return None
            declared_object_count = raw_object_count
        raw_objects = source_index.get("objects")
        raw_path_index = source_index.get("path_source_object_index")
        if not isinstance(raw_objects, list):
            return None
        if declared_object_count is not None and declared_object_count < len(
            raw_objects
        ):
            return None
        if raw_path_index is None:
            raw_path_index = []
        if not isinstance(raw_path_index, list):
            return None
    object_rows: list[Mapping[str, object]] = []
    path_source_object_ids: dict[str, tuple[UUID, ...]] = {}
    try:
        with commit_perf_span(
            phase="code_package.source_object_state_index.raw_view_objects",
            category="code_package.source_object_state_index",
            metadata={"object_count": len(raw_objects)},
        ):
            for raw_item in raw_objects:
                if not isinstance(raw_item, Mapping):
                    return None
                object_rows.append(
                    {
                        str(key): value
                        for key, value in raw_item.items()
                        if isinstance(key, str)
                    }
                )
        with commit_perf_span(
            phase="code_package.source_object_state_index.raw_view_path_index",
            category="code_package.source_object_state_index",
            metadata={"path_count": len(raw_path_index)},
        ):
            for raw_item in raw_path_index:
                if not isinstance(raw_item, Mapping):
                    return None
                item = {
                    str(key): value
                    for key, value in raw_item.items()
                    if isinstance(key, str)
                }
                relative_path = str(item["relative_path"]).strip().strip("/")
                raw_source_object_ids = item.get("source_object_ids")
                if not relative_path or not isinstance(raw_source_object_ids, list):
                    return None
                source_object_ids = tuple(
                    sorted(
                        {
                            UUID(str(raw_source_object_id))
                            for raw_source_object_id in raw_source_object_ids
                        },
                        key=str,
                    )
                )
                if relative_path in path_source_object_ids:
                    return None
                path_source_object_ids[relative_path] = source_object_ids
    except Exception:
        return None
    return _CodePackageSourceObjectRawIndexView(
        object_rows=tuple(object_rows),
        path_source_object_ids=path_source_object_ids,
        declared_object_count=declared_object_count,
        partial=partial,
    )


_CODE_PACKAGE_SOURCE_OBJECT_STATE_ROW_KEYS = frozenset(
    {
        "source_object_id",
        "class_config_id",
        "class_instance_id",
        "signature_hash",
    }
)


def _validated_code_package_source_object_state_row(
    raw_item: object,
) -> dict[str, object] | None:
    if not isinstance(raw_item, Mapping):
        return None
    item = {str(key): value for key, value in raw_item.items() if isinstance(key, str)}
    if set(item) != _CODE_PACKAGE_SOURCE_OBJECT_STATE_ROW_KEYS:
        return None
    try:
        source_object_id = UUID(str(item["source_object_id"]))
        class_config_id = UUID(str(item["class_config_id"]))
        class_instance_id = UUID(str(item["class_instance_id"]))
    except Exception:
        return None
    signature_hash = item.get("signature_hash")
    if not isinstance(signature_hash, str) or not signature_hash:
        return None
    return {
        "source_object_id": str(source_object_id),
        "class_config_id": str(class_config_id),
        "class_instance_id": str(class_instance_id),
        "signature_hash": signature_hash,
    }


def _code_package_source_object_state_from_index_row(
    raw_item: Mapping[str, object],
) -> _CodePackageSourceObjectState:
    item = _validated_code_package_source_object_state_row(raw_item)
    if item is None:
        raise ValueError("Invalid CodePackage source object state row")
    source_object_id = UUID(str(item["source_object_id"]))
    return _CodePackageSourceObjectState(
        source_object_id=source_object_id,
        class_config_id=UUID(str(item["class_config_id"])),
        class_instance_id=UUID(str(item["class_instance_id"])),
        signature_hash=str(item["signature_hash"]),
    )


def _code_package_source_object_rows_for_source_ids(
    *,
    previous_source_index_view: (
        _CodePackageSourceObjectIndexView | _CodePackageSourceObjectRawIndexView
    ),
    source_object_ids: Iterable[UUID],
) -> dict[UUID, Mapping[str, object]] | None:
    target_source_ids_by_text = {
        str(source_object_id): source_object_id
        for source_object_id in source_object_ids
    }
    if isinstance(previous_source_index_view, _CodePackageSourceObjectIndexView):
        return {
            source_object_id: row
            for source_object_id, row in (
                previous_source_index_view.object_rows_by_source_id.items()
            )
            if str(source_object_id) in target_source_ids_by_text
        }
    rows_by_source_id: dict[UUID, Mapping[str, object]] = {}
    for raw_row in previous_source_index_view.object_rows:
        source_object_id = target_source_ids_by_text.get(
            str(raw_row.get("source_object_id")),
        )
        if source_object_id is None:
            continue
        row = _validated_code_package_source_object_state_row(raw_row)
        if row is None:
            return None
        if source_object_id in rows_by_source_id:
            return None
        rows_by_source_id[source_object_id] = row
        if len(rows_by_source_id) == len(target_source_ids_by_text):
            break
    return rows_by_source_id


def _code_package_source_object_path_index_from_index_payload(
    payload: Mapping[str, object] | None,
) -> dict[str, tuple[UUID, ...]] | None:
    view = _code_package_source_object_index_view_from_index_payload(payload)
    if view is None:
        return None
    return dict(view.path_source_object_ids)


def _normalize_code_package_changed_relative_paths(
    value: Iterable[str] | None,
) -> frozenset[str]:
    if value is None:
        return frozenset()
    return frozenset(
        relative_path
        for raw_item in value
        for relative_path in (str(raw_item or "").strip().strip("/"),)
        if relative_path
    )


def _code_package_changed_path_source_state_from_snapshot_inputs(
    *,
    domain_oig_id: UUID,
    code_package_id: UUID,
    code_package_config_id: UUID,
    package_name: str,
    language: CodeLanguage,
    surface: str,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
    plans_by_relative_path: Mapping[str, CodeContentPlan],
    path_roles_by_relative_path: Mapping[str, CodePackagePathRole],
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
    changed_relative_paths: frozenset[str],
    previous_source_index_view: (
        _CodePackageSourceObjectIndexView | _CodePackageSourceObjectRawIndexView
    ),
) -> _CodePackageChangedPathSourceState | None:
    if not changed_relative_paths:
        return None
    previous_path_index = previous_source_index_view.path_source_object_ids
    if not previous_path_index:
        return None
    with commit_perf_span(
        phase="code_package.changed_path_source_state.build_selected_states",
        category="code_package.changed_path_source_state",
        metadata={"changed_path_count": len(changed_relative_paths)},
    ):
        changed_build = _code_package_source_object_state_build_from_snapshot_inputs(
            domain_oig_id=domain_oig_id,
            code_package_id=code_package_id,
            code_package_config_id=code_package_config_id,
            package_name=package_name,
            language=language,
            surface=surface,
            manifest_kind=manifest_kind,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root,
            sources_root=sources_root,
            fqn_prefix=fqn_prefix,
            plans_by_relative_path=plans_by_relative_path,
            path_roles_by_relative_path=path_roles_by_relative_path,
            code_package_artifact_refs=code_package_artifact_refs,
            include_relative_paths=changed_relative_paths,
        )
    with commit_perf_span(
        phase="code_package.changed_path_source_state.changed_source_ids",
        category="code_package.changed_path_source_state",
        metadata={"changed_path_count": len(changed_relative_paths)},
    ):
        previous_changed_source_object_ids = {
            source_object_id
            for relative_path in changed_relative_paths
            for source_object_id in previous_path_index.get(relative_path, ())
        }
        current_changed_source_object_ids = {
            source_object_id
            for relative_path in changed_relative_paths
            for source_object_id in changed_build.path_source_object_ids.get(
                relative_path,
                (),
            )
        }
    if previous_changed_source_object_ids != current_changed_source_object_ids:
        return None
    root_source_state = changed_build.states_by_id.get(code_package_id)
    if root_source_state is None:
        return None

    with commit_perf_span(
        phase="code_package.changed_path_source_state.previous_changed_rows",
        category="code_package.changed_path_source_state",
        metadata={"source_object_count": len(previous_changed_source_object_ids)},
    ):
        previous_changed_rows_by_id = _code_package_source_object_rows_for_source_ids(
            previous_source_index_view=previous_source_index_view,
            source_object_ids=previous_changed_source_object_ids,
        )
    if previous_changed_rows_by_id is None:
        return None
    if set(previous_changed_rows_by_id) != previous_changed_source_object_ids:
        return None
    with commit_perf_span(
        phase="code_package.changed_path_source_state.compare_changed_rows",
        category="code_package.changed_path_source_state",
        metadata={"source_object_count": len(previous_changed_source_object_ids)},
    ):
        changed_source_object_ids = {
            source_object_id
            for source_object_id in previous_changed_source_object_ids
            for previous_row in (previous_changed_rows_by_id.get(source_object_id),)
            for current_source_state in (
                changed_build.states_by_id.get(source_object_id),
            )
            if previous_row is None
            or current_source_state is None
            or _code_package_source_object_state_from_index_row(previous_row)
            != current_source_state
        }
        changed_source_object_ids.add(code_package_id)
    changed_source_states_by_id: dict[UUID, _CodePackageSourceObjectState] = {}
    changed_rows_by_source_id: dict[UUID, Mapping[str, object]] = {}
    for source_object_id in changed_source_object_ids:
        source_state = (
            root_source_state
            if source_object_id == code_package_id
            else changed_build.states_by_id.get(source_object_id)
        )
        if source_state is None:
            return None
        changed_source_states_by_id[source_object_id] = source_state
        changed_rows_by_source_id[source_object_id] = (
            _code_package_source_object_state_index_row(source_state=source_state)
        )

    source_object_path_index = dict(previous_path_index)
    for relative_path in changed_relative_paths:
        current_path_source_object_ids = changed_build.path_source_object_ids.get(
            relative_path,
        )
        if current_path_source_object_ids:
            source_object_path_index[relative_path] = current_path_source_object_ids
        else:
            source_object_path_index.pop(relative_path, None)
    with commit_perf_span(
        phase="code_package.changed_path_source_state.merge_source_index",
        category="code_package.changed_path_source_state",
        metadata={"changed_source_object_count": len(changed_rows_by_source_id)},
    ):
        source_object_state_index = (
            _code_package_source_object_state_index_from_index_view_delta(
                previous_source_index_view=previous_source_index_view,
                changed_rows_by_source_id=changed_rows_by_source_id,
                source_object_path_index=source_object_path_index,
                changed_relative_paths=changed_relative_paths,
            )
        )
    if source_object_state_index is None:
        return None
    return _CodePackageChangedPathSourceState(
        changed_source_states_by_id=changed_source_states_by_id,
        root_source_state=root_source_state,
        changed_source_object_ids=frozenset(changed_source_object_ids),
        source_object_path_index=source_object_path_index,
        source_object_state_index=source_object_state_index,
        source_object_count=previous_source_index_view.object_count,
        build_relationship_topology=False,
    )


def _code_package_text_snapshot_state_snapshot_witness(
    payload: Mapping[str, object] | None,
) -> dict[str, object] | None:
    if payload is None:
        return None
    raw_metadata = payload.get("state_snapshot")
    if not isinstance(raw_metadata, Mapping):
        return None
    metadata = {
        str(key): value for key, value in raw_metadata.items() if isinstance(key, str)
    }
    payload_sha256 = metadata.get("state_snapshot_payload_sha256")
    state_hash = metadata.get("state_snapshot_state_hash")
    if not isinstance(payload_sha256, str) or not payload_sha256:
        return None
    if not isinstance(state_hash, str) or not state_hash:
        return None
    file_size = _payload_int(metadata, "state_snapshot_file_size")
    file_mtime_ns = _payload_int(metadata, "state_snapshot_file_mtime_ns")
    file_ctime_ns = _payload_int(metadata, "state_snapshot_file_ctime_ns")
    if file_size is None or file_mtime_ns is None or file_ctime_ns is None:
        return None
    return {
        "file_size": file_size,
        "file_mtime_ns": file_mtime_ns,
        "file_ctime_ns": file_ctime_ns,
        "payload_sha256": payload_sha256,
        "state_hash": state_hash,
    }


def _code_package_text_snapshot_state_snapshot_witness_cursor(
    payload: Mapping[str, object] | None,
) -> CommitStateWitnessCursorSummary | None:
    if payload is None:
        return None
    raw_metadata = payload.get("state_snapshot")
    if not isinstance(raw_metadata, Mapping):
        return None
    metadata = {
        str(key): value for key, value in raw_metadata.items() if isinstance(key, str)
    }
    raw_cursor = metadata.get("state_snapshot_witness_cursor")
    if not isinstance(raw_cursor, Mapping):
        return None
    return commit_state_witness_cursor_summary_from_payload(
        {str(key): value for key, value in raw_cursor.items() if isinstance(key, str)},
    )


async def _get_code_package_text_snapshot_state_selection(
    *,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    class_instance_ids: Iterable[UUID],
    previous_snapshot_index_payload: Mapping[str, object] | None,
    expected_object_instance_graph_id: UUID | None,
    expected_graph_hash: str | None,
    include_state_row_maps: bool = False,
) -> ObjectInstanceGraphSnapshotStateSelection | None:
    snapshot_store = FSSnapshotStore()
    witness = _code_package_text_snapshot_state_snapshot_witness(
        previous_snapshot_index_payload,
    )
    if witness is not None:
        selection = await snapshot_store.get_snapshot_state_selection_by_file_witness(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=class_instance_ids,
            expected_file_size=int(witness["file_size"]),
            expected_file_mtime_ns=int(witness["file_mtime_ns"]),
            expected_file_ctime_ns=int(witness["file_ctime_ns"]),
            expected_payload_sha256=str(witness["payload_sha256"]),
            expected_state_hash=str(witness["state_hash"]),
            expected_object_instance_graph_id=expected_object_instance_graph_id,
            expected_graph_hash=expected_graph_hash,
            include_state_row_maps=include_state_row_maps,
        )
        if selection is not None:
            return selection
    return await snapshot_store.get_snapshot_state_selection(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        class_instance_ids=class_instance_ids,
        expected_object_instance_graph_id=expected_object_instance_graph_id,
        expected_graph_hash=expected_graph_hash,
        include_state_row_maps=include_state_row_maps,
    )


def _snapshot_state_class_instance_payloads_by_id(
    payload: Mapping[str, object],
) -> dict[UUID, Mapping[str, object]] | None:
    raw_payloads_by_id = _snapshot_state_class_instance_payloads_by_raw_id(payload)
    if raw_payloads_by_id is None:
        return None
    try:
        return {
            UUID(class_instance_id): member_payload
            for class_instance_id, member_payload in raw_payloads_by_id.items()
        }
    except Exception:
        return None


def _snapshot_state_class_instance_payloads_by_raw_id(
    payload: Mapping[str, object],
) -> dict[str, Mapping[str, object]] | None:
    raw_class_instances = payload.get("class_instances")
    if not isinstance(raw_class_instances, list):
        return None
    out: dict[str, Mapping[str, object]] = {}
    try:
        for raw_item in raw_class_instances:
            if not isinstance(raw_item, Mapping):
                return None
            item = {
                str(key): value
                for key, value in raw_item.items()
                if isinstance(key, str)
            }
            class_instance_id = str(item["id"])
            UUID(class_instance_id)
            out[class_instance_id] = item
    except Exception:
        return None
    return out


def _code_package_source_object_signature_hash(source_object: BaseORMModel) -> str:
    payload = {
        "model": (
            f"{source_object.__class__.__module__}."
            f"{source_object.__class__.__qualname__}"
        ),
        "id": str(source_object.id),
        "fields": _code_package_source_object_signature_fields(source_object),
    }
    return _stable_json_hash(payload)


def _code_package_source_object_signature_fields(
    source_object: BaseORMModel,
) -> dict[str, object]:
    field_names = _CODE_PACKAGE_SOURCE_SIGNATURE_FIELD_NAMES_BY_CLASS.get(
        source_object.__class__,
    )
    if field_names is not None:
        return _code_package_source_object_signature_fields_from_names(
            source_object,
            field_names,
        )
    return _code_package_source_object_signature_fields_generic(source_object)


def _code_package_source_object_signature_fields_generic(
    source_object: BaseORMModel,
) -> dict[str, object]:
    fields: dict[str, object] = {}
    model_fields = getattr(source_object.__class__, "model_fields", {})
    if not isinstance(model_fields, Mapping):
        return fields
    for field_name in sorted(str(name) for name in model_fields):
        if field_name == "id":
            continue
        value = getattr(source_object, field_name, None)
        encoded = _code_package_source_signature_value(value)
        if encoded is _SOURCE_SIGNATURE_SKIP:
            continue
        fields[field_name] = encoded
    return fields


def _code_package_source_object_signature_fields_from_names(
    source_object: BaseORMModel,
    field_names: tuple[str, ...],
) -> dict[str, object]:
    fields: dict[str, object] = {}
    for field_name in field_names:
        value = getattr(source_object, field_name, None)
        encoded = _code_package_source_signature_value(value)
        if encoded is _SOURCE_SIGNATURE_SKIP:
            continue
        fields[field_name] = encoded
    return fields


def _code_package_source_signature_value(value: object) -> object:
    if isinstance(value, BaseORMModel):
        return _SOURCE_SIGNATURE_SKIP
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Path):
        return value.as_posix()
    raw_enum_value = getattr(value, "value", None)
    if isinstance(raw_enum_value, str | int | float | bool) or raw_enum_value is None:
        if raw_enum_value is not None:
            return raw_enum_value
    if isinstance(value, list | tuple):
        encoded_items = []
        for item in value:
            encoded = _code_package_source_signature_value(item)
            if encoded is _SOURCE_SIGNATURE_SKIP:
                return _SOURCE_SIGNATURE_SKIP
            encoded_items.append(encoded)
        return encoded_items
    if isinstance(value, Mapping):
        encoded_mapping: dict[str, object] = {}
        for key, item in sorted(value.items(), key=lambda entry: str(entry[0])):
            encoded = _code_package_source_signature_value(item)
            if encoded is _SOURCE_SIGNATURE_SKIP:
                continue
            encoded_mapping[str(key)] = encoded
        return encoded_mapping
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)


def _stable_code_content_part_text_id(*, code_id: UUID) -> UUID:
    return uuid5(_CODE_PACKAGE_TEXT_CONTENT_NAMESPACE, f"content_part_text:{code_id}")


def _code_package_text_snapshot_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    parent_commit_id: UUID | None,
    graph_hash_pre: str,
    graph_hash_post: str,
) -> UUID:
    return uuid5(
        _CODE_PACKAGE_TEXT_SNAPSHOT_COMMIT_NAMESPACE,
        f"{branch_id}:{projection_hash}:{code_package_id}:"
        f"{parent_commit_id or ''}:{graph_hash_pre}:{graph_hash_post}",
    )


def _code_package_text_snapshot_fingerprint(
    *,
    source_snapshot_fingerprint: str,
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
) -> str:
    payload = {
        "v": _CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION,
        "fingerprint_kind": "code_package_text_snapshot",
        "source_snapshot_fingerprint": source_snapshot_fingerprint,
        "artifacts": _artifact_ref_payload(code_package_artifact_refs),
    }
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _text_mapping_payload(value: Mapping[str, str]) -> list[dict[str, str]]:
    return [
        {"relative_path": str(relative_path), "content_text": content_text}
        for relative_path, content_text in sorted(value.items())
    ]


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


def _artifact_ref_payload(
    value: tuple[CodePackageArtifactRef, ...],
) -> list[dict[str, object]]:
    return [
        artifact_ref.model_dump(mode="json", exclude_none=True)
        for artifact_ref in sorted(
            value,
            key=lambda item: (
                str(item.code_package_id or ""),
                item.output_key,
                item.artifact_key,
            ),
        )
    ]


async def load_code_package_text_snapshot_artifact_state_index(
    *,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
) -> dict[str, object] | None:
    payload = await _load_current_code_package_text_snapshot_index_payload(
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
    )
    if payload is None:
        return None
    state = payload.get("artifact_state_index")
    if not isinstance(state, Mapping):
        return None
    if state.get("schema") != CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA:
        return None
    if state.get("code_package_id") != str(code_package_id):
        return None
    result = {str(key): value for key, value in state.items() if isinstance(key, str)}
    result["current_state_status"] = "hydrated_from_code_package_text_snapshot_index"
    result["snapshot_fingerprint"] = payload.get("snapshot_fingerprint")
    result["source_snapshot_fingerprint"] = payload.get("source_snapshot_fingerprint")
    result["head_commit_id"] = payload.get("head_commit_id")
    result["object_instance_graph_commit_id"] = payload.get(
        "object_instance_graph_commit_id"
    )
    result["graph_hash_post"] = payload.get("graph_hash_post")
    return result


async def load_code_package_text_snapshot_commit_index(
    *,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
) -> dict[str, object] | None:
    payload = await _load_current_code_package_text_snapshot_index_payload(
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
    )
    if payload is None:
        return None
    return {
        "v": payload.get("v"),
        "code_package_id": payload.get("code_package_id"),
        "commit_id": payload.get("commit_id"),
        "head_commit_id": payload.get("head_commit_id"),
        "object_instance_graph_commit_id": payload.get(
            "object_instance_graph_commit_id"
        ),
        "object_instance_graph_id": payload.get("object_instance_graph_id"),
        "graph_hash_post": payload.get("graph_hash_post"),
        "snapshot_fingerprint": payload.get("snapshot_fingerprint"),
        "source_snapshot_fingerprint": payload.get("source_snapshot_fingerprint"),
    }


def _code_package_snapshot_index_payload_has_reuse_sections(
    payload: Mapping[str, object],
) -> bool:
    return isinstance(payload.get("artifact_state_index"), Mapping) and (
        isinstance(payload.get("source_object_state_index"), Mapping)
        or isinstance(payload.get("source_object_state_index_ref"), Mapping)
    )


async def _code_package_text_snapshot_index_noop_result(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    code_package_config_id: UUID,
    package_name: str,
    language: CodeLanguage,
    surface: str,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None,
    fqn_prefix: str | None,
    domain_oig_id: UUID,
    snapshot_fingerprint: str,
    snapshot_index_payload: Mapping[str, object] | None = None,
) -> CodePackageTextSnapshotCommitResult | None:
    payload = _code_package_text_snapshot_index_payload_hit(
        payload=snapshot_index_payload,
        code_package_id=code_package_id,
        snapshot_fingerprint=snapshot_fingerprint,
    )
    if payload is None and snapshot_index_payload is not None:
        return None
    if payload is None:
        payload = await _code_package_text_snapshot_index_hit(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
            snapshot_fingerprint=snapshot_fingerprint,
        )
    if payload is None:
        return None
    if payload.get("object_instance_graph_id") != str(domain_oig_id):
        return None
    head_commit_id = _head_uuid(payload, "head_commit_id")
    object_instance_graph_commit_id = _head_uuid(
        payload,
        "object_instance_graph_commit_id",
    )
    if head_commit_id is None or object_instance_graph_commit_id is None:
        return None
    if not _code_package_text_snapshot_state_snapshot_index_hit(
        payload=payload,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=head_commit_id,
    ):
        return None
    object_count = _payload_int(payload, "object_count")
    if object_count is None:
        return None
    code_package = _build_code_package_identity(
        code_package_id=code_package_id,
        code_package_config_id=code_package_config_id,
        package_name=package_name,
        language=language,
        surface=surface,
        manifest_kind=manifest_kind,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        fqn_prefix=fqn_prefix,
    )
    return CodePackageTextSnapshotCommitResult(
        code_package=code_package,
        commit_id=head_commit_id,
        head_commit_id=head_commit_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        object_count=object_count,
        change_count=0,
    )


def _code_package_text_snapshot_state_snapshot_index_hit(
    *,
    payload: Mapping[str, object],
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
) -> bool:
    raw_metadata = payload.get("state_snapshot")
    if not isinstance(raw_metadata, Mapping):
        return False
    metadata = {
        str(key): value for key, value in raw_metadata.items() if isinstance(key, str)
    }
    if metadata.get("state_snapshot_kind") == "class_segment_index":
        expected_graph_hash = payload.get("graph_hash_post")
        if not isinstance(expected_graph_hash, str) or not expected_graph_hash:
            return False
        if _code_package_text_snapshot_cursor_metadata_hit(
            payload=payload,
            metadata=metadata,
            expected_graph_hash=expected_graph_hash,
        ):
            return True
        return (
            FSSnapshotStore().snapshot_state_class_segment_index_metadata(
                branch_id=branch_id,
                projection_hash=projection_hash,
                commit_id=commit_id,
                expected_graph_hash=expected_graph_hash,
            )
            is not None
        )
    if not isinstance(metadata.get("state_snapshot_payload_sha256"), str):
        return False
    if not isinstance(metadata.get("state_snapshot_state_hash"), str):
        return False
    file_size = _payload_int(metadata, "state_snapshot_file_size")
    file_mtime_ns = _payload_int(metadata, "state_snapshot_file_mtime_ns")
    file_ctime_ns = _payload_int(metadata, "state_snapshot_file_ctime_ns")
    if file_size is None or file_mtime_ns is None or file_ctime_ns is None:
        return False
    return FSSnapshotStore().has_snapshot_state_rows_file_metadata(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        expected_file_size=file_size,
        expected_file_mtime_ns=file_mtime_ns,
        expected_file_ctime_ns=file_ctime_ns,
    )


def _code_package_text_snapshot_cursor_metadata_hit(
    *,
    payload: Mapping[str, object],
    metadata: Mapping[str, object],
    expected_graph_hash: str,
) -> bool:
    if metadata.get("state_snapshot_graph_hash_source") != "witness_cursor_hash":
        return False
    if metadata.get("state_snapshot_graph_hash") != expected_graph_hash:
        return False
    cursor_summary = _code_package_text_snapshot_state_snapshot_witness_cursor(
        payload,
    )
    if cursor_summary is None or cursor_summary.cursor_hash != expected_graph_hash:
        return False
    row_count = _payload_int(metadata, "state_snapshot_row_count")
    if row_count is not None and row_count != cursor_summary.row_count:
        return False
    segment_count = _payload_int(metadata, "state_snapshot_segment_count")
    if segment_count is not None and segment_count != cursor_summary.segment_count:
        return False
    return True
