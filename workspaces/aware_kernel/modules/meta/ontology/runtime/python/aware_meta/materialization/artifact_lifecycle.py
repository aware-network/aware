from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from pathlib import Path
import re
from typing import Mapping

from aware_meta.semantic_contract import (
    META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
    META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_FILENAME,
    META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY,
    META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_REQUIRED_FOR,
    META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
    META_OBJECT_CONFIG_GRAPH_OWNER,
)


_META_PROVIDER_KEY = "aware_meta"
_LIFECYCLE_RECEIPT_SCHEMA = (
    "aware.meta.language_materialization.lifecycle_receipt.v1"
)
_LIFECYCLE_RECEIPT_RUNTIME_CONTRACT_VERSION = (
    "aware.meta.language_materialization.lifecycle_receipt.v1"
)


class LanguageMaterializationArtifactChangeKind(str, Enum):
    """Canonical file-level mutation taxonomy for language materializations."""

    create = "create"
    update = "update"
    delete = "delete"


class LanguageMaterializationArtifactKind(str, Enum):
    """Canonical artifact classification for language materialization outcomes."""

    source_code = "source_code"
    generated_support = "generated_support"
    manifest = "manifest"
    catalog = "catalog"
    schema = "schema"
    package_metadata = "package_metadata"
    embedded_artifact = "embedded_artifact"


class LanguageMaterializationProducerStep(str, Enum):
    """Producer step that last produced the reported artifact mutation."""

    render = "render"
    format_ = "format"
    package_build = "package_build"
    post_step = "post_step"
    manifest_write = "manifest_write"
    artifact_embed = "artifact_embed"
    stale_prune = "stale_prune"


class LanguageMaterializationStageability(str, Enum):
    """Downstream staging policy for a reported artifact mutation."""

    stage = "stage"
    review = "review"
    skip = "skip"


@dataclass(frozen=True, slots=True)
class LanguageMaterializationFileSnapshot:
    exists: bool
    hash_value: str | None
    size_bytes: int | None


@dataclass(slots=True)
class _LanguageMaterializationArtifactMutation:
    before: LanguageMaterializationFileSnapshot
    producer_step: LanguageMaterializationProducerStep
    artifact_kind: LanguageMaterializationArtifactKind
    package_name: str | None = None
    ownership_receipt: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class LanguageMaterializationArtifactChange:
    repo_rel_path: Path
    materialization_rel_path: Path | None = None
    package_rel_path: Path | None = None
    package_name: str | None = None
    change_kind: LanguageMaterializationArtifactChangeKind = (
        LanguageMaterializationArtifactChangeKind.update
    )
    artifact_kind: LanguageMaterializationArtifactKind = (
        LanguageMaterializationArtifactKind.generated_support
    )
    producer_step: LanguageMaterializationProducerStep = (
        LanguageMaterializationProducerStep.render
    )
    stageability: LanguageMaterializationStageability = (
        LanguageMaterializationStageability.stage
    )
    stageability_reason: str | None = None
    hash_before: str | None = None
    hash_after: str | None = None
    bytes_before: int | None = None
    bytes_after: int | None = None
    ownership_receipt: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class LanguageMaterializationPackageOutcome:
    package_name: str
    output_root: Path
    import_root: str | None = None
    artifact_change_refs: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class LanguageMaterializationOutcomeSummary:
    changes_total: int = 0
    changes_by_kind: Mapping[str, int] = field(default_factory=dict)
    changes_by_producer_step: Mapping[str, int] = field(default_factory=dict)
    changes_by_stageability: Mapping[str, int] = field(default_factory=dict)
    package_count: int = 0
    warning_count: int = 0


@dataclass(frozen=True, slots=True)
class LanguageMaterializationArtifactLifecycleResult:
    artifact_changes: tuple[LanguageMaterializationArtifactChange, ...] = ()
    package_outcomes: tuple[LanguageMaterializationPackageOutcome, ...] = ()
    summary: LanguageMaterializationOutcomeSummary = field(
        default_factory=LanguageMaterializationOutcomeSummary
    )


@dataclass(frozen=True, slots=True)
class LanguageMaterializationArtifactLifecycleReceipt:
    path: Path
    payload: Mapping[str, object]
    content_bytes: bytes
    sha256: str
    size_bytes: int
    ownership_receipt: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class LanguageMaterializationArtifactMutationRecord:
    path: Path
    before: LanguageMaterializationFileSnapshot
    producer_step: LanguageMaterializationProducerStep
    artifact_kind: LanguageMaterializationArtifactKind
    package_name: str | None = None
    ownership_receipt: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class LanguageMaterializationArtifactLifecycleBuildRequest:
    aware_root: Path
    materialization_output_root: Path
    package_roots_by_name: Mapping[str, Path]
    package_import_roots: Mapping[str, str | None]
    mutation_records: tuple[
        LanguageMaterializationArtifactMutationRecord, ...
    ] = ()
    warning_count: int = 0


class LanguageMaterializationArtifactTracker:
    """Meta-owned lifecycle tracker for materialized language artifacts."""

    def __init__(self) -> None:
        self._mutations: dict[Path, _LanguageMaterializationArtifactMutation] = {}

    def remember_mutation(
        self,
        *,
        path: Path,
        before: LanguageMaterializationFileSnapshot,
        producer_step: LanguageMaterializationProducerStep,
        artifact_kind: LanguageMaterializationArtifactKind,
        package_name: str | None = None,
        ownership_receipt: Mapping[str, object] | None = None,
    ) -> None:
        resolved = Path(path).resolve()
        existing = self._mutations.get(resolved)
        if existing is None:
            self._mutations[resolved] = _LanguageMaterializationArtifactMutation(
                before=before,
                producer_step=producer_step,
                artifact_kind=artifact_kind,
                package_name=package_name,
                ownership_receipt=ownership_receipt,
            )
            return
        existing.producer_step = producer_step
        existing.artifact_kind = artifact_kind
        if package_name is not None:
            existing.package_name = package_name
        if ownership_receipt is not None:
            existing.ownership_receipt = ownership_receipt

    def record_direct_write(
        self,
        *,
        path: Path,
        producer_step: LanguageMaterializationProducerStep,
        artifact_kind: LanguageMaterializationArtifactKind,
        package_name: str | None = None,
        ownership_receipt: Mapping[str, object] | None = None,
    ) -> None:
        self.remember_mutation(
            path=path,
            before=language_materialization_snapshot_file(path),
            producer_step=producer_step,
            artifact_kind=artifact_kind,
            package_name=package_name,
            ownership_receipt=ownership_receipt,
        )

    def build_result(
        self,
        *,
        aware_root: Path,
        materialization_output_root: Path,
        package_roots_by_name: Mapping[str, Path],
        package_import_roots: Mapping[str, str | None],
        warning_count: int = 0,
    ) -> LanguageMaterializationArtifactLifecycleResult:
        artifact_changes = tuple(
            self._build_artifact_changes(
                aware_root=aware_root,
                materialization_output_root=materialization_output_root,
                package_roots_by_name=package_roots_by_name,
            )
        )
        package_outcomes = tuple(
            _build_package_outcomes(
                aware_root=aware_root,
                package_roots_by_name=package_roots_by_name,
                package_import_roots=package_import_roots,
                artifact_changes=artifact_changes,
            )
        )
        return LanguageMaterializationArtifactLifecycleResult(
            artifact_changes=artifact_changes,
            package_outcomes=package_outcomes,
            summary=_summarize_artifact_changes(
                artifact_changes=artifact_changes,
                package_count=len(package_outcomes),
                warning_count=warning_count,
            ),
        )

    def _build_artifact_changes(
        self,
        *,
        aware_root: Path,
        materialization_output_root: Path,
        package_roots_by_name: Mapping[str, Path],
    ) -> tuple[LanguageMaterializationArtifactChange, ...]:
        changes: list[LanguageMaterializationArtifactChange] = []
        for path, mutation in sorted(
            self._mutations.items(),
            key=lambda item: item[0].as_posix(),
        ):
            after = language_materialization_snapshot_file(path)
            before = mutation.before
            if not before.exists and not after.exists:
                continue
            if not before.exists and after.exists:
                change_kind = LanguageMaterializationArtifactChangeKind.create
            elif before.exists and not after.exists:
                change_kind = LanguageMaterializationArtifactChangeKind.delete
            elif (
                before.hash_value != after.hash_value
                or before.size_bytes != after.size_bytes
            ):
                change_kind = LanguageMaterializationArtifactChangeKind.update
            else:
                continue

            stageability, stageability_reason = language_materialization_stageability(
                aware_root=aware_root,
                path=path,
            )
            package_name = mutation.package_name
            package_root = (
                package_roots_by_name.get(package_name)
                if package_name is not None
                else None
            )
            changes.append(
                LanguageMaterializationArtifactChange(
                    repo_rel_path=language_materialization_repo_identity_path(
                        aware_root=aware_root,
                        path=path,
                    ),
                    materialization_rel_path=language_materialization_path_relative_to(
                        path,
                        materialization_output_root,
                    ),
                    package_rel_path=(
                        language_materialization_path_relative_to(path, package_root)
                        if package_root is not None
                        else None
                    ),
                    package_name=package_name,
                    change_kind=change_kind,
                    artifact_kind=mutation.artifact_kind,
                    producer_step=mutation.producer_step,
                    stageability=stageability,
                    stageability_reason=stageability_reason,
                    hash_before=before.hash_value,
                    hash_after=after.hash_value,
                    bytes_before=before.size_bytes,
                    bytes_after=after.size_bytes,
                    ownership_receipt=mutation.ownership_receipt,
                )
            )
        return tuple(changes)


def language_materialization_artifact_mutation_record(
    *,
    path: Path,
    before: LanguageMaterializationFileSnapshot,
    producer_step: LanguageMaterializationProducerStep,
    artifact_kind: LanguageMaterializationArtifactKind,
    package_name: str | None = None,
    ownership_receipt: Mapping[str, object] | None = None,
) -> LanguageMaterializationArtifactMutationRecord:
    return LanguageMaterializationArtifactMutationRecord(
        path=Path(path).resolve(),
        before=before,
        producer_step=producer_step,
        artifact_kind=artifact_kind,
        package_name=package_name,
        ownership_receipt=ownership_receipt,
    )


def language_materialization_direct_write_mutation_record(
    *,
    path: Path,
    producer_step: LanguageMaterializationProducerStep,
    artifact_kind: LanguageMaterializationArtifactKind,
    package_name: str | None = None,
    ownership_receipt: Mapping[str, object] | None = None,
) -> LanguageMaterializationArtifactMutationRecord:
    return language_materialization_artifact_mutation_record(
        path=path,
        before=language_materialization_snapshot_file(path),
        producer_step=producer_step,
        artifact_kind=artifact_kind,
        package_name=package_name,
        ownership_receipt=ownership_receipt,
    )


def build_language_materialization_artifact_lifecycle(
    request: LanguageMaterializationArtifactLifecycleBuildRequest,
) -> LanguageMaterializationArtifactLifecycleResult:
    tracker = LanguageMaterializationArtifactTracker()
    for record in request.mutation_records:
        tracker.remember_mutation(
            path=record.path,
            before=record.before,
            producer_step=record.producer_step,
            artifact_kind=record.artifact_kind,
            package_name=record.package_name,
            ownership_receipt=record.ownership_receipt,
        )
    return tracker.build_result(
        aware_root=request.aware_root,
        materialization_output_root=request.materialization_output_root,
        package_roots_by_name=request.package_roots_by_name,
        package_import_roots=request.package_import_roots,
        warning_count=request.warning_count,
    )


def build_language_materialization_artifact_lifecycle_receipt(
    *,
    aware_root: Path,
    path: Path,
    lifecycle_result: LanguageMaterializationArtifactLifecycleResult,
    target_language_plugin_id: str,
    materialization_name: str,
    source_kind: str,
    source_package_name: str | None = None,
    package_name: str | None = None,
    package_output_root: Path | None = None,
    package_import_root: str | None = None,
    package_rel_path: Path | None = None,
    manifest_path: Path | None = None,
    producer_step: str = LanguageMaterializationProducerStep.manifest_write.value,
    source_code_package_id: object | None = None,
    object_config_graph_package_id: object | None = None,
    object_config_graph_commit_id: object | None = None,
    source_object_instance_graph_commit_id: object | None = None,
    input_object_instance_graph_commit_id: object | None = None,
) -> LanguageMaterializationArtifactLifecycleReceipt:
    resolved_path = Path(path).resolve()
    repo_rel_path = language_materialization_repo_identity_path(
        aware_root=aware_root,
        path=resolved_path,
    )
    receipt_package_rel_path = (
        package_rel_path.as_posix() if package_rel_path is not None else None
    )
    receipt_manifest_path = (
        manifest_path if manifest_path is not None else package_rel_path
    )
    receipt_manifest_rel_path = (
        receipt_manifest_path.as_posix()
        if receipt_manifest_path is not None
        else None
    )
    payload = {
        "schema": _LIFECYCLE_RECEIPT_SCHEMA,
        "provider_key": _META_PROVIDER_KEY,
        "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
        "producer_key": META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        "output_key": META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY,
        "artifact_family": META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
        "artifact_role": "lifecycle_receipt",
        "output_kind": "materialization_lifecycle_receipt",
        "status": "available",
        "target_language_plugin_id": target_language_plugin_id,
        "materialization": {
            "name": materialization_name,
            "source_kind": source_kind,
            "source_package_name": source_package_name,
        },
        "package": {
            "name": package_name,
            "output_root": (
                language_materialization_repo_identity_path(
                    aware_root=aware_root,
                    path=package_output_root,
                ).as_posix()
                if package_output_root is not None
                else None
            ),
            "import_root": package_import_root,
            "receipt_path": repo_rel_path.as_posix(),
            "receipt_package_rel_path": receipt_package_rel_path,
            "receipt_manifest_path": receipt_manifest_rel_path,
        },
        "provenance": {
            "source_code_package_id": _stable_scalar(source_code_package_id),
            "object_config_graph_package_id": _stable_scalar(
                object_config_graph_package_id
            ),
            "object_config_graph_commit_id": _stable_scalar(
                object_config_graph_commit_id
            ),
            "source_object_instance_graph_commit_id": _stable_scalar(
                source_object_instance_graph_commit_id
            ),
            "input_object_instance_graph_commit_id": _stable_scalar(
                input_object_instance_graph_commit_id
            ),
        },
        "required_for": sorted(
            META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_REQUIRED_FOR
        ),
        "summary": _summary_payload(lifecycle_result.summary),
        "package_outcomes": [
            _package_outcome_payload(outcome)
            for outcome in sorted(
                lifecycle_result.package_outcomes,
                key=lambda item: item.package_name,
            )
        ],
        "artifact_changes": [
            _artifact_change_payload(
                aware_root=aware_root,
                change=change,
            )
            for change in sorted(
                lifecycle_result.artifact_changes,
                key=lambda item: item.repo_rel_path.as_posix(),
            )
        ],
    }
    content_bytes = _stable_json_bytes(payload)
    digest = sha256(content_bytes).hexdigest()
    ownership_receipt = {
        "producer_provider_key": _META_PROVIDER_KEY,
        "semantic_owner": META_OBJECT_CONFIG_GRAPH_OWNER,
        "producer_key": META_LANGUAGE_MATERIALIZATION_PRODUCER_KEY,
        "producer_kind": "semantic_materializer",
        "output_key": META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY,
        "artifact_key": _lifecycle_receipt_artifact_key(
            target_language_plugin_id=target_language_plugin_id,
            package_name=package_name,
            repo_rel_path=repo_rel_path,
        ),
        "artifact_family": META_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY,
        "artifact_role": "lifecycle_receipt",
        "output_kind": "materialization_lifecycle_receipt",
        "target_language_plugin_id": target_language_plugin_id,
        "status": "available",
        "producer_step": producer_step,
        "package_name": package_name,
        "package_output_key": None,
        "required_for": sorted(
            META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_REQUIRED_FOR
        ),
        "path": resolved_path.as_posix(),
        "manifest_path": receipt_manifest_rel_path,
        "digest": digest,
        "digest_algorithm": "sha256",
        "size_bytes": len(content_bytes),
        "source_code_package_id": _stable_scalar(source_code_package_id),
        "object_config_graph_package_id": _stable_scalar(
            object_config_graph_package_id
        ),
        "object_config_graph_commit_id": _stable_scalar(
            object_config_graph_commit_id
        ),
        "source_object_instance_graph_commit_id": _stable_scalar(
            source_object_instance_graph_commit_id
        ),
        "input_object_instance_graph_commit_id": _stable_scalar(
            input_object_instance_graph_commit_id
        ),
        "runtime_contract_version": _LIFECYCLE_RECEIPT_RUNTIME_CONTRACT_VERSION,
        "provider_payload": {
            "receipt_schema": _LIFECYCLE_RECEIPT_SCHEMA,
            "receipt_path": repo_rel_path.as_posix(),
            "receipt_package_rel_path": receipt_package_rel_path,
            "receipt_manifest_path": receipt_manifest_rel_path,
            "summary_changes_total": lifecycle_result.summary.changes_total,
            "summary_package_count": lifecycle_result.summary.package_count,
        },
    }
    return LanguageMaterializationArtifactLifecycleReceipt(
        path=resolved_path,
        payload=payload,
        content_bytes=content_bytes,
        sha256=digest,
        size_bytes=len(content_bytes),
        ownership_receipt=ownership_receipt,
    )


def build_object_config_graph_package_language_lifecycle_receipts(
    *,
    aware_root: Path,
    aware_toml_path: Path,
    package_name: str,
    source_code_package_id: object | None,
    object_config_graph_package_id: object | None,
    object_config_graph_commit_id: object | None,
    source_object_instance_graph_commit_id: object | None,
    input_object_instance_graph_commit_id: object | None,
) -> tuple[LanguageMaterializationArtifactLifecycleReceipt, ...]:
    source_kind = _source_kind_from_aware_toml_path(aware_toml_path)
    receipt_path = _lifecycle_receipt_cache_path(
        aware_root=aware_root,
        source_kind=source_kind,
        package_name=package_name,
    )
    package_output_root = _python_package_output_root(
        aware_toml_path=aware_toml_path,
        package_name=package_name,
    )
    lifecycle_result = build_language_materialization_artifact_lifecycle(
        LanguageMaterializationArtifactLifecycleBuildRequest(
            aware_root=aware_root,
            materialization_output_root=(
                package_output_root
                if package_output_root is not None
                else aware_toml_path.parent
            ),
            package_roots_by_name=(
                {package_name: package_output_root}
                if package_output_root is not None
                else {}
            ),
            package_import_roots={package_name: _python_import_root(package_output_root)},
            mutation_records=(),
            warning_count=0,
        )
    )
    receipt = build_language_materialization_artifact_lifecycle_receipt(
        aware_root=aware_root,
        path=receipt_path,
        lifecycle_result=lifecycle_result,
        target_language_plugin_id="python",
        materialization_name="materialize",
        source_kind=source_kind,
        source_package_name=package_name,
        package_name=package_name,
        package_output_root=package_output_root,
        package_import_root=_python_import_root(package_output_root),
        manifest_path=(
            aware_toml_path.relative_to(aware_root)
            if _is_relative_to(aware_toml_path, aware_root)
            else aware_toml_path
        ),
        source_code_package_id=source_code_package_id,
        object_config_graph_package_id=object_config_graph_package_id,
        object_config_graph_commit_id=object_config_graph_commit_id,
        source_object_instance_graph_commit_id=source_object_instance_graph_commit_id,
        input_object_instance_graph_commit_id=input_object_instance_graph_commit_id,
    )
    receipt.path.parent.mkdir(parents=True, exist_ok=True)
    receipt.path.write_bytes(receipt.content_bytes)
    return (receipt,)


def _lifecycle_receipt_cache_path(
    *,
    aware_root: Path,
    source_kind: str,
    package_name: str,
) -> Path:
    return (
        aware_root
        / ".aware"
        / "materializations"
        / "lifecycle_receipts"
        / _cache_path_segment(source_kind, fallback="source")
        / "materialize"
        / "python"
        / _cache_path_segment(package_name, fallback="package")
        / META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_FILENAME
    )


def _source_kind_from_aware_toml_path(path: Path) -> str:
    parent_name = path.parent.name.strip()
    return parent_name or "source"


def _cache_path_segment(raw: str | None, *, fallback: str) -> str:
    value = (raw or "").strip()
    if not value:
        return fallback
    segment = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return segment or fallback


def _python_package_output_root(
    *,
    aware_toml_path: Path,
    package_name: str,
) -> Path | None:
    python_root = aware_toml_path.parent / "python"
    if not python_root.is_dir():
        return None
    candidates = tuple(
        path.parent
        for path in sorted(python_root.glob("*/pyproject.toml"))
        if path.is_file()
    )
    if len(candidates) == 1:
        return candidates[0]
    normalized_package_name = package_name.replace("-", "_")
    named = tuple(
        candidate
        for candidate in candidates
        if candidate.name == normalized_package_name
        or candidate.name.endswith("_" + normalized_package_name)
    )
    if len(named) == 1:
        return named[0]
    return None


def _python_import_root(package_output_root: Path | None) -> str | None:
    return package_output_root.name if package_output_root is not None else None


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def language_materialization_snapshot_file(
    path: Path,
) -> LanguageMaterializationFileSnapshot:
    path = Path(path).resolve()
    if not path.exists() or path.is_dir():
        return LanguageMaterializationFileSnapshot(
            exists=False,
            hash_value=None,
            size_bytes=None,
        )
    try:
        payload = path.read_bytes()
    except Exception:
        try:
            size_bytes = path.stat().st_size
        except Exception:
            size_bytes = None
        return LanguageMaterializationFileSnapshot(
            exists=True,
            hash_value=None,
            size_bytes=size_bytes,
        )
    return LanguageMaterializationFileSnapshot(
        exists=True,
        hash_value=sha256(payload).hexdigest(),
        size_bytes=len(payload),
    )


def language_materialization_path_relative_to(
    path: Path,
    root: Path | None,
) -> Path | None:
    if root is None:
        return None
    try:
        return Path(path).resolve().relative_to(Path(root).resolve())
    except Exception:
        return None


def language_materialization_repo_identity_path(
    *,
    aware_root: Path,
    path: Path,
) -> Path:
    rel = language_materialization_path_relative_to(path, aware_root)
    if rel is not None:
        return rel
    return Path(path).resolve()


def language_materialization_classify_output_artifact_kind(
    path: Path,
) -> LanguageMaterializationArtifactKind:
    name = path.name
    lower_name = name.lower()
    suffix = path.suffix.lower()

    if lower_name in {
        "pyproject.toml",
        "pubspec.yaml",
        "package.json",
        "setup.py",
        "setup.cfg",
    }:
        return LanguageMaterializationArtifactKind.package_metadata
    if name.endswith((".g.dart", ".freezed.dart")) or lower_name == "py.typed":
        return LanguageMaterializationArtifactKind.generated_support
    if suffix in {".py", ".pyi", ".dart", ".sql"}:
        return LanguageMaterializationArtifactKind.source_code
    if suffix in {".json", ".toml", ".yaml", ".yml"}:
        return LanguageMaterializationArtifactKind.generated_support
    return LanguageMaterializationArtifactKind.generated_support


def language_materialization_stageability(
    *,
    aware_root: Path,
    path: Path,
) -> tuple[LanguageMaterializationStageability, str | None]:
    internal_roots = (
        Path(aware_root).resolve() / ".aware",
        Path(aware_root).resolve() / "_aware",
    )
    resolved = Path(path).resolve()
    for internal_root in internal_roots:
        if language_materialization_path_relative_to(resolved, internal_root) is not None:
            return (
                LanguageMaterializationStageability.skip,
                "internal compiler/runtime artifact outside canonical staging output",
            )
    return LanguageMaterializationStageability.stage, None


def _build_package_outcomes(
    *,
    aware_root: Path,
    package_roots_by_name: Mapping[str, Path],
    package_import_roots: Mapping[str, str | None],
    artifact_changes: tuple[LanguageMaterializationArtifactChange, ...],
) -> tuple[LanguageMaterializationPackageOutcome, ...]:
    outcomes: list[LanguageMaterializationPackageOutcome] = []
    for package_name, package_root in sorted(package_roots_by_name.items()):
        package_change_refs = tuple(
            change.repo_rel_path
            for change in artifact_changes
            if change.package_name == package_name
        )
        outcomes.append(
            LanguageMaterializationPackageOutcome(
                package_name=package_name,
                output_root=language_materialization_repo_identity_path(
                    aware_root=aware_root,
                    path=package_root,
                ),
                import_root=package_import_roots.get(package_name),
                artifact_change_refs=package_change_refs,
            )
        )
    return tuple(outcomes)


def _summarize_artifact_changes(
    *,
    artifact_changes: tuple[LanguageMaterializationArtifactChange, ...],
    package_count: int,
    warning_count: int,
) -> LanguageMaterializationOutcomeSummary:
    changes_by_kind: dict[str, int] = {}
    changes_by_producer_step: dict[str, int] = {}
    changes_by_stageability: dict[str, int] = {}
    for change in artifact_changes:
        kind_key = change.change_kind.value
        changes_by_kind[kind_key] = changes_by_kind.get(kind_key, 0) + 1
        producer_key = change.producer_step.value
        changes_by_producer_step[producer_key] = (
            changes_by_producer_step.get(producer_key, 0) + 1
        )
        stageability_key = change.stageability.value
        changes_by_stageability[stageability_key] = (
            changes_by_stageability.get(stageability_key, 0) + 1
        )

    return LanguageMaterializationOutcomeSummary(
        changes_total=len(artifact_changes),
        changes_by_kind=changes_by_kind,
        changes_by_producer_step=changes_by_producer_step,
        changes_by_stageability=changes_by_stageability,
        package_count=package_count,
        warning_count=warning_count,
    )


def _stable_json_bytes(payload: Mapping[str, object]) -> bytes:
    text = json.dumps(
        _canonical_value(payload),
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
    )
    if not text.endswith("\n"):
        text += "\n"
    return text.encode("utf-8")


def _summary_payload(
    summary: LanguageMaterializationOutcomeSummary,
) -> dict[str, object]:
    return {
        "changes_total": summary.changes_total,
        "changes_by_kind": dict(sorted(summary.changes_by_kind.items())),
        "changes_by_producer_step": dict(
            sorted(summary.changes_by_producer_step.items())
        ),
        "changes_by_stageability": dict(
            sorted(summary.changes_by_stageability.items())
        ),
        "package_count": summary.package_count,
        "warning_count": summary.warning_count,
    }


def _package_outcome_payload(
    outcome: LanguageMaterializationPackageOutcome,
) -> dict[str, object]:
    return {
        "package_name": outcome.package_name,
        "output_root": outcome.output_root.as_posix(),
        "import_root": outcome.import_root,
        "artifact_change_refs": sorted(
            path.as_posix() for path in outcome.artifact_change_refs
        ),
    }


def _artifact_change_payload(
    *,
    aware_root: Path,
    change: LanguageMaterializationArtifactChange,
) -> dict[str, object]:
    return {
        "repo_rel_path": change.repo_rel_path.as_posix(),
        "materialization_rel_path": (
            change.materialization_rel_path.as_posix()
            if change.materialization_rel_path is not None
            else None
        ),
        "package_rel_path": (
            change.package_rel_path.as_posix()
            if change.package_rel_path is not None
            else None
        ),
        "package_name": change.package_name,
        "change_kind": change.change_kind.value,
        "artifact_kind": change.artifact_kind.value,
        "producer_step": change.producer_step.value,
        "stageability": change.stageability.value,
        "stageability_reason": change.stageability_reason,
        "hash_before": change.hash_before,
        "hash_after": change.hash_after,
        "bytes_before": change.bytes_before,
        "bytes_after": change.bytes_after,
        "ownership_receipt": _ownership_receipt_lifecycle_payload(
            aware_root=aware_root,
            receipt=change.ownership_receipt,
        ),
    }


def _ownership_receipt_lifecycle_payload(
    *,
    aware_root: Path,
    receipt: Mapping[str, object] | None,
) -> object:
    if receipt is None:
        return None
    payload = dict(receipt)
    raw_path = payload.get("path")
    if isinstance(raw_path, str) and raw_path:
        payload["path"] = language_materialization_repo_identity_path(
            aware_root=aware_root,
            path=Path(raw_path),
        ).as_posix()
    return _canonical_value(payload)


def _canonical_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_value(item_value)
            for key, item_value in sorted(
                value.items(),
                key=lambda item: str(item[0]),
            )
        }
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_canonical_value(item) for item in value]
    return str(value)


def _stable_scalar(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _lifecycle_receipt_artifact_key(
    *,
    target_language_plugin_id: str,
    package_name: str | None,
    repo_rel_path: Path,
) -> str:
    parts = [
        target_language_plugin_id,
        META_LANGUAGE_MATERIALIZATION_LIFECYCLE_RECEIPT_OUTPUT_KEY,
    ]
    if package_name:
        parts.append(package_name)
    parts.append(repo_rel_path.as_posix())
    return ":".join(parts)


__all__ = [
    "LanguageMaterializationArtifactChange",
    "LanguageMaterializationArtifactChangeKind",
    "LanguageMaterializationArtifactKind",
    "LanguageMaterializationArtifactLifecycleBuildRequest",
    "LanguageMaterializationArtifactLifecycleReceipt",
    "LanguageMaterializationArtifactLifecycleResult",
    "LanguageMaterializationArtifactMutationRecord",
    "LanguageMaterializationArtifactTracker",
    "LanguageMaterializationFileSnapshot",
    "LanguageMaterializationOutcomeSummary",
    "LanguageMaterializationPackageOutcome",
    "LanguageMaterializationProducerStep",
    "LanguageMaterializationStageability",
    "build_object_config_graph_package_language_lifecycle_receipts",
    "build_language_materialization_artifact_lifecycle",
    "build_language_materialization_artifact_lifecycle_receipt",
    "language_materialization_artifact_mutation_record",
    "language_materialization_classify_output_artifact_kind",
    "language_materialization_direct_write_mutation_record",
    "language_materialization_path_relative_to",
    "language_materialization_repo_identity_path",
    "language_materialization_snapshot_file",
    "language_materialization_stageability",
]
