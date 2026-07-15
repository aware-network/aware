from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar
from uuid import UUID

from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
from aware_service_runtime.manifest.spec import AwareServiceTomlDependencySpec
from aware_meta.graph.instance.commit.contract import ObjectInstanceGraphCommitRef
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_orm.models.orm_model import ORMModel
from aware_api_ontology.api.api_package import ApiPackage
from aware_service_ontology.service.service_config import ServiceConfig
from aware_service_ontology.service.service_package import ServicePackage
from aware_service_ontology.service.service_package_provided_api_package import (
    ServicePackageProvidedApiPackage,
)
from aware_service_ontology.stable_ids import stable_service_package_id

_REVISION_FILESYSTEM_MANIFEST_RELATIVE_PATH = Path(
    ".aware/workspace/revision-filesystem.manifest.json"
)
_TRoot = TypeVar("_TRoot", bound=ORMModel)


@dataclass(frozen=True, slots=True)
class ServiceRuntimePackageRef:
    """Runtime ref for a Workspace-selected ServicePackage semantic package."""

    family_key: str
    package_kind: str
    package_name: str
    manifest_path: str | Path | None = None
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_branch_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    source_code_package_id: str | None = None

    @property
    def has_semantic_identity(self) -> bool:
        return bool(_clean(self.semantic_package_id) or _clean(self.semantic_root_id))


@dataclass(frozen=True, slots=True)
class ServiceRuntimePackageDependency:
    package_name: str
    kind: str
    version_number: int | None = None
    service_package_provided_api_package_id: str | None = None
    api_package_id: str | None = None
    api_package_object_instance_graph_commit_id: str | None = None
    service_protocol_package_id: str | None = None
    service_protocol_code_package_id: str | None = None
    service_protocol_code_package_object_instance_graph_commit_id: str | None = None
    service_protocol_plan_hash_sha256: str | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "package_name": self.package_name,
            "kind": self.kind,
        }
        if self.version_number is not None:
            payload["version_number"] = self.version_number
        for key in (
            "service_package_provided_api_package_id",
            "api_package_id",
            "api_package_object_instance_graph_commit_id",
            "service_protocol_package_id",
            "service_protocol_code_package_id",
            "service_protocol_code_package_object_instance_graph_commit_id",
            "service_protocol_plan_hash_sha256",
        ):
            value = getattr(self, key)
            if value is not None:
                payload[key] = value
        return payload


@dataclass(frozen=True, slots=True)
class ResolvedServiceRuntimePackageRef:
    """Resolved ServicePackage execution coordinates inside a revision filesystem."""

    package_ref: ServiceRuntimePackageRef
    materialized_workspace_root: Path
    manifest_path: Path | None
    manifest_relative_path: str | None
    package_name: str
    fqn_prefix: str
    dependencies: tuple[ServiceRuntimePackageDependency, ...]
    service_package: ServicePackage | None = None
    service_config: ServiceConfig | None = None
    service_package_id: UUID | None = None
    service_config_id: UUID | None = None
    service_config_object_instance_graph_commit_id: UUID | None = None
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_branch_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    source_code_package_id: str | None = None
    dependency_workspace_roots: tuple[Path, ...] = ()

    @property
    def toml_paths(self) -> tuple[Path, ...]:
        """Compatibility shape for callers still accepting implementation TOML paths."""

        if self.manifest_path is None:
            return ()
        return (self.manifest_path,)

    @property
    def dependency_payloads(self) -> tuple[dict[str, object], ...]:
        return tuple(dependency.to_payload() for dependency in self.dependencies)


def resolve_service_runtime_package_ref(
    *,
    package_ref: ServiceRuntimePackageRef,
    materialized_workspace_root: str | Path,
) -> ResolvedServiceRuntimePackageRef:
    """Resolve a committed service package ref into revision-local runtime inputs."""

    _validate_service_ref(package_ref)
    root = Path(materialized_workspace_root).expanduser().resolve()
    _validate_revision_filesystem_root(root)
    manifest_path = _resolve_manifest_path_from_ref(
        package_ref=package_ref,
        materialized_workspace_root=root,
    )
    spec = load_aware_service_toml_spec(toml_path=manifest_path)
    spec_package_name = spec.service.package_name.strip()
    if spec_package_name != package_ref.package_name:
        raise RuntimeError(
            "Service runtime package ref package_name does not match "
            f"aware.service.toml: ref={package_ref.package_name!r} "
            f"manifest={spec_package_name!r} path={manifest_path}"
        )
    return ResolvedServiceRuntimePackageRef(
        package_ref=package_ref,
        materialized_workspace_root=root,
        manifest_path=manifest_path,
        manifest_relative_path=_relative_to_root(
            path=manifest_path,
            root=root,
            label="manifest_path",
        ),
        package_name=spec_package_name,
        fqn_prefix=spec.service.fqn_prefix,
        dependencies=tuple(
            _dependency_from_spec(dependency) for dependency in spec.dependencies
        ),
        workspace_package_id=_clean(package_ref.workspace_package_id),
        semantic_package_id=_clean(package_ref.semantic_package_id),
        semantic_object_instance_graph_commit_id=_clean(
            package_ref.semantic_object_instance_graph_commit_id
        ),
        semantic_head_commit_id=_clean(package_ref.semantic_head_commit_id),
        semantic_branch_id=_clean(package_ref.semantic_branch_id),
        semantic_root_kind=_clean(package_ref.semantic_root_kind),
        semantic_root_id=_clean(package_ref.semantic_root_id),
        semantic_root_object_instance_graph_commit_id=_clean(
            package_ref.semantic_root_object_instance_graph_commit_id
        ),
        source_code_package_id=_clean(package_ref.source_code_package_id),
    )


def resolve_service_runtime_package_ref_from_manifest_path(
    *,
    package_ref: ServiceRuntimePackageRef,
) -> ResolvedServiceRuntimePackageRef:
    """Resolve a service package ref from an explicit implementation manifest."""

    _validate_service_ref(package_ref)
    manifest_path = _resolve_direct_manifest_path_from_ref(package_ref=package_ref)
    spec = load_aware_service_toml_spec(toml_path=manifest_path)
    spec_package_name = spec.service.package_name.strip()
    if spec_package_name != package_ref.package_name:
        raise RuntimeError(
            "Service runtime package ref package_name does not match "
            f"aware.service.toml: ref={package_ref.package_name!r} "
            f"manifest={spec_package_name!r} path={manifest_path}"
        )
    return ResolvedServiceRuntimePackageRef(
        package_ref=package_ref,
        materialized_workspace_root=manifest_path.parent,
        manifest_path=manifest_path,
        manifest_relative_path=manifest_path.name,
        package_name=spec_package_name,
        fqn_prefix=spec.service.fqn_prefix,
        dependencies=tuple(
            _dependency_from_spec(dependency) for dependency in spec.dependencies
        ),
        workspace_package_id=_clean(package_ref.workspace_package_id),
        semantic_package_id=_clean(package_ref.semantic_package_id),
        semantic_object_instance_graph_commit_id=_clean(
            package_ref.semantic_object_instance_graph_commit_id
        ),
        semantic_head_commit_id=_clean(package_ref.semantic_head_commit_id),
        semantic_branch_id=_clean(package_ref.semantic_branch_id),
        semantic_root_kind=_clean(package_ref.semantic_root_kind),
        semantic_root_id=_clean(package_ref.semantic_root_id),
        semantic_root_object_instance_graph_commit_id=_clean(
            package_ref.semantic_root_object_instance_graph_commit_id
        ),
        source_code_package_id=_clean(package_ref.source_code_package_id),
    )


async def resolve_committed_service_runtime_package_ref(
    *,
    index: MetaGraphRuntimeIndex,
    package_ref: ServiceRuntimePackageRef,
    materialized_workspace_root: str | Path,
    dependency_workspace_roots: Sequence[str | Path] = (),
) -> ResolvedServiceRuntimePackageRef:
    """Resolve a committed ServicePackage ref without reopening TOML as truth."""

    _validate_service_ref(package_ref)
    root = Path(materialized_workspace_root).expanduser().resolve()
    _validate_revision_filesystem_root(root)
    package_commit_ref_label = "semantic_object_instance_graph_commit_id"
    package_commit_ref_value = _clean(
        package_ref.semantic_object_instance_graph_commit_id
    )
    if package_commit_ref_value is None:
        package_commit_ref_label = "semantic_head_commit_id"
        package_commit_ref_value = _clean(package_ref.semantic_head_commit_id)
    package_commit_ref_id = _required_uuid(
        package_commit_ref_value,
        label=package_commit_ref_label,
    )
    service_package_projection_hash = _find_projection_hash_by_name(
        index=index,
        projection_name="ServicePackage",
    )
    store = FSCommitStore(root_dir=root)
    dependency_stores = _revision_commit_stores(
        materialized_workspace_root=root,
        dependency_workspace_roots=dependency_workspace_roots,
    )
    resolved_dependency_workspace_roots = tuple(
        dict.fromkeys(
            Path(raw_root).expanduser().resolve()
            for raw_root in dependency_workspace_roots
        )
    )
    branch_id = _optional_uuid(package_ref.semantic_branch_id)
    if branch_id is None:
        if _clean(package_ref.semantic_object_instance_graph_commit_id) is None:
            raise RuntimeError(
                "Branchless Service runtime package refs require "
                "semantic_object_instance_graph_commit_id; legacy "
                "semantic_head_commit_id refs must also provide semantic_branch_id."
            )
        package_commit_refs = (
            await store.domain_commit_refs_for_object_instance_graph_commit_id(
                projection_hash=service_package_projection_hash,
                object_instance_graph_commit_id=package_commit_ref_id,
            )
        )
        if not package_commit_refs:
            raise RuntimeError(
                "Service runtime package ref semantic_object_instance_graph_commit_id "
                "did not resolve to any indexed ServicePackage branch: "
                f"semantic_object_instance_graph_commit_id={package_commit_ref_id} "
                f"projection_hash={service_package_projection_hash}"
            )
        if len(package_commit_refs) != 1:
            raise RuntimeError(
                "Service runtime package ref semantic_object_instance_graph_commit_id "
                "resolved to multiple ServicePackage branches: "
                f"semantic_object_instance_graph_commit_id={package_commit_ref_id} "
                f"projection_hash={service_package_projection_hash} "
                f"branches={[str(ref.branch_id) for ref in package_commit_refs]!r}"
            )
        package_commit_ref = package_commit_refs[0]
        branch_id = package_commit_ref.branch_id
        package_domain_commit_id = package_commit_ref.domain_commit_id
    else:
        package_domain_commit_id = (
            await store.domain_commit_id_for_object_instance_graph_commit_id(
                branch_id=branch_id,
                projection_hash=service_package_projection_hash,
                object_instance_graph_commit_id=package_commit_ref_id,
            )
        )
        if package_domain_commit_id is None:
            legacy_domain_commit = await store.get_commit(
                branch_id=branch_id,
                projection_hash=service_package_projection_hash,
                commit_id=package_commit_ref_id,
            )
            if legacy_domain_commit is None:
                raise RuntimeError(
                    f"Service runtime package ref {package_commit_ref_label} is neither "
                    "an indexed ObjectInstanceGraphCommit id nor a domain commit id: "
                    f"{package_commit_ref_label}={package_commit_ref_id} "
                    f"branch_id={branch_id} "
                    f"projection_hash={service_package_projection_hash}"
                )
            package_domain_commit_id = package_commit_ref_id

    resolved_semantic_branch_id = str(branch_id)

    service_package_id = _optional_uuid(
        package_ref.semantic_package_id
    ) or stable_service_package_id(
        name=package_ref.package_name,
    )
    service_package = await _hydrate_root_from_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=service_package_projection_hash,
        commit_id=package_domain_commit_id,
        root_id=service_package_id,
        root_type=ServicePackage,
        hydrate_portal_targets=True,
        store=store,
    )
    if service_package is None:
        raise RuntimeError(
            "Service runtime package ref could not hydrate ServicePackage from "
            "semantic commit: "
            f"package_name={package_ref.package_name!r} semantic_package_id={service_package_id}"
        )

    _validate_service_package_ref_pair(
        package_ref=package_ref,
        service_package=service_package,
    )
    preferred_service_config_projection_hash = _find_projection_hash_by_name(
        index=index,
        projection_name="ServiceConfig",
    )
    service_config_commit_ref = await _service_config_domain_commit_ref_from_package(
        index=index,
        store=store,
        service_package=service_package,
        branch_id=branch_id,
        preferred_projection_hash=preferred_service_config_projection_hash,
    )
    if service_config_commit_ref is None:
        raise RuntimeError(
            "Service runtime package ref resolved ServicePackage without a hydrated "
            "service_config_object_instance_graph_commit.commit_id: "
            f"service_package={service_package.id}"
        )
    service_config_projection_hash, service_config_domain_commit_id = (
        service_config_commit_ref
    )
    service_config = await _hydrate_root_from_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=service_config_projection_hash,
        commit_id=service_config_domain_commit_id,
        root_id=service_package.service_config_id,
        root_type=ServiceConfig,
        hydrate_portal_targets=True,
        store=store,
    )
    if service_config is None:
        raise RuntimeError(
            "Service runtime package ref could not hydrate pinned ServiceConfig "
            f"root: service_config_id={service_package.service_config_id} "
            f"commit_id={service_config_domain_commit_id}"
        )
    _validate_service_config_ref_pair(
        package_ref=package_ref,
        service_package=service_package,
        service_config=service_config,
    )

    manifest_relative_path = _manifest_relative_path_from_service_package(
        service_package=service_package,
        package_ref=package_ref,
    )
    dependencies = await _dependencies_from_committed_service_package(
        index=index,
        stores=dependency_stores,
        service_package=service_package,
    )
    return ResolvedServiceRuntimePackageRef(
        package_ref=package_ref,
        materialized_workspace_root=root,
        manifest_path=None,
        manifest_relative_path=manifest_relative_path,
        service_package=service_package,
        service_config=service_config,
        service_package_id=service_package.id,
        service_config_id=service_config.id,
        service_config_object_instance_graph_commit_id=(
            service_package.service_config_object_instance_graph_commit_id
        ),
        package_name=service_package.name,
        fqn_prefix=service_package.fqn_prefix or "",
        dependencies=dependencies,
        workspace_package_id=_clean(package_ref.workspace_package_id),
        semantic_package_id=str(service_package.id),
        semantic_object_instance_graph_commit_id=_clean(
            package_ref.semantic_object_instance_graph_commit_id
        ),
        semantic_head_commit_id=_clean(package_ref.semantic_head_commit_id),
        semantic_branch_id=resolved_semantic_branch_id,
        semantic_root_kind=_clean(package_ref.semantic_root_kind),
        semantic_root_id=_clean(package_ref.semantic_root_id),
        semantic_root_object_instance_graph_commit_id=(
            str(service_package.service_config_object_instance_graph_commit_id)
            if service_package.service_config_object_instance_graph_commit_id
            is not None
            else None
        ),
        source_code_package_id=(
            str(service_package.source_code_package_id)
            if service_package.source_code_package_id is not None
            else _clean(package_ref.source_code_package_id)
        ),
        dependency_workspace_roots=resolved_dependency_workspace_roots,
    )


async def resolve_committed_service_runtime_package_refs(
    *,
    index: MetaGraphRuntimeIndex,
    package_refs: Sequence[ServiceRuntimePackageRef],
    materialized_workspace_root: str | Path,
    dependency_workspace_roots: Sequence[str | Path] = (),
) -> tuple[ResolvedServiceRuntimePackageRef, ...]:
    resolved = tuple(
        [
            await resolve_committed_service_runtime_package_ref(
                index=index,
                package_ref=package_ref,
                materialized_workspace_root=materialized_workspace_root,
                dependency_workspace_roots=dependency_workspace_roots,
            )
            for package_ref in package_refs
        ]
    )
    _reject_duplicate_resolved_refs(resolved)
    return resolved


def resolve_service_runtime_package_refs(
    *,
    package_refs: Sequence[ServiceRuntimePackageRef],
    materialized_workspace_root: str | Path,
) -> tuple[ResolvedServiceRuntimePackageRef, ...]:
    resolved = tuple(
        resolve_service_runtime_package_ref(
            package_ref=package_ref,
            materialized_workspace_root=materialized_workspace_root,
        )
        for package_ref in package_refs
    )
    _reject_duplicate_resolved_refs(resolved)
    return resolved


def resolve_service_runtime_package_refs_from_manifest_paths(
    *,
    package_refs: Sequence[ServiceRuntimePackageRef],
) -> tuple[ResolvedServiceRuntimePackageRef, ...]:
    resolved = tuple(
        resolve_service_runtime_package_ref_from_manifest_path(
            package_ref=package_ref,
        )
        for package_ref in package_refs
    )
    _reject_duplicate_resolved_refs(resolved)
    return resolved


def _validate_service_ref(package_ref: ServiceRuntimePackageRef) -> None:
    if _clean(package_ref.family_key) != "service":
        raise RuntimeError(
            "Service runtime package ref requires family_key='service': "
            f"{package_ref.family_key!r}"
        )
    if _clean(package_ref.package_kind) != "service":
        raise RuntimeError(
            "Service runtime package ref requires package_kind='service': "
            f"{package_ref.package_kind!r}"
        )
    if not _clean(package_ref.package_name):
        raise RuntimeError("Service runtime package ref requires a package_name.")
    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    if semantic_root_kind is not None and semantic_root_kind not in {
        "service_config",
        "service_package",
    }:
        raise RuntimeError(
            "Service runtime package ref semantic_root_kind must be "
            "'service_config' or 'service_package' when provided: "
            f"{semantic_root_kind!r}"
        )


def _validate_revision_filesystem_root(root: Path) -> None:
    if not root.is_dir():
        raise FileNotFoundError(
            "Service runtime package ref requires an existing materialized "
            f"workspace root: {root}"
        )
    manifest_path = (root / _REVISION_FILESYSTEM_MANIFEST_RELATIVE_PATH).resolve()
    if not manifest_path.is_file():
        raise FileNotFoundError(
            "Service runtime package ref requires a WorkspaceRevision filesystem "
            f"manifest at {manifest_path}"
        )


def _resolve_manifest_path_from_ref(
    *,
    package_ref: ServiceRuntimePackageRef,
    materialized_workspace_root: Path,
) -> Path:
    raw_manifest_path = package_ref.manifest_path
    if raw_manifest_path is None or not str(raw_manifest_path).strip():
        raise RuntimeError(
            "Service runtime package ref requires manifest_path until committed "
            "ServicePackage artifact hydration is wired."
        )
    manifest_path = Path(raw_manifest_path).expanduser()
    if not manifest_path.is_absolute():
        manifest_path = materialized_workspace_root / manifest_path
    resolved_manifest_path = manifest_path.resolve()
    _relative_to_root(
        path=resolved_manifest_path,
        root=materialized_workspace_root,
        label="manifest_path",
    )
    if not resolved_manifest_path.is_file():
        raise FileNotFoundError(
            "Service runtime package ref manifest_path does not exist inside "
            f"the materialized workspace root: {resolved_manifest_path}"
        )
    return resolved_manifest_path


def _resolve_direct_manifest_path_from_ref(
    *,
    package_ref: ServiceRuntimePackageRef,
) -> Path:
    raw_manifest_path = package_ref.manifest_path
    if raw_manifest_path is None or not str(raw_manifest_path).strip():
        raise RuntimeError(
            "Service runtime package ref requires manifest_path for "
            "artifact-first ServiceHost startup."
        )
    resolved_manifest_path = Path(raw_manifest_path).expanduser().resolve()
    if not resolved_manifest_path.is_file():
        raise FileNotFoundError(
            "Service runtime package ref manifest_path does not exist: "
            f"{resolved_manifest_path}"
        )
    return resolved_manifest_path


def _manifest_relative_path_from_service_package(
    *,
    service_package: ServicePackage,
    package_ref: ServiceRuntimePackageRef,
) -> str | None:
    raw_manifest_path = _clean(service_package.manifest_relative_path)
    if raw_manifest_path is None:
        raw_manifest_path = (
            str(package_ref.manifest_path)
            if package_ref.manifest_path is not None
            else None
        )
    if raw_manifest_path is None or not raw_manifest_path.strip():
        return None
    manifest_path = Path(raw_manifest_path).expanduser()
    return manifest_path.as_posix()


def _dependency_from_spec(
    dependency: AwareServiceTomlDependencySpec,
) -> ServiceRuntimePackageDependency:
    return ServiceRuntimePackageDependency(
        package_name=dependency.package_name,
        kind=str(dependency.kind.value),
        version_number=dependency.version_number,
    )


def _dependencies_from_package_payload(
    payload: object,
) -> tuple[ServiceRuntimePackageDependency, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes)):
        raise RuntimeError("ServicePackage.dependencies must be a JSON array.")
    dependencies: list[ServiceRuntimePackageDependency] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise RuntimeError("ServicePackage.dependencies entries must be objects.")
        package_name = _required_text(
            item.get("package_name"), label="dependencies[].package_name"
        )
        kind = _required_text(item.get("kind"), label="dependencies[].kind")
        if kind == "api_service_protocol":
            raise RuntimeError(
                "Committed ServicePackage.dependencies must not contain "
                "api_service_protocol entries; protocol locks belong to "
                "ServicePackage.provided_api_packages."
            )
        version_number = item.get("version_number")
        dependencies.append(
            ServiceRuntimePackageDependency(
                package_name=package_name,
                kind=kind,
                version_number=_optional_int(
                    version_number,
                    label="dependencies[].version_number",
                ),
            )
        )
    return tuple(dependencies)


async def _dependencies_from_committed_service_package(
    *,
    index: MetaGraphRuntimeIndex,
    stores: Sequence[FSCommitStore],
    service_package: ServicePackage,
) -> tuple[ServiceRuntimePackageDependency, ...]:
    dependencies = list(
        _dependencies_from_package_payload(service_package.dependencies)
    )
    protocol_dependencies: dict[str, ServiceRuntimePackageDependency] = {}
    for bridge in service_package.provided_api_packages:
        api_package = bridge.api_package
        if api_package is None:
            api_package = await _hydrate_protocol_lock_api_package(
                index=index,
                stores=stores,
                bridge=bridge,
            )
        protocol_package = bridge.service_protocol_package
        if protocol_package is None and api_package is not None:
            protocol_package = next(
                (
                    language_package
                    for language_package in api_package.language_packages
                    if language_package.id == bridge.service_protocol_package_id
                ),
                None,
            )
        if api_package is None:
            raise RuntimeError(
                "Committed ServicePackage protocol lock could not hydrate its exact "
                f"ApiPackage pin: bridge_id={bridge.id}"
            )
        if protocol_package is None:
            raise RuntimeError(
                "Committed ServicePackage protocol lock did not hydrate its "
                f"ApiPackageLanguagePackage portal: bridge_id={bridge.id}"
            )
        if bridge.api_package_id != api_package.id:
            raise RuntimeError(
                "Committed ServicePackage protocol lock ApiPackage identity "
                f"mismatch: bridge={bridge.api_package_id} portal={api_package.id}"
            )
        if bridge.service_protocol_package_id != protocol_package.id:
            raise RuntimeError(
                "Committed ServicePackage protocol lock language package identity "
                "mismatch: "
                f"bridge={bridge.service_protocol_package_id} "
                f"portal={protocol_package.id}"
            )
        if protocol_package.api_package_id != api_package.id:
            raise RuntimeError(
                "Committed ServicePackage protocol lock selected a language "
                "package owned by a different ApiPackage."
            )
        if protocol_package.output_key != "python.service_protocol_package":
            raise RuntimeError(
                "Committed ServicePackage protocol lock selected a non-protocol "
                f"API output: output_key={protocol_package.output_key!r}"
            )
        if protocol_package.object_instance_graph_commit_id is None:
            raise RuntimeError(
                "Committed ServicePackage protocol lock selected an API output "
                "without an exact CodePackage commit pin."
            )
        if bridge.api_package_object_instance_graph_commit_id is None:
            raise RuntimeError(
                "Committed ServicePackage protocol lock has no exact ApiPackage "
                "commit pin."
            )
        expected_hash = (bridge.service_protocol_plan_hash_sha256 or "").strip()
        if len(expected_hash) != 64 or any(
            character not in "0123456789abcdef" for character in expected_hash
        ):
            raise RuntimeError(
                "Committed ServicePackage protocol lock has an invalid protocol "
                f"plan digest: bridge_id={bridge.id}"
            )
        package_name = _required_text(
            api_package.name,
            label="provided_api_packages[].api_package.name",
        )
        bridge_id = _required_uuid(
            bridge.id,
            label="provided_api_packages[].id",
        )
        api_package_id = _required_uuid(
            api_package.id,
            label="provided_api_packages[].api_package.id",
        )
        protocol_package_id = _required_uuid(
            protocol_package.id,
            label="provided_api_packages[].service_protocol_package.id",
        )
        protocol_code_package_id = _required_uuid(
            protocol_package.code_package_id,
            label=("provided_api_packages[].service_protocol_package.code_package_id"),
        )
        dependency = ServiceRuntimePackageDependency(
            package_name=package_name,
            kind="api_service_protocol",
            version_number=api_package.version_number,
            service_package_provided_api_package_id=str(bridge_id),
            api_package_id=str(api_package_id),
            api_package_object_instance_graph_commit_id=str(
                bridge.api_package_object_instance_graph_commit_id
            ),
            service_protocol_package_id=str(protocol_package_id),
            service_protocol_code_package_id=str(protocol_code_package_id),
            service_protocol_code_package_object_instance_graph_commit_id=str(
                protocol_package.object_instance_graph_commit_id
            ),
            service_protocol_plan_hash_sha256=expected_hash,
        )
        existing = protocol_dependencies.get(package_name)
        if existing is not None and existing != dependency:
            raise RuntimeError(
                "Committed ServicePackage contains conflicting protocol locks "
                f"for ApiPackage {package_name!r}."
            )
        protocol_dependencies[package_name] = dependency
    dependencies.extend(
        protocol_dependencies[package_name]
        for package_name in sorted(protocol_dependencies, key=str.casefold)
    )
    return tuple(dependencies)


async def _hydrate_protocol_lock_api_package(
    *,
    index: MetaGraphRuntimeIndex,
    stores: Sequence[FSCommitStore],
    bridge: ServicePackageProvidedApiPackage,
) -> ApiPackage | None:
    pinned_commit_id = bridge.api_package_object_instance_graph_commit_id
    if pinned_commit_id is None:
        return None
    projection_hash = _find_projection_hash_by_name(
        index=index,
        projection_name="ApiPackage",
    )
    matches: dict[
        tuple[UUID, str, UUID],
        tuple[ObjectInstanceGraphCommitRef, FSCommitStore],
    ] = {}
    for store in stores:
        commit_refs = (
            await store.domain_commit_refs_for_object_instance_graph_commit_id(
                projection_hash=projection_hash,
                object_instance_graph_commit_id=pinned_commit_id,
            )
        )
        for commit_ref in commit_refs:
            key = (
                commit_ref.branch_id,
                commit_ref.projection_hash,
                commit_ref.domain_commit_id,
            )
            matches.setdefault(key, (commit_ref, store))
    if not matches:
        raise RuntimeError(
            "Committed ServicePackage protocol lock ApiPackage pin did not resolve "
            "inside the WorkspaceRevision: "
            f"bridge_id={bridge.id} "
            f"api_package_id={bridge.api_package_id} "
            f"object_instance_graph_commit_id={pinned_commit_id}"
        )
    if len(matches) != 1:
        raise RuntimeError(
            "Committed ServicePackage protocol lock ApiPackage pin resolved to "
            "multiple branches: "
            f"bridge_id={bridge.id} "
            f"object_instance_graph_commit_id={pinned_commit_id} "
            f"branches={[str(key[0]) for key in sorted(matches, key=str)]!r}"
        )
    commit_ref, store = next(iter(matches.values()))
    return await _hydrate_root_from_commit(
        index=index,
        branch_id=commit_ref.branch_id,
        projection_hash=projection_hash,
        commit_id=commit_ref.domain_commit_id,
        root_id=bridge.api_package_id,
        root_type=ApiPackage,
        hydrate_portal_targets=False,
        store=store,
    )


def _revision_commit_stores(
    *,
    materialized_workspace_root: Path,
    dependency_workspace_roots: Sequence[str | Path],
) -> tuple[FSCommitStore, ...]:
    roots = [materialized_workspace_root]
    seen = {materialized_workspace_root}
    for raw_root in dependency_workspace_roots:
        root = Path(raw_root).expanduser().resolve()
        _validate_revision_filesystem_root(root)
        if root in seen:
            continue
        roots.append(root)
        seen.add(root)
    return tuple(FSCommitStore(root_dir=root) for root in roots)


def _reject_duplicate_resolved_refs(
    refs: tuple[ResolvedServiceRuntimePackageRef, ...],
) -> None:
    seen: dict[str, ResolvedServiceRuntimePackageRef] = {}
    for ref in refs:
        key = _resolved_ref_key(ref)
        existing = seen.get(key)
        if (
            existing is not None
            and existing.manifest_path is not None
            and ref.manifest_path is not None
            and existing.manifest_path != ref.manifest_path
        ):
            raise RuntimeError(
                "Conflicting service runtime package refs resolve to the same "
                f"semantic package identity: {key!r}"
            )
        seen[key] = ref


def _resolved_ref_key(ref: ResolvedServiceRuntimePackageRef) -> str:
    if ref.semantic_package_id is not None:
        return f"semantic_package_id:{ref.semantic_package_id}"
    if ref.semantic_root_id is not None:
        return f"semantic_root_id:{ref.semantic_root_id}"
    if ref.manifest_path is None:
        return f"package_name:{ref.package_name}"
    return f"manifest_path:{ref.manifest_path.as_posix()}"


def _validate_service_package_ref_pair(
    *,
    package_ref: ServiceRuntimePackageRef,
    service_package: ServicePackage,
) -> None:
    if service_package.name != package_ref.package_name:
        raise RuntimeError(
            "Service runtime package ref package_name does not match "
            f"ServicePackage: ref={package_ref.package_name!r} "
            f"service_package={service_package.name!r}"
        )
    semantic_package_id = _optional_uuid(package_ref.semantic_package_id)
    if semantic_package_id is not None and semantic_package_id != service_package.id:
        raise RuntimeError(
            "Service runtime package ref semantic_package_id does not match "
            f"ServicePackage: ref={semantic_package_id} service_package={service_package.id}"
        )
    pinned_commit_id = _optional_uuid(
        package_ref.semantic_root_object_instance_graph_commit_id
    )
    if (
        pinned_commit_id is not None
        and pinned_commit_id
        != service_package.service_config_object_instance_graph_commit_id
    ):
        raise RuntimeError(
            "Service runtime package ref semantic_root_object_instance_graph_commit_id "
            "does not match ServicePackage pin: "
            f"ref={pinned_commit_id} "
            f"service_package={service_package.service_config_object_instance_graph_commit_id}"
        )


def _validate_service_config_ref_pair(
    *,
    package_ref: ServiceRuntimePackageRef,
    service_package: ServicePackage,
    service_config: ServiceConfig,
) -> None:
    if service_config.id != service_package.service_config_id:
        raise RuntimeError(
            "ServicePackage points at a different ServiceConfig than the "
            f"hydrated service root: package={service_package.service_config_id} "
            f"service_config={service_config.id}"
        )
    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    semantic_root_id = _optional_uuid(package_ref.semantic_root_id)
    if semantic_root_id is None:
        return
    expected_root_id = (
        service_config.id
        if semantic_root_kind == "service_config"
        else service_package.id
    )
    if semantic_root_id != expected_root_id:
        raise RuntimeError(
            "Service runtime package ref semantic_root_id does not match "
            f"{semantic_root_kind or 'service_package'} root: "
            f"ref={semantic_root_id} expected={expected_root_id}"
        )


async def _service_config_domain_commit_ref_from_package(
    *,
    index: MetaGraphRuntimeIndex,
    store: FSCommitStore,
    service_package: ServicePackage,
    branch_id: UUID,
    preferred_projection_hash: str,
) -> tuple[str, UUID] | None:
    service_config_commit = service_package.service_config_object_instance_graph_commit
    if (
        service_config_commit is not None
        and service_config_commit.commit_id is not None
    ):
        return preferred_projection_hash, service_config_commit.commit_id
    pinned_commit_id = service_package.service_config_object_instance_graph_commit_id
    if pinned_commit_id is None:
        return None
    matches: list[tuple[str, UUID]] = []
    for projection_hash in _candidate_projection_hashes_by_name(
        index=index,
        projection_name="ServiceConfig",
        preferred_projection_hash=preferred_projection_hash,
    ):
        domain_commit_id = (
            await store.domain_commit_id_for_object_instance_graph_commit_id(
                branch_id=branch_id,
                projection_hash=projection_hash,
                object_instance_graph_commit_id=pinned_commit_id,
            )
        )
        if domain_commit_id is not None:
            matches.append((projection_hash, domain_commit_id))
    if len(matches) > 1:
        raise RuntimeError(
            "Service runtime package ref service_config_object_instance_graph_commit_id "
            "resolved to multiple ServiceConfig projections: "
            f"service_package={service_package.id} "
            f"service_config_object_instance_graph_commit_id={pinned_commit_id} "
            f"matches={matches!r}"
        )
    return matches[0] if matches else None


def _candidate_projection_hashes_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
    preferred_projection_hash: str,
) -> tuple[str, ...]:
    projection_token = projection_name.strip()
    candidates: list[str] = [preferred_projection_hash]
    candidates.extend(
        projection_hash
        for projection_hash, opg in sorted(
            index.opg_by_hash.items(),
            key=lambda item: item[0],
        )
        if (opg.name or "").strip() == projection_token
    )
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        deduped.append(candidate)
        seen.add(candidate)
    return tuple(deduped)


async def _hydrate_root_from_commit(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    root_id: UUID,
    root_type: type[_TRoot],
    hydrate_portal_targets: bool,
    store: FSCommitStore,
) -> _TRoot | None:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"Service runtime package ref missing projection hash: {projection_hash}"
        )
    oig, _ = await CachedLaneMaterializer(commits=store).get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=commit_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_root_model(
        index=index,
        opg=opg,
        oig=oig,
        model_type=root_type,
        root_id=root_id,
        branch_id=branch_id,
    )


def _find_projection_hash_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> str:
    target = (projection_name or "").strip()
    for opg in index.ocg.object_projection_graphs:
        name = (opg.name or "").strip()
        if name == target:
            return opg.projection_hash
    raise ValueError(
        f"Projection {projection_name!r} was not found in Service runtime OCG"
    )


def _relative_to_root(*, path: Path, root: Path, label: str) -> str:
    resolved_path = path.expanduser().resolve()
    resolved_root = root.expanduser().resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(
            "Service runtime package ref path resolved outside materialized "
            f"workspace root: label={label} root={resolved_root} path={resolved_path}"
        ) from exc
    return relative.as_posix() or "."


def _required_uuid(value: str | UUID | None, *, label: str) -> UUID:
    parsed = _optional_uuid(value)
    if parsed is None:
        raise RuntimeError(f"Service runtime package ref requires {label}.")
    return parsed


def _optional_uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    stripped = value.strip()
    if not stripped:
        return None
    return UUID(stripped)


def _required_text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"ServicePackage dependency payload requires {label}.")
    return value.strip()


def _optional_int(value: object, *, label: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise RuntimeError(
            f"ServicePackage dependency payload {label} must be an integer."
        )
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        return int(value)
    raise RuntimeError(f"ServicePackage dependency payload {label} must be an integer.")


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "ResolvedServiceRuntimePackageRef",
    "ServiceRuntimePackageDependency",
    "ServiceRuntimePackageRef",
    "resolve_committed_service_runtime_package_ref",
    "resolve_committed_service_runtime_package_refs",
    "resolve_service_runtime_package_ref",
    "resolve_service_runtime_package_ref_from_manifest_path",
    "resolve_service_runtime_package_refs",
    "resolve_service_runtime_package_refs_from_manifest_paths",
]
