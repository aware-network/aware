from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from collections.abc import Iterable
from pathlib import Path
import shutil
import tomllib
from typing import Mapping, TypeAlias, TypeVar

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.module_manifest.loader import load_aware_module_spec
from aware_code.package.manifest_loader import load_pubspec_yaml_package_manifest
from aware_meta.manifest.loader import load_aware_toml_spec
from aware_meta.manifest.spec import AwarePackageKind
from aware_orm.runtime.package_artifacts import DEFAULT_ARTIFACTS_DIR
from aware_meta.language_plugin import MetaLanguageMaterializationDestination
from aware_meta.materialization.language_service import (
    GraphMaterializationProfile,
    GraphMaterializationTransformRequest,
    GraphMaterializationTransformService,
    LanguagePluginDeclaredOutputProductionRequest,
    LanguageMaterializationRenderRequest,
    produce_language_plugin_declared_outputs,
    render_language_materialization,
)
from aware_meta.materialization.post_step_executor import (
    LanguageMaterializationPostStepExecutionRequest,
    execute_language_materialization_post_steps,
)
from aware_meta.materialization.post_step_plan import (
    LanguageMaterializationPostStepInput,
)
from aware_meta.materialization.package_runner import (
    LanguageMaterializationPackageBuildRequest,
    build_language_materialization_packages,
)
from aware_meta.materialization.schemas import (
    LocalMaterializationExecutionResult,
    MaterializationConfig,
    MaterializationOutcomeSummary,
    MaterializationPackageOutcome,
    MaterializationSource,
)
from aware_meta.graph.config.package_strategy import (
    ObjectConfigGraphPackageResult,
    ObjectConfigGraphPackageSpec,
)
from aware_meta.graph.config.handlers import (
    build_object_config_graph_overlays_from_annotations,
)
from aware_meta.graph.config.render.layout_strategy import (
    ObjectConfigGraphRenderLayoutStrategy,
)
from aware_meta.graph.config.model_bootstrap import get_node_function_config
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from python_grammar.layout_strategy import PythonLayoutStrategyTemplateMixin
from aware_utils.logging import logger
from aware_utils.string_transform import to_snake_case

from ..ir import (
    APICompilePlan,
    APICompilePlanArtifact,
    APIRuntimeArtifacts,
    emit_api_runtime_artifacts,
)
from ..interface.builder import ApiInterfaceSpecArtifact
from ..invocation.builder import ApiInvocationManifestArtifact
from ..manifest.spec import (
    AwareApiSemanticPackageExportKind,
    AwareApiTomlSemanticPackageExportSpec,
)
from ..workspace import APIWorkspaceSnapshot
from .lowering import (
    build_api_public_package_lowering_handoff,
    build_api_service_protocol_lowering_handoff,
)
from .models import (
    ApiProductRuntimeArtifactRef,
    ApiPublicPackagePlan,
    ApiPublicPackagePlanArtifact,
    ApiPublicPackageRenderJob,
    ApiPublicPackageRenderTarget,
    ApiServiceProtocolPlan,
    ApiServiceProtocolPlanArtifact,
    ApiServiceProtocolRenderJob,
    ApiServiceProtocolRenderTarget,
    ApiProductBackendHandoff,
    ApiPublicPackageApiPlan,
    ApiPublicPackageCapabilityPlan,
    ApiPublicPackageEndpointPlan,
    ApiPublicPackageRequestPlan,
    ApiPublicPackageResponsePlan,
    ApiPublicPackageStreamEventPlan,
    ApiPublicPackageStreamPlan,
    ApiServiceProtocolApiPlan,
    ApiServiceProtocolCapabilityPlan,
    ApiServiceProtocolEndpointFunctionPlan,
    ApiServiceProtocolEndpointPlan,
)
from .planner import build_api_public_package_plan, build_api_service_protocol_plan
from .dto_graph import build_api_public_package_dto_graph
from .service_protocol_graph import build_api_service_protocol_render_graph
from ..dependencies.runtime_resolution import (
    API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME,
    _RuntimeDependencyPackage,
    _build_aware_toml_package_index as _build_runtime_aware_toml_package_index,
    _load_required_dependency_object_config_graph as _load_required_runtime_dependency_object_config_graph,
    _resolve_api_dependency_packages,
    _resolve_aware_toml_path_by_package_name as _resolve_runtime_aware_toml_path_by_package_name,
    compute_api_dependency_source_digest_for_aware_toml,
    dump_api_accessible_dependency_graph_artifact_payload,
    load_api_accessible_dependency_graphs,
    load_api_accessible_dependency_graphs_from_runtime_artifact,
)
from .render_inputs import (
    build_api_public_package_render_inputs,
    build_api_service_protocol_render_inputs,
)
from .render_job import (
    build_api_public_package_render_job,
    build_api_service_protocol_render_job,
)


@dataclass(frozen=True, slots=True)
class ApiPublicPackageMaterializationResult:
    runtime_package_dir: Path
    runtime_artifacts: APIRuntimeArtifacts
    public_package_plan: ApiPublicPackagePlan
    render_job: ApiPublicPackageRenderJob
    dto_graph: ObjectConfigGraph
    materialization_result: LocalMaterializationExecutionResult


@dataclass(frozen=True, slots=True)
class ApiServiceProtocolMaterializationResult:
    runtime_package_dir: Path
    runtime_artifacts: APIRuntimeArtifacts
    public_package_materialization: ApiPublicPackageMaterializationResult
    service_protocol_plan: ApiServiceProtocolPlan
    render_job: ApiServiceProtocolRenderJob
    materialization_result: LocalMaterializationExecutionResult


@dataclass(frozen=True, slots=True)
class ApiDtoPackageMaterializationResult:
    runtime_package_dir: Path
    semantic_package_export: AwareApiTomlSemanticPackageExportSpec
    dependency_package: "_AccessibleDependencyPackage"
    package_root: Path
    import_root: str
    materialization_result: LocalMaterializationExecutionResult


_JsonObject: TypeAlias = dict[str, object]
_ArtifactT = TypeVar(
    "_ArtifactT",
    APICompilePlanArtifact,
    ApiInterfaceSpecArtifact,
    ApiInvocationManifestArtifact,
    ApiPublicPackagePlanArtifact,
    ApiServiceProtocolPlanArtifact,
)
_DART_PART_DIRECTIVE_RE = re.compile(
    r"^\s*part\s+(?!of\b)['\"]([^'\"]+)['\"]\s*;",
    re.MULTILINE,
)


def refresh_api_public_package_from_runtime_artifacts(
    *,
    snapshot: APIWorkspaceSnapshot,
    runtime_package_dir: Path,
    repo_root: Path,
    public_package_target_language: CodeLanguage = CodeLanguage.python,
    candidate_paths: tuple[Path, ...] = (),
    render_input_class_refs: tuple[str, ...] | None = None,
    accessible_graphs: tuple[ObjectConfigGraph, ...] | None = None,
    dependency_repo_roots: Iterable[str | Path] = (),
    execute_language_post_steps: bool = False,
    post_step_tool_env_by_tool_id: Mapping[str, Mapping[str, str]] | None = None,
    post_step_executable_overrides_by_tool_id: (
        Mapping[str, Mapping[str, str]] | None
    ) = None,
) -> ApiPublicPackageMaterializationResult:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_artifacts = _load_api_runtime_artifacts(
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
    )
    public_package_plan = _load_api_public_package_plan(
        runtime_package_dir=runtime_package_dir,
    )
    resolved_accessible_graphs = accessible_graphs
    if resolved_accessible_graphs is None:
        resolved_accessible_graphs = (
            _load_accessible_dependency_graphs_from_runtime_artifact_if_present(
                runtime_package_dir=runtime_package_dir,
            )
        )
    accessible_dependency_packages = _build_accessible_dependency_packages(
        snapshot=snapshot,
        accessible_graphs=resolved_accessible_graphs,
        dependency_repo_roots=dependency_repo_roots,
    )
    api_dto_export_package_names = _api_dto_export_package_names(snapshot=snapshot)
    use_external_api_dto_types = bool(
        api_dto_export_package_names
        and public_package_target_language == CodeLanguage.python
    )
    if api_dto_export_package_names:
        accessible_dependency_packages = _with_api_dto_export_packages(
            snapshot=snapshot,
            accessible_dependency_packages=accessible_dependency_packages,
            accessible_graphs=resolved_accessible_graphs,
            api_dto_exports=_api_dto_exports(snapshot=snapshot),
            dependency_repo_roots=dependency_repo_roots,
        )
    accessible_graphs = tuple(
        package.graph for package in accessible_dependency_packages
    )
    external_python_type_index_artifact = None
    if use_external_api_dto_types:
        external_python_type_index_artifact = (
            _emit_api_service_protocol_external_python_type_index_artifact(
                accessible_dependency_packages=accessible_dependency_packages,
                runtime_package_dir=runtime_package_dir,
                repo_root=repo_root,
                api_dto_package_names=api_dto_export_package_names,
            )
        )

    handoff = build_api_public_package_lowering_handoff(
        plan=public_package_plan,
        interface_spec_artifact=runtime_artifacts.interface_spec,
        invocation_manifest_artifact=runtime_artifacts.invocation_manifest,
        public_package_plan_artifact=runtime_artifacts.public_package_plan,
        extra_runtime_artifacts=(
            (external_python_type_index_artifact,)
            if external_python_type_index_artifact is not None
            else ()
        ),
    )
    render_job = build_api_public_package_render_job(
        handoff=handoff,
        target=_build_public_package_render_target(
            snapshot=snapshot,
            runtime_package_dir=runtime_package_dir,
            target_language=public_package_target_language,
            dependency_repo_roots=dependency_repo_roots,
        ),
        dependency_import_roots=_api_dto_dependency_import_roots(
            snapshot=snapshot,
            accessible_dependency_packages=accessible_dependency_packages,
        ),
    )
    render_job = build_api_public_package_render_inputs(render_job=render_job)

    dto_graph_root_class_refs = (
        _dart_public_package_root_class_refs(
            plan=public_package_plan,
            accessible_dependency_packages=accessible_dependency_packages,
            api_dto_package_names=api_dto_export_package_names,
        )
        if public_package_target_language == CodeLanguage.dart
        and api_dto_export_package_names
        else (
            ()
            if use_external_api_dto_types and render_input_class_refs is None
            else render_input_class_refs
        )
    )
    dto_graph = build_api_public_package_dto_graph(
        plan=public_package_plan,
        accessible_graphs=accessible_graphs,
        root_class_refs=dto_graph_root_class_refs,
    )

    layout = _build_public_package_layout_strategy(render_job=render_job)
    layout.bind_graph(dto_graph)

    materialization_result = _materialize_graph_via_meta(
        aware_root=repo_root,
        layout_strategy=layout,
        materialization_config=_with_runtime_package_spec(
            materialization_config=render_job.materialization_config,
            runtime_package_root=_runtime_public_package_root(
                runtime_package_dir=runtime_package_dir,
                target_language=public_package_target_language,
            ),
            destination_key="runtime_public_package",
        ),
        object_config_graph=dto_graph,
        candidate_paths=candidate_paths,
        execute_post_steps=execute_language_post_steps,
        post_step_tool_env_by_tool_id=post_step_tool_env_by_tool_id,
        post_step_executable_overrides_by_tool_id=(
            post_step_executable_overrides_by_tool_id
        ),
    )
    return ApiPublicPackageMaterializationResult(
        runtime_package_dir=runtime_package_dir,
        runtime_artifacts=runtime_artifacts,
        public_package_plan=public_package_plan,
        render_job=render_job,
        dto_graph=dto_graph,
        materialization_result=materialization_result,
    )


def refresh_api_service_protocol_from_runtime_artifacts(
    *,
    snapshot: APIWorkspaceSnapshot,
    runtime_package_dir: Path,
    repo_root: Path,
    public_package_candidate_paths: tuple[Path, ...] = (),
    service_protocol_candidate_paths: tuple[Path, ...] = (),
    public_package_render_input_class_refs: tuple[str, ...] | None = None,
    accessible_graphs: tuple[ObjectConfigGraph, ...] | None = None,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> ApiServiceProtocolMaterializationResult:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    public_package_materialization = refresh_api_public_package_from_runtime_artifacts(
        snapshot=snapshot,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
        candidate_paths=public_package_candidate_paths,
        render_input_class_refs=public_package_render_input_class_refs,
        accessible_graphs=accessible_graphs,
        dependency_repo_roots=dependency_repo_roots,
    )
    runtime_artifacts = public_package_materialization.runtime_artifacts
    service_protocol_plan = _load_api_service_protocol_plan(
        runtime_package_dir=runtime_package_dir,
    )
    resolved_accessible_graphs = accessible_graphs
    if resolved_accessible_graphs is None:
        resolved_accessible_graphs = (
            _load_accessible_dependency_graphs_from_runtime_artifact_if_present(
                runtime_package_dir=runtime_package_dir,
            )
        )
    accessible_dependency_packages = _build_accessible_dependency_packages(
        snapshot=snapshot,
        accessible_graphs=resolved_accessible_graphs,
        dependency_repo_roots=dependency_repo_roots,
    )
    api_dto_export_package_names = _api_dto_export_package_names(snapshot=snapshot)
    if api_dto_export_package_names:
        accessible_dependency_packages = _with_api_dto_export_packages(
            snapshot=snapshot,
            accessible_dependency_packages=accessible_dependency_packages,
            accessible_graphs=resolved_accessible_graphs,
            api_dto_exports=_api_dto_exports(snapshot=snapshot),
            dependency_repo_roots=dependency_repo_roots,
        )
    accessible_graphs = tuple(
        package.graph for package in accessible_dependency_packages
    )
    _ = _emit_api_accessible_dependency_graphs_artifact(
        accessible_graphs=accessible_graphs,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
        accessible_dependency_packages=accessible_dependency_packages,
        source_digest_package_names=_accessible_dependency_source_digest_package_names(
            accessible_dependency_packages=accessible_dependency_packages,
        ),
    )
    external_python_type_index_artifact = (
        _emit_api_service_protocol_external_python_type_index_artifact(
            accessible_dependency_packages=accessible_dependency_packages,
            runtime_package_dir=runtime_package_dir,
            repo_root=repo_root,
            api_dto_package_names=api_dto_export_package_names,
        )
    )
    handoff = build_api_service_protocol_lowering_handoff(
        plan=service_protocol_plan,
        interface_spec_artifact=runtime_artifacts.interface_spec,
        invocation_manifest_artifact=runtime_artifacts.invocation_manifest,
        public_package_plan_artifact=runtime_artifacts.public_package_plan,
        service_protocol_plan_artifact=runtime_artifacts.service_protocol_plan,
        extra_runtime_artifacts=(external_python_type_index_artifact,),
    )
    contract_dependency_import_roots = _api_contract_dependency_import_roots(
        snapshot=snapshot,
        accessible_dependency_packages=accessible_dependency_packages,
    )
    render_job = build_api_service_protocol_render_job(
        handoff=handoff,
        target=_build_default_service_protocol_render_target(
            snapshot=snapshot,
            runtime_package_dir=runtime_package_dir,
        ),
        dependency_import_roots=contract_dependency_import_roots,
        include_public_package_dependency=not bool(contract_dependency_import_roots),
    )
    render_job = build_api_service_protocol_render_inputs(render_job=render_job)
    render_graph = build_api_service_protocol_render_graph(
        plan=service_protocol_plan,
        accessible_graphs=accessible_graphs,
    )

    layout = _ApiServiceProtocolPythonLayout(
        base_dir=render_job.materialization_config.target_output_dir,
        import_root=render_job.materialization_config.import_root,
    )
    layout.bind_graph(render_graph)

    materialization_result = _materialize_graph_via_meta(
        aware_root=repo_root,
        layout_strategy=layout,
        materialization_config=_with_runtime_package_spec(
            materialization_config=render_job.materialization_config,
            runtime_package_root=_runtime_service_protocol_package_root(
                runtime_package_dir=runtime_package_dir
            ),
            destination_key="runtime_service_protocol_package",
        ),
        object_config_graph=render_graph,
        python_external_import_overrides_by_entity_id=(
            _python_import_overrides_from_dependency_artifacts(
                accessible_dependency_packages
            )
        ),
        candidate_paths=service_protocol_candidate_paths,
    )
    return ApiServiceProtocolMaterializationResult(
        runtime_package_dir=runtime_package_dir,
        runtime_artifacts=runtime_artifacts,
        public_package_materialization=public_package_materialization,
        service_protocol_plan=service_protocol_plan,
        render_job=render_job,
        materialization_result=materialization_result,
    )


@dataclass(frozen=True, slots=True)
class _AccessibleDependencyPackage:
    package_name: str
    package_kind: str
    package_root: Path
    import_root: str
    graph: ObjectConfigGraph


@dataclass(slots=True)
class _PrecompiledDependencyGraphLookup:
    graphs_by_fqn_prefix: dict[str, ObjectConfigGraph]
    graphs_by_name: dict[str, ObjectConfigGraph]
    consumed_graph_ids: set[object]


@dataclass
class _ApiPublicPackagePythonLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = None

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return Path("models") / f"{to_snake_case(class_config.name)}.py"

    def get_enum_file_path(self, enum_config) -> Path:  # pragma: no cover
        return Path("models") / f"{to_snake_case(enum_config.name)}.py"

    def get_function_file_path(self, function_config) -> Path:  # pragma: no cover
        return Path("models") / "functions.py"

    def get_file_extension(self) -> str:
        return ".py"

    def get_module_import_path(self, file_path: Path) -> str:
        parts = list(file_path.parts)
        if parts:
            parts[-1] = Path(parts[-1]).stem
        module_parts = [part for part in parts if part]
        if self.import_root:
            module_parts.insert(0, self.import_root)
        return ".".join(module_parts).strip(".")


@dataclass
class _ApiServiceProtocolPythonLayout(ObjectConfigGraphRenderLayoutStrategy):
    base_dir: Path
    import_root: str | None = None

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.python

    def get_class_file_path(self, class_config: ClassConfig) -> Path:
        return Path("models") / f"{to_snake_case(class_config.name)}.py"

    def get_enum_file_path(self, enum_config) -> Path:  # pragma: no cover
        return Path("models") / f"{to_snake_case(enum_config.name)}.py"

    def get_function_file_path(self, function_config) -> Path:  # pragma: no cover
        return Path("models") / "functions.py"

    def get_file_extension(self) -> str:
        return ".py"

    def get_module_import_path(self, file_path: Path) -> str:
        parts = list(file_path.parts)
        if parts:
            parts[-1] = Path(parts[-1]).stem
        module_parts = [part for part in parts if part]
        if self.import_root:
            module_parts.insert(0, self.import_root)
        return ".".join(module_parts).strip(".")


def materialize_api_public_package(
    *,
    snapshot: APIWorkspaceSnapshot,
    plan: APICompilePlan,
    runtime_package_dir: Path,
    repo_root: Path,
    public_package_target_language: CodeLanguage = CodeLanguage.python,
    accessible_graphs: tuple[ObjectConfigGraph, ...] | None = None,
    candidate_paths: tuple[Path, ...] = (),
    dependency_repo_roots: Iterable[str | Path] = (),
    execute_language_post_steps: bool = False,
    post_step_tool_env_by_tool_id: Mapping[str, Mapping[str, str]] | None = None,
    post_step_executable_overrides_by_tool_id: (
        Mapping[str, Mapping[str, str]] | None
    ) = None,
) -> ApiPublicPackageMaterializationResult:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)
    accessible_dependency_packages = _build_accessible_dependency_packages(
        snapshot=snapshot,
        accessible_graphs=accessible_graphs,
        dependency_repo_roots=dependency_repo_roots,
    )
    api_dto_export_package_names = _api_dto_export_package_names(snapshot=snapshot)
    use_external_api_dto_types = bool(
        api_dto_export_package_names
        and public_package_target_language == CodeLanguage.python
    )
    if api_dto_export_package_names:
        accessible_dependency_packages = _with_api_dto_export_packages(
            snapshot=snapshot,
            accessible_dependency_packages=accessible_dependency_packages,
            accessible_graphs=accessible_graphs,
            api_dto_exports=_api_dto_exports(snapshot=snapshot),
            dependency_repo_roots=dependency_repo_roots,
        )
    resolved_accessible_graphs = tuple(
        package.graph for package in accessible_dependency_packages
    )
    _ = _emit_api_accessible_dependency_graphs_artifact(
        accessible_graphs=resolved_accessible_graphs,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
        accessible_dependency_packages=accessible_dependency_packages,
        source_digest_package_names=_accessible_dependency_source_digest_package_names(
            accessible_dependency_packages=accessible_dependency_packages,
        ),
    )

    runtime_artifacts = emit_api_runtime_artifacts(
        plan=plan,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
        accessible_graphs=resolved_accessible_graphs,
    )
    public_package_plan = build_api_public_package_plan(
        package_name=plan.package_name,
        fqn_prefix=plan.fqn_prefix,
        api_ontology=plan.api_ontology,
    )
    external_python_type_index_artifact = None
    if use_external_api_dto_types:
        external_python_type_index_artifact = (
            _emit_api_service_protocol_external_python_type_index_artifact(
                accessible_dependency_packages=accessible_dependency_packages,
                runtime_package_dir=runtime_package_dir,
                repo_root=repo_root,
                api_dto_package_names=api_dto_export_package_names,
            )
        )
    handoff = build_api_public_package_lowering_handoff(
        plan=public_package_plan,
        interface_spec_artifact=runtime_artifacts.interface_spec,
        invocation_manifest_artifact=runtime_artifacts.invocation_manifest,
        public_package_plan_artifact=runtime_artifacts.public_package_plan,
        extra_runtime_artifacts=(
            (external_python_type_index_artifact,)
            if external_python_type_index_artifact is not None
            else ()
        ),
    )
    render_job = build_api_public_package_render_job(
        handoff=handoff,
        target=_build_public_package_render_target(
            snapshot=snapshot,
            runtime_package_dir=runtime_package_dir,
            target_language=public_package_target_language,
            dependency_repo_roots=dependency_repo_roots,
        ),
        dependency_import_roots=_api_dto_dependency_import_roots(
            snapshot=snapshot,
            accessible_dependency_packages=accessible_dependency_packages,
        ),
    )
    render_job = build_api_public_package_render_inputs(render_job=render_job)

    dto_graph_root_class_refs = (
        _dart_public_package_root_class_refs(
            plan=public_package_plan,
            accessible_dependency_packages=accessible_dependency_packages,
            api_dto_package_names=api_dto_export_package_names,
        )
        if public_package_target_language == CodeLanguage.dart
        and api_dto_export_package_names
        else (() if use_external_api_dto_types else None)
    )
    dto_graph = build_api_public_package_dto_graph(
        plan=public_package_plan,
        accessible_graphs=resolved_accessible_graphs,
        root_class_refs=dto_graph_root_class_refs,
    )

    layout = _build_public_package_layout_strategy(render_job=render_job)
    layout.bind_graph(dto_graph)

    materialization_result = _materialize_graph_via_meta(
        aware_root=repo_root,
        layout_strategy=layout,
        materialization_config=_with_runtime_package_spec(
            materialization_config=render_job.materialization_config,
            runtime_package_root=_runtime_public_package_root(
                runtime_package_dir=runtime_package_dir,
                target_language=public_package_target_language,
            ),
            destination_key="runtime_public_package",
        ),
        object_config_graph=dto_graph,
        candidate_paths=candidate_paths,
        execute_post_steps=execute_language_post_steps,
        post_step_tool_env_by_tool_id=post_step_tool_env_by_tool_id,
        post_step_executable_overrides_by_tool_id=(
            post_step_executable_overrides_by_tool_id
        ),
    )
    return ApiPublicPackageMaterializationResult(
        runtime_package_dir=runtime_package_dir,
        runtime_artifacts=runtime_artifacts,
        public_package_plan=public_package_plan,
        render_job=render_job,
        dto_graph=dto_graph,
        materialization_result=materialization_result,
    )


def materialize_api_service_protocol(
    *,
    snapshot: APIWorkspaceSnapshot,
    plan: APICompilePlan,
    runtime_package_dir: Path,
    repo_root: Path,
    accessible_graphs: tuple[ObjectConfigGraph, ...] | None = None,
    public_package_candidate_paths: tuple[Path, ...] = (),
    service_protocol_candidate_paths: tuple[Path, ...] = (),
    dependency_repo_roots: Iterable[str | Path] = (),
) -> ApiServiceProtocolMaterializationResult:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)

    public_package_materialization = materialize_api_public_package(
        snapshot=snapshot,
        plan=plan,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
        accessible_graphs=accessible_graphs,
        candidate_paths=public_package_candidate_paths,
        dependency_repo_roots=dependency_repo_roots,
    )
    runtime_artifacts = public_package_materialization.runtime_artifacts
    accessible_dependency_packages = _build_accessible_dependency_packages(
        snapshot=snapshot,
        accessible_graphs=accessible_graphs,
        dependency_repo_roots=dependency_repo_roots,
    )
    api_dto_export_package_names = _api_dto_export_package_names(snapshot=snapshot)
    if api_dto_export_package_names:
        accessible_dependency_packages = _with_api_dto_export_packages(
            snapshot=snapshot,
            accessible_dependency_packages=accessible_dependency_packages,
            accessible_graphs=accessible_graphs,
            api_dto_exports=_api_dto_exports(snapshot=snapshot),
            dependency_repo_roots=dependency_repo_roots,
        )
    resolved_accessible_graphs = tuple(
        package.graph for package in accessible_dependency_packages
    )
    _ = _emit_api_accessible_dependency_graphs_artifact(
        accessible_graphs=resolved_accessible_graphs,
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
        accessible_dependency_packages=accessible_dependency_packages,
        source_digest_package_names=_accessible_dependency_source_digest_package_names(
            accessible_dependency_packages=accessible_dependency_packages,
        ),
    )
    service_protocol_plan = build_api_service_protocol_plan(
        package_name=plan.package_name,
        fqn_prefix=plan.fqn_prefix,
        api_ontology=plan.api_ontology,
        accessible_graphs=resolved_accessible_graphs,
    )
    external_python_type_index_artifact = (
        _emit_api_service_protocol_external_python_type_index_artifact(
            accessible_dependency_packages=accessible_dependency_packages,
            runtime_package_dir=runtime_package_dir,
            repo_root=repo_root,
            api_dto_package_names=api_dto_export_package_names,
        )
    )
    handoff = build_api_service_protocol_lowering_handoff(
        plan=service_protocol_plan,
        interface_spec_artifact=runtime_artifacts.interface_spec,
        invocation_manifest_artifact=runtime_artifacts.invocation_manifest,
        public_package_plan_artifact=runtime_artifacts.public_package_plan,
        service_protocol_plan_artifact=runtime_artifacts.service_protocol_plan,
        extra_runtime_artifacts=(external_python_type_index_artifact,),
    )
    contract_dependency_import_roots = _api_contract_dependency_import_roots(
        snapshot=snapshot,
        accessible_dependency_packages=accessible_dependency_packages,
    )
    render_job = build_api_service_protocol_render_job(
        handoff=handoff,
        target=_build_default_service_protocol_render_target(
            snapshot=snapshot,
            runtime_package_dir=runtime_package_dir,
        ),
        dependency_import_roots=contract_dependency_import_roots,
        include_public_package_dependency=not bool(contract_dependency_import_roots),
    )
    render_job = build_api_service_protocol_render_inputs(render_job=render_job)
    render_graph = build_api_service_protocol_render_graph(
        plan=service_protocol_plan,
        accessible_graphs=resolved_accessible_graphs,
    )

    layout = _ApiServiceProtocolPythonLayout(
        base_dir=render_job.materialization_config.target_output_dir,
        import_root=render_job.materialization_config.import_root,
    )
    layout.bind_graph(render_graph)

    materialization_result = _materialize_graph_via_meta(
        aware_root=repo_root,
        layout_strategy=layout,
        materialization_config=_with_runtime_package_spec(
            materialization_config=render_job.materialization_config,
            runtime_package_root=_runtime_service_protocol_package_root(
                runtime_package_dir=runtime_package_dir
            ),
            destination_key="runtime_service_protocol_package",
        ),
        object_config_graph=render_graph,
        python_external_import_overrides_by_entity_id=(
            _python_import_overrides_from_dependency_artifacts(
                accessible_dependency_packages
            )
        ),
        candidate_paths=service_protocol_candidate_paths,
    )
    return ApiServiceProtocolMaterializationResult(
        runtime_package_dir=runtime_package_dir,
        runtime_artifacts=runtime_artifacts,
        public_package_materialization=public_package_materialization,
        service_protocol_plan=service_protocol_plan,
        render_job=render_job,
        materialization_result=materialization_result,
    )


def materialize_api_dto_packages(
    *,
    snapshot: APIWorkspaceSnapshot,
    runtime_package_dir: Path,
    repo_root: Path,
    accessible_graphs: tuple[ObjectConfigGraph, ...] | None = None,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[ApiDtoPackageMaterializationResult, ...]:
    api_dto_exports = tuple(
        export
        for export in snapshot.spec.semantic_package_exports
        if export.kind is AwareApiSemanticPackageExportKind.api_dto
    )
    if not api_dto_exports:
        return ()

    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)
    accessible_dependency_packages = _build_accessible_dependency_packages(
        snapshot=snapshot,
        accessible_graphs=accessible_graphs,
        dependency_repo_roots=dependency_repo_roots,
    )
    accessible_dependency_packages = _with_api_dto_export_packages(
        snapshot=snapshot,
        accessible_dependency_packages=accessible_dependency_packages,
        accessible_graphs=accessible_graphs,
        api_dto_exports=api_dto_exports,
        dependency_repo_roots=dependency_repo_roots,
    )
    _ = _emit_api_accessible_dependency_graphs_artifact(
        accessible_graphs=tuple(
            package.graph for package in accessible_dependency_packages
        ),
        runtime_package_dir=runtime_package_dir,
        repo_root=repo_root,
        accessible_dependency_packages=accessible_dependency_packages,
        source_digest_package_names=_accessible_dependency_source_digest_package_names(
            accessible_dependency_packages=accessible_dependency_packages,
        ),
    )
    packages_by_name = {
        package.package_name: package for package in accessible_dependency_packages
    }
    results: list[ApiDtoPackageMaterializationResult] = []
    for export in sorted(
        api_dto_exports,
        key=lambda item: (
            item.workspace_materialization_order,
            item.package_name.casefold(),
        ),
    ):
        package = packages_by_name.get(export.package_name)
        if package is None:
            raise RuntimeError(
                "API DTO semantic export is not present in the API dependency graph: "
                + f"package_name={export.package_name!r}"
            )
        manifest_path = (snapshot.package_root / export.manifest_path).resolve()
        package_manifest_path = package.package_root / "aware.toml"
        if manifest_path != package_manifest_path.resolve():
            raise RuntimeError(
                "API DTO semantic export manifest_path resolved to a different package "
                + f"than the API dependency graph: export={manifest_path} "
                + f"dependency={package_manifest_path.resolve()}"
            )
        import_root = package.import_root
        package_graph = _with_python_render_overlays(
            _api_dto_graph_with_source_layouts(
                package=package,
                snapshot=snapshot,
            )
        )
        package_root = _resolve_python_api_dto_package_root(
            snapshot=snapshot,
            import_root=import_root,
        )
        render_output_dir = (
            runtime_package_dir / "api_dto" / package.package_name / "python" / "render"
        ).resolve()
        entity_template_paths = _python_api_dto_entity_template_paths(
            package=package,
            snapshot=snapshot,
        )
        layout = PythonLayoutStrategyTemplateMixin(
            base_dir=render_output_dir,
            entity_template_paths=entity_template_paths,
            import_root=import_root,
        )
        layout.bind_graph(package_graph)
        external_dependency_packages = tuple(
            dependency
            for dependency in accessible_dependency_packages
            if dependency.package_name != package.package_name
        )
        dependency_distribution_names = _api_dto_dependency_distribution_names(
            dto_package=package,
            accessible_dependency_packages=accessible_dependency_packages,
        )
        materialization_result = _materialize_graph_via_meta(
            aware_root=repo_root,
            layout_strategy=layout,
            materialization_config=MaterializationConfig(
                name=f"api-dto-package-python-{package.package_name}",
                source_aware_toml_path=manifest_path,
                source_package_name=package.package_name,
                target_language=CodeLanguage.python,
                target_output_dir=render_output_dir,
                manifest_path=manifest_path,
                import_root=import_root,
                packages=[
                    ObjectConfigGraphPackageSpec(
                        name=import_root,
                        package_name=import_root,
                        package_root=package_root,
                        import_root=import_root,
                        version=f"0.{snapshot.spec.api.version_number}.0",
                        description=(
                            f"Generated API DTO package for {package.package_name}."
                        ),
                        dependencies=[
                            *dependency_distribution_names,
                            "aware-types",
                            "aware-utils",
                            "pydantic>=2.8.0,<3.0.0",
                        ],
                        metadata={
                            "aware_package_kind": "api_dto",
                            "semantic_package_export_kind": export.kind.value,
                            "semantic_package_name": package.package_name,
                        },
                    )
                ],
                source=MaterializationSource.api,
            ),
            object_config_graph=package_graph,
            external_runtime_graphs=tuple(
                dependency.graph for dependency in external_dependency_packages
            ),
            external_import_roots_by_graph_key=_external_import_roots_by_graph_key(
                external_dependency_packages
            ),
            python_external_import_overrides_by_entity_id=(
                _python_import_overrides_from_dependency_artifacts(
                    external_dependency_packages
                )
            ),
        )
        results.append(
            ApiDtoPackageMaterializationResult(
                runtime_package_dir=runtime_package_dir,
                semantic_package_export=export,
                dependency_package=package,
                package_root=package_root,
                import_root=import_root,
                materialization_result=materialization_result,
            )
        )
    return tuple(results)


def build_api_accessible_dependency_graphs(
    *,
    snapshot: APIWorkspaceSnapshot,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[ObjectConfigGraph, ...]:
    """Compatibility path for direct callers without a Meta service host."""

    return load_api_accessible_dependency_graphs(
        snapshot=snapshot,
        dependency_repo_roots=dependency_repo_roots,
    )


def _build_public_package_render_target(
    *,
    snapshot: APIWorkspaceSnapshot,
    runtime_package_dir: Path,
    target_language: CodeLanguage,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> ApiPublicPackageRenderTarget:
    if target_language == CodeLanguage.python:
        import_root = _derive_python_import_root(snapshot=snapshot)
        public_root = _resolve_python_public_package_root(
            snapshot=snapshot, import_root=import_root
        )
        description = snapshot.spec.api.description or snapshot.spec.api.title
        if description is None:
            description = (
                f"Generated public package for {snapshot.spec.api.package_name}."
            )
        return ApiPublicPackageRenderTarget(
            target_language=CodeLanguage.python,
            source_aware_toml_path=snapshot.spec_path,
            target_output_dir=(
                runtime_package_dir / "public_package" / "python" / "render"
            ).resolve(),
            package_root=public_root,
            package_name=import_root,
            repo_root=snapshot.repo_root,
            dependency_repo_roots=tuple(
                Path(root).expanduser().resolve() for root in dependency_repo_roots
            ),
            import_root=import_root,
            version=f"0.{snapshot.spec.api.version_number}.0",
            description=description,
        )

    if target_language == CodeLanguage.dart:
        package_name = _derive_dart_public_package_name(snapshot=snapshot)
        public_root = _resolve_dart_public_package_root(
            snapshot=snapshot, package_name=package_name
        )
        description = snapshot.spec.api.description or snapshot.spec.api.title
        if description is None:
            description = (
                f"Generated public package for {snapshot.spec.api.package_name}."
            )
        return ApiPublicPackageRenderTarget(
            target_language=CodeLanguage.dart,
            source_aware_toml_path=snapshot.spec_path,
            target_output_dir=(
                runtime_package_dir / "public_package" / "dart" / "render"
            ).resolve(),
            package_root=public_root,
            package_name=package_name,
            repo_root=snapshot.repo_root,
            dependency_repo_roots=tuple(
                Path(root).expanduser().resolve() for root in dependency_repo_roots
            ),
            path_dependencies=_dart_public_package_path_dependencies(
                snapshot=snapshot,
                dependency_repo_roots=dependency_repo_roots,
            ),
            import_root=None,
            version=f"0.{snapshot.spec.api.version_number}.0",
            description=description,
        )

    raise ValueError(
        f"Unsupported API public-package target language: {target_language.value}"
    )


def _build_default_render_target(
    *,
    snapshot: APIWorkspaceSnapshot,
    runtime_package_dir: Path,
) -> ApiPublicPackageRenderTarget:
    return _build_public_package_render_target(
        snapshot=snapshot,
        runtime_package_dir=runtime_package_dir,
        target_language=CodeLanguage.python,
    )


def _build_default_service_protocol_render_target(
    *,
    snapshot: APIWorkspaceSnapshot,
    runtime_package_dir: Path,
) -> ApiServiceProtocolRenderTarget:
    import_root = _derive_python_service_protocol_import_root(snapshot=snapshot)
    service_root = _resolve_python_service_protocol_root(
        snapshot=snapshot, import_root=import_root
    )
    description = snapshot.spec.api.description or snapshot.spec.api.title
    if description is None:
        description = (
            f"Generated service protocol package for {snapshot.spec.api.package_name}."
        )
    return ApiServiceProtocolRenderTarget(
        target_language=CodeLanguage.python,
        source_aware_toml_path=snapshot.spec_path,
        target_output_dir=(
            runtime_package_dir / "service_protocol" / "python" / "render"
        ).resolve(),
        package_root=service_root,
        package_name=import_root,
        import_root=import_root,
        version=f"0.{snapshot.spec.api.version_number}.0",
        description=description,
    )


def _runtime_public_package_root(
    *,
    runtime_package_dir: Path,
    target_language: CodeLanguage,
) -> Path:
    return (
        runtime_package_dir / "public_package" / target_language.value / "package"
    ).resolve()


def _runtime_service_protocol_package_root(*, runtime_package_dir: Path) -> Path:
    return (
        runtime_package_dir / "service_protocol" / CodeLanguage.python.value / "package"
    ).resolve()


def _with_runtime_package_spec(
    *,
    materialization_config: MaterializationConfig,
    runtime_package_root: Path,
    destination_key: str,
) -> MaterializationConfig:
    if not materialization_config.packages:
        return materialization_config
    resolved_runtime_package_root = runtime_package_root.resolve()
    for package in materialization_config.packages:
        if (
            package.package_root is not None
            and Path(package.package_root).resolve() == resolved_runtime_package_root
        ):
            return materialization_config
    runtime_spec = _runtime_package_spec(
        package=materialization_config.packages[0],
        runtime_package_root=resolved_runtime_package_root,
        destination_key=destination_key,
    )
    return materialization_config.model_copy(
        update={"packages": [*materialization_config.packages, runtime_spec]}
    )


def _runtime_package_spec(
    *,
    package: ObjectConfigGraphPackageSpec,
    runtime_package_root: Path,
    destination_key: str,
) -> ObjectConfigGraphPackageSpec:
    metadata = dict(package.metadata or {})
    metadata["api_product_runtime_package"] = "true"
    metadata["api_product_runtime_destination_key"] = destination_key
    return package.model_copy(
        update={
            "package_root": runtime_package_root,
            "metadata": metadata,
        }
    )


def _derive_python_import_root(*, snapshot: APIWorkspaceSnapshot) -> str:
    token = (snapshot.spec.api.fqn_prefix or snapshot.spec.api.package_name).strip()
    token = token.replace("-", "_")
    return token or "aware_api_public_package"


def _derive_python_service_protocol_import_root(
    *, snapshot: APIWorkspaceSnapshot
) -> str:
    token = _derive_python_import_root(snapshot=snapshot)
    if token.endswith("_api"):
        token = token[: -len("_api")]
    token = token.strip("_")
    return f"{token}_protocol" if token else "aware_api_protocol"


def _derive_dart_public_package_name(*, snapshot: APIWorkspaceSnapshot) -> str:
    token = (snapshot.spec.api.fqn_prefix or snapshot.spec.api.package_name).strip()
    token = token.replace("-", "_")
    return token or "aware_api_public_package"


def _resolve_python_public_package_root(
    *, snapshot: APIWorkspaceSnapshot, import_root: str
) -> Path:
    targets = snapshot.spec.targets.python
    return _resolve_python_product_package_root(
        snapshot=snapshot,
        targets=targets,
        legacy_root_dir=None if targets is None else targets.public_package.root_dir,
        package_dir=None if targets is None else targets.public_package.package_dir,
        import_root=import_root,
    )


def _resolve_python_service_protocol_root(
    *, snapshot: APIWorkspaceSnapshot, import_root: str
) -> Path:
    targets = snapshot.spec.targets.python
    return _resolve_python_product_package_root(
        snapshot=snapshot,
        targets=targets,
        legacy_root_dir=None if targets is None else targets.service_protocol.root_dir,
        package_dir=None if targets is None else targets.service_protocol.package_dir,
        import_root=import_root,
    )


def _resolve_python_api_dto_package_root(
    *, snapshot: APIWorkspaceSnapshot, import_root: str
) -> Path:
    targets = snapshot.spec.targets.python
    return _resolve_python_product_package_root(
        snapshot=snapshot,
        targets=targets,
        legacy_root_dir=None,
        package_dir=import_root,
        import_root=import_root,
    )


def _resolve_dart_public_package_root(
    *, snapshot: APIWorkspaceSnapshot, package_name: str
) -> Path:
    targets = snapshot.spec.targets.dart
    if targets is None:
        raise ValueError(
            "Dart public API package materialization requires [targets.dart] in aware.api.toml "
            + f"(package={snapshot.spec.api.package_name!r})"
        )
    if targets.public_package.root_dir:
        return (snapshot.package_root / targets.public_package.root_dir).resolve()
    language_root = "dart" if not targets.root_dir else targets.root_dir
    package_dir = targets.public_package.package_dir or package_name
    return (snapshot.package_root / language_root / package_dir).resolve()


def _dart_public_package_path_dependencies(
    *,
    snapshot: APIWorkspaceSnapshot,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[tuple[str, Path], ...]:
    required_package_names = ("aware_api", "aware_model_helpers")
    dependencies: dict[str, Path] = {}
    candidate_workspace_roots = tuple(
        dict.fromkeys(
            (
                snapshot.repo_root.resolve(),
                *(Path(root).expanduser().resolve() for root in dependency_repo_roots),
            )
        )
    )
    for workspace_root in candidate_workspace_roots:
        for package_name in required_package_names:
            if package_name in dependencies:
                continue
            dependency = _dart_code_path_dependency_from_workspace_root(
                workspace_root=workspace_root,
                package_name=package_name,
            )
            if dependency is not None:
                dependencies[package_name] = dependency

    for module_root in _api_module_roots_for_path_dependencies(
        snapshot=snapshot,
        dependency_repo_roots=dependency_repo_roots,
    ):
        for package_name in required_package_names:
            if package_name in dependencies:
                continue
            dependency = _dart_code_path_dependency_from_module_root(
                module_root=module_root,
                package_name=package_name,
            )
            if dependency is not None:
                dependencies[package_name] = dependency
    return tuple(
        (package_name, dependencies[package_name])
        for package_name in required_package_names
        if package_name in dependencies
    )


def _dart_code_path_dependency_from_workspace_root(
    *, workspace_root: Path, package_name: str
) -> Path | None:
    workspace_toml = workspace_root / "aware.workspace.toml"
    if not workspace_toml.is_file():
        return None
    with workspace_toml.open("rb") as stream:
        raw = tomllib.load(stream)
    workspace_spec = raw.get("workspace")
    codes = workspace_spec.get("codes") if isinstance(workspace_spec, dict) else None
    if not isinstance(codes, list):
        codes = raw.get("codes")
    if not isinstance(codes, list):
        return None
    for raw_manifest in codes:
        if not isinstance(raw_manifest, str) or not raw_manifest.strip():
            continue
        manifest_path = (workspace_root / raw_manifest).resolve()
        if manifest_path.name != "pubspec.yaml" or not manifest_path.is_file():
            continue
        package_manifest = load_pubspec_yaml_package_manifest(toml_path=manifest_path)
        if package_manifest.package_name == package_name:
            return manifest_path.parent
    return None


def _dart_code_path_dependency_from_module_root(
    *, module_root: Path, package_name: str
) -> Path | None:
    module_spec = load_aware_module_spec(toml_path=module_root / "aware.module.toml")
    for package in module_spec.packages:
        if package.kind != "code":
            continue
        manifest_path = (module_root / package.manifest).resolve()
        if manifest_path.name != "pubspec.yaml" or not manifest_path.is_file():
            continue
        package_manifest = load_pubspec_yaml_package_manifest(toml_path=manifest_path)
        if package_manifest.package_name == package_name:
            return manifest_path.parent
    return None


def _api_module_roots_for_path_dependencies(
    *,
    snapshot: APIWorkspaceSnapshot,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[Path, ...]:
    roots: list[Path] = []
    local_module_root = _module_root_for_snapshot(snapshot=snapshot)
    if local_module_root is not None:
        roots.append(local_module_root)
    roots.extend(
        _candidate_module_roots_for_path_dependencies(repo_root=snapshot.repo_root)
    )
    for repo_root in (
        Path(root).expanduser().resolve() for root in dependency_repo_roots
    ):
        module_roots = _candidate_module_roots_for_path_dependencies(
            repo_root=repo_root
        )
        roots.extend(module_roots)
    return tuple(dict.fromkeys(root.resolve() for root in roots))


def _candidate_module_roots_for_path_dependencies(
    *, repo_root: Path
) -> tuple[Path, ...]:
    roots: list[Path] = []
    modules_root = repo_root / "modules"
    workspaces_root = repo_root / "workspaces"
    if workspaces_root.is_dir():
        for module_toml in sorted(
            workspaces_root.glob("*/modules/*/aware.module.toml")
        ):
            roots.append(module_toml.parent)
    if roots or not modules_root.is_dir():
        return tuple(dict.fromkeys(root.resolve() for root in roots))
    roots.extend(
        module_toml.parent
        for module_toml in sorted(modules_root.glob("*/aware.module.toml"))
    )
    return tuple(dict.fromkeys(root.resolve() for root in roots))


def _module_root_for_snapshot(*, snapshot: APIWorkspaceSnapshot) -> Path | None:
    repo_root = snapshot.repo_root.resolve()
    for candidate in (snapshot.package_root.resolve(), *snapshot.package_root.parents):
        if (candidate / "aware.module.toml").is_file():
            return candidate
        if candidate == repo_root:
            break
    return None


def _build_public_package_layout_strategy(
    *,
    render_job: ApiPublicPackageRenderJob,
) -> ObjectConfigGraphRenderLayoutStrategy:
    if render_job.target.target_language == CodeLanguage.python:
        return _ApiPublicPackagePythonLayout(
            base_dir=render_job.materialization_config.target_output_dir,
            import_root=render_job.materialization_config.import_root,
        )
    if render_job.target.target_language == CodeLanguage.dart:
        from dart_grammar.layout_strategy import DartLayoutStrategyTemplateMixin

        return DartLayoutStrategyTemplateMixin(
            base_dir=render_job.materialization_config.target_output_dir,
            import_root=render_job.materialization_config.import_root,
        )
    raise ValueError(
        "Unsupported API public-package layout language: "
        + f"{render_job.target.target_language.value}"
    )


def _resolve_python_product_package_root(
    *,
    snapshot: APIWorkspaceSnapshot,
    targets,
    legacy_root_dir: str | None,
    package_dir: str | None,
    import_root: str,
) -> Path:
    if legacy_root_dir:
        return (snapshot.package_root / legacy_root_dir).resolve()
    language_root = (
        "python" if targets is None or not targets.root_dir else targets.root_dir
    )
    product_dir = package_dir or import_root
    return (snapshot.package_root / language_root / product_dir).resolve()


def _load_api_runtime_artifacts(
    *,
    runtime_package_dir: Path,
    repo_root: Path,
) -> APIRuntimeArtifacts:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = repo_root.resolve()
    return APIRuntimeArtifacts(
        compile_plan=_load_json_artifact(
            artifact_path=runtime_package_dir / "api.compile_plan.json",
            repo_root=repo_root,
            artifact_type=APICompilePlanArtifact,
        ),
        interface_spec=_load_json_artifact(
            artifact_path=runtime_package_dir / "api.interface_spec.json",
            repo_root=repo_root,
            artifact_type=ApiInterfaceSpecArtifact,
        ),
        invocation_manifest=_load_json_artifact(
            artifact_path=runtime_package_dir / "api.invocation_manifest.json",
            repo_root=repo_root,
            artifact_type=ApiInvocationManifestArtifact,
        ),
        public_package_plan=_load_json_artifact(
            artifact_path=runtime_package_dir / "api.public_package_plan.json",
            repo_root=repo_root,
            artifact_type=ApiPublicPackagePlanArtifact,
        ),
        service_protocol_plan=_load_json_artifact(
            artifact_path=runtime_package_dir / "api.service_protocol_plan.json",
            repo_root=repo_root,
            artifact_type=ApiServiceProtocolPlanArtifact,
        ),
    )


def _load_json_artifact(
    *,
    artifact_path: Path,
    repo_root: Path,
    artifact_type: type[_ArtifactT],
) -> _ArtifactT:
    resolved_path = artifact_path.resolve()
    if not resolved_path.is_file():
        raise FileNotFoundError(f"API runtime artifact is missing: {resolved_path}")
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()
    return artifact_type(
        path=resolved_path,
        relpath=resolved_path.relative_to(repo_root.resolve()).as_posix(),
        hash_sha256=digest,
    )


def _load_api_public_package_plan(*, runtime_package_dir: Path) -> ApiPublicPackagePlan:
    payload = _load_json_payload(
        runtime_package_dir=runtime_package_dir, filename="api.public_package_plan.json"
    )
    backend_handoff = _decode_backend_handoff(payload=payload["backend_handoff"])
    apis = tuple(
        ApiPublicPackageApiPlan(
            name=str(api_payload["name"]),
            description=_optional_str(api_payload.get("description")),
            source_path=str(api_payload["source_path"]),
            capabilities=tuple(
                ApiPublicPackageCapabilityPlan(
                    api_name=str(capability_payload["api_name"]),
                    name=str(capability_payload["name"]),
                    description=_optional_str(capability_payload.get("description")),
                    source_path=str(capability_payload["source_path"]),
                    endpoints=tuple(
                        _decode_public_package_endpoint(
                            endpoint_payload=endpoint_payload,
                        )
                        for endpoint_payload in _iter_json_objects(
                            capability_payload,
                            key="endpoints",
                            context="public package capability endpoints",
                        )
                    ),
                )
                for capability_payload in _iter_json_objects(
                    api_payload,
                    key="capabilities",
                    context="public package api capabilities",
                )
            ),
        )
        for api_payload in _iter_json_objects(
            payload,
            key="apis",
            context="public package apis",
        )
    )
    return ApiPublicPackagePlan(
        schema_version=_require_int(
            payload["schema_version"], context="public package schema_version"
        ),
        package_name=str(payload["package_name"]),
        fqn_prefix=str(payload["fqn_prefix"]),
        backend_handoff=backend_handoff,
        apis=apis,
    )


def _load_api_service_protocol_plan(
    *, runtime_package_dir: Path
) -> ApiServiceProtocolPlan:
    payload = _load_json_payload(
        runtime_package_dir=runtime_package_dir,
        filename="api.service_protocol_plan.json",
    )
    backend_handoff = _decode_backend_handoff(payload=payload["backend_handoff"])
    apis = tuple(
        ApiServiceProtocolApiPlan(
            name=str(api_payload["name"]),
            description=_optional_str(api_payload.get("description")),
            source_path=str(api_payload["source_path"]),
            capabilities=tuple(
                ApiServiceProtocolCapabilityPlan(
                    api_name=str(capability_payload["api_name"]),
                    name=str(capability_payload["name"]),
                    description=_optional_str(capability_payload.get("description")),
                    source_path=str(capability_payload["source_path"]),
                    endpoints=tuple(
                        _decode_service_protocol_endpoint(
                            endpoint_payload=endpoint_payload,
                        )
                        for endpoint_payload in _iter_json_objects(
                            capability_payload,
                            key="endpoints",
                            context="service protocol capability endpoints",
                        )
                    ),
                )
                for capability_payload in _iter_json_objects(
                    api_payload,
                    key="capabilities",
                    context="service protocol api capabilities",
                )
            ),
        )
        for api_payload in _iter_json_objects(
            payload,
            key="apis",
            context="service protocol apis",
        )
    )
    return ApiServiceProtocolPlan(
        schema_version=_require_int(
            payload["schema_version"], context="service protocol schema_version"
        ),
        package_name=str(payload["package_name"]),
        fqn_prefix=str(payload["fqn_prefix"]),
        backend_handoff=backend_handoff,
        apis=apis,
    )


def _load_json_payload(*, runtime_package_dir: Path, filename: str) -> _JsonObject:
    artifact_path = runtime_package_dir.resolve() / filename
    if not artifact_path.is_file():
        raise FileNotFoundError(f"API runtime artifact is missing: {artifact_path}")
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    return _require_json_object(
        payload,
        context=f"API runtime artifact {artifact_path}",
    )


def _decode_backend_handoff(*, payload: object) -> ApiProductBackendHandoff:
    payload = _require_json_object(payload, context="backend_handoff")
    return ApiProductBackendHandoff(
        materialization_source=MaterializationSource(
            str(payload["materialization_source"])
        ),
        aware_package_kind=str(payload["aware_package_kind"]),
        expected_renderer_profile=str(payload["expected_renderer_profile"]),
    )


def _decode_request_plan(*, payload: object) -> ApiPublicPackageRequestPlan:
    payload = _require_json_object(payload, context="request")
    return ApiPublicPackageRequestPlan(
        class_ref=str(payload["class_ref"]),
        description=_optional_str(payload.get("description")),
        source_path=str(payload["source_path"]),
    )


def _decode_response_plan(*, payload: object) -> ApiPublicPackageResponsePlan:
    payload = _require_json_object(payload, context="response")
    return ApiPublicPackageResponsePlan(
        class_ref=str(payload["class_ref"]),
        description=_optional_str(payload.get("description")),
        source_path=str(payload["source_path"]),
    )


def _decode_stream_plan(*, payload: object | None) -> ApiPublicPackageStreamPlan | None:
    if payload is None:
        return None
    payload = _require_json_object(payload, context="stream")
    return ApiPublicPackageStreamPlan(
        stream_mode=str(payload["stream_mode"]),
        description=_optional_str(payload.get("description")),
        source_path=str(payload["source_path"]),
        events=tuple(
            _decode_stream_event_plan(event_payload=event_payload)
            for event_payload in _iter_json_objects(
                payload,
                key="events",
                context="stream events",
            )
        ),
    )


def _decode_stream_event_plan(
    *, event_payload: object
) -> ApiPublicPackageStreamEventPlan:
    event_payload = _require_json_object(event_payload, context="stream event")
    return ApiPublicPackageStreamEventPlan(
        kind=str(event_payload["kind"]),
        class_ref=str(event_payload["class_ref"]),
        description=_optional_str(event_payload.get("description")),
        source_path=str(event_payload["source_path"]),
    )


def _decode_public_package_endpoint(
    *, endpoint_payload: object
) -> ApiPublicPackageEndpointPlan:
    endpoint_payload = _require_json_object(
        endpoint_payload, context="public package endpoint"
    )
    response_payload = endpoint_payload.get("response")
    return ApiPublicPackageEndpointPlan(
        api_name=str(endpoint_payload["api_name"]),
        capability_name=str(endpoint_payload["capability_name"]),
        name=str(endpoint_payload["name"]),
        discriminant=str(endpoint_payload["discriminant"]),
        description=_optional_str(endpoint_payload.get("description")),
        source_path=str(endpoint_payload["source_path"]),
        request=_decode_request_plan(payload=endpoint_payload["request"]),
        response=(
            None
            if response_payload is None
            else _decode_response_plan(payload=response_payload)
        ),
        stream=_decode_stream_plan(payload=endpoint_payload.get("stream")),
    )


def _decode_service_protocol_endpoint(
    *,
    endpoint_payload: object,
) -> ApiServiceProtocolEndpointPlan:
    endpoint_payload = _require_json_object(
        endpoint_payload, context="service protocol endpoint"
    )
    response_payload = endpoint_payload.get("response")
    return ApiServiceProtocolEndpointPlan(
        api_name=str(endpoint_payload["api_name"]),
        capability_name=str(endpoint_payload["capability_name"]),
        name=str(endpoint_payload["name"]),
        endpoint_ref=str(endpoint_payload["endpoint_ref"]),
        discriminant=str(endpoint_payload["discriminant"]),
        description=_optional_str(endpoint_payload.get("description")),
        source_path=str(endpoint_payload["source_path"]),
        request=_decode_request_plan(payload=endpoint_payload["request"]),
        response=(
            None
            if response_payload is None
            else _decode_response_plan(payload=response_payload)
        ),
        stream=_decode_stream_plan(payload=endpoint_payload.get("stream")),
        fulfillment_bindings=tuple(
            _decode_service_protocol_binding(binding_payload=binding_payload)
            for binding_payload in _iter_json_objects(
                endpoint_payload,
                key="fulfillment_bindings",
                context="service protocol fulfillment bindings",
            )
        ),
    )


def _decode_service_protocol_binding(
    *,
    binding_payload: object,
) -> ApiServiceProtocolEndpointFunctionPlan:
    binding_payload = _require_json_object(
        binding_payload,
        context="service protocol fulfillment binding",
    )
    return ApiServiceProtocolEndpointFunctionPlan(
        name=str(binding_payload["name"]),
        graph_target=str(binding_payload["graph_target"]),
        graph_capability_function_name=str(
            binding_payload["graph_capability_function_name"]
        ),
        graph_function_python_ref=str(binding_payload["graph_function_python_ref"]),
        source_path=str(binding_payload["source_path"]),
        graph_function_runtime_target=_optional_str(
            binding_payload.get("graph_function_runtime_target")
        ),
        call_target_kind=_optional_str(binding_payload.get("call_target_kind")),
        exact_output_field_name=_optional_str(
            binding_payload.get("exact_output_field_name")
        ),
    )


def _optional_str(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _require_int(value: object, *, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError(
            f"Invalid API runtime artifact: {context} must be an integer"
        )
    return value


def _require_json_object(value: object, *, context: str) -> _JsonObject:
    if not isinstance(value, dict):
        raise RuntimeError(
            f"Invalid API runtime artifact: {context} must be a JSON object"
        )
    return value


def _iter_json_objects(
    payload: _JsonObject, *, key: str, context: str
) -> tuple[_JsonObject, ...]:
    values = payload.get(key, ())
    if not isinstance(values, list):
        raise RuntimeError(
            f"Invalid API runtime artifact: {context} must be a JSON list"
        )
    return tuple(
        _require_json_object(value, context=f"{context}[]") for value in values
    )


def _build_accessible_dependency_packages(
    *,
    snapshot: APIWorkspaceSnapshot,
    accessible_graphs: tuple[ObjectConfigGraph, ...] | None = None,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[_AccessibleDependencyPackage, ...]:
    if accessible_graphs is None:
        dependencies = _resolve_api_dependency_packages(
            snapshot=snapshot,
            dependency_repo_roots=dependency_repo_roots,
        )
        if dependencies:
            names = ", ".join(package.package_name for package in dependencies)
            raise RuntimeError(
                "API materialization requires package-owned dependency "
                "ObjectConfigGraph artifacts; source-local Structure repository "
                "fallback is retired. Materialize dependencies or pass "
                f"accessible_graphs first (packages={names})"
            )
        return ()
    if _snapshot_is_compile_plan_input(snapshot=snapshot):
        return _build_accessible_dependency_packages_from_precompiled_graphs(
            snapshot=snapshot,
            accessible_graphs=accessible_graphs,
            dependency_repo_roots=dependency_repo_roots,
        )
    precompiled_graphs = _build_precompiled_dependency_graph_lookup(
        accessible_graphs=accessible_graphs
    )
    package_index = _build_runtime_aware_toml_package_index(
        repo_root=snapshot.repo_root,
        dependency_repo_roots=dependency_repo_roots,
    )
    cache: dict[str, _AccessibleDependencyPackage] = {}
    for dependency in _resolve_api_dependency_packages(
        snapshot=snapshot,
        dependency_repo_roots=dependency_repo_roots,
    ):
        _ = _build_dependency_package(
            package_name=dependency.package_name,
            repo_root=snapshot.repo_root,
            package_index=package_index,
            cache=cache,
            stack=(),
            precompiled_graphs=precompiled_graphs,
        )
    packages_by_name = {
        package_name: cache[package_name]
        for package_name in sorted(cache, key=str.casefold)
    }
    if precompiled_graphs is not None:
        for package in _compile_plan_local_accessible_packages(
            snapshot=snapshot,
            accessible_graphs=accessible_graphs or (),
            consumed_graph_ids=precompiled_graphs.consumed_graph_ids,
        ):
            packages_by_name.setdefault(package.package_name, package)
    return tuple(
        packages_by_name[package_name]
        for package_name in sorted(packages_by_name, key=str.casefold)
    )


def _with_api_dto_export_packages(
    *,
    snapshot: APIWorkspaceSnapshot,
    accessible_dependency_packages: tuple[_AccessibleDependencyPackage, ...],
    accessible_graphs: tuple[ObjectConfigGraph, ...] | None,
    api_dto_exports: tuple[AwareApiTomlSemanticPackageExportSpec, ...],
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[_AccessibleDependencyPackage, ...]:
    cache = {
        package.package_name: package for package in accessible_dependency_packages
    }
    package_index = _build_runtime_aware_toml_package_index(
        repo_root=snapshot.repo_root,
        dependency_repo_roots=dependency_repo_roots,
    )
    precompiled_graphs = _build_precompiled_dependency_graph_lookup(
        accessible_graphs=accessible_graphs or ()
    )
    for export in api_dto_exports:
        if export.package_name in cache:
            continue
        manifest_path = (snapshot.package_root / export.manifest_path).resolve()
        spec = load_aware_toml_spec(toml_path=manifest_path)
        graph = _precompiled_graph_for_spec(spec=spec, lookup=precompiled_graphs)
        if graph is None:
            raise RuntimeError(
                "API DTO export package requires an accessible ObjectConfigGraph "
                "artifact; source-local Structure repository fallback is retired "
                + f"(package={export.package_name!r}, manifest={manifest_path})"
            )
        _ = _build_dependency_package_from_manifest_path(
            aware_toml_path=manifest_path,
            repo_root=snapshot.repo_root,
            package_index=package_index,
            cache=cache,
            stack=(),
            precompiled_graphs=precompiled_graphs,
        )
    return tuple(
        cache[package_name] for package_name in sorted(cache, key=str.casefold)
    )


def _api_dto_exports(
    *,
    snapshot: APIWorkspaceSnapshot,
) -> tuple[AwareApiTomlSemanticPackageExportSpec, ...]:
    return tuple(
        export
        for export in snapshot.spec.semantic_package_exports
        if export.kind is AwareApiSemanticPackageExportKind.api_dto
    )


def _api_dto_export_package_names(*, snapshot: APIWorkspaceSnapshot) -> frozenset[str]:
    return frozenset(
        export.package_name for export in _api_dto_exports(snapshot=snapshot)
    )


def _accessible_dependency_source_digest_package_names(
    *,
    accessible_dependency_packages: tuple[_AccessibleDependencyPackage, ...],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            package.package_name
            for package in accessible_dependency_packages
            if package.package_name.strip()
        )
    )


def _dart_public_package_root_class_refs(
    *,
    plan: ApiPublicPackagePlan,
    accessible_dependency_packages: tuple[_AccessibleDependencyPackage, ...],
    api_dto_package_names: frozenset[str],
) -> tuple[str, ...]:
    refs = set(_api_public_package_endpoint_class_refs(plan=plan))
    for package in accessible_dependency_packages:
        if package.package_name not in api_dto_package_names:
            continue
        for node in package.graph.object_config_graph_nodes:
            class_config = node.class_config
            if class_config is None:
                continue
            class_ref = (class_config.class_fqn or "").strip()
            if class_ref:
                refs.add(class_ref)
    return tuple(sorted(refs, key=str.casefold))


def _api_public_package_endpoint_class_refs(
    *, plan: ApiPublicPackagePlan
) -> tuple[str, ...]:
    refs: set[str] = set()
    for api in plan.apis:
        for capability in api.capabilities:
            for endpoint in capability.endpoints:
                refs.add(endpoint.request.class_ref)
                if endpoint.response is not None:
                    refs.add(endpoint.response.class_ref)
                if endpoint.stream is not None:
                    for event in endpoint.stream.events:
                        refs.add(event.class_ref)
    return tuple(sorted(refs, key=str.casefold))


def _api_dto_dependency_import_roots(
    *,
    snapshot: APIWorkspaceSnapshot,
    accessible_dependency_packages: tuple[_AccessibleDependencyPackage, ...],
) -> tuple[str, ...]:
    api_dto_package_names = _api_dto_export_package_names(snapshot=snapshot)
    return tuple(
        sorted(
            {
                package.import_root
                for package in accessible_dependency_packages
                if _is_api_dto_dependency_package(
                    package=package,
                    api_dto_package_names=api_dto_package_names,
                )
            },
            key=str.casefold,
        )
    )


def _api_contract_dependency_import_roots(
    *,
    snapshot: APIWorkspaceSnapshot,
    accessible_dependency_packages: tuple[_AccessibleDependencyPackage, ...],
) -> tuple[str, ...]:
    _ = snapshot
    return tuple(
        sorted(
            {
                package.import_root
                for package in accessible_dependency_packages
                if package.package_kind != "api_generated_dto"
            },
            key=str.casefold,
        )
    )


def _is_api_dto_dependency_package(
    *,
    package: _AccessibleDependencyPackage,
    api_dto_package_names: frozenset[str],
) -> bool:
    return package.package_name in api_dto_package_names or package.package_kind in {
        "api",
        "api_dto",
    }


def _build_accessible_dependency_packages_from_precompiled_graphs(
    *,
    snapshot: APIWorkspaceSnapshot,
    accessible_graphs: tuple[ObjectConfigGraph, ...],
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[_AccessibleDependencyPackage, ...]:
    if _snapshot_is_compile_plan_input(snapshot=snapshot):
        return _compile_plan_input_accessible_packages(
            snapshot=snapshot,
            accessible_graphs=accessible_graphs,
            dependency_repo_roots=dependency_repo_roots,
        )
    graphs_by_fqn_prefix = {
        (graph.fqn_prefix or "").strip().casefold(): graph
        for graph in accessible_graphs
        if (graph.fqn_prefix or "").strip()
    }
    graphs_by_name = {
        (graph.name or "").strip().casefold(): graph
        for graph in accessible_graphs
        if (graph.name or "").strip()
    }
    packages: list[_AccessibleDependencyPackage] = []
    consumed_graph_ids: set[object] = set()
    for package in _resolve_api_dependency_packages(
        snapshot=snapshot,
        dependency_repo_roots=dependency_repo_roots,
    ):
        fqn_prefix = (package.spec.package.fqn_prefix or "").strip().casefold()
        package_name = package.package_name.strip().casefold()
        graph = graphs_by_fqn_prefix.get(fqn_prefix) or graphs_by_name.get(package_name)
        if graph is None:
            raise RuntimeError(
                "API compile dependency graph mode produced no ObjectConfigGraph for "
                f"package={package.package_name!r} fqn_prefix={package.spec.package.fqn_prefix!r}"
            )
        packages.append(
            _AccessibleDependencyPackage(
                package_name=package.package_name,
                package_kind=_normalize_package_kind(package.kind),
                package_root=package.package_root,
                import_root=_derive_dependency_import_root(spec=package.spec),
                graph=graph,
            )
        )
        consumed_graph_ids.add(graph.id)
    packages.extend(
        _compile_plan_local_accessible_packages(
            snapshot=snapshot,
            accessible_graphs=accessible_graphs,
            consumed_graph_ids=consumed_graph_ids,
        )
    )
    return tuple(packages)


def _compile_plan_local_accessible_packages(
    *,
    snapshot: APIWorkspaceSnapshot,
    accessible_graphs: tuple[ObjectConfigGraph, ...],
    consumed_graph_ids: set[object],
) -> tuple[_AccessibleDependencyPackage, ...]:
    package_name = (snapshot.spec.api.package_name or "").strip()
    fqn_prefix = (snapshot.spec.api.fqn_prefix or "").strip()
    if not package_name or not fqn_prefix:
        return ()
    generated_graph_name = f"{package_name}_generated_dto".replace("-", "_")
    packages: list[_AccessibleDependencyPackage] = []
    for graph in accessible_graphs:
        if graph.id in consumed_graph_ids:
            continue
        graph_fqn_prefix = (graph.fqn_prefix or "").strip()
        graph_name = (graph.name or "").strip()
        if graph_fqn_prefix != fqn_prefix and graph_name != generated_graph_name:
            continue
        packages.append(
            _AccessibleDependencyPackage(
                package_name=graph_name or package_name,
                package_kind="api_generated_dto",
                package_root=snapshot.package_root,
                import_root=fqn_prefix.replace("-", "_"),
                graph=graph,
            )
        )
        consumed_graph_ids.add(graph.id)
    return tuple(sorted(packages, key=lambda item: item.package_name.casefold()))


def _compile_plan_input_accessible_packages(
    *,
    snapshot: APIWorkspaceSnapshot,
    accessible_graphs: tuple[ObjectConfigGraph, ...],
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[_AccessibleDependencyPackage, ...]:
    packages: list[_AccessibleDependencyPackage] = []
    package_index = _build_runtime_aware_toml_package_index(
        repo_root=snapshot.repo_root,
        dependency_repo_roots=dependency_repo_roots,
    )
    for graph in accessible_graphs:
        default_import_root = _compile_plan_input_graph_import_root(graph=graph)
        package_name = (graph.name or "").strip() or default_import_root
        default_package_kind = _compile_plan_input_graph_package_kind(
            snapshot=snapshot,
            graph=graph,
        )
        package_root, package_kind, import_root = (
            _compile_plan_input_graph_package_resolution(
                snapshot=snapshot,
                graph=graph,
                package_name=package_name,
                default_package_kind=default_package_kind,
                default_import_root=default_import_root,
                package_index=package_index,
            )
        )
        packages.append(
            _AccessibleDependencyPackage(
                package_name=package_name,
                package_kind=package_kind,
                package_root=package_root,
                import_root=import_root,
                graph=graph,
            )
        )
    return tuple(sorted(packages, key=lambda item: item.package_name.casefold()))


def _snapshot_is_compile_plan_input(*, snapshot: APIWorkspaceSnapshot) -> bool:
    return snapshot.spec_path.name == "api.compile_plan.json"


def _compile_plan_input_graph_package_kind(
    *,
    snapshot: APIWorkspaceSnapshot,
    graph: ObjectConfigGraph,
) -> str:
    if (graph.fqn_prefix or "").strip() == (snapshot.spec.api.fqn_prefix or "").strip():
        return "api_generated_dto"
    return "semantic_dependency"


def _compile_plan_input_graph_package_resolution(
    *,
    snapshot: APIWorkspaceSnapshot,
    graph: ObjectConfigGraph,
    package_name: str,
    default_package_kind: str,
    default_import_root: str,
    package_index: Mapping[str, Path],
) -> tuple[Path, str, str]:
    if default_package_kind == "api_generated_dto":
        return snapshot.package_root, default_package_kind, default_import_root

    graph_name = (graph.name or "").strip().casefold()
    graph_fqn_prefix = (graph.fqn_prefix or "").strip().casefold()
    package_name_key = package_name.strip().casefold()
    for indexed_package_name, aware_toml_path in sorted(
        package_index.items(),
        key=lambda item: item[0].casefold(),
    ):
        try:
            spec = load_aware_toml_spec(toml_path=aware_toml_path)
        except Exception:
            continue
        spec_package_name = (spec.package.package_name or indexed_package_name).strip()
        spec_fqn_prefix = (spec.package.fqn_prefix or "").strip()
        candidate_keys = {
            indexed_package_name.casefold(),
            spec_package_name.casefold(),
        }
        if spec_fqn_prefix:
            candidate_keys.add(spec_fqn_prefix.casefold())
        if candidate_keys.intersection(
            key for key in (graph_name, graph_fqn_prefix, package_name_key) if key
        ):
            return (
                aware_toml_path.parent.resolve(),
                _normalize_package_kind(spec.package.kind),
                _derive_dependency_import_root(spec=spec),
            )
    return snapshot.package_root, default_package_kind, default_import_root


def _compile_plan_input_graph_import_root(*, graph: ObjectConfigGraph) -> str:
    token = (graph.fqn_prefix or "").strip() or (graph.name or "").strip()
    return token.replace("-", "_") or "aware_api_dependency"


def _load_accessible_dependency_graphs_from_runtime_artifact_if_present(
    *,
    runtime_package_dir: Path,
) -> tuple[ObjectConfigGraph, ...] | None:
    artifact_path = (
        runtime_package_dir.resolve() / API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME
    )
    if not artifact_path.is_file():
        return None
    return load_api_accessible_dependency_graphs_from_runtime_artifact(
        runtime_package_dir=runtime_package_dir,
    )


def _build_precompiled_dependency_graph_lookup(
    *,
    accessible_graphs: tuple[ObjectConfigGraph, ...],
) -> _PrecompiledDependencyGraphLookup:
    lookup = _PrecompiledDependencyGraphLookup(
        graphs_by_fqn_prefix={},
        graphs_by_name={},
        consumed_graph_ids=set(),
    )
    for graph in accessible_graphs:
        fqn_prefix = (graph.fqn_prefix or "").strip().casefold()
        if fqn_prefix:
            _register_precompiled_dependency_graph_key(
                bucket=lookup.graphs_by_fqn_prefix,
                key=fqn_prefix,
                graph=graph,
            )
        graph_name = (graph.name or "").strip().casefold()
        if graph_name:
            _register_precompiled_dependency_graph_key(
                bucket=lookup.graphs_by_name,
                key=graph_name,
                graph=graph,
            )
    return lookup


def _register_precompiled_dependency_graph_key(
    *,
    bucket: dict[str, ObjectConfigGraph],
    key: str,
    graph: ObjectConfigGraph,
) -> None:
    existing = bucket.get(key)
    if existing is not None and existing.id != graph.id:
        raise RuntimeError(
            "Ambiguous API dependency graph semantic context: "
            + f"key={key!r} graph_ids={str(existing.id)!r}, {str(graph.id)!r}"
        )
    bucket[key] = graph


def _precompiled_graph_for_spec(
    *,
    spec: object,
    lookup: _PrecompiledDependencyGraphLookup,
) -> ObjectConfigGraph | None:
    package_spec = getattr(spec, "package", None)
    package_name = str(getattr(package_spec, "package_name", "") or "").strip()
    fqn_prefix = str(getattr(package_spec, "fqn_prefix", "") or "").strip()
    graph = None
    if fqn_prefix:
        graph = lookup.graphs_by_fqn_prefix.get(fqn_prefix.casefold())
    if graph is None and package_name:
        graph = lookup.graphs_by_name.get(package_name.casefold())
    if graph is not None:
        lookup.consumed_graph_ids.add(graph.id)
    return graph


def _build_dependency_package(
    *,
    package_name: str,
    repo_root: Path,
    package_index: Mapping[str, Path],
    cache: dict[str, _AccessibleDependencyPackage],
    stack: tuple[str, ...],
    precompiled_graphs: _PrecompiledDependencyGraphLookup | None = None,
) -> _AccessibleDependencyPackage:
    if package_name in cache:
        return cache[package_name]
    if package_name in stack:
        cycle = " -> ".join([*stack, package_name])
        raise ValueError(
            f"Cyclic API dependency while building public API package DTO graphs: {cycle}"
        )

    aware_toml_path = _resolve_aware_toml_path_by_package_name(
        package_name=package_name,
        repo_root=repo_root,
        package_index=package_index,
    )
    return _build_dependency_package_from_manifest_path(
        aware_toml_path=aware_toml_path,
        repo_root=repo_root,
        package_index=package_index,
        cache=cache,
        stack=stack,
        precompiled_graphs=precompiled_graphs,
    )


def _build_dependency_package_from_manifest_path(
    *,
    aware_toml_path: Path,
    repo_root: Path,
    package_index: Mapping[str, Path],
    cache: dict[str, _AccessibleDependencyPackage],
    stack: tuple[str, ...],
    precompiled_graphs: _PrecompiledDependencyGraphLookup | None = None,
) -> _AccessibleDependencyPackage:
    spec = load_aware_toml_spec(toml_path=aware_toml_path)
    package_name = spec.package.package_name
    if package_name in cache:
        return cache[package_name]
    if package_name in stack:
        cycle = " -> ".join([*stack, package_name])
        raise ValueError(
            f"Cyclic API dependency while building public API package DTO graphs: {cycle}"
        )
    package_root = aware_toml_path.parent.resolve()
    for dependency in sorted(
        spec.dependencies, key=lambda item: item.package_name.casefold()
    ):
        _ = _build_dependency_package(
            package_name=dependency.package_name,
            repo_root=repo_root,
            package_index=package_index,
            cache=cache,
            stack=(*stack, package_name),
            precompiled_graphs=precompiled_graphs,
        )
    graph = _dependency_object_config_graph_from_context_or_runtime(
        aware_toml_path=aware_toml_path,
        package_root=package_root,
        spec=spec,
        precompiled_graphs=precompiled_graphs,
    )
    package = _AccessibleDependencyPackage(
        package_name=spec.package.package_name,
        package_kind=_normalize_package_kind(spec.package.kind),
        package_root=package_root,
        import_root=_derive_dependency_import_root(spec=spec),
        graph=graph,
    )
    cache[package_name] = package
    return package


def _dependency_object_config_graph_from_context_or_runtime(
    *,
    aware_toml_path: Path,
    package_root: Path,
    spec: object,
    precompiled_graphs: _PrecompiledDependencyGraphLookup | None,
) -> ObjectConfigGraph:
    graph = (
        _precompiled_graph_for_spec(spec=spec, lookup=precompiled_graphs)
        if precompiled_graphs is not None
        else None
    )
    if graph is not None:
        return graph

    package_spec = getattr(spec, "package", None)
    package_name = str(getattr(package_spec, "package_name", "") or "").strip()
    package_kind = getattr(package_spec, "kind", None)
    if package_kind is not AwarePackageKind.api:
        return _load_required_runtime_dependency_object_config_graph(
            package=_RuntimeDependencyPackage(
                package_name=package_name,
                aware_toml_path=aware_toml_path,
                package_root=package_root,
                spec=spec,
            )
        )

    raise RuntimeError(
        "API dependency package requires an accessible ObjectConfigGraph "
        "artifact; source-local Structure repository fallback is retired "
        + f"(package={package_name!r}, fqn_prefix={getattr(package_spec, 'fqn_prefix', None)!r}, manifest={aware_toml_path})"
    )


def _with_python_render_overlays(graph: ObjectConfigGraph) -> ObjectConfigGraph:
    graph.object_config_graph_overlays = (
        build_object_config_graph_overlays_from_annotations(graph)
    )
    return graph


def _api_dto_graph_with_source_layouts(
    *,
    package: _AccessibleDependencyPackage,
    snapshot: APIWorkspaceSnapshot,
) -> ObjectConfigGraph:
    _ = snapshot
    graph = package.graph.model_copy(deep=True)
    if _python_entity_template_paths_from_graph(graph):
        return graph
    return graph


def _python_api_dto_entity_template_paths(
    *,
    package: _AccessibleDependencyPackage,
    snapshot: APIWorkspaceSnapshot,
) -> dict[str, Path]:
    _ = snapshot
    return _python_entity_template_paths_from_graph(package.graph)


def _python_entity_layouts_from_graph(
    graph: ObjectConfigGraph,
) -> dict[str, tuple[object, ...]]:
    layouts_by_entity_id: dict[str, tuple[object, ...]] = {}
    for node in graph.object_config_graph_nodes:
        entity_id = _node_entity_id(node)
        if entity_id is None:
            continue
        aware_layouts = tuple(
            layout
            for layout in (node.layouts or ())
            if (not layout.layout_kind or layout.layout_kind == "aware")
            and layout.relative_path
        )
        if aware_layouts:
            layouts_by_entity_id[entity_id] = aware_layouts
    return layouts_by_entity_id


def _python_entity_template_paths_from_graph(
    graph: ObjectConfigGraph,
) -> dict[str, Path]:
    template_paths: dict[str, Path] = {}
    for node in graph.object_config_graph_nodes:
        layouts = node.layouts
        if not layouts:
            continue
        aware_layouts = [
            layout
            for layout in layouts
            if not layout.layout_kind or layout.layout_kind == "aware"
        ]
        if not aware_layouts:
            continue
        layout = min(
            aware_layouts,
            key=lambda item: (
                item.source_position is None,
                item.source_position or 0,
                item.relative_path or "",
            ),
        )
        if not layout.relative_path:
            continue

        entity_id = _node_entity_id(node)
        if entity_id is None:
            continue
        template_paths[entity_id] = Path(layout.relative_path).with_suffix(".py")
    return dict(sorted(template_paths.items()))


def _node_entity_id(node: object) -> str | None:
    class_config = getattr(node, "class_config", None)
    if class_config is not None:
        return str(class_config.id)
    enum_config = getattr(node, "enum_config", None)
    if enum_config is not None:
        return str(enum_config.id)
    node_function_config = get_node_function_config(node)
    if node_function_config is not None:
        return str(node_function_config.id)
    return None


def _external_import_roots_by_graph_key(
    packages: tuple[_AccessibleDependencyPackage, ...],
) -> dict[str, str]:
    roots: dict[str, str] = {}
    for package in packages:
        import_root = package.import_root.strip()
        if not import_root:
            continue
        roots[str(package.graph.id)] = import_root
        for graph_key in (package.graph.fqn_prefix, package.graph.name):
            key = (graph_key or "").strip()
            if key:
                roots[key] = import_root
    return roots


def _python_import_overrides_from_dependency_artifacts(
    packages: tuple[_AccessibleDependencyPackage, ...],
) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for package in packages:
        for models_path in _python_models_json_candidates(package=package):
            if not models_path.is_file():
                continue
            try:
                payload = json.loads(models_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(payload, dict):
                continue
            for class_payload in payload.get("classes") or ():
                if not isinstance(class_payload, dict):
                    continue
                class_id = class_payload.get("class_config_id")
                module = class_payload.get("module")
                if isinstance(class_id, str) and isinstance(module, str):
                    overrides[class_id] = module
            for enum_payload in payload.get("enums") or ():
                if not isinstance(enum_payload, dict):
                    continue
                enum_id = enum_payload.get("enum_config_id")
                module = enum_payload.get("module")
                if isinstance(enum_id, str) and isinstance(module, str):
                    overrides[enum_id] = module
            break
    return dict(sorted(overrides.items()))


def _python_models_json_candidates(
    *, package: _AccessibleDependencyPackage
) -> tuple[Path, ...]:
    return (
        package.package_root
        / "python"
        / package.import_root
        / DEFAULT_ARTIFACTS_DIR
        / "python.models.json",
        package.package_root
        / "python"
        / package.import_root
        / package.import_root
        / DEFAULT_ARTIFACTS_DIR
        / "python.models.json",
        package.package_root.parent
        / "python"
        / package.import_root
        / package.import_root
        / DEFAULT_ARTIFACTS_DIR
        / "python.models.json",
    )


def _api_dto_dependency_distribution_names(
    *,
    dto_package: _AccessibleDependencyPackage,
    accessible_dependency_packages: tuple[_AccessibleDependencyPackage, ...],
) -> tuple[str, ...]:
    dependency_names = {
        _python_distribution_name_for_dependency_package(package=package)
        for package in accessible_dependency_packages
        if package.package_name != dto_package.package_name
    }
    return tuple(name for name in sorted(dependency_names, key=str.casefold) if name)


def _python_distribution_name_for_dependency_package(
    *, package: _AccessibleDependencyPackage
) -> str:
    for pyproject_path in (
        package.package_root / "python" / "pyproject.toml",
        package.package_root / "python" / package.import_root / "pyproject.toml",
        package.package_root.parent / "python" / package.import_root / "pyproject.toml",
    ):
        if not pyproject_path.is_file():
            continue
        try:
            payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            continue
        project = payload.get("project")
        if not isinstance(project, dict):
            continue
        name = project.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return package.import_root.replace("_", "-")


def _resolve_aware_toml_path_by_package_name(
    *,
    package_name: str,
    repo_root: Path,
    package_index: Mapping[str, Path],
) -> Path:
    return _resolve_runtime_aware_toml_path_by_package_name(
        package_name=package_name,
        repo_root=repo_root,
        package_index=package_index,
    )


def _materialize_graph_via_meta(
    *,
    aware_root: Path,
    layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
    materialization_config: MaterializationConfig,
    object_config_graph: ObjectConfigGraph,
    external_runtime_graphs: tuple[ObjectConfigGraph, ...] = (),
    external_import_roots_by_graph_key: Mapping[str, str] | None = None,
    python_external_import_overrides_by_entity_id: Mapping[str, str] | None = None,
    candidate_paths: tuple[Path, ...] = (),
    execute_post_steps: bool = False,
    post_step_tool_env_by_tool_id: Mapping[str, Mapping[str, str]] | None = None,
    post_step_executable_overrides_by_tool_id: (
        Mapping[str, Mapping[str, str]] | None
    ) = None,
) -> LocalMaterializationExecutionResult:
    renderer_profile = _materialization_renderer_profile(
        materialization_config=materialization_config
    )
    profile_inputs = _load_profile_inputs(
        aware_root=aware_root,
        materialization_config=materialization_config,
    )
    transform_result = GraphMaterializationTransformService().transform(
        GraphMaterializationTransformRequest(
            source_graph=object_config_graph,
            target_language_plugin_id=materialization_config.target_language,
            source_stage="source_graph",
            target_stage="language_graph",
            graph_profile=_graph_materialization_profile(
                materialization_config=materialization_config,
            ),
            external_runtime_graphs=external_runtime_graphs,
            include_projection_graphs=True,
        )
    )
    language_graph = transform_result.require_language_graph()
    layout_strategy.bind_graph(language_graph)
    candidate_paths = _expand_entity_candidate_paths_for_graph(
        layout_strategy=layout_strategy,
        language_graph=language_graph,
        candidate_paths=candidate_paths,
    )
    _clean_api_runtime_render_output_for_full_render(
        aware_root=aware_root,
        materialization_config=materialization_config,
        candidate_paths=candidate_paths,
    )
    _clean_api_python_package_output_for_full_render(
        aware_root=aware_root,
        materialization_config=materialization_config,
        candidate_paths=candidate_paths,
    )
    import_overrides = _python_language_external_import_overrides(
        target_language=materialization_config.target_language,
        language_external_graphs=transform_result.language_external_graphs,
        external_import_roots_by_graph_key=external_import_roots_by_graph_key,
        python_external_import_overrides_by_entity_id=(
            python_external_import_overrides_by_entity_id
        ),
    )
    render_result = render_language_materialization(
        LanguageMaterializationRenderRequest(
            target_language_plugin_id=materialization_config.target_language,
            language_graph=language_graph,
            output_root=materialization_config.target_output_dir,
            layout_strategy=layout_strategy,
            renderer_profile=renderer_profile,
            renderer_kind=materialization_config.renderer_kind,
            source_graph=transform_result.source_graph,
            language_external_graphs=transform_result.language_external_graphs,
            profile_inputs=profile_inputs,
            import_overrides=import_overrides,
            candidate_paths=candidate_paths,
        )
    )
    package_result = build_language_materialization_packages(
        LanguageMaterializationPackageBuildRequest(
            target_language_plugin_id=materialization_config.target_language,
            layout_base_dir=materialization_config.target_output_dir,
            target_output_dir=materialization_config.target_output_dir,
            rendered_files=tuple(render_result.written_files),
            package_specs=tuple(materialization_config.packages),
            materialization_source=materialization_config.source.value,
            renderer_profile=renderer_profile,
            renderer_kind=materialization_config.renderer_kind,
            package_kind=renderer_profile,
        )
    )
    package_results = tuple(package_result.package_results)
    declared_outputs = produce_language_plugin_declared_outputs(
        LanguagePluginDeclaredOutputProductionRequest(
            target_language_plugin_id=materialization_config.target_language,
            output_root=materialization_config.target_output_dir,
            source_graph=transform_result.source_graph,
            runtime_graph=transform_result.runtime_graph,
            language_graph=language_graph,
            generated_ocg_node_manifest=(transform_result.generated_ocg_node_manifest),
            language_external_graphs=transform_result.language_external_graphs,
            destinations=_build_declared_output_destinations(
                aware_root=aware_root,
                materialization_config=materialization_config,
                package_results=tuple(package_result.package_results),
            ),
            generated_file_paths=tuple(render_result.written_files),
            package_name=materialization_config.source_package_name,
            import_root=materialization_config.import_root,
            renderer_profile=renderer_profile,
            renderer_kind=materialization_config.renderer_kind,
            entity_file_paths=_declared_output_entity_file_paths(
                layout_strategy=layout_strategy,
            ),
            profile_inputs=profile_inputs,
            import_overrides=import_overrides,
            source_graph_ref=transform_result.source_graph_ref,
            runtime_graph_ref=transform_result.runtime_graph_ref,
            language_graph_ref=transform_result.language_graph_ref,
        )
    )
    post_step_receipts: tuple[dict[str, object], ...] = ()
    post_step_warnings: tuple[str, ...] = ()
    if execute_post_steps and package_results:
        package_results, post_step_receipts, post_step_warnings = (
            _execute_materialization_package_post_steps(
                materialization_config=materialization_config,
                renderer_profile=renderer_profile,
                package_results=package_results,
                post_step_tool_env_by_tool_id=post_step_tool_env_by_tool_id,
                post_step_executable_overrides_by_tool_id=(
                    post_step_executable_overrides_by_tool_id
                ),
            )
        )
    materialized_files = _materialized_result_files(
        render_files=tuple(render_result.written_files),
        declared_output_files=tuple(
            (
                file.path
                if file.path.is_absolute()
                else materialization_config.target_output_dir / file.path
            )
            for file in declared_outputs.generated_files
        ),
        package_results=package_results,
    )
    package_outcomes = [
        MaterializationPackageOutcome(
            package_name=package.name,
            output_root=package.output_root,
            import_root=materialization_config.import_root,
        )
        for package in package_results
    ]
    warnings = [
        *render_result.warnings,
        *declared_outputs.warnings,
        *package_result.warnings,
        *post_step_warnings,
    ]
    return LocalMaterializationExecutionResult(
        materialization_name=materialization_config.name,
        source_package_name=materialization_config.source_package_name,
        source_kind=materialization_config.source,
        target_language=materialization_config.target_language,
        aware_root=aware_root,
        output_root=materialization_config.target_output_dir,
        manifest_path=materialization_config.manifest_path,
        warnings=warnings,
        package_outcomes=package_outcomes,
        summary=MaterializationOutcomeSummary(
            package_count=len(package_outcomes),
            warning_count=len(warnings),
        ),
        files=list(materialized_files),
        packages=list(package_results),
        post_step_receipts=list(post_step_receipts),
    )


def _clean_api_runtime_render_output_for_full_render(
    *,
    aware_root: Path,
    materialization_config: MaterializationConfig,
    candidate_paths: tuple[Path, ...],
) -> None:
    if candidate_paths:
        return
    if not _is_full_api_render_cleanup_config(materialization_config):
        return
    output_dir = materialization_config.target_output_dir.resolve()
    safe_root = (aware_root / ".aware" / "api" / "runtime").resolve()
    try:
        if output_dir.exists() and output_dir.is_relative_to(safe_root):
            shutil.rmtree(output_dir)
    except Exception:
        logger.warning(
            "Unable to clean API runtime render output before full render: %s",
            output_dir,
            exc_info=True,
        )


def _clean_api_python_package_output_for_full_render(
    *,
    aware_root: Path,
    materialization_config: MaterializationConfig,
    candidate_paths: tuple[Path, ...],
) -> None:
    if candidate_paths:
        return
    if materialization_config.target_language is not CodeLanguage.python:
        return
    if not _has_aware_package_kind(
        materialization_config,
        aware_package_kinds={"api_dto"},
    ):
        return
    safe_root = aware_root.resolve()
    for package in materialization_config.packages:
        import_root = str(package.import_root or package.package_name or "").strip()
        if not import_root:
            continue
        package_root = Path(package.package_root).resolve()
        package_dir = (package_root / import_root.replace(".", "/")).resolve()
        try:
            if package_dir.exists() and package_dir.is_relative_to(safe_root):
                shutil.rmtree(package_dir)
        except Exception:
            logger.warning(
                "Unable to clean API DTO Python package output before full render: %s",
                package_dir,
                exc_info=True,
            )


def _is_full_api_render_cleanup_config(
    materialization_config: MaterializationConfig,
) -> bool:
    source = getattr(materialization_config.source, "value", "")
    if source in {"api_public_package", "api_service_protocol"}:
        return True
    return _has_aware_package_kind(
        materialization_config,
        aware_package_kinds={"api_dto", "api_public_package", "api_service_protocol"},
    )


def _has_aware_package_kind(
    materialization_config: MaterializationConfig,
    *,
    aware_package_kinds: set[str],
) -> bool:
    for package in materialization_config.packages:
        metadata = getattr(package, "metadata", None) or {}
        if str(metadata.get("aware_package_kind") or "") in aware_package_kinds:
            return True
    return False


def _execute_materialization_package_post_steps(
    *,
    materialization_config: MaterializationConfig,
    renderer_profile: str,
    package_results: tuple[ObjectConfigGraphPackageResult, ...],
    post_step_tool_env_by_tool_id: Mapping[str, Mapping[str, str]] | None,
    post_step_executable_overrides_by_tool_id: Mapping[str, Mapping[str, str]] | None,
) -> tuple[
    tuple[ObjectConfigGraphPackageResult, ...],
    tuple[dict[str, object], ...],
    tuple[str, ...],
]:
    updated_packages: list[ObjectConfigGraphPackageResult] = []
    receipts: list[dict[str, object]] = []
    warnings: list[str] = []
    for package in package_results:
        package_root = package.output_root.resolve()
        generated_file_paths = _package_result_files(
            package_root=package_root,
            files=tuple(package.files),
        )
        if not generated_file_paths:
            updated_packages.append(package)
            continue
        execution = execute_language_materialization_post_steps(
            LanguageMaterializationPostStepExecutionRequest(
                target_language_plugin_id=materialization_config.target_language,
                output_root=package_root,
                generated_file_paths=generated_file_paths,
                package_name=package.name,
                materialization_source=materialization_config.source.value,
                renderer_profile=renderer_profile,
                renderer_kind=materialization_config.renderer_kind,
                explicit_steps=_materialization_post_step_inputs(
                    materialization_config=materialization_config
                ),
                tool_env_by_tool_id=post_step_tool_env_by_tool_id or {},
                executable_overrides_by_tool_id=(
                    post_step_executable_overrides_by_tool_id or {}
                ),
            )
        )
        refreshed_files = _refreshed_package_files_after_post_steps(
            package_root=package_root,
            package_files=generated_file_paths,
            execution_results=execution.execution_results,
        )
        if materialization_config.target_language == CodeLanguage.dart:
            _assert_dart_part_files_exist(package_root=package_root)
        updated_packages.append(
            package.model_copy(
                update={
                    "files": list(refreshed_files),
                    "changed_files": list(
                        _dedupe_paths(
                            (
                                *_package_result_files(
                                    package_root=package_root,
                                    files=tuple(package.changed_files),
                                ),
                                *(
                                    path
                                    for result in execution.execution_results
                                    for path in (
                                        *result.changed_paths,
                                        *result.produced_paths,
                                    )
                                ),
                            )
                        )
                    ),
                }
            )
        )
        receipts.extend(dict(receipt) for receipt in execution.receipts)
        warnings.extend(execution.warnings)
    return tuple(updated_packages), tuple(receipts), tuple(warnings)


def _materialization_post_step_inputs(
    *,
    materialization_config: MaterializationConfig,
) -> tuple[LanguageMaterializationPostStepInput, ...]:
    return tuple(
        LanguageMaterializationPostStepInput(
            name=step.name,
            packages=tuple(step.packages),
            on_fail=step.on_fail,
            args=tuple(step.args),
        )
        for step in materialization_config.post_steps
    )


def _package_result_files(
    *,
    package_root: Path,
    files: tuple[Path, ...],
) -> tuple[Path, ...]:
    resolved_root = package_root.resolve()
    return _dedupe_paths(
        _resolve_package_file(package_root=resolved_root, path=path)
        for path in files
        if _resolve_package_file(package_root=resolved_root, path=path).is_file()
    )


def _resolve_package_file(*, package_root: Path, path: Path) -> Path:
    candidate = (
        path.resolve() if path.is_absolute() else (package_root / path).resolve()
    )
    if not _is_path_within(path=candidate, root=package_root):
        raise RuntimeError(
            "Materialized package file escaped package root: "
            f"package_root={package_root} path={candidate}"
        )
    return candidate


def _refreshed_package_files_after_post_steps(
    *,
    package_root: Path,
    package_files: tuple[Path, ...],
    execution_results: tuple[object, ...],
) -> tuple[Path, ...]:
    return _dedupe_paths(
        path
        for path in (
            *package_files,
            *(
                effect_path
                for result in execution_results
                for effect_path in (
                    *getattr(result, "changed_paths", ()),
                    *getattr(result, "produced_paths", ()),
                )
            ),
        )
        if Path(path).exists()
        and Path(path).is_file()
        and _is_path_within(path=Path(path), root=package_root)
    )


def _materialized_result_files(
    *,
    render_files: tuple[Path, ...],
    declared_output_files: tuple[Path, ...],
    package_results: tuple[ObjectConfigGraphPackageResult, ...],
) -> tuple[Path, ...]:
    return _dedupe_paths(
        (
            *render_files,
            *declared_output_files,
            *(
                file
                for package in package_results
                for file in _package_result_files(
                    package_root=package.output_root,
                    files=tuple(package.files),
                )
            ),
        )
    )


def _assert_dart_part_files_exist(*, package_root: Path) -> None:
    lib_root = package_root / "lib"
    if not lib_root.is_dir():
        return
    missing: list[str] = []
    for source in sorted(lib_root.rglob("*.dart"), key=lambda path: path.as_posix()):
        if source.name.endswith((".g.dart", ".freezed.dart")):
            continue
        text = source.read_text(encoding="utf-8")
        for match in _DART_PART_DIRECTIVE_RE.finditer(text):
            part_path = (source.parent / match.group(1)).resolve()
            if not _is_path_within(path=part_path, root=package_root):
                raise RuntimeError(
                    "Dart part directive escapes generated package root: "
                    f"package_root={package_root} source={source} part={part_path}"
                )
            if not part_path.is_file():
                missing.append(part_path.relative_to(package_root).as_posix())
    if missing:
        examples = ", ".join(missing[:8])
        raise RuntimeError(
            "Dart generated part files are missing after build_runner: "
            f"package_root={package_root} missing={examples}"
        )


def _dedupe_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    return tuple(
        sorted(
            {Path(path).resolve() for path in paths},
            key=lambda path: path.as_posix(),
        )
    )


def _is_path_within(*, path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _declared_output_entity_file_paths(
    *,
    layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
) -> dict[str, Path]:
    entity_file_paths: dict[str, Path] = {}
    for attr_name in ("entity_template_paths", "entity_layout_paths"):
        raw_paths = getattr(layout_strategy, attr_name, None)
        if not isinstance(raw_paths, Mapping):
            continue
        for key, value in raw_paths.items():
            if not isinstance(key, str):
                continue
            entity_file_paths[key] = Path(value)
    return dict(sorted(entity_file_paths.items()))


def _expand_entity_candidate_paths_for_graph(
    *,
    layout_strategy: ObjectConfigGraphRenderLayoutStrategy,
    language_graph: ObjectConfigGraph,
    candidate_paths: tuple[Path, ...],
) -> tuple[Path, ...]:
    if not candidate_paths or layout_strategy.language is not CodeLanguage.python:
        return candidate_paths

    entity_paths: set[Path] = set()
    for node in language_graph.object_config_graph_nodes:
        if node.class_config is not None:
            entity_paths.add(layout_strategy.get_class_file_path(node.class_config))
        if node.enum_config is not None:
            entity_paths.add(layout_strategy.get_enum_file_path(node.enum_config))
    if not entity_paths:
        return candidate_paths

    candidate_path_set = {Path(path) for path in candidate_paths}
    if candidate_path_set.isdisjoint(entity_paths):
        return candidate_paths

    return tuple(
        sorted(
            (*candidate_path_set, *entity_paths),
            key=lambda path: path.as_posix(),
        )
    )


def _python_language_external_import_overrides(
    *,
    target_language: CodeLanguage,
    language_external_graphs: tuple[ObjectConfigGraph, ...],
    external_import_roots_by_graph_key: Mapping[str, str] | None = None,
    python_external_import_overrides_by_entity_id: Mapping[str, str] | None = None,
) -> dict[str, str]:
    if target_language is not CodeLanguage.python:
        return {}

    overrides: dict[str, str] = dict(
        python_external_import_overrides_by_entity_id or {}
    )
    if not language_external_graphs:
        return dict(sorted(overrides.items()))

    import_roots_by_graph_key = external_import_roots_by_graph_key or {}
    for graph in sorted(
        language_external_graphs,
        key=lambda item: (
            (item.fqn_prefix or item.name or "").casefold(),
            str(item.id),
        ),
    ):
        import_root = _external_graph_import_root(
            graph=graph,
            import_roots_by_graph_key=import_roots_by_graph_key,
        )
        if not import_root:
            continue
        layout = PythonLayoutStrategyTemplateMixin(
            base_dir=Path("."),
            import_root=import_root,
        )
        layout.bind_graph(graph)
        for node in graph.object_config_graph_nodes:
            if node.class_config is not None:
                path = layout.get_class_file_path(node.class_config)
                overrides.setdefault(
                    str(node.class_config.id),
                    layout.get_module_import_path(path),
                )
            if node.enum_config is not None:
                path = layout.get_enum_file_path(node.enum_config)
                overrides.setdefault(
                    str(node.enum_config.id),
                    layout.get_module_import_path(path),
                )
    return dict(sorted(overrides.items()))


def _external_graph_import_root(
    *,
    graph: ObjectConfigGraph,
    import_roots_by_graph_key: Mapping[str, str],
) -> str:
    for graph_key in (str(graph.id), graph.fqn_prefix, graph.name):
        key = (graph_key or "").strip()
        if not key:
            continue
        import_root = import_roots_by_graph_key.get(key)
        if isinstance(import_root, str) and import_root.strip():
            return import_root.strip().replace("-", "_")
    return (graph.fqn_prefix or graph.name or "").strip().replace("-", "_")


def _materialization_renderer_profile(
    *,
    materialization_config: MaterializationConfig,
) -> str | None:
    for package in materialization_config.packages:
        raw = package.metadata.get("aware_package_kind")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def _graph_materialization_profile(
    *,
    materialization_config: MaterializationConfig,
) -> GraphMaterializationProfile:
    renderer_profile = _materialization_renderer_profile(
        materialization_config=materialization_config,
    )
    source = materialization_config.source
    if source in {MaterializationSource.api, MaterializationSource.ontology_dto}:
        return "public_dto"
    if renderer_profile in {
        "api_public_package",
        "api_service_protocol",
        "ontology_dto",
    }:
        return "public_dto"
    return "runtime_orm"


def _load_profile_inputs(
    *,
    aware_root: Path,
    materialization_config: MaterializationConfig,
) -> dict[str, object]:
    payloads: dict[str, object] = {}
    for ref in materialization_config.profile_input_refs:
        key = ref.key.strip()
        if not key:
            raise ValueError(
                "materialization.profile_input_refs[].key must be non-empty"
            )
        if key in payloads:
            raise ValueError(
                f"Duplicate materialization.profile_input_refs key: {key!r}"
            )
        raw_path = Path(ref.path)
        resolved = raw_path if raw_path.is_absolute() else (aware_root / raw_path)
        if not resolved.exists():
            if ref.required:
                raise ValueError(
                    f"Required profile input {key!r} not found at {resolved}"
                )
            continue
        raw = resolved.read_bytes()
        if ref.format.value == "json":
            payloads[key] = json.loads(raw.decode("utf-8"))
        elif ref.format.value == "text":
            payloads[key] = raw.decode("utf-8")
        else:
            raise ValueError(
                f"Unsupported MaterializationProfileInputFormat: {ref.format!r}"
            )
    return payloads


def _build_declared_output_destinations(
    *,
    aware_root: Path,
    materialization_config: MaterializationConfig,
    package_results: tuple[ObjectConfigGraphPackageResult, ...],
) -> tuple[MetaLanguageMaterializationDestination, ...]:
    destinations: list[MetaLanguageMaterializationDestination] = [
        MetaLanguageMaterializationDestination(
            key="materialization_root",
            kind="materialization_root",
            root=(aware_root / ".aware" / "materializations").resolve(),
            import_root=materialization_config.import_root,
        )
    ]
    package_results_by_index = tuple(package_results)
    for index, spec in enumerate(materialization_config.packages):
        package_name = spec.package_name or spec.name
        if not package_name:
            continue
        package_result = (
            package_results_by_index[index]
            if index < len(package_results_by_index)
            else None
        )
        raw_output_root = (
            package_result.output_root
            if package_result is not None
            else spec.package_root
        )
        if raw_output_root is None:
            continue
        package_root = Path(raw_output_root).resolve()
        import_root = spec.import_root or package_name.replace("-", "_")
        destination_key = str(
            (spec.metadata or {}).get("api_product_runtime_destination_key")
            or f"package:{package_name}:{index}"
        )
        destinations.append(
            MetaLanguageMaterializationDestination(
                key=destination_key,
                kind="package_artifacts_root",
                root=(package_root / import_root / DEFAULT_ARTIFACTS_DIR).resolve(),
                package_name=package_name,
                package_root=package_root,
                import_root=import_root,
                file_paths=_declared_output_package_file_paths(
                    package_root=package_root,
                    import_root=import_root,
                    package_result=package_result,
                ),
                metadata=dict(spec.metadata or {}),
            )
        )
    return tuple(destinations)


def _declared_output_package_file_paths(
    *,
    package_root: Path,
    import_root: str,
    package_result: ObjectConfigGraphPackageResult | None,
) -> tuple[Path, ...]:
    paths: dict[str, Path] = {}
    for path in package_result.files if package_result is not None else ():
        resolved = Path(path).resolve()
        paths[resolved.as_posix()] = resolved
    import_root_dir = (package_root / import_root).resolve()
    if import_root_dir.is_dir():
        for path in import_root_dir.rglob("*"):
            if path.is_file():
                resolved = path.resolve()
                paths[resolved.as_posix()] = resolved
    return tuple(paths[key] for key in sorted(paths))


def _emit_api_service_protocol_external_python_type_index_artifact(
    *,
    accessible_dependency_packages: tuple[_AccessibleDependencyPackage, ...],
    runtime_package_dir: Path,
    repo_root: Path,
    api_dto_package_names: frozenset[str] = frozenset(),
) -> ApiProductRuntimeArtifactRef:
    payload = _build_external_python_type_index_payload(
        accessible_dependency_packages=accessible_dependency_packages,
        api_dto_package_names=api_dto_package_names,
    )
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (
        runtime_package_dir / "api.external_python_type_index.json"
    ).resolve()
    _ = artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return ApiProductRuntimeArtifactRef(
        kind="api.external_python_type_index",
        relpath=relpath,
        hash_sha256=digest,
    )


def _emit_api_accessible_dependency_graphs_artifact(
    *,
    accessible_graphs: tuple[ObjectConfigGraph, ...],
    runtime_package_dir: Path,
    repo_root: Path,
    accessible_dependency_packages: tuple[_AccessibleDependencyPackage, ...] = (),
    source_digest_package_names: Iterable[str] = (),
) -> ApiProductRuntimeArtifactRef:
    dependency_source_digests = _api_dependency_source_digests_payload(
        accessible_dependency_packages=accessible_dependency_packages,
        source_digest_package_names=source_digest_package_names,
    )
    payload = {
        "schema_version": 1,
        "dependency_source_digests": dependency_source_digests,
        "graphs": [
            dump_api_accessible_dependency_graph_artifact_payload(graph=graph)
            for graph in sorted(
                accessible_graphs,
                key=lambda item: (
                    (item.fqn_prefix or "").casefold(),
                    (item.name or "").casefold(),
                    str(item.id),
                ),
            )
        ],
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    digest = sha256(canonical).hexdigest()

    artifact_path = (
        runtime_package_dir / API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME
    ).resolve()
    _ = artifact_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    relpath = artifact_path.relative_to(repo_root).as_posix()
    return ApiProductRuntimeArtifactRef(
        kind="api.accessible_dependency_graphs",
        relpath=relpath,
        hash_sha256=digest,
    )


def _api_dependency_source_digests_payload(
    *,
    accessible_dependency_packages: tuple[_AccessibleDependencyPackage, ...],
    source_digest_package_names: Iterable[str],
) -> dict[str, str]:
    selected_package_names = {
        package_name.strip()
        for package_name in source_digest_package_names
        if package_name.strip()
    }
    if not selected_package_names:
        return {}
    package_by_name = {
        package.package_name: package for package in accessible_dependency_packages
    }
    digests: dict[str, str] = {}
    for package_name, package in sorted(package_by_name.items()):
        if package_name not in selected_package_names:
            continue
        aware_toml_path = (package.package_root / "aware.toml").resolve()
        if not aware_toml_path.is_file():
            continue
        digests[package_name] = compute_api_dependency_source_digest_for_aware_toml(
            aware_toml_path=aware_toml_path,
        )
    return digests


def _build_external_python_type_index_payload(
    *,
    accessible_dependency_packages: tuple[_AccessibleDependencyPackage, ...],
    api_dto_package_names: frozenset[str] = frozenset(),
) -> dict[str, object]:
    classes: dict[str, dict[str, str]] = {}
    enums: dict[str, dict[str, str]] = {}
    for package in accessible_dependency_packages:
        if package.package_kind != "ontology" and not _is_api_dto_dependency_package(
            package=package,
            api_dto_package_names=api_dto_package_names,
        ):
            continue
        metadata = _load_dependency_python_type_metadata(package=package)
        raw_classes = metadata.get("classes", [])
        if not isinstance(raw_classes, list):
            raise ValueError(
                "Invalid service protocol package dependency Python type metadata: classes must be a list "
                + f"(package={package.package_name!r})"
            )
        for item in raw_classes:
            if not isinstance(item, dict):
                raise ValueError(
                    "Invalid service protocol package dependency Python type metadata: class entries must be objects "
                    + f"(package={package.package_name!r})"
                )
            class_config_id = str(item.get("class_config_id") or "").strip()
            module = str(item.get("module") or "").strip()
            name = str(item.get("name") or "").strip()
            class_ref = str(
                item.get("aware_class_ref") or item.get("class_ref") or ""
            ).strip()
            if not class_config_id or not module or not name:
                raise ValueError(
                    "Invalid service protocol package dependency Python type metadata: class entries must include "
                    + f"class_config_id/module/name (package={package.package_name!r})"
                )
            candidate = {"module": module, "name": name}
            if class_ref:
                candidate["class_ref"] = class_ref
            existing = classes.get(class_config_id)
            if existing is not None and existing != candidate:
                raise ValueError(
                    "Conflicting service protocol package dependency Python class metadata for "
                    + f"{class_config_id!r}: existing={existing!r} candidate={candidate!r}"
                )
            classes[class_config_id] = candidate
        raw_enums = metadata.get("enums", [])
        if not isinstance(raw_enums, list):
            raise ValueError(
                "Invalid service protocol package dependency Python type metadata: enums must be a list "
                + f"(package={package.package_name!r})"
            )
        for item in raw_enums:
            if not isinstance(item, dict):
                raise ValueError(
                    "Invalid service protocol package dependency Python type metadata: enum entries must be objects "
                    + f"(package={package.package_name!r})"
                )
            enum_config_id = str(item.get("enum_config_id") or "").strip()
            module = str(item.get("module") or "").strip()
            name = str(item.get("name") or "").strip()
            enum_ref = str(
                item.get("aware_enum_ref") or item.get("enum_ref") or ""
            ).strip()
            if not enum_config_id or not module or not name:
                raise ValueError(
                    "Invalid service protocol package dependency Python type metadata: enum entries must include "
                    + f"enum_config_id/module/name (package={package.package_name!r})"
                )
            candidate = {"module": module, "name": name}
            if enum_ref:
                candidate["enum_ref"] = enum_ref
            existing = enums.get(enum_config_id)
            if existing is not None and existing != candidate:
                raise ValueError(
                    "Conflicting service protocol package dependency Python enum metadata for "
                    + f"{enum_config_id!r}: existing={existing!r} candidate={candidate!r}"
                )
            enums[enum_config_id] = candidate
    return {
        "language": "python",
        "classes": classes,
        "enums": enums,
    }


def _load_dependency_python_type_metadata(
    *,
    package: _AccessibleDependencyPackage,
) -> dict[str, object]:
    metadata_path = _resolve_dependency_python_models_path(package=package)
    if metadata_path is not None:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    return _build_dependency_python_type_metadata_from_graph(package=package)


def _resolve_dependency_python_models_path(
    *, package: _AccessibleDependencyPackage
) -> Path | None:
    candidate_roots = (package.package_root, *package.package_root.parents)
    for candidate_root in candidate_roots:
        for metadata_path in (
            candidate_root
            / "python"
            / package.import_root
            / "_aware"
            / "python.models.json",
            candidate_root
            / "python"
            / package.import_root
            / package.import_root
            / "_aware"
            / "python.models.json",
        ):
            if metadata_path.is_file():
                return metadata_path
    return None


def _build_dependency_python_type_metadata_from_graph(
    *,
    package: _AccessibleDependencyPackage,
) -> dict[str, object]:
    classes: list[dict[str, str]] = []
    enums: list[dict[str, str]] = []
    layout = PythonLayoutStrategyTemplateMixin(
        base_dir=Path("."),
        entity_template_paths=_python_entity_template_paths_from_graph(package.graph),
        import_root=package.import_root,
    )
    layout.bind_graph(package.graph)

    for node in package.graph.object_config_graph_nodes:
        class_config = node.class_config
        if class_config is not None:
            authored_ref = _authored_ref_from_fqn(class_config.class_fqn)
            file_path = layout.get_class_file_path(class_config)
            classes.append(
                {
                    "class_config_id": str(class_config.id),
                    "module": layout.get_module_import_path(file_path),
                    "name": class_config.name,
                    "aware_class_ref": authored_ref,
                }
            )
            continue

        enum_config = node.enum_config
        if enum_config is None:
            continue
        authored_ref = _authored_ref_from_fqn(enum_config.enum_fqn)
        file_path = layout.get_enum_file_path(enum_config)
        enums.append(
            {
                "enum_config_id": str(enum_config.id),
                "module": layout.get_module_import_path(file_path),
                "name": enum_config.name,
                "aware_enum_ref": authored_ref,
            }
        )

    classes.sort(
        key=lambda item: (item["module"], item["name"], item["class_config_id"])
    )
    enums.sort(key=lambda item: (item["module"], item["name"], item["enum_config_id"]))
    return {
        "language": "python",
        "classes": classes,
        "enums": enums,
    }


def _authored_ref_from_fqn(fqn: str) -> str:
    parts = [part.strip() for part in fqn.split(".") if part.strip()]
    if len(parts) <= 2:
        return fqn.strip()
    return ".".join(
        [
            parts[0],
            *[part for part in parts[1:-1] if part.casefold() != "default"],
            parts[-1],
        ]
    )


def _normalize_package_kind(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw).strip().lower()


def _derive_dependency_import_root(*, spec) -> str:
    fqn_prefix = (
        (spec.package.fqn_prefix or spec.package.package_name).strip().replace("-", "_")
    )
    package_kind = _normalize_package_kind(spec.package.kind)
    if package_kind == "ontology":
        return f"{fqn_prefix}_ontology" if fqn_prefix else "aware_ontology"
    return fqn_prefix or spec.package.package_name.replace("-", "_")


__all__ = [
    "ApiPublicPackageMaterializationResult",
    "ApiServiceProtocolMaterializationResult",
    "refresh_api_public_package_from_runtime_artifacts",
    "refresh_api_service_protocol_from_runtime_artifacts",
    "build_api_accessible_dependency_graphs",
    "materialize_api_public_package",
    "materialize_api_dto_packages",
    "materialize_api_service_protocol",
]
