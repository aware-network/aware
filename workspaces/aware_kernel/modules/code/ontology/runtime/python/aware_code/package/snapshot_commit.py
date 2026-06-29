from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.package.artifact_delta_plan import artifact_identity_key
from aware_code.package.artifact_delta_plan import (
    code_package_artifact_ref_signature_hash,
)
from aware_meta.attribute.instance.value import AttributeValueTreeValidationError
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
from aware_meta.graph.instance.builder import build_object_instance_graph
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.fs_store import (
    CommitActionDescriptor,
    FSCommitStore,
)
from aware_meta.graph.instance.commit.hash_contract import compute_oig_lane_hash_state
from aware_meta.graph.instance.commit.materialization_cache import (
    get_shared_materialization_cache,
)
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.diff_orm import (
    build_object_instance_graph_changes_from_orm_change_set,
)
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
)
from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_orm.models.base_model import BaseORMModel
from aware_orm.models.introspection import ModelIntrospection
from aware_orm.session.change_collector import ORMChangeSet


@dataclass(frozen=True, slots=True)
class CodePackageTextSnapshotCommitResult:
    code_package: CodePackage
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


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
CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA = "aware.code.package.artifact_state_index.v1"
_CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION = 5


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
) -> CodePackageTextSnapshotCommitResult:
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
    source_snapshot_fingerprint = code_package_text_source_snapshot_fingerprint(
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
    )
    snapshot_fingerprint = _code_package_text_snapshot_fingerprint(
        source_snapshot_fingerprint=source_snapshot_fingerprint,
        code_package_artifact_refs=code_package_artifact_refs,
    )
    store = FSCommitStore()
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
    )
    artifact_state_index = _code_package_artifact_state_index_from_refs(
        code_package_id=code_package.id,
        code_package_artifact_refs=code_package_artifact_refs,
    )
    domain_oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=projection_hash,
    )
    if opgi is None:
        raise RuntimeError(
            "CodePackage text snapshot commit missing ObjectProjectionGraphIdentity: "
            f"projection_hash={projection_hash}"
        )
    oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=domain_oig_id,
    )
    desired_oig = _build_code_package_desired_oig(
        index=index,
        opg=opg,
        branch_id=branch_id,
        domain_oig_id=domain_oig_id,
        code_package=code_package,
        code_package_config_id=code_package_config_id,
        manifest_kind=manifest_kind,
        surface=surface,
        objects_by_id=objects_by_id,
    )
    desired_hash_state = compute_oig_lane_hash_state(
        graph=desired_oig,
        schema_attribute_configs_by_id=index.attribute_configs_by_id,
        expected_hash=None,
    )
    desired_oig.hash = desired_hash_state.lane_hash
    head = await store.head(branch_id=branch_id, projection_hash=projection_hash)
    head_commit_id = _head_uuid(head, "commit_id")
    head_oig_id = _head_uuid(head, "object_instance_graph_id")
    head_root_object_id = _head_uuid(head, "root_object_id")
    head_oig_commit_id = _head_uuid(head, "object_instance_graph_commit_id")
    head_graph_hash_post = _head_string(head, "graph_hash_post")
    timeline_parent_commit_id = head_commit_id
    if (
        head_commit_id is not None
        and head_oig_commit_id is not None
        and head_oig_id == domain_oig_id
        and head_root_object_id == code_package.id
        and head_graph_hash_post in desired_hash_state.accepted_hashes()
    ):
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
            graph_hash_post=head_graph_hash_post,
            object_count=len(objects_by_id),
            change_count=0,
            artifact_state_index=artifact_state_index,
        )
        return CodePackageTextSnapshotCommitResult(
            code_package=code_package,
            commit_id=head_commit_id,
            head_commit_id=head_commit_id,
            object_instance_graph_commit_id=head_oig_commit_id,
            object_count=len(objects_by_id),
            change_count=0,
        )
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

    changes = _build_code_package_text_snapshot_changes(
        before_oig=before_oig,
        oigi_id=oigi_id,
        opg=opg,
        index=index,
        code_package=code_package,
        code_package_config_id=code_package_config_id,
        surface=surface,
        objects_by_id=objects_by_id,
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
            graph_hash_post=raw_head_graph_hash_post or before_oig.hash,
            object_count=len(objects_by_id),
            change_count=0,
            artifact_state_index=artifact_state_index,
        )
        return CodePackageTextSnapshotCommitResult(
            code_package=code_package,
            commit_id=head_commit_id,
            head_commit_id=head_commit_id,
            object_instance_graph_commit_id=raw_head_oig_commit_id,
            object_count=len(objects_by_id),
            change_count=0,
        )
    try:
        after_oig = materialize_meta_oig_post(
            before_oig=before_oig,
            changes=changes,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
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
        changes = _build_code_package_text_snapshot_changes(
            before_oig=before_oig,
            oigi_id=oigi_id,
            opg=opg,
            index=index,
            code_package=code_package,
            code_package_config_id=code_package_config_id,
            surface=surface,
            objects_by_id=objects_by_id,
        )
        if not changes:
            raise RuntimeError(
                "CodePackage text snapshot reset produced no OIG changes: "
                f"package_name={package_name!r}"
            )
        after_oig = materialize_meta_oig_post(
            before_oig=before_oig,
            changes=changes,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
    commit_id = _code_package_text_snapshot_commit_id(
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package.id,
        parent_commit_id=timeline_parent_commit_id,
        graph_hash_pre=before_oig.hash,
        graph_hash_post=after_oig.hash,
    )
    commit = await FSLaneCommitter().commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        before_oig=before_oig,
        root_object_id=code_package.id,
        changes=changes,
        graph_hash_pre=before_oig.hash,
        graph_hash_post=after_oig.hash,
        author_id=resolve_meta_author_id(actor_id),
        commit_id=commit_id,
        commit_action=CommitActionDescriptor(
            operation_label="CodePackage.materialize_text_snapshot",
            call_target="generated_materialization",
            object_id=code_package.id,
        ),
    )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "CodePackage text snapshot commit did not append a lane commit: "
            f"package_name={package_name!r}"
        )

    object_instance_graph_commit_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
        commit_id=commit.commit.id,
    )
    _write_code_package_text_snapshot_index(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package.id,
        snapshot_fingerprint=snapshot_fingerprint,
        source_snapshot_fingerprint=source_snapshot_fingerprint,
        commit_id=commit.commit.id,
        head_commit_id=commit.commit.id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        object_instance_graph_id=domain_oig_id,
        graph_hash_post=after_oig.hash,
        object_count=len(objects_by_id),
        change_count=len(changes),
        artifact_state_index=artifact_state_index,
    )
    return CodePackageTextSnapshotCommitResult(
        code_package=code_package,
        commit_id=commit.commit.id,
        head_commit_id=commit.commit.id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
        object_count=len(objects_by_id),
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
) -> tuple[CodePackage, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
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
    plans_by_relative_path: dict[str, CodeContentPlan] = {}
    for relative_path, content_text in source_texts_by_relative_path.items():
        plans_by_relative_path[relative_path] = build_code_content_plan_copy_from_text(
            content_text=content_text,
            language=language,
        )
    for relative_path, content_plan in source_plans_by_relative_path.items():
        if relative_path in plans_by_relative_path:
            raise RuntimeError(
                "CodePackage snapshot received duplicate text/plan path: "
                f"{relative_path}"
            )
        plans_by_relative_path[relative_path] = content_plan
    for relative_path, content_text in unparsed_texts_by_relative_path.items():
        if relative_path in plans_by_relative_path:
            raise RuntimeError(
                "CodePackage snapshot received duplicate parsed/unparsed path: "
                f"{relative_path}"
            )
        plans_by_relative_path[relative_path] = CodeContentPlan(
            language=language,
            content_text=content_text,
            section_plans=[],
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
                language=CodeLanguage(plan.language.value),
            ),
        )
        package_code = _remember(
            objects_by_id,
            CodePackageCode(
                id=code_package_code_id,
                code_package_id=code_package.id,
                code=code,
                relative_path=relative_path,
                path_role=path_roles_by_relative_path.get(
                    relative_path,
                    CodePackagePathRole.authored_source,
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
                    type=section_type,
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
        status=artifact_ref.status,
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
        language=language,
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


def _build_code_package_desired_oig(
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
    oigi_id: UUID,
    opg,
    index: MetaGraphRuntimeIndex,
    code_package: CodePackage,
    code_package_config_id: UUID,
    surface: str,
    objects_by_id: Mapping[UUID, BaseORMModel],
):
    created_ids = frozenset(objects_by_id)
    deleted_ids = _code_package_text_snapshot_deleted_ids(
        before_oig=before_oig,
        desired_object_ids=frozenset(objects_by_id),
    )
    change_set = ORMChangeSet(
        collected_at=datetime.now(UTC),
        created_ids=created_ids,
        touched_ids=created_ids,
        deleted_ids=deleted_ids,
        objects_by_id={
            **objects_by_id,
            code_package.id: _code_package_config_overlay(
                code_package=code_package,
                code_package_config_id=code_package_config_id,
                surface=surface,
            ),
        },
        scalar_fields_by_id={},
        list_fields_by_id={},
        scalar_baseline={},
        list_baseline={},
        list_added={},
        list_removed={},
    )
    return build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=oigi_id,
        ocg=index.ocg,
        opg=opg,
        change_set=change_set,
        class_configs_by_id=index.class_configs_by_id,
        relationships_by_id=index.relationships_by_id,
        enum_option_resolver=default_meta_enum_option_resolver,
        class_instance_resolver=None,
        union_selections=None,
    )


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
    return value if isinstance(value, UUID) else None


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
    if head is not None and head.get("commit_id") is not None:
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


def _code_package_text_snapshot_deleted_ids(
    *,
    before_oig,
    desired_object_ids: frozenset[UUID],
) -> frozenset[UUID]:
    before_source_ids = {
        class_instance.source_object_id
        for class_instance in before_oig.class_instances
        if isinstance(getattr(class_instance, "source_object_id", None), UUID)
    }
    return frozenset(before_source_ids - set(desired_object_ids))


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


def code_package_text_source_snapshot_fingerprint(
    *,
    package_name: str,
    code_package_config_id: UUID,
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
) -> str:
    payload = {
        "v": _CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION,
        "fingerprint_kind": "code_package_text_source_snapshot",
        "code_package_config_id": str(code_package_config_id),
        "package_name": (package_name or "").strip(),
        "language": language.value,
        "surface": surface,
        "manifest_kind": manifest_kind,
        "manifest_relative_path": (manifest_relative_path or "").strip(),
        "package_root": (package_root or "").strip(),
        "sources_root": (sources_root or "").strip() or None,
        "fqn_prefix": (fqn_prefix or "").strip() or None,
        "source_texts": _text_mapping_payload(source_texts_by_relative_path),
        "source_plans": _plan_mapping_payload(source_plans_by_relative_path),
        "unparsed_texts": _text_mapping_payload(unparsed_texts_by_relative_path),
        "path_roles": {
            key: value.value
            for key, value in sorted(path_roles_by_relative_path.items())
        },
    }
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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


def _plan_mapping_payload(
    value: Mapping[str, CodeContentPlan],
) -> list[dict[str, object]]:
    return [
        {
            "relative_path": str(relative_path),
            "content_plan": plan.model_dump(mode="json", exclude_none=True),
        }
        for relative_path, plan in sorted(value.items())
    ]


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


async def _load_current_code_package_text_snapshot_index_payload(
    *,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
) -> dict[str, object] | None:
    store = FSCommitStore()
    payload = _read_json_object_or_none(
        _code_package_text_snapshot_index_path(
            store=store,
            branch_id=branch_id,
            projection_hash=projection_hash,
            code_package_id=code_package_id,
        )
    )
    if payload is None:
        return None
    if payload.get("v") != _CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION:
        return None
    if payload.get("code_package_id") != str(code_package_id):
        return None
    head = await store.head(branch_id=branch_id, projection_hash=projection_hash)
    if head is None:
        return None
    if _head_string(head, "commit_id") != payload.get("head_commit_id"):
        return None
    if _head_string(head, "graph_hash_post") != payload.get("graph_hash_post"):
        return None
    if _head_string(head, "object_instance_graph_commit_id") != payload.get(
        "object_instance_graph_commit_id"
    ):
        return None
    if _head_string(head, "object_instance_graph_id") != payload.get(
        "object_instance_graph_id"
    ):
        return None
    return {str(key): value for key, value in payload.items() if isinstance(key, str)}


def _code_package_artifact_state_index_from_refs(
    *,
    code_package_id: UUID,
    code_package_artifact_refs: tuple[CodePackageArtifactRef, ...],
) -> dict[str, object]:
    artifacts = [
        _artifact_state_row_from_ref(
            code_package_id=code_package_id,
            artifact_ref=artifact_ref,
        )
        for artifact_ref in sorted(
            code_package_artifact_refs,
            key=lambda item: (item.output_key, item.artifact_key),
        )
    ]
    payload: dict[str, object] = {
        "schema": CODE_PACKAGE_ARTIFACT_STATE_INDEX_SCHEMA,
        "code_package_id": str(code_package_id),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    payload["signature_hash"] = _stable_json_hash(payload)
    return payload


def _artifact_state_row_from_ref(
    *,
    code_package_id: UUID,
    artifact_ref: CodePackageArtifactRef,
) -> dict[str, object]:
    if artifact_ref.code_package_id != code_package_id:
        raise RuntimeError(
            "CodePackage artifact state index ref targets a different package: "
            f"expected={code_package_id} actual={artifact_ref.code_package_id}"
        )
    output_key = (artifact_ref.output_key or "").strip()
    artifact_key = (artifact_ref.artifact_key or "").strip()
    if not output_key:
        raise RuntimeError("CodePackage artifact state index ref missing output_key")
    if not artifact_key:
        raise RuntimeError("CodePackage artifact state index ref missing artifact_key")
    return {
        "output_key": output_key,
        "artifact_key": artifact_key,
        "identity_key": artifact_identity_key(
            output_key=output_key,
            artifact_key=artifact_key,
        ),
        "signature_hash": code_package_artifact_ref_signature_hash(
            artifact_ref=artifact_ref
        ),
        "status": str(getattr(artifact_ref.status, "value", artifact_ref.status)),
        "digest": _optional_text(artifact_ref.digest),
        "relative_path": _optional_text(artifact_ref.relative_path),
        "uri": _optional_text(artifact_ref.uri),
        "media_type": _optional_text(artifact_ref.media_type),
        "artifact_family": _optional_text(artifact_ref.artifact_family),
        "artifact_role": _optional_text(artifact_ref.artifact_role),
        "producer_key": _optional_text(artifact_ref.producer_key),
    }


def _stable_json_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(dict(payload), separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _code_package_text_snapshot_index_path(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
) -> Path:
    return (
        store.aware_root
        / ".aware"
        / "oig"
        / str(branch_id)
        / projection_hash
        / "indexes"
        / "code_package_text_snapshots"
        / f"{code_package_id}.json"
    )


async def _code_package_text_snapshot_index_hit(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    snapshot_fingerprint: str,
) -> dict[str, object] | None:
    path = _code_package_text_snapshot_index_path(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
    )
    payload = _read_json_object_or_none(path)
    if payload is None:
        return None
    if payload.get("v") != _CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION:
        return None
    if payload.get("snapshot_fingerprint") != snapshot_fingerprint:
        return None
    if payload.get("code_package_id") != str(code_package_id):
        return None
    head = await store.head(branch_id=branch_id, projection_hash=projection_hash)
    if head is None:
        return None
    if _head_string(head, "commit_id") != payload.get("head_commit_id"):
        return None
    if _head_string(head, "graph_hash_post") != payload.get("graph_hash_post"):
        return None
    if _head_string(head, "object_instance_graph_commit_id") != payload.get(
        "object_instance_graph_commit_id"
    ):
        return None
    if _head_string(head, "object_instance_graph_id") != payload.get(
        "object_instance_graph_id"
    ):
        return None
    return payload


def _write_code_package_text_snapshot_index(
    *,
    store: FSCommitStore,
    branch_id: UUID,
    projection_hash: str,
    code_package_id: UUID,
    snapshot_fingerprint: str,
    source_snapshot_fingerprint: str,
    commit_id: UUID,
    head_commit_id: UUID,
    object_instance_graph_commit_id: UUID,
    object_instance_graph_id: UUID,
    graph_hash_post: str,
    object_count: int,
    change_count: int,
    artifact_state_index: Mapping[str, object],
) -> None:
    payload: dict[str, object] = {
        "v": _CODE_PACKAGE_TEXT_SNAPSHOT_INDEX_VERSION,
        "snapshot_fingerprint": snapshot_fingerprint,
        "source_snapshot_fingerprint": source_snapshot_fingerprint,
        "code_package_id": str(code_package_id),
        "commit_id": str(commit_id),
        "head_commit_id": str(head_commit_id),
        "object_instance_graph_commit_id": str(object_instance_graph_commit_id),
        "object_instance_graph_id": str(object_instance_graph_id),
        "graph_hash_post": graph_hash_post,
        "object_count": object_count,
        "change_count": change_count,
        "artifact_state_index": dict(artifact_state_index),
    }
    path = _code_package_text_snapshot_index_path(
        store=store,
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
    )
    existing = _read_json_object_or_none(path)
    if existing == payload:
        return
    _atomic_write_json(path, payload)


def _read_json_object_or_none(path: Path) -> dict[str, object] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None
    result: dict[str, object] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            return None
        result[key] = value
    return result


def _atomic_write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    encoded = json.dumps(dict(payload), separators=(",", ":"), sort_keys=True)
    with open(tmp, "w", encoding="utf-8") as file_handle:
        file_handle.write(encoded)
        file_handle.flush()
        os.fsync(file_handle.fileno())
    tmp.replace(path)


def _head_string(head: object, key: str) -> str | None:
    if not isinstance(head, Mapping):
        return None
    value = head.get(key)
    if isinstance(value, str) and value.strip():
        return value
    return None


def _head_uuid(head: object, key: str) -> UUID | None:
    value = _head_string(head, key)
    if value is None:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None
