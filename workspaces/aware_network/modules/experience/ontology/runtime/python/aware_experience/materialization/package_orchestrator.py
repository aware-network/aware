from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol
from uuid import UUID

from aware_code.package.snapshot_commit import commit_code_package_text_snapshot
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage
from aware_attention_ontology.stable_ids import stable_attention_package_id
from aware_experience import stable_ids as experience_stable_ids
from aware_experience.language_contracts import (
    ExperienceLanguageContractPackage,
    materialize_experience_language_contracts,
)
from aware_experience.manifest.spec import (
    AwareExperienceDependencyKind,
    AwareExperienceTomlSpec,
)
from aware_experience.materialization.branches import (
    derive_experience_reference_branch_id,
)
from aware_experience.materialization.lane_state import (
    hydrate_lane_root_from_head,
    reset_stale_generated_projection_lane_if_needed,
)
from aware_experience.materialization.snapshot_commit import (
    ExperiencePackageAttentionPackageSnapshotRef,
    ExperiencePackageDependencySnapshot,
    ExperiencePackageLanguagePackageSnapshotRef,
    commit_environment_experience_snapshot,
    commit_experience_package_manifest_snapshot,
)
from aware_experience.environment_profile.runtime_support import ocg_support
from aware_experience_ontology.environment.environment_experience import (
    EnvironmentExperience,
)
from aware_experience_ontology.environment.experience_package import ExperiencePackage
from aware_meta.materialization import (
    MaterializationLaneContext,
    MaterializationRunReceipt,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex


class RuntimeProtocol(Protocol):
    pass


class ExperiencePackageInstallScope(str, Enum):
    activation = "activation"
    dependency_reference = "dependency_reference"


def coerce_experience_package_install_scope(
    value: ExperiencePackageInstallScope | str,
) -> ExperiencePackageInstallScope:
    if isinstance(value, ExperiencePackageInstallScope):
        return value
    try:
        return ExperiencePackageInstallScope(value)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in ExperiencePackageInstallScope)
        raise RuntimeError(
            "Invalid Experience package install scope: "
            f"{value!r}; expected one of {allowed}"
        ) from exc


@dataclass(frozen=True, slots=True)
class ExperiencePackageMaterializationSpec:
    experience_toml_path: Path
    workspace_root: Path
    manifest_spec: AwareExperienceTomlSpec
    package_name: str
    package_fqn_prefix: str
    experience_names: tuple[str, ...]
    experience_name: str
    experience_source_path: str
    source_files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExperiencePackageMaterializationResult:
    experience_toml_path: Path
    workspace_root: Path
    manifest_spec: AwareExperienceTomlSpec
    environment_experience: EnvironmentExperience
    experience_package: ExperiencePackage
    experience_names: tuple[str, ...]
    experience_name: str
    experience_source_path: str
    source_files: tuple[str, ...]
    language_contract_packages: tuple[ExperienceLanguageContractPackage, ...]
    phase_timings_s: Mapping[str, float]
    source_code_package_id: UUID | None
    environment_experience_commit_id: UUID | None
    environment_experience_head_commit_id: UUID | None
    projection_experience_commit_id: UUID | None
    projection_experience_head_commit_id: UUID | None
    projection_experience_graph_commit_id: UUID | None
    projection_experience_graph_head_commit_id: UUID | None
    projection_experience_section_surface_commit_id: UUID | None
    projection_experience_section_surface_head_commit_id: UUID | None
    activation_profile_config_commit_id: UUID | None
    activation_profile_config_head_commit_id: UUID | None
    activation_profile_config_branch_id: UUID | None
    activation_profile_config_projection_hash: str | None
    activation_profile_config_domain_object_instance_graph_id: UUID | None
    activation_profile_config_object_instance_graph_commit_id: UUID | None
    activation_action_experience_commit_id: UUID | None
    activation_action_experience_head_commit_id: UUID | None
    activation_invocation_config_commit_id: UUID | None
    activation_invocation_config_head_commit_id: UUID | None
    activation_reference_branch_ids_by_experience_name: Mapping[str, UUID]
    program_config_commit_id: UUID | None
    program_config_head_commit_id: UUID | None
    program_impl_commit_id: UUID | None
    program_impl_head_commit_id: UUID | None
    package_commit_id: UUID | None
    package_head_commit_id: UUID | None
    package_projection_hash: str
    package_object_instance_graph_commit_id: UUID


class ExperienceWorkspaceCompileResult(Protocol):
    snapshot: Any


class ResolveExperiencePackageMaterializationSpec(Protocol):
    def __call__(
        self,
        *,
        experience_toml_path: Path,
        workspace_root: Path,
    ) -> ExperiencePackageMaterializationSpec: ...


class CompileExperienceWorkspace(Protocol):
    def __call__(
        self,
        *,
        toml_path: Path,
        repo_root: Path,
    ) -> ExperienceWorkspaceCompileResult: ...


class BuildSourceExperienceCompilePlanPayload(Protocol):
    def __call__(self, *, snapshot: Any) -> dict[str, object]: ...


class LoadApiCompilePlanPayloadsForWorkspace(Protocol):
    def __call__(self, *, workspace_root: Path) -> list[dict[str, object]]: ...


class SourceCodePackageConfigId(Protocol):
    def __call__(self) -> UUID: ...


class SourceCodePackageId(Protocol):
    def __call__(self, *, package_name: str) -> UUID: ...


class RelativeTo(Protocol):
    def __call__(self, *, path: Path, root: Path, label: str) -> str: ...


class LanguageContractPackageSnapshotRefs(Protocol):
    def __call__(
        self,
        *,
        language_contract_packages: tuple[ExperienceLanguageContractPackage, ...],
    ) -> tuple[ExperiencePackageLanguagePackageSnapshotRef, ...]: ...


class ValidateEnvironmentExperienceMaterializationResult(Protocol):
    def __call__(
        self,
        *,
        environment_experience: EnvironmentExperience,
        spec: ExperiencePackageMaterializationSpec,
    ) -> None: ...


class ValidateExperiencePackageMaterializationResult(Protocol):
    def __call__(
        self,
        *,
        experience_package: ExperiencePackage,
        environment_experience: EnvironmentExperience,
        spec: ExperiencePackageMaterializationSpec,
        language_package_refs: Sequence[ExperiencePackageLanguagePackageSnapshotRef],
    ) -> None: ...


class SupportsSourceExperienceProjectionMaterialization(Protocol):
    def __call__(
        self,
        *,
        index: MetaGraphRuntimeIndex,
        compile_plan_payload: Mapping[str, object],
    ) -> bool: ...


class MaterializeExperienceProjectionOntology(Protocol):
    async def __call__(
        self,
        *,
        runtime: RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        actor_id: UUID | None,
        lane: MaterializationLaneContext,
        compile_plan_payloads: Sequence[Mapping[str, object]],
        api_compile_plan_payloads: Sequence[Mapping[str, object]],
        phase_timings_s: dict[str, float],
        allow_unresolved_projection_experiences: bool,
        semantic_materialization_context: Mapping[str, object] | None,
        source_experience_toml_path: Path,
    ) -> MaterializationRunReceipt | None: ...


class MaterializeExperienceGraphOntology(Protocol):
    async def __call__(
        self,
        *,
        runtime: RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        actor_id: UUID | None,
        lane: MaterializationLaneContext,
        compile_plan_payloads: Sequence[Mapping[str, object]],
        phase_timings_s: dict[str, float],
        allow_unresolved_projection_experiences: bool,
    ) -> MaterializationRunReceipt | None: ...


class MaterializeExperienceSectionSurfaceOntology(Protocol):
    async def __call__(
        self,
        *,
        runtime: RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        actor_id: UUID | None,
        lane: MaterializationLaneContext,
        compile_plan_payloads: Sequence[Mapping[str, object]],
        projection_reference_branch_ids_by_name: Mapping[str, UUID] | None,
        allow_unresolved_projection_experiences: bool,
    ) -> MaterializationRunReceipt | None: ...


class MaterializeExperienceActivationTopologyOntology(Protocol):
    async def __call__(
        self,
        *,
        runtime: RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        actor_id: UUID | None,
        lane: MaterializationLaneContext,
        compile_plan_payloads: Sequence[Mapping[str, object]],
        api_compile_plan_payloads: Sequence[Mapping[str, object]],
        projection_reference_branch_ids_by_name: Mapping[str, UUID] | None,
        allow_unresolved_projection_experiences: bool,
    ) -> MaterializationRunReceipt | None: ...


class MaterializeExperienceEnvironmentProfileOntology(Protocol):
    async def __call__(
        self,
        *,
        runtime: RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        actor_id: UUID | None,
        lane: MaterializationLaneContext,
        environment_id: UUID | None,
        process_id: UUID | None,
        thread_id: UUID | None,
        compile_plan_payloads: Sequence[Mapping[str, object]],
        projection_reference_branch_ids_by_name: Mapping[str, UUID] | None,
        prefer_snapshot_materialization: bool,
        allow_unresolved_projection_experiences: bool,
        environment_api_client: Any | None,
    ) -> MaterializationRunReceipt | None: ...


class MaterializeExperienceProgramOntology(Protocol):
    async def __call__(
        self,
        *,
        runtime: RuntimeProtocol,
        index: MetaGraphRuntimeIndex,
        actor_id: UUID | None,
        lane: MaterializationLaneContext,
        compile_plan_payloads: Sequence[Mapping[str, object]],
        phase_timings_s: dict[str, float],
        projection_reference_branch_ids_by_name: Mapping[str, UUID] | None,
    ) -> tuple[MaterializationRunReceipt | None, MaterializationRunReceipt | None]: ...


@dataclass(frozen=True, slots=True)
class ExperiencePackageMaterializationOrchestratorDependencies:
    resolve_experience_package_materialization_spec: (
        ResolveExperiencePackageMaterializationSpec
    )
    compile_experience_workspace: CompileExperienceWorkspace
    build_source_experience_compile_plan_payload: (
        BuildSourceExperienceCompilePlanPayload
    )
    load_api_compile_plan_payloads_for_workspace: LoadApiCompilePlanPayloadsForWorkspace
    source_code_package_config_id: SourceCodePackageConfigId
    source_code_package_id: SourceCodePackageId
    relative_to: RelativeTo
    language_contract_package_snapshot_refs: LanguageContractPackageSnapshotRefs
    validate_environment_experience_materialization_result: (
        ValidateEnvironmentExperienceMaterializationResult
    )
    validate_experience_package_materialization_result: (
        ValidateExperiencePackageMaterializationResult
    )
    supports_source_experience_projection_materialization: (
        SupportsSourceExperienceProjectionMaterialization
    )
    materialize_experience_projection_ontology: MaterializeExperienceProjectionOntology
    materialize_experience_graph_ontology: MaterializeExperienceGraphOntology
    materialize_experience_section_surface_ontology: (
        MaterializeExperienceSectionSurfaceOntology
    )
    materialize_experience_activation_topology_ontology: (
        MaterializeExperienceActivationTopologyOntology
    )
    materialize_experience_environment_profile_ontology: (
        MaterializeExperienceEnvironmentProfileOntology
    )
    materialize_experience_program_ontology: MaterializeExperienceProgramOntology


def _round_duration_s(duration_s: float) -> float:
    return round(max(duration_s, 0.0), 6)


def _resolve_experience_compile_repo_root(*, workspace_root: Path) -> Path:
    resolved_workspace_root = workspace_root.expanduser().resolve()
    for candidate in (resolved_workspace_root, *resolved_workspace_root.parents):
        if (candidate / "aware.repo.toml").is_file():
            return candidate
    return resolved_workspace_root


async def _reset_stale_generated_package_lanes_if_needed(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hashes_by_name: Sequence[tuple[str, str]],
) -> tuple[str, ...]:
    reset_projection_names: list[str] = []
    for projection_name, projection_hash in projection_hashes_by_name:
        reset = await reset_stale_generated_projection_lane_if_needed(
            index=index,
            branch_id=branch_id,
            projection_hash=projection_hash,
            error_context=(
                "Experience package generated lane preflight " f"({projection_name})"
            ),
        )
        if reset:
            reset_projection_names.append(projection_name)
    return tuple(reset_projection_names)


@contextmanager
def _record_optional_phase(
    timings: dict[str, float],
    phase_name: str,
) -> Iterator[None]:
    started_at = perf_counter()
    try:
        yield
    finally:
        timings[phase_name] = _round_duration_s(perf_counter() - started_at)


async def run_experience_package_materialization(
    *,
    runtime: RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    workspace_root: Path,
    experience_toml_path: Path,
    allow_unresolved_projection_experiences: bool = False,
    install_scope: ExperiencePackageInstallScope | str = (
        ExperiencePackageInstallScope.activation
    ),
    projection_reference_branch_ids_by_name: Mapping[str, UUID] | None = None,
    prefer_snapshot_environment_profiles: bool = False,
    environment_api_client: Any | None = None,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    semantic_materialization_context: Mapping[str, object] | None = None,
    dependencies: ExperiencePackageMaterializationOrchestratorDependencies,
) -> ExperiencePackageMaterializationResult:
    materialization_started_at = perf_counter()
    phase_timings_s: dict[str, float] = {}
    experience_package_install_scope = coerce_experience_package_install_scope(
        install_scope
    )
    with _record_optional_phase(
        phase_timings_s, "resolve_experience_package_materialization_spec"
    ):
        spec = dependencies.resolve_experience_package_materialization_spec(
            experience_toml_path=experience_toml_path,
            workspace_root=workspace_root,
        )
    with _record_optional_phase(
        phase_timings_s, "compile_experience_workspace_snapshot"
    ):
        compile_result = dependencies.compile_experience_workspace(
            toml_path=spec.experience_toml_path,
            repo_root=_resolve_experience_compile_repo_root(
                workspace_root=spec.workspace_root,
            ),
        )
        snapshot = compile_result.snapshot
        sources_root = (
            snapshot.package_root / snapshot.spec.build.sources_dir
        ).resolve()
    with _record_optional_phase(
        phase_timings_s, "build_source_experience_compile_plan_payload"
    ):
        source_compile_plan_payload = (
            dependencies.build_source_experience_compile_plan_payload(
                snapshot=snapshot,
            )
        )
    with _record_optional_phase(
        phase_timings_s, "resolve_dependency_projection_reference_branches"
    ):
        projection_reference_branch_ids_by_name = (
            _resolve_dependency_projection_reference_branch_ids(
                manifest_spec=spec.manifest_spec,
                compile_plan_payload=source_compile_plan_payload,
                semantic_materialization_context=semantic_materialization_context,
                existing=projection_reference_branch_ids_by_name,
            )
        )
    with _record_optional_phase(phase_timings_s, "load_api_compile_plan_payloads"):
        api_compile_plan_payloads = (
            dependencies.load_api_compile_plan_payloads_for_workspace(
                workspace_root=spec.workspace_root,
            )
        )
    with _record_optional_phase(phase_timings_s, "resolve_stable_ids"):
        expected_environment_experience_id = (
            experience_stable_ids.stable_environment_experience_id(
                fqn_prefix=spec.package_fqn_prefix
            )
        )
        expected_experience_package_id = (
            experience_stable_ids.stable_experience_package_id(name=spec.package_name)
        )
        source_code_package_config_id = dependencies.source_code_package_config_id()
        expected_source_code_package_id = dependencies.source_code_package_id(
            package_name=spec.package_name,
        )
    with _record_optional_phase(phase_timings_s, "resolve_relative_paths"):
        manifest_relative_path = dependencies.relative_to(
            path=spec.experience_toml_path,
            root=spec.workspace_root,
            label="aware.experience.toml",
        )
        package_root_relative = dependencies.relative_to(
            path=snapshot.package_root,
            root=spec.workspace_root,
            label="package_root",
        )
        manifest_package_relative_path = dependencies.relative_to(
            path=spec.experience_toml_path,
            root=snapshot.package_root,
            label="package manifest",
        )
        sources_root_relative = dependencies.relative_to(
            path=sources_root,
            root=spec.workspace_root,
            label="sources_root",
        )

    with _record_optional_phase(phase_timings_s, "resolve_projection_hashes"):
        environment_experience_projection_hash = (
            ocg_support.find_projection_hash_by_name(
                index=index,
                projection_name="EnvironmentExperience",
            )
        )
        experience_package_projection_hash = ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="ExperiencePackage",
        )
        code_package_projection_hash = ocg_support.find_projection_hash_by_name(
            index=index,
            projection_name="CodePackage",
        )

    with _record_optional_phase(phase_timings_s, "preflight_generated_package_lanes"):
        await _reset_stale_generated_package_lanes_if_needed(
            index=index,
            branch_id=branch_id,
            projection_hashes_by_name=(
                (
                    "EnvironmentExperience",
                    environment_experience_projection_hash,
                ),
                ("CodePackage", code_package_projection_hash),
                ("ExperiencePackage", experience_package_projection_hash),
            ),
        )

    with _record_optional_phase(
        phase_timings_s, "commit_environment_experience_snapshot"
    ):
        environment_experience_snapshot = await commit_environment_experience_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=environment_experience_projection_hash,
            fqn_prefix=spec.package_fqn_prefix,
            title=spec.manifest_spec.experience.title,
            description=spec.manifest_spec.experience.description,
        )
    with _record_optional_phase(
        phase_timings_s, "hydrate_environment_experience_from_head"
    ):
        environment_experience = await hydrate_lane_root_from_head(
            index=index,
            branch_id=branch_id,
            projection_hash=environment_experience_projection_hash,
            root_id=expected_environment_experience_id,
            root_type=EnvironmentExperience,
        )
    if environment_experience is None:
        raise RuntimeError(
            "Experience package materialization could not hydrate canonical EnvironmentExperience after build: "
            + f"fqn_prefix={spec.package_fqn_prefix!r}"
        )
    with _record_optional_phase(phase_timings_s, "validate_environment_experience"):
        dependencies.validate_environment_experience_materialization_result(
            environment_experience=environment_experience,
            spec=spec,
        )

    source_texts_by_relative_path: dict[str, str] = {}
    for source_file in snapshot.source_files:
        source_path = (snapshot.package_root / source_file).resolve()
        with _record_optional_phase(
            phase_timings_s,
            f"read_source_text:{source_file.as_posix()}",
        ):
            source_texts_by_relative_path[source_file.as_posix()] = (
                source_path.read_text(encoding="utf-8")
            )
    with _record_optional_phase(phase_timings_s, "commit_code_package_text_snapshot"):
        code_package_snapshot = await commit_code_package_text_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
            code_package_config_id=source_code_package_config_id,
            package_name=spec.package_name,
            language=CodeLanguage.aware,
            surface="experience",
            manifest_kind="aware_experience_toml",
            manifest_relative_path=manifest_relative_path,
            package_root=package_root_relative,
            sources_root=sources_root_relative,
            fqn_prefix=spec.package_fqn_prefix,
            source_texts_by_relative_path=source_texts_by_relative_path,
            unparsed_texts_by_relative_path={
                manifest_package_relative_path: spec.experience_toml_path.read_text(
                    encoding="utf-8"
                )
            },
        )
    with _record_optional_phase(phase_timings_s, "rehydrate_code_package_from_head"):
        code_package = await hydrate_lane_root_from_head(
            index=index,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
            root_id=expected_source_code_package_id,
            root_type=CodePackage,
        )
    if code_package is None:
        raise RuntimeError(
            "Experience package materialization could not hydrate canonical CodePackage after build: "
            + f"package_name={spec.package_name!r}"
        )
    if code_package_snapshot.code_package.id != expected_source_code_package_id:
        raise RuntimeError(
            "Experience package materialization committed CodePackage with unexpected id: "
            + f"package_name={spec.package_name!r} "
            + f"expected={expected_source_code_package_id} actual={code_package_snapshot.code_package.id}"
        )

    with _record_optional_phase(
        phase_timings_s, "materialize_language_contract_packages"
    ):
        language_contract_packages = (
            materialize_experience_language_contracts(
                snapshot=snapshot,
                languages=tuple(sorted(snapshot.spec.targets)),
            ).packages
            if snapshot.spec.targets
            else ()
        )
        language_package_refs = dependencies.language_contract_package_snapshot_refs(
            language_contract_packages=language_contract_packages,
        )

    with _record_optional_phase(
        phase_timings_s, "commit_experience_package_manifest_snapshot"
    ):
        dependency_snapshots = tuple(
            ExperiencePackageDependencySnapshot(
                target_experience_package_id=(
                    experience_stable_ids.stable_experience_package_id(
                        name=dependency.package_name
                    )
                ),
                target_package_name=dependency.package_name,
                target_version_number=dependency.version_number,
            )
            for dependency in spec.manifest_spec.dependencies
            if dependency.kind is AwareExperienceDependencyKind.experience_package
        )
        attention_package_refs = tuple(
            ExperiencePackageAttentionPackageSnapshotRef(
                attention_package_id=stable_attention_package_id(
                    name=dependency.package_name
                ),
                package_name=dependency.package_name,
            )
            for dependency in spec.manifest_spec.dependencies
            if dependency.kind is AwareExperienceDependencyKind.attention_package
        )
        experience_package_snapshot = await commit_experience_package_manifest_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=experience_package_projection_hash,
            name=spec.package_name,
            environment_experience_id=environment_experience.id,
            source_code_package_id=code_package.id,
            dependencies=dependency_snapshots,
            attention_package_refs=attention_package_refs,
            language_package_refs=language_package_refs,
        )
    with _record_optional_phase(
        phase_timings_s, "hydrate_experience_package_from_head"
    ):
        experience_package = await hydrate_lane_root_from_head(
            index=index,
            branch_id=branch_id,
            projection_hash=experience_package_projection_hash,
            root_id=expected_experience_package_id,
            root_type=ExperiencePackage,
        )
    if experience_package is None:
        raise RuntimeError(
            "Experience package materialization could not hydrate canonical ExperiencePackage after build: "
            + f"package_name={spec.package_name!r}"
        )
    if experience_package_snapshot.experience_package.experience_package_dependencies:
        dependency_ids = {
            dependency.id
            for dependency in experience_package.experience_package_dependencies
            if dependency.id is not None
        }
        for (
            dependency
        ) in (
            experience_package_snapshot.experience_package.experience_package_dependencies
        ):
            if dependency.id in dependency_ids:
                continue
            experience_package.experience_package_dependencies.append(dependency)
            if dependency.id is not None:
                dependency_ids.add(dependency.id)
    if experience_package_snapshot.experience_package.attention_packages:
        attention_package_ids = {
            attention_package.id
            for attention_package in experience_package.attention_packages
            if attention_package.id is not None
        }
        for (
            attention_package
        ) in experience_package_snapshot.experience_package.attention_packages:
            if attention_package.id in attention_package_ids:
                continue
            experience_package.attention_packages.append(attention_package)
            if attention_package.id is not None:
                attention_package_ids.add(attention_package.id)
    if experience_package_snapshot.experience_package.language_packages:
        language_package_ids = {
            language_package.id
            for language_package in experience_package.language_packages
            if language_package.id is not None
        }
        for (
            language_package
        ) in experience_package_snapshot.experience_package.language_packages:
            if language_package.id in language_package_ids:
                continue
            experience_package.language_packages.append(language_package)
            if language_package.id is not None:
                language_package_ids.add(language_package.id)
    with _record_optional_phase(phase_timings_s, "validate_experience_package"):
        dependencies.validate_experience_package_materialization_result(
            experience_package=experience_package,
            environment_experience=environment_experience,
            spec=spec,
            language_package_refs=language_package_refs,
        )

    projection_receipt: MaterializationRunReceipt | None = None
    graph_receipt: MaterializationRunReceipt | None = None
    section_surface_receipt: MaterializationRunReceipt | None = None
    activation_topology_receipt: MaterializationRunReceipt | None = None
    environment_profile_receipt: MaterializationRunReceipt | None = None
    program_receipts: tuple[
        MaterializationRunReceipt | None, MaterializationRunReceipt | None
    ] = (
        None,
        None,
    )
    with _record_optional_phase(
        phase_timings_s, "supports_source_experience_projection_materialization"
    ):
        supports_projection_materialization = (
            True
            if allow_unresolved_projection_experiences
            else dependencies.supports_source_experience_projection_materialization(
                index=index,
                compile_plan_payload=source_compile_plan_payload,
            )
        )
    if supports_projection_materialization:
        projection_experience_projection_hash = (
            ocg_support.find_projection_hash_by_name(
                index=index,
                projection_name="ProjectionExperience",
            )
        )
        projection_lane = MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=projection_experience_projection_hash,
        )
        with _record_optional_phase(phase_timings_s, "materialize_projection_ontology"):
            projection_receipt = (
                await dependencies.materialize_experience_projection_ontology(
                    runtime=runtime,
                    index=index,
                    actor_id=actor_id,
                    lane=projection_lane,
                    compile_plan_payloads=(source_compile_plan_payload,),
                    api_compile_plan_payloads=api_compile_plan_payloads,
                    phase_timings_s=phase_timings_s,
                    allow_unresolved_projection_experiences=(
                        allow_unresolved_projection_experiences
                    ),
                    semantic_materialization_context=semantic_materialization_context,
                    source_experience_toml_path=spec.experience_toml_path,
                )
            )
        with _record_optional_phase(phase_timings_s, "materialize_graph_ontology"):
            graph_receipt = await dependencies.materialize_experience_graph_ontology(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                lane=projection_lane,
                compile_plan_payloads=(source_compile_plan_payload,),
                phase_timings_s=phase_timings_s,
                allow_unresolved_projection_experiences=(
                    allow_unresolved_projection_experiences
                ),
            )
        if experience_package_install_scope is ExperiencePackageInstallScope.activation:
            if environment_id is None:
                raise RuntimeError(
                    "Experience activation materialization requires explicit "
                    "environment_id; dependency_reference materialization must not "
                    "activate environment profile topology."
                )
            with _record_optional_phase(
                phase_timings_s, "materialize_environment_profile_ontology"
            ):
                environment_profile_receipt = await dependencies.materialize_experience_environment_profile_ontology(
                    runtime=runtime,
                    index=index,
                    actor_id=actor_id,
                    lane=projection_lane,
                    environment_id=environment_id,
                    process_id=process_id,
                    thread_id=thread_id,
                    compile_plan_payloads=(source_compile_plan_payload,),
                    projection_reference_branch_ids_by_name=(
                        projection_reference_branch_ids_by_name
                    ),
                    prefer_snapshot_materialization=(
                        prefer_snapshot_environment_profiles
                    ),
                    allow_unresolved_projection_experiences=(
                        allow_unresolved_projection_experiences
                    ),
                    environment_api_client=environment_api_client,
                )
        else:
            phase_timings_s["materialize_environment_profile_ontology.skipped"] = 0.0
        materialize_section_surfaces = (
            experience_package_install_scope is ExperiencePackageInstallScope.activation
            or any(
                dependency.kind is AwareExperienceDependencyKind.attention_package
                for dependency in spec.manifest_spec.dependencies
            )
        )
        if materialize_section_surfaces:
            with _record_optional_phase(
                phase_timings_s, "materialize_section_surface_ontology"
            ):
                section_surface_receipt = (
                    await dependencies.materialize_experience_section_surface_ontology(
                        runtime=runtime,
                        index=index,
                        actor_id=actor_id,
                        lane=projection_lane,
                        compile_plan_payloads=(source_compile_plan_payload,),
                        projection_reference_branch_ids_by_name=(
                            projection_reference_branch_ids_by_name
                        ),
                        allow_unresolved_projection_experiences=(
                            allow_unresolved_projection_experiences
                        ),
                    )
                )
        else:
            phase_timings_s["materialize_section_surface_ontology.skipped"] = 0.0
        with _record_optional_phase(
            phase_timings_s, "materialize_activation_topology_ontology"
        ):
            activation_topology_receipt = (
                await dependencies.materialize_experience_activation_topology_ontology(
                    runtime=runtime,
                    index=index,
                    actor_id=actor_id,
                    lane=projection_lane,
                    compile_plan_payloads=(source_compile_plan_payload,),
                    api_compile_plan_payloads=api_compile_plan_payloads,
                    projection_reference_branch_ids_by_name=(
                        projection_reference_branch_ids_by_name
                    ),
                    allow_unresolved_projection_experiences=(
                        allow_unresolved_projection_experiences
                    ),
                )
            )
    if experience_package_install_scope is ExperiencePackageInstallScope.activation:
        with _record_optional_phase(phase_timings_s, "materialize_program_ontology"):
            program_receipts = (
                await dependencies.materialize_experience_program_ontology(
                    runtime=runtime,
                    index=index,
                    actor_id=actor_id,
                    lane=MaterializationLaneContext(
                        branch_id=branch_id,
                        projection_hash="",
                    ),
                    compile_plan_payloads=(source_compile_plan_payload,),
                    phase_timings_s=phase_timings_s,
                    projection_reference_branch_ids_by_name=(
                        projection_reference_branch_ids_by_name
                    ),
                )
            )
    else:
        phase_timings_s["materialize_program_ontology.skipped"] = 0.0

    phase_timings_s["total"] = _round_duration_s(
        perf_counter() - materialization_started_at
    )
    environment_experience_head_commit_id = (
        environment_profile_receipt.steps[-1].head_commit_id
        if environment_profile_receipt is not None and environment_profile_receipt.steps
        else environment_experience_snapshot.head_commit_id
    )
    experience_package_head_commit_id = experience_package_snapshot.head_commit_id

    return ExperiencePackageMaterializationResult(
        experience_toml_path=spec.experience_toml_path,
        workspace_root=spec.workspace_root,
        manifest_spec=spec.manifest_spec,
        environment_experience=environment_experience,
        experience_package=experience_package,
        experience_names=spec.experience_names,
        experience_name=spec.experience_name,
        experience_source_path=spec.experience_source_path,
        source_files=spec.source_files,
        language_contract_packages=language_contract_packages,
        phase_timings_s=dict(sorted(phase_timings_s.items())),
        source_code_package_id=experience_package.source_code_package_id,
        environment_experience_commit_id=environment_experience_snapshot.commit_id,
        environment_experience_head_commit_id=environment_experience_head_commit_id,
        projection_experience_commit_id=(
            projection_receipt.steps[-1].commit_id
            if projection_receipt is not None and projection_receipt.steps
            else None
        ),
        projection_experience_head_commit_id=(
            section_surface_receipt.steps[-1].head_commit_id
            if section_surface_receipt is not None and section_surface_receipt.steps
            else (
                projection_receipt.steps[-1].head_commit_id
                if projection_receipt is not None and projection_receipt.steps
                else None
            )
        ),
        projection_experience_graph_commit_id=(
            graph_receipt.steps[-1].commit_id
            if graph_receipt is not None and graph_receipt.steps
            else None
        ),
        projection_experience_graph_head_commit_id=(
            graph_receipt.steps[-1].head_commit_id
            if graph_receipt is not None and graph_receipt.steps
            else None
        ),
        projection_experience_section_surface_commit_id=(
            section_surface_receipt.steps[-1].commit_id
            if section_surface_receipt is not None and section_surface_receipt.steps
            else None
        ),
        projection_experience_section_surface_head_commit_id=(
            section_surface_receipt.steps[-1].head_commit_id
            if section_surface_receipt is not None and section_surface_receipt.steps
            else None
        ),
        activation_profile_config_commit_id=_activation_receipt_detail_uuid(
            receipt=activation_topology_receipt,
            detail_key="profile_config_commit_id",
        ),
        activation_profile_config_head_commit_id=_activation_receipt_detail_uuid(
            receipt=activation_topology_receipt,
            detail_key="profile_config_head_commit_id",
        ),
        activation_profile_config_branch_id=_activation_receipt_detail_uuid(
            receipt=activation_topology_receipt,
            detail_key="profile_config_branch_id",
        ),
        activation_profile_config_projection_hash=_activation_receipt_detail_text(
            receipt=activation_topology_receipt,
            detail_key="profile_config_projection_hash",
        ),
        activation_profile_config_domain_object_instance_graph_id=(
            _activation_receipt_detail_uuid(
                receipt=activation_topology_receipt,
                detail_key="profile_config_domain_object_instance_graph_id",
            )
        ),
        activation_profile_config_object_instance_graph_commit_id=(
            _activation_receipt_detail_uuid(
                receipt=activation_topology_receipt,
                detail_key="profile_config_object_instance_graph_commit_id",
            )
        ),
        activation_action_experience_commit_id=_activation_receipt_detail_uuid(
            receipt=activation_topology_receipt,
            detail_key="action_experience_commit_id",
        ),
        activation_action_experience_head_commit_id=_activation_receipt_detail_uuid(
            receipt=activation_topology_receipt,
            detail_key="action_experience_head_commit_id",
        ),
        activation_invocation_config_commit_id=_activation_receipt_detail_uuid(
            receipt=activation_topology_receipt,
            detail_key="invocation_config_commit_id",
        ),
        activation_invocation_config_head_commit_id=_activation_receipt_detail_uuid(
            receipt=activation_topology_receipt,
            detail_key="invocation_config_head_commit_id",
        ),
        activation_reference_branch_ids_by_experience_name=(
            _activation_reference_branch_ids_by_experience_name(
                receipt=activation_topology_receipt,
            )
        ),
        program_config_commit_id=(
            program_receipts[0].steps[-1].commit_id
            if program_receipts[0] is not None and program_receipts[0].steps
            else None
        ),
        program_config_head_commit_id=(
            program_receipts[0].steps[-1].head_commit_id
            if program_receipts[0] is not None and program_receipts[0].steps
            else None
        ),
        program_impl_commit_id=(
            program_receipts[1].steps[-1].commit_id
            if program_receipts[1] is not None and program_receipts[1].steps
            else None
        ),
        program_impl_head_commit_id=(
            program_receipts[1].steps[-1].head_commit_id
            if program_receipts[1] is not None and program_receipts[1].steps
            else None
        ),
        package_commit_id=experience_package_snapshot.commit_id,
        package_head_commit_id=experience_package_head_commit_id,
        package_projection_hash=experience_package_projection_hash,
        package_object_instance_graph_commit_id=(
            experience_package_snapshot.object_instance_graph_commit_id
        ),
    )


def _activation_receipt_detail_uuid(
    *,
    receipt: MaterializationRunReceipt | None,
    detail_key: str,
) -> UUID | None:
    if receipt is None:
        return None
    for step in reversed(receipt.steps):
        raw_value = step.details.get(detail_key)
        if raw_value is None:
            continue
        return raw_value if isinstance(raw_value, UUID) else UUID(str(raw_value))
    return None


def _activation_receipt_detail_text(
    *,
    receipt: MaterializationRunReceipt | None,
    detail_key: str,
) -> str | None:
    if receipt is None:
        return None
    for step in reversed(receipt.steps):
        raw_value = step.details.get(detail_key)
        if raw_value is None:
            continue
        value = str(raw_value).strip()
        if value:
            return value
    return None


def _activation_reference_branch_ids_by_experience_name(
    *,
    receipt: MaterializationRunReceipt | None,
) -> Mapping[str, UUID]:
    if receipt is None:
        return {}
    branch_ids: dict[str, UUID] = {}
    for step in receipt.steps:
        raw_experience_name = step.details.get("experience_name")
        raw_branch_id = step.details.get("reference_branch_id")
        if raw_experience_name is None or raw_branch_id is None:
            continue
        branch_ids[str(raw_experience_name)] = (
            raw_branch_id
            if isinstance(raw_branch_id, UUID)
            else UUID(str(raw_branch_id))
        )
    return branch_ids


def _resolve_dependency_projection_reference_branch_ids(
    *,
    manifest_spec: AwareExperienceTomlSpec,
    compile_plan_payload: Mapping[str, object],
    semantic_materialization_context: Mapping[str, object] | None,
    existing: Mapping[str, UUID] | None,
) -> dict[str, UUID]:
    branch_ids = {str(name): branch_id for name, branch_id in (existing or {}).items()}
    local_projection_names = {
        str(row.get("name") or "").strip().casefold()
        for raw_row in compile_plan_payload.get("projection_experience_ownership", [])
        if isinstance(raw_row, Mapping)
        for row in (raw_row,)
        if str(row.get("name") or "").strip()
    }
    external_projection_names = tuple(
        sorted(
            name
            for name in _environment_profile_projection_experience_names(
                compile_plan_payload=compile_plan_payload
            )
            if name.casefold() not in local_projection_names
        )
    )
    if not external_projection_names:
        return branch_ids

    dependency_package_names = {
        dependency.package_name.strip().casefold()
        for dependency in manifest_spec.dependencies
        if dependency.kind is AwareExperienceDependencyKind.experience_package
        and dependency.package_name.strip()
    }
    dependency_base_branches: dict[str, UUID] = {
        existing_name.casefold(): branch_id
        for existing_name, branch_id in branch_ids.items()
        if existing_name.casefold() in dependency_package_names
    }
    raw_references = (semantic_materialization_context or {}).get(
        "workspace_experience_package_references", ()
    )
    if not isinstance(raw_references, Sequence) or isinstance(
        raw_references, (str, bytes)
    ):
        raise RuntimeError(
            "Experience dependency projection resolution requires Workspace Experience package references to be a sequence"
        )
    for raw_reference in raw_references:
        if not isinstance(raw_reference, Mapping):
            continue
        package_name = str(raw_reference.get("package_name") or "").strip()
        if package_name.casefold() not in dependency_package_names:
            continue
        raw_branch_id = raw_reference.get("semantic_branch_id")
        if raw_branch_id is None:
            continue
        branch_id = (
            raw_branch_id
            if isinstance(raw_branch_id, UUID)
            else UUID(str(raw_branch_id))
        )
        existing_branch_id = dependency_base_branches.get(package_name.casefold())
        if existing_branch_id is not None and existing_branch_id != branch_id:
            raise RuntimeError(
                "Experience dependency projection resolution found conflicting committed package branches "
                + f"for dependency {package_name!r}"
            )
        dependency_base_branches[package_name.casefold()] = branch_id

    unresolved_projection_names = tuple(
        name
        for name in external_projection_names
        if name.casefold()
        not in {existing_name.casefold() for existing_name in branch_ids}
    )
    if not dependency_base_branches and not unresolved_projection_names:
        return branch_ids
    if not dependency_base_branches:
        available_reference_packages = tuple(
            sorted(
                str(reference.get("package_name") or "").strip()
                for reference in raw_references
                if isinstance(reference, Mapping)
                and str(reference.get("package_name") or "").strip()
            )
        )
        raise RuntimeError(
            "Experience dependency projection resolution requires a committed Workspace Experience package reference; "
            + f"projection_refs={external_projection_names!r} declared_dependencies={tuple(sorted(dependency_package_names))!r} "
            + f"available_reference_packages={available_reference_packages!r}"
        )
    if len(dependency_base_branches) != 1:
        raise RuntimeError(
            "Experience dependency projection resolution cannot assign unowned external projection refs across multiple committed dependencies; "
            + f"projection_refs={external_projection_names!r} dependencies={tuple(sorted(dependency_base_branches))!r}"
        )
    dependency_branch_id = next(iter(dependency_base_branches.values()))
    for experience_name in external_projection_names:
        resolved_branch_id = derive_experience_reference_branch_id(
            base_branch_id=dependency_branch_id,
            experience_name=experience_name,
        )
        existing_branch_id = next(
            (
                branch_id
                for existing_name, branch_id in branch_ids.items()
                if existing_name.casefold() == experience_name.casefold()
            ),
            None,
        )
        if existing_branch_id is not None and existing_branch_id != resolved_branch_id:
            raise RuntimeError(
                "Experience dependency projection resolution found a projection branch that conflicts with committed dependency package truth "
                + f"for experience {experience_name!r}: have={existing_branch_id} expected={resolved_branch_id}"
            )
        branch_ids[experience_name] = resolved_branch_id
    return branch_ids


def _environment_profile_projection_experience_names(
    *, compile_plan_payload: Mapping[str, object]
) -> set[str]:
    names: set[str] = set()

    def _visit(value: object, *, key: str | None = None) -> None:
        if isinstance(value, Mapping):
            for child_key, child_value in value.items():
                normalized_key = str(child_key).strip()
                if normalized_key in {
                    "projection_experience_name",
                    "source_projection_experience_name",
                    "target_projection_experience_name",
                }:
                    name = str(child_value or "").strip()
                    if name:
                        names.add(name)
                    continue
                if (
                    normalized_key == "experience_name"
                    and key == "projection_experiences"
                ):
                    name = str(child_value or "").strip()
                    if name:
                        names.add(name)
                    continue
                _visit(child_value, key=normalized_key)
            return
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                _visit(item, key=key)

    _visit(
        compile_plan_payload.get("environment_profile_ownership", ()),
        key="environment_profile_ownership",
    )
    return names


__all__ = [
    "ExperiencePackageInstallScope",
    "ExperiencePackageMaterializationOrchestratorDependencies",
    "ExperiencePackageMaterializationResult",
    "ExperiencePackageMaterializationSpec",
    "coerce_experience_package_install_scope",
    "run_experience_package_materialization",
]
