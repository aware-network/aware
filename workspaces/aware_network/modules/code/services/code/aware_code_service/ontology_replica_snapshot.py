from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from uuid import UUID

from aware_service_runtime.api_ingress.ontology_replica_orm_context import (
    require_service_ontology_replica_orm_session,
)
from aware_code_service_dto.code.features.view_state import (
    CodeEditorViewStateV1,
    CodePackageSelectorViewStateV1,
    CodeViewStateCode,
    CodeViewStateCode as CodePackageSelectorCodeV1,
    CodeViewStatePackage,
    CodeViewStatePackage as CodePackageSelectorPackageV1,
    CodeViewStateSectionAnchor,
    CodeViewStateSectionAnchor as CodeSectionAnchorV1,
    CodeViewStateSourceRef,
    CodeViewStateSourceRef as CodeSourceRefV1,
    ResolveCodeEditorViewRequest,
    ResolveCodeEditorViewResponse,
    ResolveCodePackageSelectorViewRequest,
    ResolveCodePackageSelectorViewResponse,
)
from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True, slots=True)
class CodeReplicaReadModels:
    code_package_model: Any
    code_package_code_model: Any
    code_model: Any
    content_part_text_model: Any
    code_section_model: Any


class CodeReplicaPackageSnapshotV1(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    selector_key: str
    code_package_id: str
    package_name: str | None = None
    package_root: str | None = None
    manifest_relative_path: str | None = None
    package_fqn: str | None = None
    language: str | None = None
    surface: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CodeReplicaSectionSnapshotV1(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    section_key: str
    section_kind: str | None = None
    stable_identity: str | None = None
    byte_start: int | None = None
    byte_end: int | None = None
    label: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CodeReplicaCodeSnapshotV1(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    selector_key: str
    code_id: str | None = None
    code_package_code_id: str | None = None
    code_package_id: str
    package_name: str | None = None
    relative_path: str | None = None
    language: str | None = None
    path_role: str | None = None
    source_hash: str | None = None
    source_text: str | None = None
    label: str | None = None
    sections: list[CodeReplicaSectionSnapshotV1] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CodeReplicaLatestSnapshotV1(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str = "ready"
    source_kind: str = "ontology_replica"
    branch_id: str | None = None
    selected_package_key: str | None = None
    selected_code_key: str | None = None
    packages: list[CodeReplicaPackageSnapshotV1] = Field(default_factory=list)
    codes: list[CodeReplicaCodeSnapshotV1] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


async def read_code_latest_snapshot_from_ontology_replica(
    *,
    selected_package_key: str | None = None,
    selected_code_key: str | None = None,
    models: CodeReplicaReadModels | None = None,
) -> CodeReplicaLatestSnapshotV1:
    session = require_service_ontology_replica_orm_session()
    read_models = models or _default_read_models()
    package_objects = list(await read_models.code_package_model.where().all())
    package_snapshots = [
        _package_snapshot(package_obj) for package_obj in package_objects
    ]
    package_snapshots.sort(
        key=lambda item: (
            item.manifest_relative_path or "",
            item.package_name or "",
            item.code_package_id,
        )
    )
    selected_package = _selected_package_snapshot(
        packages=package_snapshots,
        selected_package_key=selected_package_key,
    )
    code_snapshots: list[CodeReplicaCodeSnapshotV1] = []
    if selected_package is not None:
        code_snapshots = await _code_snapshots_for_package(
            package=selected_package,
            read_models=read_models,
        )
    selected_code = _selected_code_snapshot(
        codes=code_snapshots,
        selected_code_key=selected_code_key,
    )
    return CodeReplicaLatestSnapshotV1(
        status="ready" if package_snapshots else "empty",
        branch_id=str(getattr(session, "branch_id", "")) or None,
        selected_package_key=(
            selected_package.selector_key if selected_package is not None else None
        ),
        selected_code_key=(
            selected_code.selector_key if selected_code is not None else None
        ),
        packages=package_snapshots,
        codes=code_snapshots,
        provenance={
            "source_kind": "ontology_replica",
            "branch_id": str(getattr(session, "branch_id", "")) or None,
            "package_count": len(package_snapshots),
            "code_count": len(code_snapshots),
        },
    )


async def code_package_selector_view_state_from_ontology_replica(
    *,
    selected_package_key: str | None = None,
    selected_code_key: str | None = None,
    models: CodeReplicaReadModels | None = None,
) -> CodePackageSelectorViewStateV1:
    snapshot = await read_code_latest_snapshot_from_ontology_replica(
        selected_package_key=selected_package_key,
        selected_code_key=selected_code_key,
        models=models,
    )
    packages = [_selector_package(package) for package in snapshot.packages]
    codes = [_selector_code(code) for code in snapshot.codes]
    return CodePackageSelectorViewStateV1(
        status=snapshot.status,
        source_mode="ontology_replica",
        selected_package_key=snapshot.selected_package_key,
        selected_code_key=snapshot.selected_code_key,
        packages=packages,
        codes=codes,
        summary=_count_summary(
            packages, singular="Code package", plural="Code packages"
        ),
        error=None,
        provenance={
            "source_kind": "ontology_replica",
            "branch_id": snapshot.branch_id,
            "package_count": len(packages),
            "code_count": len(codes),
        },
    )


async def code_editor_view_state_from_ontology_replica(
    *,
    selected_package_key: str | None = None,
    selected_code_key: str | None = None,
    selected_section_key: str | None = None,
    models: CodeReplicaReadModels | None = None,
) -> CodeEditorViewStateV1:
    snapshot = await read_code_latest_snapshot_from_ontology_replica(
        selected_package_key=selected_package_key,
        selected_code_key=selected_code_key,
        models=models,
    )
    selected_code = _selected_code_snapshot(
        codes=snapshot.codes,
        selected_code_key=snapshot.selected_code_key,
    )
    if selected_code is None:
        return CodeEditorViewStateV1(
            status="waiting",
            source_ref=None,
            source_text=None,
            selected_section_key=selected_section_key,
            section_anchors=[],
            semantic_events=[],
            semantic_deltas=[],
            diagnostics=[],
            summary=None,
            error=None,
            provenance={
                "source_kind": "ontology_replica",
                "branch_id": snapshot.branch_id,
                "package_count": len(snapshot.packages),
                "code_count": len(snapshot.codes),
            },
        )
    section_anchors = [_section_anchor(section) for section in selected_code.sections]
    return CodeEditorViewStateV1(
        status="ready",
        source_ref=_source_ref(selected_code),
        source_text=selected_code.source_text,
        selected_section_key=selected_section_key,
        section_anchors=section_anchors,
        semantic_events=[],
        semantic_deltas=[],
        diagnostics=list(snapshot.diagnostics),
        summary=(
            f"{selected_code.relative_path or selected_code.selector_key}: "
            f"{len(selected_code.source_text or '')} chars"
        ),
        error=None,
        provenance={
            "source_kind": "ontology_replica",
            "branch_id": snapshot.branch_id,
            "package_count": len(snapshot.packages),
            "code_count": len(snapshot.codes),
            "section_count": len(section_anchors),
        },
    )


async def resolve_code_package_selector_view_response_from_ontology_replica(
    request: ResolveCodePackageSelectorViewRequest,
    *,
    models: CodeReplicaReadModels | None = None,
) -> ResolveCodePackageSelectorViewResponse:
    snapshot = await read_code_latest_snapshot_from_ontology_replica(
        selected_package_key=request.selected_package_key,
        selected_code_key=request.selected_code_key,
        models=models,
    )
    packages = [_api_view_package(package) for package in snapshot.packages]
    codes = [_api_view_code(code) for code in snapshot.codes]
    return ResolveCodePackageSelectorViewResponse(
        request_id=request.request_id,
        success=True,
        status=snapshot.status,
        source_kind=snapshot.source_kind,
        branch_id=snapshot.branch_id,
        selected_package_key=snapshot.selected_package_key,
        selected_code_key=snapshot.selected_code_key,
        packages=packages,
        codes=codes,
        diagnostics=list(snapshot.diagnostics),
        provenance=_api_provenance(
            snapshot=snapshot,
            package_count=len(packages),
            code_count=len(codes),
        ),
    )


async def resolve_code_editor_view_response_from_ontology_replica(
    request: ResolveCodeEditorViewRequest,
    *,
    models: CodeReplicaReadModels | None = None,
) -> ResolveCodeEditorViewResponse:
    snapshot = await read_code_latest_snapshot_from_ontology_replica(
        selected_package_key=request.selected_package_key,
        selected_code_key=request.selected_code_key,
        models=models,
    )
    selected_code = _selected_code_snapshot(
        codes=snapshot.codes,
        selected_code_key=snapshot.selected_code_key,
    )
    provenance = _api_provenance(
        snapshot=snapshot,
        package_count=len(snapshot.packages),
        code_count=len(snapshot.codes),
    )
    if selected_code is None:
        return ResolveCodeEditorViewResponse(
            request_id=request.request_id,
            success=True,
            status="waiting",
            source_kind=snapshot.source_kind,
            branch_id=snapshot.branch_id,
            selected_section_key=request.selected_section_key,
            diagnostics=list(snapshot.diagnostics),
            provenance=provenance,
        )
    section_anchors = [
        _api_section_anchor(section) for section in selected_code.sections
    ]
    return ResolveCodeEditorViewResponse(
        request_id=request.request_id,
        success=True,
        status="ready",
        source_kind=snapshot.source_kind,
        branch_id=snapshot.branch_id,
        source_ref=_api_source_ref(selected_code),
        source_text=selected_code.source_text,
        selected_section_key=request.selected_section_key,
        section_anchors=section_anchors,
        semantic_events=[],
        semantic_deltas=[],
        diagnostics=list(snapshot.diagnostics),
        summary=(
            f"{selected_code.relative_path or selected_code.selector_key}: "
            f"{len(selected_code.source_text or '')} chars"
        ),
        provenance={
            **provenance,
            "section_count": len(section_anchors),
        },
    )


def _default_read_models() -> CodeReplicaReadModels:
    from aware_code_ontology_orm_models.code.code import Code
    from aware_code_ontology_orm_models.code.code_section import CodeSection
    from aware_code_ontology_orm_models.package.code_package import CodePackage
    from aware_code_ontology_orm_models.package.code_package_code import (
        CodePackageCode,
    )
    from aware_content_ontology_orm_models.part.content_part_text import (
        ContentPartText,
    )

    return CodeReplicaReadModels(
        code_package_model=CodePackage,
        code_package_code_model=CodePackageCode,
        code_model=Code,
        content_part_text_model=ContentPartText,
        code_section_model=CodeSection,
    )


async def _code_snapshots_for_package(
    *,
    package: CodeReplicaPackageSnapshotV1,
    read_models: CodeReplicaReadModels,
) -> list[CodeReplicaCodeSnapshotV1]:
    package_id = UUID(package.code_package_id)
    code_edges = list(
        await read_models.code_package_code_model.many(
            code_package_id=package_id,
        )
    )
    snapshots = [
        await _code_snapshot(
            package=package,
            code_edge=code_edge,
            read_models=read_models,
        )
        for code_edge in code_edges
    ]
    snapshots.sort(key=lambda item: (item.relative_path or "", item.selector_key))
    return snapshots


async def _code_snapshot(
    *,
    package: CodeReplicaPackageSnapshotV1,
    code_edge: object,
    read_models: CodeReplicaReadModels,
) -> CodeReplicaCodeSnapshotV1:
    edge_id = _optional_uuid_text(getattr(code_edge, "id", None))
    relative_path = _optional_text(getattr(code_edge, "relative_path", None))
    code_obj = getattr(code_edge, "code", None)
    if code_obj is None and edge_id is not None:
        code_obj = await read_models.code_model.one(code_package_code_id=UUID(edge_id))
    if code_obj is not None:
        relative_path = (
            _optional_text(getattr(code_obj, "relative_path", None)) or relative_path
        )
    source_text = await _source_text_for_code(
        code_obj=code_obj,
        read_models=read_models,
    )
    sections = await _sections_for_code(code_obj=code_obj, read_models=read_models)
    selector_key = relative_path or _optional_uuid_text(getattr(code_obj, "id", None))
    selector_key = selector_key or edge_id or package.selector_key
    return CodeReplicaCodeSnapshotV1(
        selector_key=selector_key,
        code_id=_optional_uuid_text(getattr(code_obj, "id", None)),
        code_package_code_id=edge_id,
        code_package_id=package.code_package_id,
        package_name=package.package_name,
        relative_path=relative_path,
        language=_enum_text(
            getattr(code_obj, "language", None)
            if code_obj is not None
            else getattr(code_edge, "language", None)
        ),
        path_role=_enum_text(getattr(code_edge, "path_role", None)),
        source_hash=_source_hash(source_text),
        source_text=source_text,
        label=relative_path,
        sections=sections,
        metadata={
            "package_selector_key": package.selector_key,
            "source_kind": "ontology_replica",
        },
    )


async def _source_text_for_code(
    *,
    code_obj: object | None,
    read_models: CodeReplicaReadModels,
) -> str | None:
    if code_obj is None:
        return None
    content_part_text = getattr(code_obj, "content_part_text", None)
    content_part_text_id = getattr(code_obj, "content_part_text_id", None)
    if content_part_text is None and content_part_text_id is not None:
        content_part_text = await read_models.content_part_text_model.by_id(
            content_part_text_id
        )
    return _optional_source_text(getattr(content_part_text, "inline_text", None))


async def _sections_for_code(
    *,
    code_obj: object | None,
    read_models: CodeReplicaReadModels,
) -> list[CodeReplicaSectionSnapshotV1]:
    if code_obj is None or getattr(code_obj, "id", None) is None:
        return []
    sections = list(await read_models.code_section_model.many(code_id=code_obj.id))
    snapshots = [_section_snapshot(section) for section in sections]
    snapshots.sort(
        key=lambda item: (
            item.byte_start if item.byte_start is not None else -1,
            item.section_key,
        )
    )
    return snapshots


def _package_snapshot(package_obj: object) -> CodeReplicaPackageSnapshotV1:
    package_id = _required_uuid_text(getattr(package_obj, "id", None))
    manifest_relative_path = _optional_text(
        getattr(package_obj, "manifest_relative_path", None)
    )
    package_name = _optional_text(getattr(package_obj, "package_name", None))
    selector_key = manifest_relative_path or package_name or package_id
    return CodeReplicaPackageSnapshotV1(
        selector_key=selector_key,
        code_package_id=package_id,
        package_name=package_name,
        package_root=_optional_text(getattr(package_obj, "package_root", None)),
        manifest_relative_path=manifest_relative_path,
        package_fqn=_optional_text(getattr(package_obj, "fqn_prefix", None)),
        language=_enum_text(getattr(package_obj, "language", None)),
        surface=_optional_text(getattr(package_obj, "surface", None)),
        metadata={"source_kind": "ontology_replica"},
    )


def _section_snapshot(section_obj: object) -> CodeReplicaSectionSnapshotV1:
    section_key = _optional_text(getattr(section_obj, "section_key", None))
    section_key = section_key or _required_uuid_text(getattr(section_obj, "id", None))
    return CodeReplicaSectionSnapshotV1(
        section_key=section_key,
        section_kind=_enum_text(getattr(section_obj, "type", None)),
        stable_identity=_optional_text(getattr(section_obj, "identity_hash", None)),
        byte_start=_optional_int(getattr(section_obj, "byte_start", None)),
        byte_end=_optional_int(getattr(section_obj, "byte_end", None)),
        label=_optional_text(getattr(section_obj, "qualname", None)) or section_key,
        metadata=_json_object(getattr(section_obj, "metadata", None)),
    )


def _selected_package_snapshot(
    *,
    packages: list[CodeReplicaPackageSnapshotV1],
    selected_package_key: str | None,
) -> CodeReplicaPackageSnapshotV1 | None:
    if selected_package_key is None:
        return None
    return next(
        (
            package
            for package in packages
            if selected_package_key
            in {
                package.selector_key,
                package.code_package_id,
                package.package_name,
                package.manifest_relative_path,
            }
        ),
        None,
    )


def _selected_code_snapshot(
    *,
    codes: list[CodeReplicaCodeSnapshotV1],
    selected_code_key: str | None,
) -> CodeReplicaCodeSnapshotV1 | None:
    if selected_code_key is None:
        return None
    return next(
        (
            code
            for code in codes
            if selected_code_key
            in {
                code.selector_key,
                code.code_id,
                code.code_package_code_id,
                code.relative_path,
            }
        ),
        None,
    )


def _selector_package(
    package: CodeReplicaPackageSnapshotV1,
) -> CodePackageSelectorPackageV1:
    return CodePackageSelectorPackageV1(
        selector_key=package.selector_key,
        code_package_id=package.code_package_id,
        code_package_name=package.package_name,
        package_root=package.package_root,
        manifest_path=package.manifest_relative_path,
        package_fqn=package.package_fqn,
        provider_key="aware_code",
        metadata={
            **package.metadata,
            "language": package.language,
            "surface": package.surface,
        },
    )


def _selector_code(code: CodeReplicaCodeSnapshotV1) -> CodePackageSelectorCodeV1:
    return CodePackageSelectorCodeV1(
        selector_key=code.selector_key,
        code_id=code.code_id,
        code_package_code_id=code.code_package_code_id,
        code_package_id=code.code_package_id,
        relative_path=code.relative_path,
        language=code.language,
        source_hash=code.source_hash,
        label=code.label,
        metadata={**code.metadata, "path_role": code.path_role},
    )


def _source_ref(code: CodeReplicaCodeSnapshotV1) -> CodeSourceRefV1:
    return CodeSourceRefV1(
        source_key=code.selector_key,
        code_id=code.code_id,
        code_package_id=code.code_package_id,
        code_package_code_id=code.code_package_code_id,
        package_name=code.package_name,
        relative_path=code.relative_path,
        language=code.language,
        source_hash=code.source_hash,
        metadata={**code.metadata, "path_role": code.path_role},
    )


def _section_anchor(section: CodeReplicaSectionSnapshotV1) -> CodeSectionAnchorV1:
    return CodeSectionAnchorV1(
        section_key=section.section_key,
        section_kind=section.section_kind,
        stable_identity=section.stable_identity,
        byte_start=section.byte_start,
        byte_end=section.byte_end,
        label=section.label,
        metadata=section.metadata,
    )


def _api_view_package(
    package: CodeReplicaPackageSnapshotV1,
) -> CodeViewStatePackage:
    return CodeViewStatePackage(
        selector_key=package.selector_key,
        code_package_id=package.code_package_id,
        code_package_name=package.package_name,
        package_root=package.package_root,
        manifest_path=package.manifest_relative_path,
        package_fqn=package.package_fqn,
        provider_key="aware_code",
        language=package.language,
        surface=package.surface,
        metadata=package.metadata,
    )


def _api_view_code(code: CodeReplicaCodeSnapshotV1) -> CodeViewStateCode:
    return CodeViewStateCode(
        selector_key=code.selector_key,
        code_id=code.code_id,
        code_package_code_id=code.code_package_code_id,
        code_package_id=code.code_package_id,
        code_package_name=code.package_name,
        relative_path=code.relative_path,
        language=code.language,
        path_role=code.path_role,
        source_hash=code.source_hash,
        label=code.label,
        metadata=code.metadata,
    )


def _api_source_ref(code: CodeReplicaCodeSnapshotV1) -> CodeViewStateSourceRef:
    return CodeViewStateSourceRef(
        source_key=code.selector_key,
        code_id=code.code_id,
        code_package_id=code.code_package_id,
        code_package_code_id=code.code_package_code_id,
        package_name=code.package_name,
        relative_path=code.relative_path,
        language=code.language,
        source_hash=code.source_hash,
        metadata={**code.metadata, "path_role": code.path_role},
    )


def _api_section_anchor(
    section: CodeReplicaSectionSnapshotV1,
) -> CodeViewStateSectionAnchor:
    return CodeViewStateSectionAnchor(
        section_key=section.section_key,
        section_kind=section.section_kind,
        stable_identity=section.stable_identity,
        byte_start=section.byte_start,
        byte_end=section.byte_end,
        label=section.label,
        metadata=section.metadata,
    )


def _api_provenance(
    *,
    snapshot: CodeReplicaLatestSnapshotV1,
    package_count: int,
    code_count: int,
) -> dict[str, Any]:
    return {
        "source_kind": snapshot.source_kind,
        "branch_id": snapshot.branch_id,
        "package_count": package_count,
        "code_count": code_count,
    }


def _count_summary(items: list[object], *, singular: str, plural: str) -> str:
    count = len(items)
    noun = singular if count == 1 else plural
    return f"{count} {noun}"


def _source_hash(source_text: str | None) -> str | None:
    if source_text is None:
        return None
    return "sha256:" + sha256(source_text.encode("utf-8")).hexdigest()


def _enum_text(value: object) -> str | None:
    raw_value = getattr(value, "value", value)
    return _optional_text(raw_value)


def _optional_uuid_text(value: object) -> str | None:
    if isinstance(value, UUID):
        return str(value)
    return _optional_text(value)


def _required_uuid_text(value: object) -> str:
    text = _optional_uuid_text(value)
    if text is None:
        raise ValueError("Code replica snapshot requires model id.")
    return text


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_source_text(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _json_object(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


__all__ = [
    "CodeReplicaCodeSnapshotV1",
    "CodeReplicaLatestSnapshotV1",
    "CodeReplicaPackageSnapshotV1",
    "CodeReplicaReadModels",
    "CodeReplicaSectionSnapshotV1",
    "code_editor_view_state_from_ontology_replica",
    "code_package_selector_view_state_from_ontology_replica",
    "read_code_latest_snapshot_from_ontology_replica",
    "resolve_code_editor_view_response_from_ontology_replica",
    "resolve_code_package_selector_view_response_from_ontology_replica",
]
