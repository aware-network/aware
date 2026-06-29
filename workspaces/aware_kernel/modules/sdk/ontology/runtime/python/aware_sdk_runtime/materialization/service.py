from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
import tomllib
from pathlib import Path
from pathlib import PurePosixPath
from time import perf_counter
from typing import Sequence, TypeVar, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_api_ontology.stable_ids import (
    stable_api_package_id,
)
from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_code.package.snapshot_commit import commit_code_package_text_snapshot
from aware_code.package_surface import (
    code_package_surface_from_semantic_manifest_descriptor,
)
from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage

from aware_sdk_runtime.manifest.spec import (
    AwareSdkCompilationMode,
    AwareSdkDependencyKind,
    AwareSdkTomlDartTargetSpec,
    AwareSdkTomlPythonTargetSpec,
    AwareSdkTomlSpec,
)
from aware_meta.manifest.loader import load_aware_toml_spec
from aware_meta_ontology.stable_ids import (
    stable_object_config_graph_id,
    stable_object_config_graph_package_id,
)
from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta_ontology.stable_ids import stable_object_instance_graph_commit_id
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.semantic_contract import META_MANIFEST_RESOLUTION
from ..builder import (
    SdkCompilePlan,
    build_sdk_compile_plan,
    encode_sdk_compile_plan,
)
from ..workspace import SdkWorkspace, SdkWorkspaceSnapshot
from .snapshot_commit import (
    SdkConfigManifestSnapshotCommitResult,
    SdkPackageDependencySnapshotRef,
    SdkPackageImplementationPackageSnapshotRef,
    SdkPackageObjectConfigGraphPackageSnapshotRef,
    commit_sdk_config_manifest_snapshot,
    commit_sdk_package_manifest_snapshot,
)
from aware_sdk_ontology.sdk.sdk_config import SdkConfig
from aware_sdk_ontology.sdk.sdk_package import SdkPackage
from aware_sdk_ontology.stable_ids import (
    stable_sdk_config_id,
    stable_sdk_package_id,
)
from aware_utils.logging import logger

_TRoot = TypeVar("_TRoot", SdkConfig, SdkPackage, CodePackage)

_SDK_IMPLEMENTATION_CODE_PACKAGE_EXCLUDED_PATH_PARTS = frozenset(
    {
        ".aware",
        "_aware",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
    }
)
_SDK_IMPLEMENTATION_CODE_PACKAGE_BRANCH_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware:sdk:semantic-materialization:implementation-code-package-branch",
)


@dataclass(frozen=True, slots=True)
class SdkPackageMaterializationSpec:
    sdk_toml_path: Path
    workspace_root: Path
    manifest_spec: AwareSdkTomlSpec
    package_name: str
    package_fqn_prefix: str
    sdk_config_name: str
    sdk_source_path: str
    source_files: tuple[str, ...]
    compile_plan: SdkCompilePlan
    compile_plan_payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class SdkOwnedObjectConfigGraphPackageMaterialization:
    manifest_path: Path
    manifest_relative_path: str
    role: str
    package_name: str
    package_fqn_prefix: str
    package_kind: str
    object_config_graph_package_id: UUID
    object_config_graph_id: UUID
    package_branch_id: UUID | None
    source_code_package_id: UUID | None
    object_config_graph_package_commit_id: UUID | None
    object_config_graph_package_head_commit_id: UUID | None
    object_config_graph_package_object_instance_graph_commit_id: UUID | None
    object_config_graph_commit_id: UUID | None
    object_config_graph_head_commit_id: UUID | None
    object_config_graph_object_instance_graph_commit_id: UUID | None
    language_materialization_targets: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class SdkImplementationCodePackageTarget:
    language: CodeLanguage
    package_name: str
    import_root: str
    package_root: Path
    manifest_path: Path
    sources_root: Path
    manifest_kind: str
    role: str
    include_paths: tuple[str, ...]
    exclude_paths: tuple[str, ...]
    entrypoint: str | None = None


@dataclass(frozen=True, slots=True)
class SdkImplementationCodePackageMaterialization:
    code_package: CodePackage
    branch_id: UUID
    domain_commit_id: UUID
    object_instance_graph_commit_id: UUID
    role: str
    include_paths: tuple[str, ...]
    exclude_paths: tuple[str, ...]
    entrypoint: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            "code_package_id": self.code_package.id,
            "source_code_package_id": self.code_package.id,
            "branch_id": self.branch_id,
            "domain_commit_id": self.domain_commit_id,
            "object_instance_graph_commit_id": self.object_instance_graph_commit_id,
            "package_name": self.code_package.package_name,
            "language": self.code_package.language.value,
            "manifest_relative_path": self.code_package.manifest_relative_path,
            "package_root": self.code_package.package_root,
            "sources_root": self.code_package.sources_root,
            "fqn_prefix": self.code_package.fqn_prefix,
            "role": self.role,
            "include_paths": list(self.include_paths),
            "exclude_paths": list(self.exclude_paths),
            "entrypoint": self.entrypoint,
        }


@dataclass(frozen=True, slots=True)
class SdkPackageMaterializationResult:
    sdk_toml_path: Path
    workspace_root: Path
    manifest_spec: AwareSdkTomlSpec
    sdk_config: SdkConfig
    sdk_package: SdkPackage
    sdk_source_path: str
    source_files: tuple[str, ...]
    phase_timings_s: Mapping[str, float]
    source_code_package_id: UUID | None
    sdk_config_commit_id: UUID | None
    sdk_config_object_instance_graph_commit_id: UUID | None
    package_commit_id: UUID | None
    package_head_commit_id: UUID | None
    api_package_ids: tuple[UUID, ...] = ()
    implementation_code_package_ids: tuple[UUID, ...] = ()
    implementation_code_package_refs: tuple[dict[str, object], ...] = ()
    object_config_graph_packages: tuple[
        SdkOwnedObjectConfigGraphPackageMaterialization, ...
    ] = ()
    sdk_package_dependency_ids: tuple[UUID, ...] = ()


def _round_duration_s(duration_s: float) -> float:
    return round(max(duration_s, 0.0), 6)


@contextmanager
def _record_phase(
    phase_timings_s: dict[str, float],
    phase_name: str,
) -> Iterator[None]:
    started_at = perf_counter()
    logger.info("SDK package materialization phase started: %s", phase_name)
    try:
        yield
    finally:
        duration_s = _round_duration_s(perf_counter() - started_at)
        phase_timings_s[phase_name] = duration_s
        logger.info(
            "SDK package materialization phase finished: %s (%.6fs)",
            phase_name,
            duration_s,
        )


def resolve_sdk_package_materialization_spec(
    *,
    sdk_toml_path: Path,
    workspace_root: Path,
    phase_timings_s: dict[str, float] | None = None,
) -> SdkPackageMaterializationSpec:
    timings = phase_timings_s if phase_timings_s is not None else {}
    with _record_phase(
        timings, "resolve_sdk_package_materialization_spec.resolve_paths"
    ):
        resolved_sdk_toml_path = sdk_toml_path.resolve()
        resolved_workspace_root = workspace_root.resolve()
    with _record_phase(
        timings, "resolve_sdk_package_materialization_spec.workspace_from_toml"
    ):
        workspace = SdkWorkspace.from_toml(
            toml_path=resolved_sdk_toml_path,
            repo_root=resolved_workspace_root,
        )
    with _record_phase(
        timings, "resolve_sdk_package_materialization_spec.build_snapshot"
    ):
        snapshot = workspace.build_snapshot()
    with _record_phase(
        timings, "resolve_sdk_package_materialization_spec.validate_build_mode"
    ):
        if snapshot.spec.build.compilation_mode != AwareSdkCompilationMode.sdk_ontology:
            raise RuntimeError(
                "SDK package materialization requires "
                + "[build].compilation_mode=`sdk_ontology`: "
                + str(resolved_sdk_toml_path)
            )
    with _record_phase(
        timings, "resolve_sdk_package_materialization_spec.build_sdk_compile_plan"
    ):
        compile_plan = build_sdk_compile_plan(snapshot=snapshot)
    with _record_phase(
        timings, "resolve_sdk_package_materialization_spec.validate_sdk_ownership"
    ):
        if len(compile_plan.sdk_configs) != 1:
            discovered_sdk_names = sorted(
                item.name for item in compile_plan.sdk_configs
            )
            raise RuntimeError(
                "SDK package materialization v0 requires exactly one canonical "
                + "`sdk` declaration per aware.sdk.toml package: "
                + f"sdk_toml_path={resolved_sdk_toml_path} "
                + f"discovered={discovered_sdk_names!r}"
            )
        canonical_sdk = compile_plan.sdk_configs[0]
    with _record_phase(
        timings, "resolve_sdk_package_materialization_spec.validate_package_fields"
    ):
        package_name = (snapshot.spec.sdk.package_name or "").strip()
        if not package_name:
            raise RuntimeError(
                "SDK package materialization requires non-empty "
                + "[sdk].package_name in aware.sdk.toml: "
                + str(resolved_sdk_toml_path)
            )
        package_fqn_prefix = (snapshot.spec.sdk.fqn_prefix or "").strip()
        if not package_fqn_prefix:
            raise RuntimeError(
                "SDK package materialization requires non-empty "
                + "[sdk].fqn_prefix in aware.sdk.toml: "
                + str(resolved_sdk_toml_path)
            )
    with _record_phase(
        timings,
        "resolve_sdk_package_materialization_spec.encode_sdk_compile_plan_payload",
    ):
        compile_plan_payload = encode_sdk_compile_plan(plan=compile_plan)
    with _record_phase(
        timings, "resolve_sdk_package_materialization_spec.assemble_result"
    ):
        return SdkPackageMaterializationSpec(
            sdk_toml_path=resolved_sdk_toml_path,
            workspace_root=resolved_workspace_root,
            manifest_spec=snapshot.spec,
            package_name=package_name,
            package_fqn_prefix=package_fqn_prefix,
            sdk_config_name=canonical_sdk.name,
            sdk_source_path=canonical_sdk.source_path,
            source_files=tuple(path.as_posix() for path in snapshot.source_files),
            compile_plan=compile_plan,
            compile_plan_payload=compile_plan_payload,
        )


async def materialize_sdk_package_from_manifest(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    sdk_toml_path: Path,
) -> SdkPackageMaterializationResult:
    materialization_started_at = perf_counter()
    phase_timings_s: dict[str, float] = {}
    with _record_phase(phase_timings_s, "resolve_sdk_package_materialization_spec"):
        spec = resolve_sdk_package_materialization_spec(
            sdk_toml_path=sdk_toml_path,
            workspace_root=workspace_root,
            phase_timings_s=phase_timings_s,
        )
    with _record_phase(phase_timings_s, "build_sdk_workspace_snapshot"):
        snapshot = SdkWorkspace.from_toml(
            toml_path=spec.sdk_toml_path,
            repo_root=spec.workspace_root,
        ).build_snapshot()
    sources_root = (snapshot.package_root / snapshot.spec.build.sources_dir).resolve()
    with _record_phase(phase_timings_s, "resolve_stable_ids"):
        expected_sdk_config_id = stable_sdk_config_id(name=spec.sdk_config_name)
        expected_sdk_package_id = stable_sdk_package_id(name=spec.package_name)
        source_code_package_config_id = _sdk_source_code_package_config_id()
        expected_source_code_package_id = stable_code_package_id(
            code_package_config_id=source_code_package_config_id,
            package_name=spec.package_name,
            language=CodeLanguage.aware.value,
        )
    with _record_phase(phase_timings_s, "resolve_projection_hashes"):
        sdk_config_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="SdkConfig",
        )
        sdk_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="SdkPackage",
        )
        code_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="CodePackage",
        )

    sdk_config_snapshot: SdkConfigManifestSnapshotCommitResult | None = None
    with _record_phase(phase_timings_s, "hydrate_sdk_config_from_head"):
        sdk_config = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=branch_id,
            projection_hash=sdk_config_projection_hash,
            root_id=expected_sdk_config_id,
            root_type=SdkConfig,
        )
    if sdk_config is None:
        with _record_phase(phase_timings_s, "build_sdk_config_manifest_truth"):
            canonical_sdk = spec.compile_plan.sdk_configs[0]
            sdk_config_snapshot = await commit_sdk_config_manifest_snapshot(
                index=index,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=sdk_config_projection_hash,
                name=canonical_sdk.name,
                title=spec.manifest_spec.sdk.title,
                description=(
                    canonical_sdk.description or spec.manifest_spec.sdk.description
                ),
                operations=canonical_sdk.operations,
            )
            sdk_config = sdk_config_snapshot.sdk_config
        with _record_phase(phase_timings_s, "rehydrate_sdk_config_from_head"):
            sdk_config = await _hydrate_lane_root_from_head(
                index=index,
                branch_id=branch_id,
                projection_hash=sdk_config_projection_hash,
                root_id=expected_sdk_config_id,
                root_type=SdkConfig,
            )
    if sdk_config is None:
        raise RuntimeError(
            "SDK package materialization could not hydrate canonical "
            + "SdkConfig after manifest materialization: "
            + f"sdk_config_name={spec.sdk_config_name!r}"
        )

    with _record_phase(phase_timings_s, "resolve_sdk_config_semantic_root_commit_id"):
        sdk_config_domain_head_commit_id = (
            sdk_config_snapshot.commit_id if sdk_config_snapshot is not None else None
        ) or (
            await _lane_head_commit_id(
                branch_id=branch_id,
                projection_hash=sdk_config_projection_hash,
            )
        )
        sdk_config_object_instance_graph_commit_id = (
            sdk_config_snapshot.object_instance_graph_commit_id
            if sdk_config_snapshot is not None
            else None
        ) or (
            await _object_instance_graph_commit_id_from_domain_commit(
                branch_id=branch_id,
                projection_hash=sdk_config_projection_hash,
                domain_commit_id=sdk_config_domain_head_commit_id,
            )
            if sdk_config_domain_head_commit_id is not None
            else None
        )
    if sdk_config_object_instance_graph_commit_id is None:
        raise RuntimeError(
            "SDK package materialization requires a committed SdkConfig "
            + "semantic root before building SdkPackage: "
            + f"sdk_config_name={spec.sdk_config_name!r}"
        )

    with _record_phase(phase_timings_s, "hydrate_code_package_from_head"):
        code_package = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
            root_id=expected_source_code_package_id,
            root_type=CodePackage,
        )
    manifest_relative_path = _relative_to(
        path=spec.sdk_toml_path,
        root=spec.workspace_root,
        label="aware.sdk.toml",
    )
    package_root_relative = _relative_to(
        path=snapshot.package_root,
        root=spec.workspace_root,
        label="package_root",
    )
    sources_root_relative = _relative_to(
        path=sources_root,
        root=spec.workspace_root,
        label="sources_root",
    )
    with _record_phase(phase_timings_s, "read_source_texts"):
        source_texts_by_relative_path: dict[str, str] = {}
        for source_file in snapshot.source_files:
            source_path = (snapshot.package_root / source_file).resolve()
            source_texts_by_relative_path[source_file.as_posix()] = (
                source_path.read_text(encoding="utf-8")
            )
    with _record_phase(phase_timings_s, "commit_code_package_text_snapshot"):
        source_snapshot = await commit_code_package_text_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
            code_package_config_id=source_code_package_config_id,
            package_name=spec.package_name,
            language=CodeLanguage.aware,
            surface="sdk",
            manifest_kind="aware_sdk_toml",
            manifest_relative_path=manifest_relative_path,
            package_root=package_root_relative,
            sources_root=sources_root_relative,
            fqn_prefix=spec.package_fqn_prefix,
            source_texts_by_relative_path=source_texts_by_relative_path,
        )
        code_package = source_snapshot.code_package

    sdk_package_fqn_prefix = (snapshot.spec.sdk.fqn_prefix or "").strip() or None
    sdk_package_include_paths = JsonArray(snapshot.spec.build.include_paths)
    sdk_package_exclude_paths = JsonArray(snapshot.spec.build.exclude_paths)
    sdk_package_compilation_mode = cast(
        str,
        _enum_value(snapshot.spec.build.compilation_mode),
    )
    sdk_package_dependencies = _sdk_package_dependencies_payload(snapshot.spec)
    sdk_package_targets = _sdk_package_targets_payload(snapshot.spec)
    api_package_ids = _sdk_package_api_package_ids(snapshot.spec)
    sdk_package_dependency_refs = _sdk_package_dependency_refs(snapshot.spec)
    with _record_phase(
        phase_timings_s,
        "materialize_sdk_implementation_code_packages",
    ):
        implementation_code_package_refs = (
            await _materialize_sdk_implementation_code_packages(
                index=index,
                actor_id=actor_id,
                code_package_projection_hash=code_package_projection_hash,
                workspace_root=spec.workspace_root,
                snapshot=snapshot,
            )
        )
    implementation_code_packages = tuple(
        ref.code_package for ref in implementation_code_package_refs
    )
    implementation_package_snapshot_refs = _sdk_package_implementation_snapshots(
        implementation_code_package_refs=implementation_code_package_refs,
    )
    with _record_phase(
        phase_timings_s,
        "materialize_sdk_owned_object_config_graph_packages",
    ):
        (
            owned_object_config_graph_packages,
            object_config_graph_package_refs,
        ) = await _materialize_sdk_owned_object_config_graph_packages(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            workspace_root=spec.workspace_root,
            snapshot=snapshot,
        )
    with _record_phase(phase_timings_s, "hydrate_sdk_package_from_head"):
        sdk_package = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=branch_id,
            projection_hash=sdk_package_projection_hash,
            root_id=expected_sdk_package_id,
            root_type=SdkPackage,
        )
    if sdk_package is not None and sdk_package.sdk_config_id != sdk_config.id:
        raise RuntimeError(
            "SDK package materialization resolved committed SdkPackage "
            + "with unexpected sdk_config_id: "
            + f"package_name={spec.package_name!r} "
            + f"expected={sdk_config.id} actual={sdk_package.sdk_config_id}"
        )
    with _record_phase(phase_timings_s, "commit_sdk_package_manifest_snapshot"):
        sdk_package_snapshot = await commit_sdk_package_manifest_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=sdk_package_projection_hash,
            name=spec.package_name,
            sdk_config_id=sdk_config.id,
            sdk_config_object_instance_graph_commit_id=(
                sdk_config_object_instance_graph_commit_id
            ),
            source_code_package_id=code_package.id,
            fqn_prefix=sdk_package_fqn_prefix,
            version_number=snapshot.spec.sdk.version_number,
            title=snapshot.spec.sdk.title,
            description=snapshot.spec.sdk.description,
            aware_sdk_version=snapshot.spec.aware_sdk,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root_relative,
            sources_root=sources_root_relative,
            include_paths=sdk_package_include_paths,
            exclude_paths=sdk_package_exclude_paths,
            force_fresh_scan=snapshot.spec.build.force_fresh_scan,
            compilation_mode=sdk_package_compilation_mode,
            dependencies=sdk_package_dependencies,
            targets=sdk_package_targets,
            api_package_ids=api_package_ids,
            object_config_graph_package_refs=object_config_graph_package_refs,
            implementation_package_refs=implementation_package_snapshot_refs,
            sdk_package_dependency_refs=sdk_package_dependency_refs,
        )
        sdk_package = sdk_package_snapshot.sdk_package
    if sdk_package.sdk_config_id != sdk_config.id:
        raise RuntimeError(
            "SDK package materialization resolved SdkPackage with "
            + "unexpected sdk_config_id: "
            + f"package_name={spec.package_name!r} "
            + f"expected={sdk_config.id} actual={sdk_package.sdk_config_id}"
        )
    with _record_phase(phase_timings_s, "validate_sdk_implementation_packages"):
        _validate_sdk_implementation_package_bridges(
            sdk_package=sdk_package,
            implementation_code_packages=implementation_code_packages,
        )
    with _record_phase(phase_timings_s, "resolve_sdk_package_semantic_root_commit_id"):
        sdk_package_domain_commit_id = (
            sdk_package_snapshot.commit_id
            or await _lane_head_commit_id(
                branch_id=branch_id,
                projection_hash=sdk_package_projection_hash,
            )
        )
        sdk_package_object_instance_graph_commit_id = (
            sdk_package_snapshot.object_instance_graph_commit_id
        ) or (
            await _object_instance_graph_commit_id_from_domain_commit(
                branch_id=branch_id,
                projection_hash=sdk_package_projection_hash,
                domain_commit_id=sdk_package_domain_commit_id,
            )
            if sdk_package_domain_commit_id is not None
            else None
        )

    phase_timings_s["total"] = _round_duration_s(
        perf_counter() - materialization_started_at
    )

    return SdkPackageMaterializationResult(
        sdk_toml_path=spec.sdk_toml_path,
        workspace_root=spec.workspace_root,
        manifest_spec=spec.manifest_spec,
        sdk_config=sdk_config,
        sdk_package=sdk_package,
        sdk_source_path=spec.sdk_source_path,
        source_files=spec.source_files,
        phase_timings_s=dict(sorted(phase_timings_s.items())),
        source_code_package_id=sdk_package.source_code_package_id,
        sdk_config_commit_id=sdk_config_domain_head_commit_id,
        sdk_config_object_instance_graph_commit_id=(
            sdk_config_object_instance_graph_commit_id
        ),
        package_commit_id=sdk_package_domain_commit_id,
        package_head_commit_id=sdk_package_object_instance_graph_commit_id,
        api_package_ids=api_package_ids,
        implementation_code_package_ids=tuple(
            ref.code_package.id
            for ref in implementation_code_package_refs
            if ref.code_package.id is not None
        ),
        implementation_code_package_refs=tuple(
            ref.to_payload() for ref in implementation_code_package_refs
        ),
        object_config_graph_packages=owned_object_config_graph_packages,
        sdk_package_dependency_ids=tuple(
            ref.target_sdk_package_id for ref in sdk_package_dependency_refs
        ),
    )


async def _materialize_sdk_implementation_code_packages(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    code_package_projection_hash: str,
    workspace_root: Path,
    snapshot: SdkWorkspaceSnapshot,
) -> tuple[SdkImplementationCodePackageMaterialization, ...]:
    refs: list[SdkImplementationCodePackageMaterialization] = []
    for target in _sdk_implementation_code_package_targets(
        snapshot=snapshot,
        workspace_root=workspace_root,
    ):
        code_package_config_id = _sdk_implementation_code_package_config_id(
            manifest_kind=target.manifest_kind,
        )
        expected_code_package_id = stable_code_package_id(
            code_package_config_id=code_package_config_id,
            package_name=target.package_name,
            language=target.language.value,
        )
        implementation_branch_id = _implementation_code_package_branch_id(
            code_package_id=expected_code_package_id,
        )
        manifest_relative_path = _relative_to(
            path=target.manifest_path,
            root=workspace_root,
            label="sdk_implementation.manifest_path",
        )
        package_root_relative = _relative_to(
            path=target.package_root,
            root=workspace_root,
            label="sdk_implementation.package_root",
        )
        sources_root_relative = _relative_to(
            path=target.sources_root,
            root=workspace_root,
            label="sdk_implementation.sources_root",
        )
        unparsed_texts_by_relative_path: dict[str, str] = {}
        for source_file in _implementation_code_source_files(target=target):
            relative_path = source_file.relative_to(target.package_root).as_posix()
            unparsed_texts_by_relative_path[relative_path] = source_file.read_text(
                encoding="utf-8"
            )
        snapshot_commit = await commit_code_package_text_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=implementation_branch_id,
            projection_hash=code_package_projection_hash,
            code_package_config_id=code_package_config_id,
            package_name=target.package_name,
            language=target.language,
            surface="sdk",
            manifest_kind=target.manifest_kind,
            manifest_relative_path=manifest_relative_path,
            package_root=package_root_relative,
            sources_root=sources_root_relative,
            fqn_prefix=target.import_root,
            source_texts_by_relative_path={},
            unparsed_texts_by_relative_path=unparsed_texts_by_relative_path,
        )
        hydrated_code_package = await _hydrate_lane_root_from_head(
            index=index,
            branch_id=implementation_branch_id,
            projection_hash=code_package_projection_hash,
            root_id=expected_code_package_id,
            root_type=CodePackage,
        )
        if hydrated_code_package is None:
            raise RuntimeError(
                "SDK implementation CodePackage materialization did not hydrate: "
                f"package_name={target.package_name!r} "
                f"language={target.language.value!r} "
                f"code_package_id={expected_code_package_id}"
            )
        refs.append(
            SdkImplementationCodePackageMaterialization(
                code_package=hydrated_code_package,
                branch_id=implementation_branch_id,
                domain_commit_id=snapshot_commit.commit_id,
                object_instance_graph_commit_id=(
                    snapshot_commit.object_instance_graph_commit_id
                ),
                role=target.role,
                include_paths=target.include_paths,
                exclude_paths=target.exclude_paths,
                entrypoint=target.entrypoint,
            )
        )
    return tuple(refs)


def _sdk_implementation_code_package_targets(
    *,
    snapshot: SdkWorkspaceSnapshot,
    workspace_root: Path,
) -> tuple[SdkImplementationCodePackageTarget, ...]:
    targets: list[SdkImplementationCodePackageTarget] = []
    if snapshot.spec.targets.python is not None:
        targets.append(
            _python_sdk_implementation_code_package_target(
                snapshot=snapshot,
                target=snapshot.spec.targets.python,
                workspace_root=workspace_root,
            )
        )
    if snapshot.spec.targets.dart is not None:
        targets.append(
            _dart_sdk_implementation_code_package_target(
                snapshot=snapshot,
                target=snapshot.spec.targets.dart,
                workspace_root=workspace_root,
            )
        )
    return tuple(targets)


def _python_sdk_implementation_code_package_target(
    *,
    snapshot: SdkWorkspaceSnapshot,
    target: AwareSdkTomlPythonTargetSpec,
    workspace_root: Path,
) -> SdkImplementationCodePackageTarget:
    language_root = (snapshot.sdk_root / (target.root_dir or "python")).resolve()
    _assert_existing_dir_within(
        root=snapshot.sdk_root,
        path=language_root,
        label="targets.python.root_dir",
    )
    package_root = (
        language_root / ((target.public_package.root_dir or ".").strip() or ".")
    ).resolve()
    _assert_existing_dir_within(
        root=language_root,
        path=package_root,
        label="targets.python.public_package.root_dir",
    )
    package_dir = (
        target.public_package.package_dir or snapshot.spec.sdk.fqn_prefix
    ).strip() or snapshot.spec.sdk.fqn_prefix
    import_root = package_dir.replace("/", ".")
    sources_root = (package_root / package_dir).resolve()
    _assert_existing_dir_within(
        root=package_root,
        path=sources_root,
        label="targets.python.public_package.package_dir",
    )
    manifest_path = (package_root / "pyproject.toml").resolve()
    _assert_existing_file_within(
        root=package_root,
        path=manifest_path,
        label="targets.python.pyproject_toml",
    )
    _assert_path_within(
        base=workspace_root,
        candidate=manifest_path,
        label="targets.python.workspace_root",
    )
    package_name = _read_pyproject_package_name(manifest_path)
    return SdkImplementationCodePackageTarget(
        language=CodeLanguage.python,
        package_name=package_name,
        import_root=import_root,
        package_root=package_root,
        manifest_path=manifest_path,
        sources_root=sources_root,
        manifest_kind="pyproject_toml",
        role="public_package",
        include_paths=(
            "pyproject.toml",
            "README.md",
            f"{package_dir}/**/*",
            "tests/**/*.py",
        ),
        exclude_paths=(
            "**/__pycache__/**",
            "**/*.pyc",
            ".pytest_cache/**",
            ".venv/**",
            "build/**",
            "dist/**",
        ),
    )


def _dart_sdk_implementation_code_package_target(
    *,
    snapshot: SdkWorkspaceSnapshot,
    target: AwareSdkTomlDartTargetSpec,
    workspace_root: Path,
) -> SdkImplementationCodePackageTarget:
    language_root = (snapshot.sdk_root / (target.root_dir or "dart")).resolve()
    _assert_existing_dir_within(
        root=snapshot.sdk_root,
        path=language_root,
        label="targets.dart.root_dir",
    )
    package_dir = (
        target.public_package.package_dir or snapshot.spec.sdk.fqn_prefix
    ).strip() or snapshot.spec.sdk.fqn_prefix
    package_root = (
        language_root
        / ((target.public_package.root_dir or package_dir).strip() or package_dir)
    ).resolve()
    _assert_existing_dir_within(
        root=language_root,
        path=package_root,
        label="targets.dart.public_package.root_dir",
    )
    manifest_path = (package_root / "pubspec.yaml").resolve()
    _assert_existing_file_within(
        root=package_root,
        path=manifest_path,
        label="targets.dart.pubspec_yaml",
    )
    _assert_path_within(
        base=workspace_root,
        candidate=manifest_path,
        label="targets.dart.workspace_root",
    )
    sources_root = (package_root / "lib").resolve()
    _assert_existing_dir_within(
        root=package_root,
        path=sources_root,
        label="targets.dart.lib",
    )
    package_name = _read_pubspec_package_name(manifest_path)
    return SdkImplementationCodePackageTarget(
        language=CodeLanguage.dart,
        package_name=package_name,
        import_root=package_name,
        package_root=package_root,
        manifest_path=manifest_path,
        sources_root=sources_root,
        manifest_kind="pubspec_yaml",
        role="public_package",
        include_paths=(
            "pubspec.yaml",
            "pubspec.lock",
            "README.md",
            "analysis_options.yaml",
            "lib/**/*",
            "test/**/*.dart",
        ),
        exclude_paths=(
            ".dart_tool/**",
            "build/**",
            ".pub/**",
        ),
    )


def _read_pyproject_package_name(pyproject_path: Path) -> str:
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = payload.get("project")
    if not isinstance(project, dict):
        raise RuntimeError(
            "SDK Python target pyproject.toml must define [project]: "
            f"{pyproject_path}"
        )
    raw_name = project.get("name")
    if not isinstance(raw_name, str) or not raw_name.strip():
        raise RuntimeError(
            "SDK Python target pyproject.toml must define [project].name: "
            f"{pyproject_path}"
        )
    return raw_name.strip()


def _read_pubspec_package_name(pubspec_path: Path) -> str:
    for line in pubspec_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("name:"):
            continue
        raw_name = stripped.removeprefix("name:").split("#", 1)[0].strip()
        if raw_name:
            return raw_name
    raise RuntimeError(
        "SDK Dart target pubspec.yaml must define package name: " f"{pubspec_path}"
    )


def _implementation_code_package_branch_id(
    *,
    code_package_id: UUID,
) -> UUID:
    return uuid5(
        _SDK_IMPLEMENTATION_CODE_PACKAGE_BRANCH_NAMESPACE,
        str(code_package_id).strip().casefold(),
    )


def _implementation_code_source_files(
    *,
    target: SdkImplementationCodePackageTarget,
) -> tuple[Path, ...]:
    files_by_rel: dict[str, Path] = {}
    for include_path in target.include_paths:
        pattern = (include_path or "").strip()
        if not pattern:
            continue
        for candidate in target.package_root.glob(pattern):
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            _assert_existing_file_within(
                root=target.package_root,
                path=resolved,
                label="sdk_implementation.include_paths",
            )
            rel_path = resolved.relative_to(target.package_root).as_posix()
            if _is_path_excluded(
                rel_path=rel_path,
                exclude_patterns=target.exclude_paths,
            ):
                continue
            files_by_rel[rel_path] = resolved
    return tuple(files_by_rel[key] for key in sorted(files_by_rel))


def _is_path_excluded(*, rel_path: str, exclude_patterns: Sequence[str]) -> bool:
    token = PurePosixPath(rel_path)
    if any(
        part in _SDK_IMPLEMENTATION_CODE_PACKAGE_EXCLUDED_PATH_PARTS
        for part in token.parts
    ):
        return True
    for raw_pattern in exclude_patterns:
        pattern = (raw_pattern or "").strip()
        if pattern and token.match(pattern):
            return True
    return False


def _sdk_package_implementation_snapshots(
    *,
    implementation_code_package_refs: tuple[
        SdkImplementationCodePackageMaterialization, ...
    ],
) -> tuple[SdkPackageImplementationPackageSnapshotRef, ...]:
    refs: list[SdkPackageImplementationPackageSnapshotRef] = []
    for implementation_ref in implementation_code_package_refs:
        code_package = implementation_ref.code_package
        if code_package.id is None:
            raise RuntimeError(
                "SDK implementation package bridge requires committed CodePackage id: "
                f"package_name={code_package.package_name!r} "
                f"language={code_package.language.value!r}"
            )
        refs.append(
            SdkPackageImplementationPackageSnapshotRef(
                code_package_id=code_package.id,
                package_name=code_package.package_name,
                language=code_package.language,
                import_root=code_package.fqn_prefix or code_package.package_name,
                manifest_relative_path=code_package.manifest_relative_path,
                package_root=code_package.package_root,
                entrypoint=implementation_ref.entrypoint,
                role=implementation_ref.role,
                include_paths=JsonArray(implementation_ref.include_paths),
                exclude_paths=JsonArray(implementation_ref.exclude_paths),
            )
        )
    return tuple(refs)


def _validate_sdk_implementation_package_bridges(
    *,
    sdk_package: SdkPackage,
    implementation_code_packages: tuple[CodePackage, ...],
) -> None:
    expected_ids = {
        code_package.id
        for code_package in implementation_code_packages
        if code_package.id is not None
    }
    attached_ids = {
        bridge.code_package_id for bridge in sdk_package.implementation_packages
    }
    missing = expected_ids - attached_ids
    if missing:
        raise RuntimeError(
            "SdkPackage implementation package bridge hydration is incomplete: "
            f"sdk_package_id={sdk_package.id} "
            f"missing_code_package_ids={sorted(str(item) for item in missing)}"
        )


def _assert_existing_file_within(*, root: Path, path: Path, label: str) -> None:
    _assert_path_within(base=root, candidate=path, label=label)
    if not path.resolve().is_file():
        raise FileNotFoundError(f"{label} must resolve to a file: {path.resolve()}")


def _assert_existing_dir_within(*, root: Path, path: Path, label: str) -> None:
    _assert_path_within(base=root, candidate=path, label=label)
    if not path.resolve().is_dir():
        raise NotADirectoryError(
            f"{label} must resolve to a directory: {path.resolve()}"
        )


async def _materialize_sdk_owned_object_config_graph_packages(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    snapshot: SdkWorkspaceSnapshot,
) -> tuple[
    tuple[SdkOwnedObjectConfigGraphPackageMaterialization, ...],
    tuple[SdkPackageObjectConfigGraphPackageSnapshotRef, ...],
]:
    manifest_spec = snapshot.spec
    sdk_root = snapshot.sdk_root.resolve()
    materializations: list[SdkOwnedObjectConfigGraphPackageMaterialization] = []
    refs: list[SdkPackageObjectConfigGraphPackageSnapshotRef] = []
    for declared_package in manifest_spec.object_config_graph_packages:
        declared_manifest_path = (sdk_root / declared_package.manifest).resolve()
        _assert_path_within(
            base=sdk_root,
            candidate=declared_manifest_path,
            label="object_config_graph_packages.manifest",
        )
        if not declared_manifest_path.exists():
            raise FileNotFoundError(
                "SDK-owned ObjectConfigGraphPackage manifest not found: "
                f"{declared_manifest_path}"
            )
        if not declared_manifest_path.is_file():
            raise RuntimeError(
                "SDK-owned ObjectConfigGraphPackage manifest must be a file: "
                f"{declared_manifest_path}"
            )

        child_spec = load_aware_toml_spec(toml_path=declared_manifest_path)
        manifest_relative_path = _relative_to(
            path=declared_manifest_path,
            root=workspace_root,
            label="sdk_owned_object_config_graph_package",
        )
        object_config_graph_package_oig_commit_id = _optional_uuid_from_manifest_pin(
            declared_oig_commit_id=declared_package.object_instance_graph_commit_id,
            manifest_path=declared_manifest_path,
        )
        role = (declared_package.role or "").strip() or "local_state"
        package_kind = cast(str, _enum_value(child_spec.package.kind))
        object_config_graph_package_id = stable_object_config_graph_package_id(
            package_name=child_spec.package.package_name,
            fqn_prefix=child_spec.package.fqn_prefix,
        )
        object_config_graph_id = stable_object_config_graph_id(
            fqn_prefix=child_spec.package.fqn_prefix,
            language=CodeLanguage.aware.value,
        )
        source_code_package_config_id = _sdk_owned_aware_toml_code_package_config_id(
            package_kind=child_spec.package.kind,
        )
        source_code_package_id = stable_code_package_id(
            code_package_config_id=source_code_package_config_id,
            package_name=child_spec.package.package_name,
            language=CodeLanguage.aware.value,
        )
        materializations.append(
            SdkOwnedObjectConfigGraphPackageMaterialization(
                manifest_path=declared_manifest_path,
                manifest_relative_path=manifest_relative_path,
                role=role,
                package_name=child_spec.package.package_name,
                package_fqn_prefix=child_spec.package.fqn_prefix,
                package_kind=package_kind,
                language_materialization_targets=(
                    _aware_toml_materialization_targets_payload(
                        child_spec.language_materializations
                    )
                ),
                object_config_graph_package_id=object_config_graph_package_id,
                object_config_graph_id=object_config_graph_id,
                package_branch_id=None,
                source_code_package_id=source_code_package_id,
                object_config_graph_package_commit_id=None,
                object_config_graph_package_head_commit_id=None,
                object_config_graph_package_object_instance_graph_commit_id=(
                    object_config_graph_package_oig_commit_id
                ),
                object_config_graph_commit_id=None,
                object_config_graph_head_commit_id=None,
                object_config_graph_object_instance_graph_commit_id=None,
            )
        )
        refs.append(
            SdkPackageObjectConfigGraphPackageSnapshotRef(
                object_config_graph_package_id=object_config_graph_package_id,
                manifest_relative_path=manifest_relative_path,
                role=role,
                package_kind=package_kind,
                object_config_graph_package_object_instance_graph_commit_id=(
                    object_config_graph_package_oig_commit_id
                ),
                expected_hash_sha256=declared_package.expected_hash_sha256,
                description=declared_package.description,
            )
        )
    return tuple(materializations), tuple(refs)


def _aware_toml_materialization_targets_payload(
    targets: Sequence[object],
) -> tuple[dict[str, object], ...]:
    payload: list[dict[str, object]] = []
    for target in targets:
        row: dict[str, object] = {
            "role": str(getattr(target, "role")),
            "language": str(getattr(target, "language")),
            "output_dir": str(getattr(target, "output_dir")),
            "import_root": str(getattr(target, "import_root")),
            "package_name": str(getattr(target, "package_name")),
            "materialization_source": str(getattr(target, "materialization_source")),
        }
        renderer_kind = getattr(target, "renderer_kind")
        if renderer_kind is not None:
            row["renderer_kind"] = str(renderer_kind)
        renderer_profile = getattr(target, "renderer_profile")
        if renderer_profile is not None:
            row["renderer_profile"] = str(renderer_profile)
        stable_ids_import_root = getattr(target, "stable_ids_import_root")
        if stable_ids_import_root is not None:
            row["stable_ids_import_root"] = str(stable_ids_import_root)
        if bool(getattr(target, "source_is_runtime")):
            row["source_is_runtime"] = True
        payload.append(row)
    return tuple(payload)


def _optional_uuid_from_manifest_pin(
    *,
    declared_oig_commit_id: str | None,
    manifest_path: Path,
) -> UUID | None:
    if declared_oig_commit_id is None:
        return None
    try:
        return UUID(declared_oig_commit_id)
    except ValueError as exc:
        raise RuntimeError(
            "SDK-owned ObjectConfigGraphPackage OIG pin is not a UUID: "
            f"manifest_path={manifest_path} value={declared_oig_commit_id!r}"
        ) from exc


def _enum_value(value: object) -> object:
    enum_value = getattr(value, "value", None)
    return enum_value if enum_value is not None else value


def _sdk_source_code_package_config_id() -> UUID:
    return stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_sdk_toml",
            surface="sdk",
        ),
    )


def _sdk_implementation_code_package_config_id(
    *,
    manifest_kind: str,
) -> UUID:
    return stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind=manifest_kind,
            surface="sdk",
        ),
    )


def _sdk_owned_aware_toml_code_package_config_id(*, package_kind: object) -> UUID:
    surface = _sdk_owned_aware_toml_code_package_surface_for_kind(
        package_kind=package_kind,
    )
    return stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_toml",
            surface=surface,
        ),
    )


def _sdk_owned_aware_toml_code_package_surface_for_kind(
    *,
    package_kind: object,
) -> str:
    descriptor = next(
        (
            item
            for item in META_MANIFEST_RESOLUTION
            if item.manifest_kind == "aware_toml"
        ),
        None,
    )
    if descriptor is None:
        raise RuntimeError("Meta semantic contract is missing aware.toml resolution.")
    package_kind_text = str(_enum_value(package_kind) or "").strip()
    surface = code_package_surface_from_semantic_manifest_descriptor(
        descriptor,
        package_kind=package_kind_text,
    )
    if surface is None:
        raise RuntimeError(
            "SDK-owned ObjectConfigGraphPackage source package kind does not "
            + "declare a code package surface: "
            + f"package_kind={package_kind_text!r}"
        )
    return str(surface)


def _sdk_package_dependencies_payload(spec: AwareSdkTomlSpec) -> JsonArray:
    payload: list[JsonValue] = []
    for dependency in spec.dependencies:
        row: dict[str, object] = {
            "kind": cast(str, _enum_value(dependency.kind)),
            "package_name": dependency.package_name,
        }
        if dependency.version_number is not None:
            row["version_number"] = dependency.version_number
        if dependency.expected_hash_sha256 is not None:
            row["expected_hash_sha256"] = dependency.expected_hash_sha256
        if dependency.object_instance_graph_commit_id is not None:
            row["object_instance_graph_commit_id"] = (
                dependency.object_instance_graph_commit_id
            )
        payload.append(row)
    return JsonArray(payload)


def _sdk_package_targets_payload(spec: AwareSdkTomlSpec) -> JsonObject:
    payload: dict[str, JsonValue] = {}
    python = spec.targets.python
    if python is not None:
        payload["python"] = {
            "root_dir": python.root_dir,
            "public_package": {
                "package_dir": python.public_package.package_dir,
                "root_dir": python.public_package.root_dir,
            },
        }
    dart = spec.targets.dart
    if dart is not None:
        payload["dart"] = {
            "root_dir": dart.root_dir,
            "public_package": {
                "package_dir": dart.public_package.package_dir,
                "root_dir": dart.public_package.root_dir,
            },
        }
    return JsonObject(payload)


def _sdk_package_api_package_ids(spec: AwareSdkTomlSpec) -> tuple[UUID, ...]:
    api_package_ids: list[UUID] = []
    for dependency in spec.dependencies:
        if dependency.kind != AwareSdkDependencyKind.api_package:
            continue
        api_package_ids.append(stable_api_package_id(name=dependency.package_name))
    return tuple(api_package_ids)


def _sdk_package_dependency_refs(
    spec: AwareSdkTomlSpec,
) -> tuple[SdkPackageDependencySnapshotRef, ...]:
    refs: list[SdkPackageDependencySnapshotRef] = []
    for dependency in spec.dependencies:
        if dependency.kind != AwareSdkDependencyKind.sdk_package:
            continue
        object_instance_graph_commit_id = (
            UUID(dependency.object_instance_graph_commit_id)
            if dependency.object_instance_graph_commit_id is not None
            else None
        )
        refs.append(
            SdkPackageDependencySnapshotRef(
                target_package_name=dependency.package_name,
                target_sdk_package_id=stable_sdk_package_id(
                    name=dependency.package_name
                ),
                target_sdk_package_object_instance_graph_commit_id=(
                    object_instance_graph_commit_id
                ),
                target_version_number=dependency.version_number,
                expected_hash_sha256=dependency.expected_hash_sha256,
                description="SDK package dependency.",
            )
        )
    return tuple(refs)


async def _hydrate_lane_root_from_head(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    root_id: UUID | None,
    root_type: type[_TRoot],
) -> _TRoot | None:
    if root_id is None:
        return None

    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"SDK package materialization missing projection hash: {projection_hash}"
        )

    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None

    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    session = reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )
    resolved_root = session.imap_get(root_type, root_id)
    if resolved_root is not None:
        return resolved_root
    return None


async def _lane_head_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
) -> UUID | None:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is None:
        return None
    raw_commit_id = head.get("commit_id")
    if raw_commit_id is None:
        return None
    if isinstance(raw_commit_id, UUID):
        return raw_commit_id
    return UUID(str(raw_commit_id))


async def _object_instance_graph_commit_id_from_domain_commit(
    *,
    branch_id: UUID,
    projection_hash: str,
    domain_commit_id: UUID,
) -> UUID | None:
    domain_commit = await FSCommitStore().get_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=domain_commit_id,
    )
    if domain_commit is None:
        return None
    return stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=(
            domain_commit.object_instance_graph_identity_id
        ),
        commit_id=domain_commit_id,
    )


def _relative_to(*, path: Path, root: Path, label: str) -> str:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(
            "SDK package materialization path resolved outside workspace root: "
            + f"label={label} root={resolved_root} path={resolved_path}"
        ) from exc
    relative_text = relative.as_posix()
    return relative_text or "."


def _assert_path_within(*, base: Path, candidate: Path, label: str) -> None:
    resolved_base = base.resolve()
    resolved_candidate = candidate.resolve()
    if (
        resolved_candidate == resolved_base
        or resolved_base in resolved_candidate.parents
    ):
        return
    raise RuntimeError(
        "SDK package materialization path resolved outside expected root: "
        + f"label={label} root={resolved_base} path={resolved_candidate}"
    )


__all__ = [
    "SdkOwnedObjectConfigGraphPackageMaterialization",
    "SdkPackageMaterializationResult",
    "SdkPackageMaterializationSpec",
    "materialize_sdk_package_from_manifest",
    "resolve_sdk_package_materialization_spec",
]
