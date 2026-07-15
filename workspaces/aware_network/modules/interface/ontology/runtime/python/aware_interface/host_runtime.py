from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
import tomllib
from uuid import UUID

from aware_interface.manifest import load_aware_interface_toml_spec
from aware_interface.commit_materialization import InterfaceCommitMaterializer
from aware_interface.config_bundle_projection import (
    project_interface_config_bundle_from_committed_package,
)
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)
from aware_interface.lane_stores import InterfaceLaneStores
from aware_interface.lane_sync import InterfaceLaneSyncService
from aware_interface.lifecycle.models import InterfaceBackendState
from aware_interface.lifecycle import InterfaceRuntimePaneRenderSpecState
from aware_interface.local_db import InterfaceLocalDb, InterfaceLocalDbConfig
from aware_interface.ontology.materialization import (
    load_pane_render_spec_runtime_states_from_materialization_artifact_oig,
)
from aware_interface.package_ref_resolution import (
    InterfaceRuntimePackageRef,
    resolve_committed_interface_runtime_package_ref,
)
from aware_interface.projection_runtime import (
    InterfaceProjectionPlanBundle,
    InterfaceProjectionRuntime,
)
from aware_interface.runtime_artifact_refs import (
    InterfaceRuntimeArtifactRef,
    build_ontology_runtime_artifact_catalog,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta.runtime import (
    MetaGraphRuntimeIndexSnapshot,
)

if TYPE_CHECKING:
    from aware_interface.lifecycle.coordinator import InterfaceRuntimeCoordinator
    from aware_interface.ports.actions import InterfaceActionPort
    from aware_interface.ports.experience import InterfaceExperiencePort
    from aware_interface.ports.gates import InterfaceGatePort
    from aware_interface.ports.session import InterfaceSessionPort
    from aware_interface.ports.navigation_context_layout import (
        InterfaceNavigationContextLayoutPort,
    )

_DB_SCHEMA_REGISTRY_FILENAME = "db.schema.registry.json"
_INTERFACE_CONFIG_BUNDLE_FILENAME = "interface.config.bundle.json"
_PANE_RENDER_SPECS_MATERIALIZATION_FILENAME = "pane_render_specs.materialization.json"
_INTERFACE_DB_FILENAME = "interface.sqlite"
_INTERFACE_CONFIG_BUNDLE_SOURCE_COMMITTED_PACKAGE = "committed_interface_package"
_INTERFACE_CONFIG_BUNDLE_SOURCE_RUNTIME_ARTIFACT = "runtime_artifact"
_INTERFACE_CONFIG_BUNDLE_SOURCE_WORKSPACE_ARTIFACT = "workspace_interface_artifact"
_RETIRED_ENVIRONMENT_RUNTIME_BOOT_MESSAGE = (
    "Interface Environment runtime manifest boot is retired. Boot Interface "
    "runtime from ontology runtime artifact-set refs produced by Workspace "
    "materialize or a WorkspaceDeployment payload."
)


@dataclass(frozen=True, slots=True)
class InterfaceConfigBundleLoadResult:
    bundle: InterfaceConfigBundle | None
    source: str | None = None
    path: Path | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostRuntime:
    repository_root: Path
    manifest_path: Path | None
    registry_path: Path
    database_path: Path
    environment_id: UUID
    interface_config_bundle: InterfaceConfigBundle | None
    interface_config_bundle_source: str | None
    interface_config_bundle_path: Path | None
    db: InterfaceLocalDb
    stores: InterfaceLaneStores
    materializer: InterfaceCommitMaterializer
    projector: InterfaceProjectionRuntime
    projection_bundle: InterfaceProjectionPlanBundle | None
    opg_count: int
    runtime_index: MetaGraphRuntimeIndexSnapshot | None = None
    runtime_artifact_refs: tuple[InterfaceRuntimeArtifactRef, ...] = ()
    runtime_artifact_set_count: int = 0

    @classmethod
    def from_runtime_artifact_refs(
        cls,
        *,
        repository_root: Path,
        state_home: Path,
        namespace: str,
        environment_id: UUID | str,
        runtime_artifact_refs: tuple[InterfaceRuntimeArtifactRef, ...],
        db_schema_registry_path: str | Path,
        database_filename: str = _INTERFACE_DB_FILENAME,
        committed_interface_config_bundle: InterfaceConfigBundle | None = None,
        allow_local_interface_config_bundle_fallback: bool = True,
        local_interface_package_name: str | None = None,
    ) -> "InterfaceHostRuntime":
        catalog = build_ontology_runtime_artifact_catalog(
            artifact_refs=runtime_artifact_refs,
        )
        resolved_environment_id = UUID(str(environment_id))
        registry_path = Path(db_schema_registry_path).expanduser().resolve()
        if not registry_path.is_file():
            raise RuntimeError(
                "Missing Interface service local-state DB schema registry: "
                f"{registry_path}"
            )
        interface_config_bundle_result = resolve_interface_config_bundle(
            manifest_path=None,
            repository_root=repository_root,
            committed_interface_config_bundle=committed_interface_config_bundle,
            allow_local_artifact_fallback=allow_local_interface_config_bundle_fallback,
            local_interface_package_name=local_interface_package_name,
        )
        database_path = (state_home / namespace / database_filename).resolve()
        db = InterfaceLocalDb(
            config=InterfaceLocalDbConfig(
                database_path=database_path,
                registry_path=registry_path,
                environment_id=resolved_environment_id,
            )
        )
        stores = InterfaceLaneStores(db=db)
        materializer = InterfaceCommitMaterializer(stores=stores)
        projector = InterfaceProjectionRuntime(db=db, stores=stores)

        return cls(
            repository_root=repository_root.resolve(),
            manifest_path=None,
            registry_path=registry_path,
            database_path=database_path,
            environment_id=resolved_environment_id,
            interface_config_bundle=interface_config_bundle_result.bundle,
            interface_config_bundle_source=interface_config_bundle_result.source,
            interface_config_bundle_path=interface_config_bundle_result.path,
            db=db,
            stores=stores,
            materializer=materializer,
            projector=projector,
            projection_bundle=None,
            opg_count=catalog.runtime_projection_descriptor_count,
            runtime_index=None,
            runtime_artifact_refs=tuple(runtime_artifact_refs),
            runtime_artifact_set_count=catalog.artifact_set_count,
        )

    def build_runtime_index(self) -> MetaGraphRuntimeIndexSnapshot:
        if self.runtime_index is not None:
            return self.runtime_index
        raise RuntimeError(
            "Interface runtime artifact-set boot does not build a local Meta "
            "runtime index from EnvironmentConfig bundles. Resolve live "
            "runtime targets through Environment/Service routes, or provide "
            "an explicit Meta runtime index on a dedicated local-dev rail."
        )

    async def describe_backend_state(self) -> InterfaceBackendState:
        await self.db.ensure_ready()
        tables = await self.db.list_tables()
        projection_bundle = self.projection_bundle
        return InterfaceBackendState(
            available=True,
            manifest_path=self.manifest_path,
            registry_path=self.registry_path,
            database_path=self.database_path,
            database_exists=self.database_path.exists(),
            environment_id=self.environment_id,
            opg_count=self.opg_count,
            projection_bundle_available=projection_bundle is not None,
            projection_plan_count=(
                len(tuple(projection_bundle.plan_cache.all()))
                if projection_bundle is not None
                else 0
            ),
            table_count=len(tables),
        )

    def build_lane_sync_service(
        self,
        *,
        session_port: "InterfaceSessionPort",
        include_commit_payload: bool = True,
    ) -> InterfaceLaneSyncService:
        return InterfaceLaneSyncService(
            source=session_port.lane_sync_source(
                include_commit_payload=include_commit_payload,
            ),
            stores=self.stores,
            materializer=self.materializer,
            projector=self.projector,
        )

    def build_coordinator(
        self,
        *,
        session_port: "InterfaceSessionPort | None" = None,
        gate_port: "InterfaceGatePort | None" = None,
        experience_port: "InterfaceExperiencePort | None" = None,
        navigation_context_layout_port: "InterfaceNavigationContextLayoutPort | None" = None,
        action_port: "InterfaceActionPort | None" = None,
    ) -> "InterfaceRuntimeCoordinator":
        from aware_interface.lifecycle import InterfaceRuntimeCoordinator

        return InterfaceRuntimeCoordinator(
            runtime=self,
            session_port=session_port,
            gate_port=gate_port,
            experience_port=experience_port,
            navigation_context_layout_port=navigation_context_layout_port,
            action_port=action_port,
        )

    def load_sync_assets(
        self,
        *,
        projection_hash: str,
    ) -> InterfaceHostRuntimeSyncAssets:
        projection_hash_value = str(projection_hash or "").strip()
        if not projection_hash_value:
            raise ValueError("projection_hash is required")
        raise RuntimeError(
            "Interface runtime artifact-set boot does not include local "
            "EnvironmentConfig OCG/OPG bundle bytes. Projection sync assets "
            "must come from ontology runtime artifact refs or routed runtime "
            "services on the clean rail."
        )

    def resolve_pane_render_spec_materialization_path(
        self,
        *,
        interface_config_bundle: InterfaceConfigBundle | None = None,
    ) -> Path | None:
        bundle = interface_config_bundle or self.interface_config_bundle
        candidates: list[Path] = []
        if self.interface_config_bundle_path is not None:
            candidates.append(
                self.interface_config_bundle_path.parent
                / _PANE_RENDER_SPECS_MATERIALIZATION_FILENAME
            )
        if bundle is not None:
            candidates.append(
                self.repository_root
                / ".aware"
                / "interface"
                / "runtime"
                / bundle.interface_package_name
                / _PANE_RENDER_SPECS_MATERIALIZATION_FILENAME
            )
        seen: set[Path] = set()
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            if resolved.is_file():
                return resolved
        return None

    async def load_pane_render_spec_runtime_states(
        self,
        *,
        interface_config_bundle: InterfaceConfigBundle | None = None,
    ) -> tuple[InterfaceRuntimePaneRenderSpecState, ...]:
        bundle = interface_config_bundle or self.interface_config_bundle
        if bundle is None:
            return ()
        materialization_path = self.resolve_pane_render_spec_materialization_path(
            interface_config_bundle=bundle,
        )
        if materialization_path is None:
            return ()
        pane_kind_by_binding_id, pane_name_by_binding_id = (
            _pane_render_spec_binding_maps(bundle)
        )
        if not pane_kind_by_binding_id:
            return ()
        return await load_pane_render_spec_runtime_states_from_materialization_artifact_oig(
            index=self.build_runtime_index(),
            materialization_path=materialization_path,
            pane_kind_by_pane_config_id=(
                pane_kind_by_binding_id
            ),
            pane_name_by_pane_config_id=(
                pane_name_by_binding_id
            ),
        )


@dataclass(frozen=True, slots=True)
class InterfaceHostRuntimeSyncAssets:
    ocg: ObjectConfigGraph
    opg: ObjectProjectionGraph


async def describe_interface_backend_state(
    *,
    repository_root: Path,
    state_home: Path,
    namespace: str,
    database_filename: str = _INTERFACE_DB_FILENAME,
    runtime_manifest_path: str | Path | None = None,
    db_schema_registry_path: str | Path | None = None,
) -> InterfaceBackendState:
    _ = repository_root
    manifest_path = (
        Path(runtime_manifest_path).expanduser().resolve()
        if runtime_manifest_path is not None
        else None
    )
    registry_path = _candidate_db_schema_registry_path(
        manifest_path=manifest_path,
        db_schema_registry_path=db_schema_registry_path,
    )
    database_path = (state_home / namespace / database_filename).resolve()
    return InterfaceBackendState(
        available=False,
        manifest_path=manifest_path,
        registry_path=(
            registry_path.resolve()
            if registry_path is not None and registry_path.exists()
            else registry_path
        ),
        database_path=database_path,
        database_exists=database_path.exists(),
        environment_id=None,
        opg_count=0,
        projection_bundle_available=False,
        projection_plan_count=0,
        table_count=0,
        reason=_RETIRED_ENVIRONMENT_RUNTIME_BOOT_MESSAGE,
    )


def _candidate_db_schema_registry_path(
    *,
    manifest_path: Path | None,
    db_schema_registry_path: str | Path | None,
) -> Path | None:
    if db_schema_registry_path is not None:
        return Path(db_schema_registry_path).expanduser().resolve()
    if manifest_path is None:
        return None
    return (manifest_path.parent / _DB_SCHEMA_REGISTRY_FILENAME).resolve()


def _optional_uuid(value: UUID | str | None) -> UUID | None:
    if value is None or isinstance(value, UUID):
        return value
    normalized = str(value).strip()
    if not normalized:
        return None
    return UUID(normalized)


def _pane_render_spec_binding_maps(
    bundle: InterfaceConfigBundle,
) -> tuple[Mapping[UUID | str, str], Mapping[UUID | str, str]]:
    pane_kind_by_binding_id: dict[UUID | str, str] = {}
    pane_name_by_binding_id: dict[UUID | str, str] = {}
    for pane_config in bundle.pane_configs:
        pane_kind = str(pane_config.pane_kind or "").strip()
        pane_name = str(pane_config.name or "").strip() or pane_kind
        if not pane_kind:
            continue
        for projection_view in pane_config.projection_experience_views:
            binding_id = projection_view.binding_id
            pane_kind_by_binding_id[binding_id] = pane_kind
            pane_name_by_binding_id[binding_id] = pane_name
    return pane_kind_by_binding_id, pane_name_by_binding_id


def load_interface_config_bundle(
    *,
    manifest_path: Path | None,
    repository_root: Path | None = None,
    committed_interface_config_bundle: InterfaceConfigBundle | None = None,
    allow_local_artifact_fallback: bool = True,
    local_interface_package_name: str | None = None,
) -> InterfaceConfigBundle | None:
    return resolve_interface_config_bundle(
        manifest_path=manifest_path,
        repository_root=repository_root,
        committed_interface_config_bundle=committed_interface_config_bundle,
        allow_local_artifact_fallback=allow_local_artifact_fallback,
        local_interface_package_name=local_interface_package_name,
    ).bundle


def load_workspace_interface_config_bundle(
    *,
    repository_root: Path,
    interface_package_id: UUID | str | None = None,
    interface_package_name: str | None = None,
) -> InterfaceConfigBundleLoadResult:
    selected_package_name = (interface_package_name or "").strip()
    normalized_package_id = _optional_uuid(interface_package_id)
    if selected_package_name:
        try:
            bundle_paths = (
                _resolve_local_interface_config_bundle_path(
                    repository_root=repository_root,
                    local_interface_package_name=selected_package_name,
                ),
            )
        except RuntimeError:
            return InterfaceConfigBundleLoadResult(bundle=None)
    else:
        bundle_paths = _local_interface_config_bundle_paths(
            repository_root=repository_root,
        )
    matches: list[InterfaceConfigBundleLoadResult] = []
    for bundle_path in bundle_paths:
        if bundle_path is None or not bundle_path.exists():
            continue
        bundle = _load_interface_config_bundle_from_path(
            bundle_path=bundle_path,
            error_label="Workspace Interface config bundle",
        )
        if (
            normalized_package_id is not None
            and bundle.interface_package_id != normalized_package_id
        ):
            continue
        if (
            selected_package_name
            and bundle.interface_package_name.casefold()
            != selected_package_name.casefold()
        ):
            continue
        matches.append(
            InterfaceConfigBundleLoadResult(
                bundle=bundle,
                source=_INTERFACE_CONFIG_BUNDLE_SOURCE_WORKSPACE_ARTIFACT,
                path=bundle_path.resolve(),
            )
        )
    if not matches:
        return InterfaceConfigBundleLoadResult(bundle=None)
    if len(matches) > 1:
        raise RuntimeError(
            "Multiple Workspace Interface config bundles matched the requested "
            "Interface package target."
        )
    return matches[0]


def _load_interface_config_bundle_from_path(
    *,
    bundle_path: Path,
    error_label: str = "Interface config bundle",
) -> InterfaceConfigBundle:
    try:
        return InterfaceConfigBundle.model_validate_json(
            bundle_path.read_text(encoding="utf-8")
        )
    except Exception as exc:
        raise RuntimeError(
            f"Invalid {error_label} artifact: bundle_path={bundle_path}"
        ) from exc


def resolve_interface_config_bundle(
    *,
    manifest_path: Path | None,
    repository_root: Path | None = None,
    committed_interface_config_bundle: InterfaceConfigBundle | None = None,
    allow_local_artifact_fallback: bool = True,
    local_interface_package_name: str | None = None,
) -> InterfaceConfigBundleLoadResult:
    if committed_interface_config_bundle is not None:
        return InterfaceConfigBundleLoadResult(
            bundle=committed_interface_config_bundle,
            source=_INTERFACE_CONFIG_BUNDLE_SOURCE_COMMITTED_PACKAGE,
        )
    if not allow_local_artifact_fallback:
        return InterfaceConfigBundleLoadResult(bundle=None)

    bundle_path: Path | None = None
    source: str | None = None
    if manifest_path is not None:
        bundle_path = manifest_path.parent / _INTERFACE_CONFIG_BUNDLE_FILENAME
        source = _INTERFACE_CONFIG_BUNDLE_SOURCE_RUNTIME_ARTIFACT
    if (
        bundle_path is None or not bundle_path.exists()
    ) and repository_root is not None:
        bundle_path = _resolve_local_interface_config_bundle_path(
            repository_root=repository_root,
            local_interface_package_name=local_interface_package_name,
        )
        source = _INTERFACE_CONFIG_BUNDLE_SOURCE_WORKSPACE_ARTIFACT
    if bundle_path is None or not bundle_path.exists():
        return InterfaceConfigBundleLoadResult(bundle=None)
    try:
        return InterfaceConfigBundleLoadResult(
            bundle=InterfaceConfigBundle.model_validate_json(
                bundle_path.read_text(encoding="utf-8")
            ),
            source=source,
            path=bundle_path.resolve(),
        )
    except Exception as exc:
        raise RuntimeError(
            "Invalid Interface config bundle artifact: " + f"bundle_path={bundle_path}"
        ) from exc


async def load_committed_interface_config_bundle_from_package_ref(
    *,
    index: MetaGraphRuntimeIndexSnapshot,
    package_ref: InterfaceRuntimePackageRef,
    materialized_workspace_root: str | Path,
) -> InterfaceConfigBundle:
    resolved = await resolve_committed_interface_runtime_package_ref(
        index=index,
        package_ref=package_ref,
        materialized_workspace_root=materialized_workspace_root,
    )
    return project_interface_config_bundle_from_committed_package(resolved)


def _resolve_local_interface_config_bundle_path(
    *,
    repository_root: Path,
    local_interface_package_name: str | None = None,
) -> Path | None:
    interface_paths = _local_interface_config_bundle_paths(
        repository_root=repository_root,
    )
    selected_package_name = (local_interface_package_name or "").strip()
    if selected_package_name:
        matches: list[Path] = []
        for bundle_path in interface_paths:
            bundle = _load_interface_config_bundle_from_path(
                bundle_path=bundle_path,
                error_label="Workspace Interface config bundle",
            )
            if (
                bundle.interface_package_name.casefold()
                == selected_package_name.casefold()
            ):
                matches.append(bundle_path)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise RuntimeError(
                "Multiple workspace Interface packages matched "
                f"local_interface_package_name {selected_package_name!r} "
                f"under {repository_root}."
            )
        raise RuntimeError(
            "No workspace Interface package matched local_interface_package_name "
            + f"{selected_package_name!r} under {repository_root}."
        )
    if len(interface_paths) == 1:
        return interface_paths[0]
    return None


def _local_interface_manifest_paths(*, repository_root: Path) -> tuple[Path, ...]:
    resolved_root = repository_root.resolve()
    search_roots = [resolved_root / "interfaces"]
    workspaces_root = resolved_root / "workspaces"
    if workspaces_root.is_dir():
        search_roots.extend(
            workspace_path / "interfaces"
            for workspace_path in sorted(workspaces_root.iterdir())
            if workspace_path.is_dir()
        )

    manifest_paths: dict[str, Path] = {}
    for search_root in search_roots:
        if not search_root.is_dir():
            continue
        for manifest_path in sorted(search_root.glob("*/aware.interface.toml")):
            _register_local_interface_manifest(
                manifest_paths=manifest_paths,
                manifest_path=manifest_path,
            )
    _register_workspace_declared_interface_manifests(
        manifest_paths=manifest_paths,
        workspace_root=resolved_root,
    )
    if workspaces_root.is_dir():
        for workspace_path in sorted(workspaces_root.iterdir()):
            if workspace_path.is_dir():
                _register_workspace_declared_interface_manifests(
                    manifest_paths=manifest_paths,
                    workspace_root=workspace_path.resolve(),
                )
    return tuple(manifest_paths[key] for key in sorted(manifest_paths))


def _register_local_interface_manifest(
    *,
    manifest_paths: dict[str, Path],
    manifest_path: Path,
) -> None:
    if not manifest_path.is_file():
        return
    resolved_manifest_path = manifest_path.resolve()
    manifest_paths[resolved_manifest_path.as_posix()] = resolved_manifest_path


def _register_workspace_declared_interface_manifests(
    *,
    manifest_paths: dict[str, Path],
    workspace_root: Path,
) -> None:
    workspace_toml_path = workspace_root / "aware.workspace.toml"
    workspace_payload = _load_toml_mapping(workspace_toml_path)
    workspace = _as_mapping(workspace_payload.get("workspace"))
    for manifest_ref in _string_items(workspace.get("interfaces")):
        _register_local_interface_manifest(
            manifest_paths=manifest_paths,
            manifest_path=workspace_root / manifest_ref,
        )
    for module_entry in _mapping_items(workspace.get("modules")):
        module_path = str(module_entry.get("path") or "").strip()
        if not module_path:
            continue
        _register_module_declared_interface_manifests(
            manifest_paths=manifest_paths,
            module_root=workspace_root / module_path,
        )


def _register_module_declared_interface_manifests(
    *,
    manifest_paths: dict[str, Path],
    module_root: Path,
) -> None:
    module_payload = _load_toml_mapping(module_root / "aware.module.toml")
    for package_entry in _mapping_items(module_payload.get("packages")):
        package_kind = str(package_entry.get("kind") or "").strip()
        if package_kind.casefold() != "interface":
            continue
        manifest_ref = str(package_entry.get("manifest") or "").strip()
        if manifest_ref:
            _register_local_interface_manifest(
                manifest_paths=manifest_paths,
                manifest_path=module_root / manifest_ref,
            )


def _load_toml_mapping(path: Path) -> Mapping[str, object]:
    if not path.is_file():
        return {}
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_items(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _string_items(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        item.strip() for item in value if isinstance(item, str) and item.strip()
    )


def _local_interface_config_bundle_paths(
    *,
    repository_root: Path,
) -> tuple[Path, ...]:
    bundle_paths: list[Path] = []
    for manifest_path in _local_interface_manifest_paths(
        repository_root=repository_root
    ):
        try:
            manifest = load_aware_interface_toml_spec(toml_path=manifest_path)
        except Exception:
            continue
        bundle_path = (
            manifest_path.parent / manifest.build.config_bundle_path
        ).resolve()
        if bundle_path.exists():
            bundle_paths.append(bundle_path)
    return tuple(bundle_paths)


__all__ = [
    "InterfaceConfigBundleLoadResult",
    "InterfaceHostRuntime",
    "InterfaceHostRuntimeSyncAssets",
    "describe_interface_backend_state",
    "load_committed_interface_config_bundle_from_package_ref",
    "load_interface_config_bundle",
    "load_workspace_interface_config_bundle",
    "resolve_interface_config_bundle",
]
