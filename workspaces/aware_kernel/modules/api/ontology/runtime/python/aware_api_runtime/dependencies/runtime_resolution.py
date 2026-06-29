from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter
import tomllib
from typing import cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import msgpack
from pydantic import BaseModel

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.manifest.loader import load_aware_toml_spec
from aware_meta.manifest.spec import (
    AwarePackageKind,
    AwareTomlSpec,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_node_layout import (
    ObjectConfigGraphNodeLayout,
)
from aware_meta.graph.config.handlers import build_object_projection_graphs
from aware_meta.graph.config.namespace.membership import (
    build_namespace_membership_payload_from_ocg_identity,
    object_config_graph_payload_has_exported_namespace_evidence,
)
from aware_orm.runtime.models_manifest import ClassModelEntry, ModelsManifest
from aware_ontology.semantic_runtime_catalog import (
    ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_ARTIFACT_ROLE,
    ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_ARTIFACT_ROLE,
    find_ontology_runtime_artifact_ref,
    ontology_runtime_artifact_ref_path,
    resolve_local_ontology_runtime_artifact_set_payload,
)
from aware_utils.logging import logger
from tree_sitter import Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from ..source.compiler import load_api_graph_targets_from_sources
from ..models import BindingMapTruth
from ..workspace import APIWorkspace, APIWorkspaceSnapshot

_API_RUNTIME_SOURCE_DIGEST_FILENAME = "api.runtime.sources.sha256"
API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME = "api.accessible_dependency_graphs.json"
API_RUNTIME_SEMANTICS_FILENAME = "api.runtime_semantics.json"
_API_ACCESSIBLE_DEPENDENCY_GRAPH_ARTIFACT_CACHE_MAX = 4
_API_ACCESSIBLE_DEPENDENCY_GRAPH_ARTIFACT_CACHE: dict[
    tuple[Path, str],
    tuple[ObjectConfigGraph, ...],
] = {}
_API_ACCESSIBLE_DEPENDENCY_GRAPH_ARTIFACT_CACHE_ORDER: list[tuple[Path, str]] = []
API_ACCESSIBLE_DEPENDENCY_GRAPH_REFERENCE_FIELDS = frozenset(
    {
        "domain_relationships",
        "target_object_config_graph",
    }
)
API_ACCESSIBLE_DEPENDENCY_GRAPH_VOLATILE_FIELDS = frozenset(
    {
        "code_section_annotation_discriminate_id",
        "code_section_annotation_id",
        "code_section_annotation_identity_id",
        "code_section_annotation_load_id",
        "code_section_annotation_oneof_id",
        "code_section_annotation_overlay_id",
        "code_section_annotation_override_id",
        "code_section_annotation_reference_id",
        "code_section_attribute_id",
        "code_section_class_id",
        "code_section_enum_id",
        "code_section_function_id",
    }
)
API_ACCESSIBLE_DEPENDENCY_GRAPH_UNORDERED_LIST_FIELDS = frozenset(
    {
        "child_links",
        "class_config_attribute_configs",
        "class_config_function_configs",
        "class_config_relationship_attributes",
        "class_config_relationships",
        "function_config_attribute_configs",
        "layouts",
        "namespace_membership",
        "object_config_graph_annotations",
        "object_config_graph_bindings",
        "object_config_graph_mirrors",
        "object_config_graph_nodes",
        "object_config_graph_overlays",
        "object_config_graph_relationships",
        "object_projection_graph_declarations",
        "object_projection_graphs",
        "object_projection_graph_nodes",
        "object_projection_graph_relationships",
        "schema_relationships",
    }
)
_AWARE_TOML_PACKAGE_DISCOVERY_PRUNED_DIR_NAMES = frozenset(
    {
        ".aware",
        "_aware",
        ".dart_tool",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "node_modules",
    }
)


class RuntimeRequirementsError(RuntimeError):
    """Raised when API runtime manifest resolution cannot compose requirements."""


def _round_duration_s(duration_s: float) -> float:
    return round(max(duration_s, 0.0), 6)


@contextmanager
def _record_optional_phase(
    phase_timings_s: dict[str, float] | None,
    phase_name: str,
) -> Iterator[None]:
    if phase_timings_s is None:
        yield
        return
    started_at = perf_counter()
    logger.info("API runtime resolution phase started: %s", phase_name)
    try:
        yield
    finally:
        duration_s = _round_duration_s(perf_counter() - started_at)
        phase_timings_s[phase_name] = duration_s
        logger.info(
            "API runtime resolution phase finished: %s (%.6fs)",
            phase_name,
            duration_s,
        )


@dataclass(frozen=True, slots=True)
class _RuntimeDependencyPackage:
    package_name: str
    aware_toml_path: Path
    package_root: Path
    spec: AwareTomlSpec

    @property
    def kind(self) -> AwarePackageKind:
        return self.spec.package.kind

    @property
    def import_root(self) -> str:
        fqn_prefix = (
            (self.spec.package.fqn_prefix or self.spec.package.package_name)
            .strip()
            .replace("-", "_")
        )
        if self.kind == AwarePackageKind.ontology:
            return f"{fqn_prefix}_ontology" if fqn_prefix else "aware_ontology"
        return fqn_prefix or self.spec.package.package_name.replace("-", "_")

    @property
    def python_root(self) -> Path:
        return (self.package_root / "python").resolve()

    @property
    def runtime_manifest_path(self) -> Path:
        if self.kind == AwarePackageKind.ontology:
            return self._ontology_runtime_artifact_path(
                artifact_role=ONTOLOGY_RUNTIME_BUNDLE_MANIFEST_ARTIFACT_ROLE,
                output_key="runtime_bundle_manifest",
                fallback_filename="ontology.runtime.manifest.json",
            )
        if self.kind == AwarePackageKind.api:
            return (
                self.package_root
                / ".aware"
                / "api"
                / "runtime"
                / self.package_name
                / "api.manifest.json"
            ).resolve()
        return (
            self.package_root
            / ".aware"
            / "runtime"
            / f"{self.package_name}.runtime.manifest.json"
        ).resolve()

    @property
    def python_models_path(self) -> Path:
        if self.kind == AwarePackageKind.ontology:
            return self._ontology_runtime_artifact_path(
                artifact_role=ONTOLOGY_RUNTIME_PYTHON_MODELS_MANIFEST_ARTIFACT_ROLE,
                output_key="python_models_manifest",
                fallback_filename="python.models.json",
            )
        return (
            self.package_root / ".aware" / "materializations" / "python.models.json"
        ).resolve()

    @property
    def runtime_source_digest_path(self) -> Path:
        return (
            self.package_root
            / ".aware"
            / "materializations"
            / _API_RUNTIME_SOURCE_DIGEST_FILENAME
        ).resolve()

    @property
    def module_root(self) -> Path:
        return self.package_root.parent.parent.resolve()

    @property
    def runtime_root(self) -> Path:
        return (self.module_root / "runtime").resolve()

    def _ontology_runtime_artifact_path(
        self,
        *,
        artifact_role: str,
        output_key: str,
        fallback_filename: str,
    ) -> Path:
        artifact_set = resolve_local_ontology_runtime_artifact_set_payload(
            package_name=self.package_name,
            fqn_prefix=self.spec.package.fqn_prefix or self.package_name,
            source_manifest_path=self.aware_toml_path,
            include_artifacts=True,
        )
        artifact_ref = find_ontology_runtime_artifact_ref(
            artifact_set=artifact_set,
            artifact_role=artifact_role,
            output_key=output_key,
            require_available=False,
        )
        if artifact_ref is not None:
            path = ontology_runtime_artifact_ref_path(artifact_ref=artifact_ref)
            if path is not None:
                return path
        return (
            self.package_root / ".aware" / "ontology" / "runtime" / fallback_filename
        ).resolve()


@dataclass(frozen=True, slots=True)
class APIRuntimeSemanticArtifacts:
    runtime_package_dir: Path
    semantic_manifest_path: Path
    accessible_dependency_graphs_path: Path
    dependency_packages: tuple[_RuntimeDependencyPackage, ...]
    dependency_python_roots: tuple[Path, ...]
    dependency_runtime_roots: tuple[Path, ...]
    registered_class_config_count: int


@dataclass(frozen=True, slots=True)
class RuntimeImportActivationPlan:
    roots: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class RuntimeManifestResolution:
    manifest_path: Path
    module_ids: tuple[str, ...]
    module_manifest_paths: tuple[Path, ...]
    python_roots: tuple[Path, ...]
    import_activation: RuntimeImportActivationPlan
    environment_handle: str

    @property
    def import_roots(self) -> tuple[Path, ...]:
        return self.import_activation.roots


def build_runtime_import_activation_plan(
    *,
    roots: Iterable[Path],
) -> RuntimeImportActivationPlan:
    normalized: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        resolved = root.resolve()
        if not resolved.exists() or resolved in seen:
            continue
        seen.add(resolved)
        normalized.append(resolved)
    return RuntimeImportActivationPlan(roots=tuple(normalized))


def resolve_api_workspace_runtime_manifest(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None = None,
    kernel_repo_root: str | Path | None = None,
    dependency_repo_roots: Iterable[str | Path] = (),
    environment_toml: str | Path | None = None,
    core_module_ids: tuple[str, ...] | list[str] = (),
    output_path: Path | None = None,
    author_id: UUID | None = None,
) -> RuntimeManifestResolution:
    if environment_toml is not None:
        raise RuntimeRequirementsError(
            "API runtime resolution no longer composes EnvironmentConfig manifests. "
            "Use a Workspace/Structure-owned EnvironmentConfig materialization "
            "receipt and pass the prepared runtime artifact to the Environment/Node "
            "host instead."
        )
    if tuple(core_module_ids):
        raise RuntimeRequirementsError(
            "API runtime resolution no longer introspects kernel/core modules. "
            "API runtime activation consumes API-owned semantic artifacts and "
            "explicit dependency package roots only; module composition belongs "
            "to Workspace/Structure or the test-harness lane."
        )

    phase_timings_s: dict[str, float] = {}
    with _record_optional_phase(phase_timings_s, "workspace_from_toml"):
        workspace = APIWorkspace.from_toml(toml_path=toml_path, repo_root=repo_root)
    with _record_optional_phase(phase_timings_s, "build_workspace_snapshot"):
        snapshot = workspace.build_snapshot()
    with _record_optional_phase(
        phase_timings_s,
        "resolve_api_runtime_semantic_artifacts",
    ):
        semantic_artifacts = resolve_api_runtime_semantic_artifacts(
            snapshot=snapshot,
            register_class_configs=True,
            dependency_repo_roots=dependency_repo_roots,
            phase_timings_s=phase_timings_s,
        )

    environment_handle = _api_runtime_environment_handle(snapshot=snapshot)
    manifest_path = (
        Path(output_path).expanduser().resolve()
        if output_path is not None
        else semantic_artifacts.semantic_manifest_path
    )
    if manifest_path != semantic_artifacts.semantic_manifest_path:
        with _record_optional_phase(
            phase_timings_s, "emit_api_runtime_semantics_manifest"
        ):
            _emit_api_runtime_semantics_manifest(
                snapshot=snapshot,
                runtime_package_dir=semantic_artifacts.runtime_package_dir,
                accessible_dependency_graphs_path=semantic_artifacts.accessible_dependency_graphs_path,
                dependency_packages=semantic_artifacts.dependency_packages,
                registered_class_config_count=semantic_artifacts.registered_class_config_count,
                output_path=manifest_path,
            )

    with _record_optional_phase(phase_timings_s, "build_python_roots"):
        combined_python_roots = _dedupe_paths(
            semantic_artifacts.dependency_python_roots,
        )
    with _record_optional_phase(phase_timings_s, "build_import_activation_plan"):
        import_activation = build_runtime_import_activation_plan(
            roots=_dedupe_paths(
                [
                    *semantic_artifacts.dependency_python_roots,
                    *semantic_artifacts.dependency_runtime_roots,
                ]
            )
        )
    resolution = RuntimeManifestResolution(
        manifest_path=manifest_path,
        module_ids=(),
        module_manifest_paths=(),
        python_roots=tuple(combined_python_roots),
        import_activation=import_activation,
        environment_handle=environment_handle,
    )
    logger.info(
        "API runtime resolution completed: manifest_path=%s dependencies=%d "
        "python_roots=%d registered_class_configs=%d phases=%s",
        resolution.manifest_path,
        len(semantic_artifacts.dependency_packages),
        len(resolution.python_roots),
        semantic_artifacts.registered_class_config_count,
        {key: round(value, 3) for key, value in phase_timings_s.items()},
    )
    return resolution


def resolve_api_runtime_semantic_artifacts(
    *,
    snapshot: APIWorkspaceSnapshot,
    register_class_configs: bool = True,
    dependency_repo_roots: Iterable[str | Path] = (),
    phase_timings_s: dict[str, float] | None = None,
) -> APIRuntimeSemanticArtifacts:
    with _record_optional_phase(
        phase_timings_s,
        "resolve_api_runtime_semantic_artifacts.resolve_dependency_packages",
    ):
        dependency_packages = _resolve_api_dependency_packages(
            snapshot=snapshot,
            dependency_repo_roots=dependency_repo_roots,
        )
    runtime_package_dir = _api_runtime_package_dir(snapshot=snapshot)
    with _record_optional_phase(
        phase_timings_s,
        "resolve_api_runtime_semantic_artifacts.load_accessible_dependency_graphs_runtime_artifact",
    ):
        accessible_graphs = _load_complete_api_accessible_dependency_graphs_artifact(
            runtime_package_dir=runtime_package_dir,
            dependency_packages=dependency_packages,
        )
    if accessible_graphs is None:
        with _record_optional_phase(
            phase_timings_s,
            "resolve_api_runtime_semantic_artifacts.load_accessible_dependency_graphs",
        ):
            accessible_graphs = load_api_accessible_dependency_graphs(
                snapshot=snapshot,
                dependency_repo_roots=dependency_repo_roots,
            )
    with _record_optional_phase(
        phase_timings_s,
        "resolve_api_runtime_semantic_artifacts.emit_accessible_dependency_graphs",
    ):
        accessible_dependency_graphs_path = (
            _emit_api_accessible_dependency_graphs_artifact(
                accessible_graphs=accessible_graphs,
                runtime_package_dir=runtime_package_dir,
                dependency_packages=dependency_packages,
                source_digest_package_names=(
                    _runtime_dependency_source_digest_package_names(
                        dependency_packages=dependency_packages,
                    )
                ),
            )
        )

    registered_count = 0
    if register_class_configs:
        with _record_optional_phase(
            phase_timings_s,
            "resolve_api_runtime_semantic_artifacts.register_class_configs",
        ):
            registered_count = _register_api_dependency_class_configs(
                accessible_graphs=accessible_graphs,
                source=accessible_dependency_graphs_path,
            )

    with _record_optional_phase(
        phase_timings_s,
        "resolve_api_runtime_semantic_artifacts.emit_semantics_manifest",
    ):
        semantic_manifest_path = _emit_api_runtime_semantics_manifest(
            snapshot=snapshot,
            runtime_package_dir=runtime_package_dir,
            accessible_dependency_graphs_path=accessible_dependency_graphs_path,
            dependency_packages=dependency_packages,
            registered_class_config_count=registered_count,
        )

    return APIRuntimeSemanticArtifacts(
        runtime_package_dir=runtime_package_dir,
        semantic_manifest_path=semantic_manifest_path,
        accessible_dependency_graphs_path=accessible_dependency_graphs_path,
        dependency_packages=dependency_packages,
        dependency_python_roots=tuple(
            _dedupe_paths(package.python_root for package in dependency_packages)
        ),
        dependency_runtime_roots=tuple(
            _dedupe_paths(package.runtime_root for package in dependency_packages)
        ),
        registered_class_config_count=registered_count,
    )


def ensure_api_dependency_runtime_artifacts(
    *,
    snapshot: APIWorkspaceSnapshot,
    author_id: UUID | None = None,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[_RuntimeDependencyPackage, ...]:
    phase_timings_s: dict[str, float] = {}
    with _record_optional_phase(phase_timings_s, "resolve_dependency_packages"):
        ordered = _resolve_api_dependency_packages(
            snapshot=snapshot,
            dependency_repo_roots=dependency_repo_roots,
        )
    resolved_author_id = author_id or uuid4()
    for package in ordered:
        logger.info(
            "API dependency runtime artifact check started: package=%s kind=%s",
            package.package_name,
            package.kind.value,
        )
        with _record_optional_phase(
            phase_timings_s,
            f"dependency.{package.package_name}.compute_source_digest",
        ):
            expected_source_digest = _compute_runtime_dependency_source_digest(
                package=package
            )
        with _record_optional_phase(
            phase_timings_s,
            f"dependency.{package.package_name}.check_freshness",
        ):
            is_fresh = False
            if (
                package.runtime_manifest_path.is_file()
                and package.python_models_path.is_file()
            ):
                manifest = ModelsManifest.model_validate_json(
                    package.python_models_path.read_text(encoding="utf-8")
                )
                is_fresh = _models_manifest_has_authored_class_refs(
                    manifest=manifest
                ) and (
                    _runtime_dependency_source_digest_matches(
                        package=package,
                        expected_digest=expected_source_digest,
                    )
                    or _runtime_dependency_outputs_are_fresh_for_inputs(package=package)
                )
        if is_fresh:
            logger.info(
                "API dependency runtime artifact check skipped fresh package: package=%s",
                package.package_name,
            )
            continue
        with _record_optional_phase(
            phase_timings_s,
            f"dependency.{package.package_name}.build_runtime_package",
        ):
            _build_runtime_dependency_package(
                package=package,
                repo_root=snapshot.repo_root,
                author_id=resolved_author_id,
            )
        with _record_optional_phase(
            phase_timings_s,
            f"dependency.{package.package_name}.validate_outputs",
        ):
            if not package.runtime_manifest_path.is_file():
                raise FileNotFoundError(
                    "API runtime dependency build did not emit runtime manifest for "
                    + f"{package.package_name!r}: {package.runtime_manifest_path}"
                )
            if not package.python_models_path.is_file():
                raise FileNotFoundError(
                    "API runtime dependency build did not emit python.models.json for "
                    + f"{package.package_name!r}: {package.python_models_path}"
                )
        with _record_optional_phase(
            phase_timings_s,
            f"dependency.{package.package_name}.write_source_digest",
        ):
            _write_runtime_dependency_source_digest(
                package=package,
                source_digest=expected_source_digest,
            )
        logger.info(
            "API dependency runtime artifact check finished: package=%s phases=%s",
            package.package_name,
            {
                key: round(value, 3)
                for key, value in phase_timings_s.items()
                if f".{package.package_name}." in key
            },
        )
    return tuple(ordered)


def resolve_api_dependency_runtime_manifest_paths(
    *,
    snapshot: APIWorkspaceSnapshot,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[Path, ...]:
    return tuple(
        package.runtime_manifest_path
        for package in _resolve_api_dependency_packages(
            snapshot=snapshot,
            dependency_repo_roots=dependency_repo_roots,
        )
    )


def load_api_accessible_dependency_graphs(
    *,
    snapshot: APIWorkspaceSnapshot,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[ObjectConfigGraph, ...]:
    packages = _resolve_api_dependency_packages(
        snapshot=snapshot,
        dependency_repo_roots=dependency_repo_roots,
    )
    graphs_by_package_name: dict[str, ObjectConfigGraph] = {}
    ordered_graphs: list[ObjectConfigGraph] = []

    for package in packages:
        graph = _load_required_dependency_object_config_graph(package=package)
        graph = _ensure_dependency_object_projection_graphs(
            package=package,
            graph=graph,
            graphs_by_package_name=graphs_by_package_name,
        )
        graphs_by_package_name[package.package_name] = graph
        ordered_graphs.append(graph)

    return tuple(ordered_graphs)


def _load_complete_api_accessible_dependency_graphs_artifact(
    *,
    runtime_package_dir: Path,
    dependency_packages: tuple[_RuntimeDependencyPackage, ...],
) -> tuple[ObjectConfigGraph, ...] | None:
    if not _api_accessible_dependency_graph_source_digests_are_current(
        runtime_package_dir=runtime_package_dir,
        dependency_packages=dependency_packages,
    ):
        return None
    try:
        artifact_graphs = load_api_accessible_dependency_graphs_from_runtime_artifact(
            runtime_package_dir=runtime_package_dir,
        )
    except FileNotFoundError:
        return None
    graph_by_package_name: dict[str, ObjectConfigGraph] = {}
    consumed_graph_ids: set[UUID] = set()
    for package in dependency_packages:
        graph = _find_accessible_graph_for_dependency_package(
            package=package,
            accessible_graphs=artifact_graphs,
        )
        if graph is None:
            return None
        graph_by_package_name[package.package_name] = graph
        consumed_graph_ids.add(graph.id)
    ordered_graphs = [
        graph_by_package_name[package.package_name] for package in dependency_packages
    ]
    ordered_graphs.extend(
        graph for graph in artifact_graphs if graph.id not in consumed_graph_ids
    )
    return tuple(ordered_graphs)


def _find_accessible_graph_for_dependency_package(
    *,
    package: _RuntimeDependencyPackage,
    accessible_graphs: tuple[ObjectConfigGraph, ...],
) -> ObjectConfigGraph | None:
    package_name = package.package_name.strip()
    fqn_prefix = (package.spec.package.fqn_prefix or "").strip()
    for graph in accessible_graphs:
        graph_name = str(getattr(graph, "name", "") or "").strip()
        graph_fqn_prefix = str(getattr(graph, "fqn_prefix", "") or "").strip()
        if package_name and graph_name == package_name:
            return graph
        if fqn_prefix and graph_fqn_prefix == fqn_prefix:
            return graph
    return None


def _api_accessible_dependency_graph_source_digests_are_current(
    *,
    runtime_package_dir: Path,
    dependency_packages: tuple[_RuntimeDependencyPackage, ...],
) -> bool:
    if not dependency_packages:
        return True
    recorded_digests = load_api_accessible_dependency_graph_source_digests(
        runtime_package_dir=runtime_package_dir,
    )
    for package in dependency_packages:
        try:
            expected_digest = _compute_runtime_dependency_source_digest(
                package=package,
            )
        except Exception as exc:
            logger.info(
                "API accessible dependency graph artifact source digest check "
                "failed; rebuilding dependency graph context: package=%s error=%s",
                package.package_name,
                exc,
            )
            return False
        recorded_digest = recorded_digests.get(package.package_name)
        if recorded_digest != expected_digest:
            logger.info(
                "API accessible dependency graph artifact is stale; rebuilding "
                "dependency graph context: package=%s recorded_digest_present=%s",
                package.package_name,
                recorded_digest is not None,
            )
            return False
    return True


def load_api_accessible_dependency_graphs_from_runtime_artifact(
    *,
    runtime_package_dir: str | Path,
) -> tuple[ObjectConfigGraph, ...]:
    from aware_meta.graph.config.model_bootstrap import (
        normalize_object_config_graph_payload_for_bootstrap,
    )

    artifact_path = (
        Path(runtime_package_dir).expanduser().resolve()
        / API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME
    )
    if not artifact_path.is_file():
        raise FileNotFoundError(
            "API runtime accessible dependency graph artifact is missing. "
            "Committed deployment activation cannot rebuild API dependency graphs "
            "from source TOML; compile the API service-protocol runtime artifact first: "
            f"{artifact_path}"
        )
    artifact_bytes = artifact_path.read_bytes()
    cache_key = (
        artifact_path,
        hashlib.sha256(artifact_bytes).hexdigest(),
    )
    cached_graphs = _cached_api_accessible_dependency_graph_artifact(cache_key)
    if cached_graphs is not None:
        return cached_graphs

    payload = json.loads(artifact_bytes)
    if not isinstance(payload, Mapping):
        raise RuntimeError(
            "Invalid API runtime accessible dependency graph artifact: root must be an object "
            f"({artifact_path})"
        )
    schema_version = payload.get("schema_version")
    if schema_version != 1:
        raise RuntimeError(
            "Invalid API runtime accessible dependency graph artifact: unsupported "
            f"schema_version={schema_version!r} ({artifact_path})"
        )
    raw_graphs = payload.get("graphs")
    if not isinstance(raw_graphs, list):
        raise RuntimeError(
            "Invalid API runtime accessible dependency graph artifact: graphs must be a list "
            f"({artifact_path})"
        )
    graphs: list[ObjectConfigGraph] = []
    for graph_payload in raw_graphs:
        normalized_payload = normalize_api_accessible_dependency_graph_artifact_payload(
            payload=graph_payload,
        )
        if not isinstance(normalized_payload, Mapping):
            raise RuntimeError(
                "Invalid API runtime accessible dependency graph artifact: graph "
                f"payload must be an object ({artifact_path})"
            )
        _validate_api_accessible_dependency_graph_namespace_evidence(
            payload=normalized_payload,
            source=str(artifact_path),
        )
        graphs.append(
            ObjectConfigGraph.model_validate(
                normalize_object_config_graph_payload_for_bootstrap(
                    payload=normalized_payload,
                )
            )
        )
    return _remember_api_accessible_dependency_graph_artifact(
        cache_key=cache_key,
        graphs=tuple(graphs),
    )


def load_api_accessible_dependency_graph_source_digests(
    *,
    runtime_package_dir: str | Path,
) -> dict[str, str]:
    artifact_path = (
        Path(runtime_package_dir).expanduser().resolve()
        / API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME
    )
    if not artifact_path.is_file():
        return {}
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, Mapping):
        return {}
    raw_digests = payload.get("dependency_source_digests")
    if not isinstance(raw_digests, Mapping):
        return {}
    digests: dict[str, str] = {}
    for raw_package_name, raw_digest in raw_digests.items():
        package_name = str(raw_package_name).strip()
        digest = str(raw_digest).strip()
        if package_name and digest:
            digests[package_name] = digest
    return digests


def _cached_api_accessible_dependency_graph_artifact(
    cache_key: tuple[Path, str],
) -> tuple[ObjectConfigGraph, ...] | None:
    return _API_ACCESSIBLE_DEPENDENCY_GRAPH_ARTIFACT_CACHE.get(cache_key)


def _remember_api_accessible_dependency_graph_artifact(
    *,
    cache_key: tuple[Path, str],
    graphs: tuple[ObjectConfigGraph, ...],
) -> tuple[ObjectConfigGraph, ...]:
    if cache_key in _API_ACCESSIBLE_DEPENDENCY_GRAPH_ARTIFACT_CACHE:
        return _API_ACCESSIBLE_DEPENDENCY_GRAPH_ARTIFACT_CACHE[cache_key]
    _API_ACCESSIBLE_DEPENDENCY_GRAPH_ARTIFACT_CACHE[cache_key] = graphs
    _API_ACCESSIBLE_DEPENDENCY_GRAPH_ARTIFACT_CACHE_ORDER.append(cache_key)
    while (
        len(_API_ACCESSIBLE_DEPENDENCY_GRAPH_ARTIFACT_CACHE_ORDER)
        > _API_ACCESSIBLE_DEPENDENCY_GRAPH_ARTIFACT_CACHE_MAX
    ):
        expired_key = _API_ACCESSIBLE_DEPENDENCY_GRAPH_ARTIFACT_CACHE_ORDER.pop(0)
        _API_ACCESSIBLE_DEPENDENCY_GRAPH_ARTIFACT_CACHE.pop(expired_key, None)
    return graphs


def normalize_api_accessible_dependency_graph_artifact_payload(
    *,
    payload: object,
) -> object:
    """Normalize dependency graph artifacts to a flat closure payload.

    API product runtime artifacts carry the accessible dependency graph closure as
    top-level graphs. Embedded graph object references are redundant with that
    closure and can include runtime-only membership/back-reference payloads that
    are not portable across a WorkspaceRevision boundary.
    """

    if isinstance(payload, Mapping):
        return {
            key: normalize_api_accessible_dependency_graph_artifact_payload(
                payload=value,
            )
            for key, value in payload.items()
            if key not in API_ACCESSIBLE_DEPENDENCY_GRAPH_REFERENCE_FIELDS
            and key not in API_ACCESSIBLE_DEPENDENCY_GRAPH_VOLATILE_FIELDS
        }
    if isinstance(payload, list):
        return [
            normalize_api_accessible_dependency_graph_artifact_payload(payload=item)
            for item in payload
        ]
    return payload


def dump_api_accessible_dependency_graph_artifact_payload(
    *,
    graph: ObjectConfigGraph,
) -> object:
    payload = _json_safe_dependency_graph_payload(graph)
    if isinstance(payload, Mapping):
        payload = dict(payload)
        namespace_membership = build_namespace_membership_payload_from_ocg_identity(
            ocg=graph,
        )
        if namespace_membership:
            payload["namespace_membership"] = [
                dict(entry) for entry in namespace_membership
            ]
    normalized_payload = normalize_api_accessible_dependency_graph_artifact_payload(
        payload=payload,
    )
    normalized_payload = canonicalize_api_accessible_dependency_graph_artifact_payload(
        payload=normalized_payload,
    )
    if isinstance(normalized_payload, Mapping):
        _validate_api_accessible_dependency_graph_namespace_evidence(
            payload=normalized_payload,
            source=graph.name,
        )
    return normalized_payload


def canonicalize_api_accessible_dependency_graph_artifact_payload(
    *,
    payload: object,
    parent_key: str | None = None,
) -> object:
    if isinstance(payload, Mapping):
        return {
            str(key): canonicalize_api_accessible_dependency_graph_artifact_payload(
                payload=value,
                parent_key=str(key),
            )
            for key, value in sorted(payload.items(), key=lambda item: str(item[0]))
        }
    if isinstance(payload, list):
        entries = [
            canonicalize_api_accessible_dependency_graph_artifact_payload(
                payload=item,
                parent_key=None,
            )
            for item in payload
        ]
        if parent_key in API_ACCESSIBLE_DEPENDENCY_GRAPH_UNORDERED_LIST_FIELDS:
            return sorted(
                entries,
                key=_api_accessible_dependency_graph_artifact_sort_key,
            )
        return entries
    return payload


def _api_accessible_dependency_graph_artifact_sort_key(
    value: object,
) -> tuple[str, ...]:
    if isinstance(value, Mapping):
        stable_parts = [
            _api_accessible_dependency_graph_artifact_sort_value(value.get(key))
            for key in (
                "package",
                "namespace",
                "entity_kind",
                "symbol",
                "node_key",
                "relationship_key",
                "class_fqn",
                "name",
                "fqn_prefix",
                "attribute_config_id",
                "function_config_id",
                "class_config_relationship_id",
                "object_config_graph_node_id",
                "schema_id",
                "domain_id",
                "target_object_config_graph_id",
                "source_object_config_graph_id",
                "object_config_graph_id",
                "position",
                "role",
                "child_id",
                "attribute_type_descriptor_id",
                "id",
            )
            if value.get(key) is not None
        ]
        if stable_parts:
            return (
                *stable_parts,
                _api_accessible_dependency_graph_artifact_json_signature(value),
            )
    return (_api_accessible_dependency_graph_artifact_json_signature(value),)


def _api_accessible_dependency_graph_artifact_sort_value(value: object) -> str:
    if isinstance(value, str):
        return value.casefold()
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:020d}"
    return str(value)


def _api_accessible_dependency_graph_artifact_json_signature(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _validate_api_accessible_dependency_graph_namespace_evidence(
    *,
    payload: Mapping[str, object],
    source: str,
) -> None:
    if object_config_graph_payload_has_exported_namespace_evidence(payload):
        return
    graph_name = payload.get("name")
    graph_fqn_prefix = payload.get("fqn_prefix")
    raise RuntimeError(
        "API accessible dependency graph payload contains graph nodes without "
        "namespace evidence. Exported/runtime OCG payloads must carry "
        "namespace_membership derived from committed node FQN identity; "
        "retired topology fallback is not allowed. "
        f"source={source!r} graph={graph_name!r} fqn_prefix={graph_fqn_prefix!r}"
    )


def canonicalize_api_accessible_dependency_graphs(
    *,
    accessible_graphs: tuple[ObjectConfigGraph, ...],
) -> tuple[ObjectConfigGraph, ...]:
    """Round-trip accessible graphs through the portable API artifact payload."""

    from aware_meta.graph.config.model_bootstrap import (
        normalize_object_config_graph_payload_for_bootstrap,
    )

    return tuple(
        ObjectConfigGraph.model_validate(
            normalize_object_config_graph_payload_for_bootstrap(
                payload=dump_api_accessible_dependency_graph_artifact_payload(
                    graph=graph,
                )
            )
        )
        for graph in accessible_graphs
    )


def _json_safe_dependency_graph_payload(value: object) -> object:
    if isinstance(value, BaseModel):
        return _json_safe_dependency_graph_payload(
            value.model_dump(mode="python", exclude_none=True, by_alias=True)
        )
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe_dependency_graph_payload(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_json_safe_dependency_graph_payload(item) for item in value]
    if isinstance(value, list):
        return [_json_safe_dependency_graph_payload(item) for item in value]
    if isinstance(value, set):
        return [
            _json_safe_dependency_graph_payload(item)
            for item in sorted(value, key=repr)
        ]
    return value


def _api_runtime_package_dir(*, snapshot: APIWorkspaceSnapshot) -> Path:
    package_name = (snapshot.spec.api.package_name or "").strip()
    if not package_name:
        raise ValueError(
            "API package_name must be non-empty for runtime semantic artifact persistence"
        )
    return (snapshot.repo_root / ".aware" / "api" / "runtime" / package_name).resolve()


def _emit_api_accessible_dependency_graphs_artifact(
    *,
    accessible_graphs: tuple[ObjectConfigGraph, ...],
    runtime_package_dir: Path,
    dependency_packages: tuple[_RuntimeDependencyPackage, ...] = (),
    source_digest_package_names: Iterable[str] = (),
) -> Path:
    runtime_package_dir = runtime_package_dir.resolve()
    runtime_package_dir.mkdir(parents=True, exist_ok=True)
    dependency_source_digests = _api_dependency_source_digests_payload(
        dependency_packages=dependency_packages,
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
    artifact_path = (
        runtime_package_dir / API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME
    ).resolve()
    _write_json_artifact(path=artifact_path, payload=payload)
    return artifact_path


def _api_dependency_source_digests_payload(
    *,
    dependency_packages: tuple[_RuntimeDependencyPackage, ...],
    source_digest_package_names: Iterable[str],
) -> dict[str, str]:
    selected_package_names = {
        package_name.strip()
        for package_name in source_digest_package_names
        if package_name.strip()
    }
    if not selected_package_names:
        return {}
    package_by_name = {package.package_name: package for package in dependency_packages}
    return {
        package_name: _compute_runtime_dependency_source_digest(package=package)
        for package_name, package in sorted(package_by_name.items())
        if package_name in selected_package_names
    }


def _runtime_dependency_source_digest_package_names(
    *,
    dependency_packages: tuple[_RuntimeDependencyPackage, ...],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            package.package_name
            for package in dependency_packages
            if package.package_name.strip()
        )
    )


def _source_owned_api_dto_export_package_names(
    *,
    snapshot: APIWorkspaceSnapshot,
) -> tuple[str, ...]:
    package_names: list[str] = []
    for export in snapshot.spec.semantic_package_exports:
        export_kind = getattr(export, "kind", None)
        export_kind_value = getattr(export_kind, "value", export_kind)
        if export_kind_value != "api_dto":
            continue
        package_name = export.package_name.strip()
        if package_name:
            package_names.append(package_name)
    return tuple(dict.fromkeys(package_names))


def _emit_api_runtime_semantics_manifest(
    *,
    snapshot: APIWorkspaceSnapshot,
    runtime_package_dir: Path,
    accessible_dependency_graphs_path: Path,
    dependency_packages: tuple[_RuntimeDependencyPackage, ...],
    registered_class_config_count: int,
    output_path: Path | None = None,
) -> Path:
    runtime_package_dir = runtime_package_dir.resolve()
    repo_root = snapshot.repo_root.resolve()
    artifact_path = (
        output_path.expanduser().resolve()
        if output_path is not None
        else (runtime_package_dir / API_RUNTIME_SEMANTICS_FILENAME).resolve()
    )
    payload = {
        "schema_version": 1,
        "kind": "api.runtime_semantics",
        "api_package_name": snapshot.spec.api.package_name,
        "api_fqn_prefix": snapshot.spec.api.fqn_prefix,
        "api_toml_relpath": snapshot.spec_path.resolve()
        .relative_to(repo_root)
        .as_posix(),
        "api_package_root_relpath": snapshot.package_root.resolve()
        .relative_to(repo_root)
        .as_posix(),
        "accessible_dependency_graphs_relpath": (
            accessible_dependency_graphs_path.resolve()
            .relative_to(repo_root)
            .as_posix()
        ),
        "dependency_packages": [
            {
                "package_name": package.package_name,
                "kind": package.kind.value,
                "aware_toml_relpath": _path_rel_or_abs(
                    path=package.aware_toml_path,
                    root=repo_root,
                ),
                "package_root_relpath": _path_rel_or_abs(
                    path=package.package_root,
                    root=repo_root,
                ),
                "python_root_relpath": _path_rel_or_abs(
                    path=package.python_root, root=repo_root
                ),
                "runtime_root_relpath": _path_rel_or_abs(
                    path=package.runtime_root, root=repo_root
                ),
            }
            for package in dependency_packages
        ],
        "registered_class_config_count": registered_class_config_count,
    }
    _write_json_artifact(path=artifact_path, payload=payload)
    return artifact_path


def _register_api_dependency_class_configs(
    *,
    accessible_graphs: tuple[ObjectConfigGraph, ...],
    source: Path,
) -> int:
    from aware_utils.pydantic.class_config_registry import (
        register_class_configs_from_binding_snapshot_bytes,
    )

    registered_count = 0
    for graph in accessible_graphs:
        payload = dump_api_accessible_dependency_graph_artifact_payload(graph=graph)
        snapshot_bytes = cast(bytes, msgpack.packb(payload, use_bin_type=True))
        registered_count += register_class_configs_from_binding_snapshot_bytes(
            snapshot_bytes,
            source=f"{source.as_posix()}#{graph.name}",
        )
    return registered_count


def _write_json_artifact(*, path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_api_dependency_class_config_ids(
    *,
    snapshot: APIWorkspaceSnapshot,
    author_id: UUID | None = None,
    ensure_runtime_artifacts: bool = False,
    phase_timings_s: dict[str, float] | None = None,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> dict[str, UUID]:
    with _record_optional_phase(
        phase_timings_s,
        "load_api_dependency_class_config_ids.resolve_dependency_packages",
    ):
        packages = (
            ensure_api_dependency_runtime_artifacts(
                snapshot=snapshot,
                author_id=author_id,
                dependency_repo_roots=dependency_repo_roots,
            )
            if ensure_runtime_artifacts
            else _resolve_api_dependency_packages(
                snapshot=snapshot,
                dependency_repo_roots=dependency_repo_roots,
            )
        )
    class_config_id_by_ref: dict[str, UUID] = {}
    resolved_author_id = author_id or uuid4()
    authored_fallback_packages: list[_RuntimeDependencyPackage] = []

    for package in packages:
        if ensure_runtime_artifacts:
            with _record_optional_phase(
                phase_timings_s,
                f"load_api_dependency_class_config_ids.package:{package.package_name}.load_python_models_manifest",
            ):
                manifest = _load_dependency_python_models_manifest(
                    package=package,
                    repo_root=snapshot.repo_root,
                    author_id=resolved_author_id,
                    ensure_runtime_artifacts=True,
                )
            _merge_dependency_class_config_ids(
                target=class_config_id_by_ref, manifest=manifest
            )
            continue

        with _record_optional_phase(
            phase_timings_s,
            f"load_api_dependency_class_config_ids.package:{package.package_name}.load_existing_python_models_manifest",
        ):
            manifest = _load_existing_dependency_python_models_manifest(package=package)
        if manifest is None or not _models_manifest_has_authored_class_refs(
            manifest=manifest
        ):
            authored_fallback_packages.append(package)
            continue
        with _record_optional_phase(
            phase_timings_s,
            f"load_api_dependency_class_config_ids.package:{package.package_name}.merge_manifest_class_config_ids",
        ):
            _merge_dependency_class_config_ids(
                target=class_config_id_by_ref,
                manifest=manifest,
            )

    if authored_fallback_packages:
        with _record_optional_phase(
            phase_timings_s,
            "load_api_dependency_class_config_ids.load_authored_fallback",
        ):
            authored_class_config_ids = _load_dependency_authored_class_config_ids(
                packages=tuple(authored_fallback_packages),
                phase_timings_s=phase_timings_s,
            )
        for aware_class_ref, class_config_id in authored_class_config_ids.items():
            class_config_id_by_ref.setdefault(aware_class_ref, class_config_id)

    return class_config_id_by_ref


def collect_api_dependency_class_config_ids_from_graphs(
    *,
    accessible_graphs: tuple[ObjectConfigGraph, ...],
) -> dict[str, UUID]:
    class_config_id_by_ref: dict[str, UUID] = {}
    for graph in accessible_graphs:
        for node in graph.object_config_graph_nodes:
            class_config = node.class_config
            if class_config is None:
                continue
            aware_class_ref = _authored_class_ref_from_class_fqn(
                class_fqn=class_config.class_fqn
            )
            _merge_dependency_class_config_id(
                target=class_config_id_by_ref,
                aware_class_ref=aware_class_ref,
                class_config_id=class_config.id,
                source="Meta package OCG compile result",
            )
    return class_config_id_by_ref


def _merge_dependency_class_config_ids(
    *,
    target: dict[str, UUID],
    manifest: ModelsManifest,
) -> None:
    for entry in manifest.classes or []:
        aware_class_ref = (entry.aware_class_ref or "").strip()
        if not aware_class_ref:
            continue
        _merge_dependency_class_config_id(
            target=target,
            aware_class_ref=aware_class_ref,
            class_config_id=entry.class_config_id,
            source="python.models.json",
        )
        authored_alias = _authored_class_ref_from_class_fqn(class_fqn=aware_class_ref)
        if authored_alias != aware_class_ref:
            _merge_dependency_class_config_id(
                target=target,
                aware_class_ref=authored_alias,
                class_config_id=entry.class_config_id,
                source="python.models.json authored alias",
            )


def _merge_dependency_class_config_id(
    *,
    target: dict[str, UUID],
    aware_class_ref: str,
    class_config_id: UUID,
    source: str,
) -> None:
    existing = target.get(aware_class_ref)
    if existing is not None and existing != class_config_id:
        raise RuntimeError(
            "Ambiguous API dependency authored class ref in "
            + source
            + f" (aware_class_ref={aware_class_ref!r}, existing={existing}, incoming={class_config_id})"
        )
    target[aware_class_ref] = class_config_id


def _load_existing_dependency_python_models_manifest(
    *,
    package: _RuntimeDependencyPackage,
) -> ModelsManifest | None:
    if not package.python_models_path.is_file():
        return None
    return ModelsManifest.model_validate_json(
        package.python_models_path.read_text(encoding="utf-8")
    )


def _load_dependency_authored_class_config_ids(
    *,
    packages: tuple[_RuntimeDependencyPackage, ...],
    phase_timings_s: dict[str, float] | None = None,
) -> dict[str, UUID]:
    graphs_by_package_name: dict[str, ObjectConfigGraph] = {}
    class_config_id_by_ref: dict[str, UUID] = {}

    for package in packages:
        with _record_optional_phase(
            phase_timings_s,
            f"load_api_dependency_class_config_ids.package:{package.package_name}.build_authored_object_config_graph",
        ):
            graph = _load_required_dependency_object_config_graph(package=package)
        graphs_by_package_name[package.package_name] = graph

        for node in graph.object_config_graph_nodes:
            class_config = node.class_config
            if class_config is None:
                continue
            aware_class_ref = _authored_class_ref_from_class_fqn(
                class_fqn=class_config.class_fqn
            )
            existing = class_config_id_by_ref.get(aware_class_ref)
            if existing is not None and existing != class_config.id:
                raise RuntimeError(
                    "Ambiguous API dependency authored class ref in authored graph fallback "
                    + f"(aware_class_ref={aware_class_ref!r}, existing={existing}, incoming={class_config.id})"
                )
            class_config_id_by_ref[aware_class_ref] = class_config.id

    return class_config_id_by_ref


def _load_required_dependency_object_config_graph(
    *,
    package: _RuntimeDependencyPackage,
) -> ObjectConfigGraph:
    graph = _load_existing_dependency_object_config_graph(package=package)
    if graph is not None:
        return graph
    raise RuntimeError(
        "API dependency ObjectConfigGraph runtime artifact is missing or stale "
        "and source-local Structure repository fallback is retired. Materialize "
        "the dependency package so its ontology runtime manifest and OCG snapshot "
        "are available before resolving API runtime dependencies "
        + f"(package={package.package_name!r}, manifest={package.runtime_manifest_path})"
    )


def _load_existing_dependency_object_config_graph(
    *,
    package: _RuntimeDependencyPackage,
) -> ObjectConfigGraph | None:
    if package.kind == AwarePackageKind.api:
        return _load_api_dependency_object_config_graph_from_models(package=package)
    if not package.runtime_manifest_path.is_file():
        return None

    expected_source_digest = _compute_runtime_dependency_source_digest(package=package)
    if not (
        _runtime_dependency_source_digest_matches(
            package=package,
            expected_digest=expected_source_digest,
        )
        or _runtime_dependency_ocg_outputs_are_fresh_for_inputs(package=package)
    ):
        return None

    try:
        return _load_runtime_dependency_object_config_graph_snapshot(package=package)
    except Exception:
        return None


def _load_api_dependency_object_config_graph_from_models(
    *,
    package: _RuntimeDependencyPackage,
) -> ObjectConfigGraph | None:
    manifest = _load_existing_dependency_python_models_manifest(package=package)
    if manifest is None or not _models_manifest_has_authored_class_refs(
        manifest=manifest
    ):
        return None
    graph_seed = "|".join(
        [
            package.package_name,
            package.spec.package.fqn_prefix or "",
            *[
                entry.aware_class_ref.strip()
                for entry in manifest.classes or ()
                if (entry.aware_class_ref or "").strip()
            ],
        ]
    )
    graph_id = uuid5(NAMESPACE_URL, f"aware-api-dependency-graph:{graph_seed}")
    nodes = [
        _api_dependency_object_config_graph_node(
            graph_id=graph_id,
            entry=entry,
        )
        for entry in manifest.classes or ()
        if (entry.aware_class_ref or "").strip()
    ]
    return ObjectConfigGraph.model_construct(
        id=graph_id,
        name=package.package_name,
        fqn_prefix=package.spec.package.fqn_prefix or package.import_root,
        hash=hashlib.sha256(graph_seed.encode("utf-8")).hexdigest(),
        language=CodeLanguage.aware,
        object_config_graph_nodes=nodes,
    )


def _api_dependency_object_config_graph_node(
    *,
    graph_id: UUID,
    entry: ClassModelEntry,
) -> ObjectConfigGraphNode:
    class_ref = entry.aware_class_ref.strip()
    class_config = ClassConfig.model_construct(
        id=entry.class_config_id,
        class_fqn=class_ref,
        name=entry.name or class_ref.rsplit(".", 1)[-1],
        is_base=True,
        class_config_attribute_configs=[],
        class_config_function_configs=[],
        class_config_relationships=[],
    )
    node_id = uuid5(
        NAMESPACE_URL,
        f"aware-api-dependency-node:{graph_id}:{entry.class_config_id}:{class_ref}",
    )
    node = ObjectConfigGraphNode.model_construct(
        id=node_id,
        type=ObjectConfigGraphNodeType.class_,
        node_key=class_ref,
        object_config_graph_id=graph_id,
        class_config=class_config,
        layouts=[],
    )
    relative_path = _api_dependency_layout_path_from_model_module(
        import_root=_authored_class_ref_from_class_fqn(class_fqn=class_ref).split(
            ".", 1
        )[0],
        module=entry.module,
    )
    if relative_path is not None:
        node.layouts.append(
            ObjectConfigGraphNodeLayout(
                object_config_graph_node_id=node.id,
                layout_kind="python",
                relative_path=relative_path,
                source_position=0,
            )
        )
    class_config.object_config_graph_node_id = node.id
    return node


def _api_dependency_layout_path_from_model_module(
    *,
    import_root: str,
    module: str | None,
) -> str | None:
    module_value = (module or "").strip()
    if not module_value:
        return None
    prefix = f"{import_root}."
    if module_value.startswith(prefix):
        module_value = module_value[len(prefix) :]
    return module_value.replace(".", "/") + ".py"


def _load_runtime_dependency_object_config_graph_snapshot(
    *,
    package: _RuntimeDependencyPackage,
) -> ObjectConfigGraph | None:
    output_paths = _runtime_dependency_ocg_output_paths(package=package)
    if len(output_paths) < 2:
        return None
    snapshot_path = output_paths[1]
    if not snapshot_path.is_file():
        return None
    payload = msgpack.unpackb(snapshot_path.read_bytes(), raw=False)
    if not isinstance(payload, Mapping):
        raise RuntimeError(
            "API runtime dependency OCG snapshot must contain a mapping payload "
            + f"(package={package.package_name!r}, snapshot={snapshot_path})"
        )
    return ObjectConfigGraph.model_validate(payload)


def _ensure_dependency_object_projection_graphs(
    *,
    package: _RuntimeDependencyPackage,
    graph: ObjectConfigGraph,
    graphs_by_package_name: dict[str, ObjectConfigGraph],
) -> ObjectConfigGraph:
    if graph.object_projection_graphs or not graph.object_projection_graph_declarations:
        return graph
    external_graphs = [
        graphs_by_package_name[dependency.package_name]
        for dependency in package.spec.dependencies
        if dependency.package_name in graphs_by_package_name
    ]
    graph.object_projection_graphs = build_object_projection_graphs(
        graph,
        external_graphs=external_graphs,
        provision_portals=False,
    )
    return graph


def _authored_class_ref_from_class_fqn(*, class_fqn: str) -> str:
    parts = [part.strip() for part in class_fqn.split(".") if part.strip()]
    if len(parts) <= 2:
        return class_fqn.strip()
    return ".".join(
        [
            parts[0],
            *[part for part in parts[1:-1] if part.casefold() != "default"],
            parts[-1],
        ]
    )


def _load_dependency_python_models_manifest(
    *,
    package: _RuntimeDependencyPackage,
    repo_root: Path,
    author_id: UUID,
    ensure_runtime_artifacts: bool,
) -> ModelsManifest:
    should_build = ensure_runtime_artifacts or not package.python_models_path.is_file()
    manifest: ModelsManifest | None = None
    if not should_build:
        manifest = ModelsManifest.model_validate_json(
            package.python_models_path.read_text(encoding="utf-8")
        )
        if not _models_manifest_has_authored_class_refs(manifest=manifest):
            should_build = True

    if should_build:
        _build_runtime_dependency_package(
            package=package,
            repo_root=repo_root,
            author_id=author_id,
        )
        if not package.python_models_path.is_file():
            raise FileNotFoundError(
                "API runtime dependency build did not emit python.models.json for "
                + f"{package.package_name!r}: {package.python_models_path}"
            )
        manifest = ModelsManifest.model_validate_json(
            package.python_models_path.read_text(encoding="utf-8")
        )
        _write_runtime_dependency_source_digest(
            package=package,
            source_digest=_compute_runtime_dependency_source_digest(package=package),
        )

    if manifest is None:
        raise RuntimeError(
            "API runtime dependency metadata could not be loaded for "
            + f"{package.package_name!r}: {package.python_models_path}"
        )
    return manifest


def load_api_dependency_binding_truths(
    *,
    snapshot: APIWorkspaceSnapshot,
    phase_timings_s: dict[str, float] | None = None,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> dict[tuple[str, str], BindingMapTruth]:
    with _record_optional_phase(
        phase_timings_s,
        "load_api_dependency_binding_truths.resolve_dependency_packages",
    ):
        packages = _resolve_api_dependency_packages(
            snapshot=snapshot,
            dependency_repo_roots=dependency_repo_roots,
        )
    with _record_optional_phase(
        phase_timings_s,
        "load_api_dependency_binding_truths.parser_init",
    ):
        parser = Parser(language=AWARE_LANGUAGE)
    truths: dict[tuple[str, str], BindingMapTruth] = {}

    for package in packages:
        if package.kind != AwarePackageKind.api:
            continue
        with _record_optional_phase(
            phase_timings_s,
            f"load_api_dependency_binding_truths.package:{package.package_name}.scan_sources",
        ):
            sources_root = (package.package_root / "aware").resolve()
            if not sources_root.is_dir():
                continue
            source_paths = tuple(
                source_path
                for source_path in sorted(sources_root.rglob("*.aware"))
                if source_path.is_file()
            )
        with _record_optional_phase(
            phase_timings_s,
            f"load_api_dependency_binding_truths.package:{package.package_name}.parse_sources",
        ):
            for source_path in source_paths:
                source_text = source_path.read_text(encoding="utf-8")
                tree = parser.parse(source_text.encode("utf-8"))
                source_rel = source_path.relative_to(package.package_root).as_posix()

                for binding_node in tree.root_node.named_children:
                    if binding_node.type != "binding_def":
                        continue
                    source_graph = _node_text(
                        source_text=source_text,
                        node=binding_node.child_by_field_name("source_graph"),
                    )
                    target_graph = _node_text(
                        source_text=source_text,
                        node=binding_node.child_by_field_name("target_graph"),
                    )
                    if not source_graph or not target_graph:
                        continue

                    for map_node in binding_node.named_children:
                        if map_node.type != "binding_map_def":
                            continue
                        map_name = _node_text(
                            source_text=source_text,
                            node=map_node.child_by_field_name("name"),
                        )
                        source_ref = _node_text(
                            source_text=source_text,
                            node=map_node.child_by_field_name("source"),
                        )
                        target_ref = _node_text(
                            source_text=source_text,
                            node=map_node.child_by_field_name("target"),
                        )
                        if not map_name or not source_ref or not target_ref:
                            continue
                        source_class_ref = _qualify_binding_source_class_ref(
                            source_graph=source_graph,
                            source_ref=source_ref,
                        )
                        target_class, target_attribute = _split_binding_target_ref(
                            target_ref=target_ref
                        )
                        binding_ref = f"{source_graph}.{map_name}"
                        truth = BindingMapTruth(
                            binding_ref=binding_ref,
                            source_graph=source_graph,
                            target_graph=target_graph,
                            source_class_ref=source_class_ref,
                            target_class=target_class,
                            target_attribute=target_attribute,
                            source_path=source_rel,
                        )
                        key = (binding_ref.casefold(), target_graph.casefold())
                        existing = truths.get(key)
                        if existing is not None and existing != truth:
                            raise RuntimeError(
                                "Ambiguous API dependency binding truth "
                                + (
                                    f"(binding_ref={binding_ref!r}, target_graph={target_graph!r}, "
                                    f"existing={existing.source_path!r}, incoming={source_rel!r})"
                                )
                            )
                        truths[key] = truth

    return truths


def _models_manifest_has_authored_class_refs(*, manifest: ModelsManifest) -> bool:
    classes = manifest.classes or []
    if not classes:
        return True
    return all((entry.aware_class_ref or "").strip() for entry in classes)


def _resolve_api_dependency_packages(
    *,
    snapshot: APIWorkspaceSnapshot,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[_RuntimeDependencyPackage, ...]:
    cache: dict[str, _RuntimeDependencyPackage] = {}
    ordered: list[_RuntimeDependencyPackage] = []
    package_index = _build_aware_toml_package_index(
        repo_root=snapshot.repo_root,
        dependency_repo_roots=dependency_repo_roots,
    )
    package_names = _api_runtime_dependency_package_names(
        snapshot=snapshot,
        package_index=package_index,
    )
    for package_name in package_names:
        _collect_runtime_dependency_packages(
            package_name=package_name,
            repo_root=snapshot.repo_root,
            package_index=package_index,
            cache=cache,
            ordered=ordered,
            stack=(),
        )
    return tuple(ordered)


def _api_runtime_dependency_package_names(
    *,
    snapshot: APIWorkspaceSnapshot,
    package_index: Mapping[str, Path],
) -> tuple[str, ...]:
    declared_package_names = tuple(
        dependency.package_name
        for dependency in sorted(
            snapshot.spec.dependencies,
            key=lambda item: item.package_name.casefold(),
        )
        if dependency.package_name.strip()
    )
    graph_target_package_names = _api_graph_target_dependency_package_names(
        graph_targets=load_api_graph_targets_from_sources(
            package_root=snapshot.package_root,
            source_files=snapshot.source_files,
        ),
        package_index=package_index,
    )
    api_dto_export_package_names = tuple(
        export.package_name.strip()
        for export in snapshot.spec.semantic_package_exports
        if getattr(
            getattr(export, "kind", None), "value", getattr(export, "kind", None)
        )
        == "api_dto"
        and export.package_name.strip()
    )
    return tuple(
        dict.fromkeys(
            sorted(
                (
                    *declared_package_names,
                    *graph_target_package_names,
                    *api_dto_export_package_names,
                ),
                key=str.casefold,
            )
        )
    )


def _api_graph_target_dependency_package_names(
    *,
    graph_targets: tuple[str, ...],
    package_index: Mapping[str, Path],
) -> tuple[str, ...]:
    if not graph_targets:
        return ()

    package_name_by_fqn_prefix = _aware_toml_package_names_by_fqn_prefix(
        package_index=package_index,
    )
    package_names: list[str] = []
    missing_targets: list[str] = []
    for graph_target in sorted(set(graph_targets), key=str.casefold):
        package_name = package_name_by_fqn_prefix.get(graph_target.casefold())
        if package_name is None and graph_target in package_index:
            package_name = graph_target
        if package_name is None:
            missing_targets.append(graph_target)
            continue
        package_names.append(package_name)
    if missing_targets:
        raise FileNotFoundError(
            "Unable to resolve API graph target package(s) from aware.toml "
            "fqn_prefix/package_name metadata: "
            + ", ".join(sorted(missing_targets, key=str.casefold))
        )
    return tuple(package_names)


def _aware_toml_package_names_by_fqn_prefix(
    *,
    package_index: Mapping[str, Path],
) -> dict[str, str]:
    package_name_by_fqn_prefix: dict[str, str] = {}
    for package_name, aware_toml_path in sorted(
        package_index.items(),
        key=lambda item: item[0].casefold(),
    ):
        try:
            spec = load_aware_toml_spec(toml_path=aware_toml_path)
        except Exception:
            continue
        fqn_prefix = (spec.package.fqn_prefix or "").strip()
        resolved_package_name = (spec.package.package_name or package_name).strip()
        if fqn_prefix and resolved_package_name:
            package_name_by_fqn_prefix.setdefault(
                fqn_prefix.casefold(),
                resolved_package_name,
            )
    return package_name_by_fqn_prefix


def _collect_runtime_dependency_packages(
    *,
    package_name: str,
    repo_root: Path,
    package_index: Mapping[str, Path],
    cache: dict[str, _RuntimeDependencyPackage],
    ordered: list[_RuntimeDependencyPackage],
    stack: tuple[str, ...],
) -> _RuntimeDependencyPackage:
    existing = cache.get(package_name)
    if existing is not None:
        return existing
    if package_name in stack:
        cycle = " -> ".join([*stack, package_name])
        raise ValueError(f"Cyclic API runtime dependency closure: {cycle}")

    aware_toml_path = _resolve_aware_toml_path_by_package_name(
        package_name=package_name,
        repo_root=repo_root,
        package_index=package_index,
    )
    spec = load_aware_toml_spec(toml_path=aware_toml_path)
    package = _RuntimeDependencyPackage(
        package_name=spec.package.package_name,
        aware_toml_path=aware_toml_path.resolve(),
        package_root=aware_toml_path.parent.resolve(),
        spec=spec,
    )
    if package.kind not in (AwarePackageKind.api, AwarePackageKind.ontology):
        raise ValueError(
            "API runtime dependency closure only supports api/ontology packages, got "
            + f"{package.kind.value!r} for {package.package_name!r}"
        )

    cache[package_name] = package
    for dependency in sorted(
        spec.dependencies, key=lambda item: item.package_name.casefold()
    ):
        _collect_runtime_dependency_packages(
            package_name=dependency.package_name,
            repo_root=repo_root,
            package_index=package_index,
            cache=cache,
            ordered=ordered,
            stack=(*stack, package_name),
        )
    ordered.append(package)
    return package


def _node_text(*, source_text: str, node: object | None) -> str:
    if node is None:
        return ""
    start_byte = getattr(node, "start_byte", None)
    end_byte = getattr(node, "end_byte", None)
    if not isinstance(start_byte, int) or not isinstance(end_byte, int):
        return ""
    return source_text.encode("utf-8")[start_byte:end_byte].decode("utf-8").strip()


def _qualify_binding_source_class_ref(*, source_graph: str, source_ref: str) -> str:
    raw = (source_ref or "").strip()
    parts = [part for part in raw.split(".") if part]
    if len(parts) < 2:
        raise ValueError(
            f"Binding map source class must be at least schema.Class, got {source_ref!r}"
        )
    if len(parts) >= 3:
        return raw
    return f"{source_graph}.{raw}"


def _split_binding_target_ref(*, target_ref: str) -> tuple[str, str]:
    raw = (target_ref or "").strip()
    parts = [part for part in raw.split(".") if part]
    if len(parts) < 3:
        raise ValueError(
            f"Binding map target must be at least schema.Class.attr, got {target_ref!r}"
        )
    return parts[-2], parts[-1]


def _build_runtime_dependency_package(
    *,
    package: _RuntimeDependencyPackage,
    repo_root: Path,
    author_id: UUID,
) -> None:
    del repo_root, author_id
    raise RuntimeError(
        "API runtime dependency artifacts are not built by aware_api_runtime. "
        "Materialize dependency packages upstream through WorkspaceRevision/Structure/Meta "
        "before resolving API runtime manifests. "
        f"package={package.package_name!r} "
        f"expected_runtime_manifest={package.runtime_manifest_path} "
        f"expected_python_models={package.python_models_path}"
    )


def _compute_runtime_dependency_source_digest(
    *,
    package: _RuntimeDependencyPackage,
) -> str:
    digest = hashlib.sha256()
    for path in sorted(
        _iter_runtime_dependency_source_input_paths(package=package),
        key=lambda item: _runtime_dependency_digest_token(package=package, path=item),
    ):
        digest.update(
            _runtime_dependency_digest_token(package=package, path=path).encode("utf-8")
        )
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def compute_api_dependency_source_digest_for_aware_toml(
    *,
    aware_toml_path: str | Path,
) -> str:
    resolved_path = Path(aware_toml_path).expanduser().resolve()
    spec = load_aware_toml_spec(toml_path=resolved_path)
    package_name = spec.package.package_name.strip()
    package = _RuntimeDependencyPackage(
        package_name=package_name,
        aware_toml_path=resolved_path,
        package_root=resolved_path.parent,
        spec=spec,
    )
    return _compute_runtime_dependency_source_digest(package=package)


def _runtime_dependency_source_digest_matches(
    *,
    package: _RuntimeDependencyPackage,
    expected_digest: str,
) -> bool:
    if not package.runtime_source_digest_path.is_file():
        return False
    recorded = package.runtime_source_digest_path.read_text(encoding="utf-8").strip()
    return bool(recorded) and recorded == expected_digest


def _runtime_dependency_outputs_are_fresh_for_inputs(
    *,
    package: _RuntimeDependencyPackage,
) -> bool:
    outputs = [package.runtime_manifest_path, package.python_models_path]
    if any(not path.is_file() for path in outputs):
        return False
    oldest_output_mtime_ns = min(path.stat().st_mtime_ns for path in outputs)
    return oldest_output_mtime_ns >= _runtime_dependency_latest_input_mtime_ns(
        package=package
    )


def _runtime_dependency_ocg_outputs_are_fresh_for_inputs(
    *,
    package: _RuntimeDependencyPackage,
) -> bool:
    outputs = _runtime_dependency_ocg_output_paths(package=package)
    if not outputs or any(not path.is_file() for path in outputs):
        return False
    oldest_output_mtime_ns = min(path.stat().st_mtime_ns for path in outputs)
    return oldest_output_mtime_ns >= _runtime_dependency_latest_input_mtime_ns(
        package=package
    )


def _runtime_dependency_ocg_output_paths(
    *,
    package: _RuntimeDependencyPackage,
) -> tuple[Path, ...]:
    if not package.runtime_manifest_path.is_file():
        return ()
    runtime_root = package.runtime_manifest_path.parent
    snapshot_path = runtime_root / "ocg.snapshot.msgpack"
    try:
        payload = json.loads(package.runtime_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return (package.runtime_manifest_path, snapshot_path.resolve())
    if isinstance(payload, Mapping):
        ocg_payload = payload.get("ocg")
        if isinstance(ocg_payload, Mapping):
            raw_snapshot = ocg_payload.get("snapshot")
            if isinstance(raw_snapshot, str) and raw_snapshot.strip():
                candidate = Path(raw_snapshot)
                snapshot_path = (
                    candidate if candidate.is_absolute() else runtime_root / candidate
                )
    return (package.runtime_manifest_path, snapshot_path.resolve())


def _runtime_dependency_latest_input_mtime_ns(
    *,
    package: _RuntimeDependencyPackage,
) -> int:
    return max(
        path.stat().st_mtime_ns
        for path in _iter_runtime_dependency_source_input_paths(package=package)
    )


def _iter_runtime_dependency_source_input_paths(
    *,
    package: _RuntimeDependencyPackage,
) -> tuple[Path, ...]:
    inputs: list[Path] = [package.aware_toml_path.resolve()]
    stable_ids_path = (package.package_root / "stable_ids.toml").resolve()
    if stable_ids_path.is_file():
        inputs.append(stable_ids_path)
    authored_root = (package.package_root / "aware").resolve()
    if authored_root.is_dir():
        for path in sorted(authored_root.rglob("*")):
            if not path.is_file():
                continue
            relative_parts = path.relative_to(authored_root).parts
            if ".aware" in relative_parts:
                continue
            inputs.append(path.resolve())
    return tuple(inputs)


def _write_runtime_dependency_source_digest(
    *,
    package: _RuntimeDependencyPackage,
    source_digest: str,
) -> None:
    package.runtime_source_digest_path.parent.mkdir(parents=True, exist_ok=True)
    package.runtime_source_digest_path.write_text(
        f"{source_digest}\n", encoding="utf-8"
    )


def _resolve_aware_toml_path_by_package_name(
    *,
    package_name: str,
    repo_root: Path,
    package_index: Mapping[str, Path] | None = None,
) -> Path:
    resolved_repo_root = repo_root.resolve()
    index = (
        package_index
        if package_index is not None
        else _build_aware_toml_package_index(repo_root=resolved_repo_root)
    )
    aware_toml_path = index.get(package_name)
    if aware_toml_path is not None:
        return aware_toml_path.resolve()
    raise FileNotFoundError(
        f"Unable to resolve aware.toml for package_name={package_name!r} "
        f"under repo_root={resolved_repo_root}"
    )


def _build_aware_toml_package_index(
    *,
    repo_root: Path,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> dict[str, Path]:
    candidates: dict[str, tuple[tuple[int, int, str], Path]] = {}
    for root_order, lookup_root in enumerate(
        _candidate_package_lookup_roots(
            primary_repo_root=repo_root,
            dependency_repo_roots=dependency_repo_roots,
        )
    ):
        module_declared_paths = _module_declared_aware_toml_paths(repo_root=lookup_root)
        for aware_toml_path in sorted(
            _iter_authored_aware_toml_paths(repo_root=lookup_root)
        ):
            try:
                spec = load_aware_toml_spec(toml_path=aware_toml_path)
            except Exception:
                continue
            resolved_package_name = (spec.package.package_name or "").strip()
            if not resolved_package_name:
                continue
            resolved_aware_toml_path = aware_toml_path.resolve()
            candidate_key = (
                root_order,
                _aware_toml_package_discovery_priority(
                    aware_toml_path=resolved_aware_toml_path,
                    repo_root=lookup_root,
                    module_declared_paths=module_declared_paths,
                ),
                _path_token(path=resolved_aware_toml_path, repo_root=lookup_root),
            )
            existing = candidates.get(resolved_package_name)
            if existing is None or candidate_key < existing[0]:
                candidates[resolved_package_name] = (
                    candidate_key,
                    resolved_aware_toml_path,
                )
    return {
        package_name: aware_toml_path
        for package_name, (_, aware_toml_path) in candidates.items()
    }


def _module_declared_aware_toml_paths(*, repo_root: Path) -> frozenset[Path]:
    modules_root = repo_root.resolve() / "modules"
    if not modules_root.is_dir():
        return frozenset()
    declared_paths: set[Path] = set()
    for module_toml_path in sorted(modules_root.glob("*/aware.module.toml")):
        try:
            payload = tomllib.loads(module_toml_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        packages = payload.get("packages")
        if not isinstance(packages, list):
            continue
        for package_payload in packages:
            if not isinstance(package_payload, dict):
                continue
            manifest = package_payload.get("manifest")
            if not isinstance(manifest, str):
                continue
            manifest = manifest.strip()
            if not manifest:
                continue
            aware_toml_path = (module_toml_path.parent / manifest).resolve()
            if aware_toml_path.name == "aware.toml" and aware_toml_path.is_file():
                declared_paths.add(aware_toml_path)
    return frozenset(declared_paths)


def _aware_toml_package_discovery_priority(
    *,
    aware_toml_path: Path,
    repo_root: Path,
    module_declared_paths: frozenset[Path],
) -> int:
    resolved_path = aware_toml_path.resolve()
    if resolved_path in module_declared_paths:
        return 0
    try:
        relative_parts = resolved_path.relative_to(repo_root.resolve()).parts
    except ValueError:
        relative_parts = resolved_path.parts
    if relative_parts[:1] == ("modules",):
        return 10
    if "docs" in relative_parts and "proofs" in relative_parts:
        return 50
    return 20


def _candidate_package_lookup_roots(
    *,
    primary_repo_root: Path,
    dependency_repo_roots: Iterable[str | Path] = (),
) -> tuple[Path, ...]:
    roots: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        resolved = path.expanduser().resolve()
        if resolved in seen:
            return
        if not resolved.exists() or not resolved.is_dir():
            return
        roots.append(resolved)
        seen.add(resolved)

    add(primary_repo_root)
    for root in dependency_repo_roots:
        add(Path(root))
    for key in ("AWARE_KERNEL_REPO_ROOT", "AWARE_REPOSITORY_ROOT"):
        raw = (os.getenv(key) or "").strip()
        if raw:
            add(Path(raw))
    return tuple(roots)


def _iter_authored_aware_toml_paths(*, repo_root: Path) -> Iterator[Path]:
    resolved_repo_root = repo_root.resolve()
    for current_root, dir_names, file_names in os.walk(resolved_repo_root):
        dir_names[:] = sorted(
            name
            for name in dir_names
            if name not in _AWARE_TOML_PACKAGE_DISCOVERY_PRUNED_DIR_NAMES
        )
        if "aware.toml" in file_names:
            yield (Path(current_root) / "aware.toml").resolve()


def _api_runtime_environment_handle(*, snapshot: APIWorkspaceSnapshot) -> str:
    package_name = (snapshot.spec.api.package_name or "api").strip() or "api"
    return f"{package_name}-runtime"


def _path_token(*, path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return resolved.as_posix()


def _path_rel_or_abs(*, path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    ordered: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        ordered.append(resolved)
    return ordered


def _resolve_runtime_dependency_handler_modules(
    *,
    package: _RuntimeDependencyPackage,
) -> tuple[str, ...]:
    if package.kind != AwarePackageKind.ontology:
        return ()
    import_root = (
        (package.spec.package.fqn_prefix or package.spec.package.package_name)
        .strip()
        .replace("-", "_")
    )
    if not import_root:
        return ()
    handlers_path = (
        package.runtime_root / import_root / "handlers" / "_generated" / "handlers.py"
    )
    if not handlers_path.is_file():
        return ()
    return (f"{import_root}.handlers._generated.handlers",)


def _runtime_dependency_digest_token(
    *,
    package: _RuntimeDependencyPackage,
    path: Path,
) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(package.module_root).as_posix()
    except ValueError:
        return resolved.relative_to(package.package_root).as_posix()


__all__ = [
    "APIRuntimeSemanticArtifacts",
    "API_ACCESSIBLE_DEPENDENCY_GRAPHS_FILENAME",
    "API_RUNTIME_SEMANTICS_FILENAME",
    "canonicalize_api_accessible_dependency_graphs",
    "collect_api_dependency_class_config_ids_from_graphs",
    "compute_api_dependency_source_digest_for_aware_toml",
    "dump_api_accessible_dependency_graph_artifact_payload",
    "ensure_api_dependency_runtime_artifacts",
    "load_api_accessible_dependency_graphs",
    "load_api_accessible_dependency_graph_source_digests",
    "load_api_accessible_dependency_graphs_from_runtime_artifact",
    "load_api_dependency_class_config_ids",
    "resolve_api_runtime_semantic_artifacts",
    "resolve_api_dependency_runtime_manifest_paths",
    "resolve_api_workspace_runtime_manifest",
]
