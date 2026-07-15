from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import tomllib


MODULE_API_OWNER = "module_api"
API_DTO_OWNER = "api_dto"
UNKNOWN_OWNER = "unknown"
_SELECTED_KERNEL_WORKSPACE_TOML = Path(
    "workspaces/aware_kernel/aware.workspace.toml",
)


class ApiDtoOwnershipViolation(RuntimeError):
    """Raised when a claimed API cutover still depends on module API DTOs."""


@dataclass(frozen=True, slots=True)
class ModuleApiPackage:
    module_id: str
    package_name: str
    fqn_prefix: str | None
    manifest_path: str
    source_paths: tuple[str, ...]

    @property
    def source_count(self) -> int:
        return len(self.source_paths)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "module_id": self.module_id,
            "package_name": self.package_name,
            "fqn_prefix": self.fqn_prefix,
            "manifest_path": self.manifest_path,
            "source_count": self.source_count,
            "source_paths": list(self.source_paths),
        }


@dataclass(frozen=True, slots=True)
class ApiOwnedDtoPackage:
    package_name: str
    fqn_prefix: str | None
    manifest_path: str

    def to_json_dict(self) -> dict[str, object]:
        return {
            "package_name": self.package_name,
            "fqn_prefix": self.fqn_prefix,
            "manifest_path": self.manifest_path,
        }


@dataclass(frozen=True, slots=True)
class ApiDependencyEdge:
    api_package_name: str
    api_manifest_path: str
    dependency_package_name: str
    dependency_owner: str
    dependency_manifest_path: str | None

    def to_json_dict(self) -> dict[str, object]:
        return {
            "api_package_name": self.api_package_name,
            "api_manifest_path": self.api_manifest_path,
            "dependency_package_name": self.dependency_package_name,
            "dependency_owner": self.dependency_owner,
            "dependency_manifest_path": self.dependency_manifest_path,
        }


@dataclass(frozen=True, slots=True)
class ApiDtoOwnershipInventory:
    module_api_packages: tuple[ModuleApiPackage, ...]
    api_owned_dto_packages: tuple[ApiOwnedDtoPackage, ...]
    kernel_api_manifest_paths: tuple[str, ...]
    kernel_api_dependency_edges: tuple[ApiDependencyEdge, ...]

    @property
    def module_api_package_names(self) -> frozenset[str]:
        return frozenset(package.package_name for package in self.module_api_packages)

    @property
    def kernel_module_api_dependency_edges(self) -> tuple[ApiDependencyEdge, ...]:
        return tuple(
            edge
            for edge in self.kernel_api_dependency_edges
            if edge.dependency_owner == MODULE_API_OWNER
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "module_api_packages": [
                package.to_json_dict() for package in self.module_api_packages
            ],
            "api_owned_dto_packages": [
                package.to_json_dict() for package in self.api_owned_dto_packages
            ],
            "kernel_api_manifest_paths": list(self.kernel_api_manifest_paths),
            "kernel_api_dependency_edges": [
                edge.to_json_dict() for edge in self.kernel_api_dependency_edges
            ],
        }


def build_api_dto_ownership_inventory(
    repo_root: Path | str,
) -> ApiDtoOwnershipInventory:
    root = Path(repo_root)
    module_api_packages = collect_module_api_packages(root)
    api_owned_dto_packages = collect_api_owned_dto_packages(root)
    kernel_api_manifest_paths = collect_kernel_api_manifest_paths(root)
    module_api_by_name = {
        package.package_name: package for package in module_api_packages
    }
    api_dto_by_name = {
        package.package_name: package for package in api_owned_dto_packages
    }
    kernel_api_dependency_edges = tuple(
        edge
        for manifest_path in kernel_api_manifest_paths
        for edge in collect_api_dependency_edges(
            root / manifest_path,
            repo_root=root,
            module_api_packages_by_name=module_api_by_name,
            api_owned_dto_packages_by_name=api_dto_by_name,
        )
    )
    return ApiDtoOwnershipInventory(
        module_api_packages=module_api_packages,
        api_owned_dto_packages=api_owned_dto_packages,
        kernel_api_manifest_paths=kernel_api_manifest_paths,
        kernel_api_dependency_edges=kernel_api_dependency_edges,
    )


def collect_module_api_packages(repo_root: Path | str) -> tuple[ModuleApiPackage, ...]:
    root = Path(repo_root)
    packages: list[ModuleApiPackage] = []
    for manifest_path in sorted(root.glob("modules/*/structure/api/aware.toml")):
        data = _load_toml(manifest_path)
        package_data = data.get("package")
        if not isinstance(package_data, dict):
            continue
        if package_data.get("kind") != "api":
            continue
        package_name = _required_str(
            package_data.get("package_name"),
            label=f"{_repo_path(root, manifest_path)} package.package_name",
        )
        source_root = manifest_path.parent / "aware"
        source_paths = tuple(
            _repo_path(root, path)
            for path in sorted(source_root.rglob("*.aware"))
            if _is_authored_source_path(path.relative_to(source_root))
        )
        packages.append(
            ModuleApiPackage(
                module_id=manifest_path.parts[-4],
                package_name=package_name,
                fqn_prefix=_optional_str(package_data.get("fqn_prefix")),
                manifest_path=_repo_path(root, manifest_path),
                source_paths=source_paths,
            )
        )
    return tuple(sorted(packages, key=lambda package: package.package_name))


def collect_api_owned_dto_packages(
    repo_root: Path | str,
) -> tuple[ApiOwnedDtoPackage, ...]:
    root = Path(repo_root)
    manifest_paths: set[Path] = set(root.glob("apis/*/dto/aware.toml"))
    for api_manifest_path in collect_kernel_api_manifest_paths(root):
        manifest_paths.update(
            _api_manifest_exported_dto_manifest_paths(root / api_manifest_path)
        )

    packages: list[ApiOwnedDtoPackage] = []
    for manifest_path in sorted(manifest_paths):
        if not manifest_path.is_file():
            continue
        data = _load_toml(manifest_path)
        package_data = data.get("package")
        if not isinstance(package_data, dict):
            continue
        package_name = _required_str(
            package_data.get("package_name"),
            label=f"{_repo_path(root, manifest_path)} package.package_name",
        )
        packages.append(
            ApiOwnedDtoPackage(
                package_name=package_name,
                fqn_prefix=_optional_str(package_data.get("fqn_prefix")),
                manifest_path=_repo_path(root, manifest_path),
            )
        )
    return tuple(sorted(packages, key=lambda package: package.package_name))


def _api_manifest_exported_dto_manifest_paths(
    api_manifest_path: Path,
) -> tuple[Path, ...]:
    if not api_manifest_path.is_file():
        return ()
    data = _load_toml(api_manifest_path)
    exported_paths: list[Path] = []
    exports = data.get("semantic_package_exports")
    if not isinstance(exports, list):
        return ()
    for export in exports:
        if not isinstance(export, dict):
            continue
        if export.get("kind") != "api_dto":
            continue
        manifest_path = export.get("manifest_path")
        if not isinstance(manifest_path, str) or not manifest_path:
            continue
        exported_paths.append(api_manifest_path.parent / manifest_path)
    return tuple(exported_paths)


def collect_kernel_api_manifest_paths(repo_root: Path | str) -> tuple[str, ...]:
    root = Path(repo_root)
    selected_workspace_toml = root / _SELECTED_KERNEL_WORKSPACE_TOML
    if not selected_workspace_toml.is_file():
        return ()
    selected_workspace_root = selected_workspace_toml.parent
    data = _load_toml(selected_workspace_toml)
    workspace_data = data.get("workspace")
    if not isinstance(workspace_data, dict):
        return ()
    api_paths: list[str] = []
    workspace_api_paths = workspace_data.get("apis")
    if isinstance(workspace_api_paths, list):
        api_paths.extend(
            _repo_path(
                root,
                selected_workspace_root
                / _required_str(path, label="workspace.apis entry"),
            )
            for path in workspace_api_paths
        )
    module_entries = workspace_data.get("modules")
    if isinstance(module_entries, list):
        for module_entry in module_entries:
            if not isinstance(module_entry, dict):
                continue
            module_path = _required_str(
                module_entry.get("path"),
                label="workspace.modules path",
            )
            module_root = selected_workspace_root / module_path
            module_manifest = module_root / "aware.module.toml"
            api_paths.extend(_module_api_manifest_paths(root, module_manifest))
    return tuple(sorted(dict.fromkeys(api_paths)))


def _module_api_manifest_paths(
    repo_root: Path,
    module_manifest_path: Path,
) -> tuple[str, ...]:
    if not module_manifest_path.is_file():
        return ()
    data = _load_toml(module_manifest_path)
    packages = data.get("packages")
    if not isinstance(packages, list):
        return ()
    api_paths: list[str] = []
    for package in packages:
        if not isinstance(package, dict):
            continue
        if package.get("kind") != "api":
            continue
        manifest = _required_str(
            package.get("manifest"),
            label=f"{_repo_path(repo_root, module_manifest_path)} package.manifest",
        )
        api_paths.append(_repo_path(repo_root, module_manifest_path.parent / manifest))
    return tuple(api_paths)


def collect_api_dependency_edges(
    api_manifest_path: Path | str,
    *,
    repo_root: Path | str,
    module_api_packages_by_name: Mapping[str, ModuleApiPackage],
    api_owned_dto_packages_by_name: Mapping[str, ApiOwnedDtoPackage],
) -> tuple[ApiDependencyEdge, ...]:
    root = Path(repo_root)
    manifest_path = Path(api_manifest_path)
    data = _load_toml(manifest_path)
    api_data = data.get("api")
    if not isinstance(api_data, dict):
        return ()
    api_package_name = _required_str(
        api_data.get("package_name"),
        label=f"{_repo_path(root, manifest_path)} api.package_name",
    )
    edges: list[ApiDependencyEdge] = []
    dependencies = data.get("dependencies")
    if not isinstance(dependencies, list):
        return ()
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            continue
        dependency_package_name = _required_str(
            dependency.get("package_name"),
            label=f"{_repo_path(root, manifest_path)} dependency.package_name",
        )
        dependency_owner = UNKNOWN_OWNER
        dependency_manifest_path: str | None = None
        module_package = module_api_packages_by_name.get(dependency_package_name)
        api_dto_package = api_owned_dto_packages_by_name.get(dependency_package_name)
        if module_package is not None:
            dependency_owner = MODULE_API_OWNER
            dependency_manifest_path = module_package.manifest_path
        elif api_dto_package is not None:
            dependency_owner = API_DTO_OWNER
            dependency_manifest_path = api_dto_package.manifest_path
        edges.append(
            ApiDependencyEdge(
                api_package_name=api_package_name,
                api_manifest_path=_repo_path(root, manifest_path),
                dependency_package_name=dependency_package_name,
                dependency_owner=dependency_owner,
                dependency_manifest_path=dependency_manifest_path,
            )
        )
    return tuple(sorted(edges, key=_edge_sort_key))


def assert_no_module_api_dependencies_for_cutovers(
    inventory: ApiDtoOwnershipInventory,
    *,
    cutover_api_package_names: set[str] | frozenset[str],
    allowed_module_api_dependencies_by_api: (
        Mapping[str, set[str] | frozenset[str]] | None
    ) = None,
) -> None:
    allowed_by_api = allowed_module_api_dependencies_by_api or {}
    violations: list[ApiDependencyEdge] = []
    for edge in inventory.kernel_module_api_dependency_edges:
        if edge.api_package_name not in cutover_api_package_names:
            continue
        allowed_dependencies = allowed_by_api.get(edge.api_package_name, frozenset())
        if edge.dependency_package_name in allowed_dependencies:
            continue
        violations.append(edge)
    if not violations:
        return
    details = ", ".join(
        f"{edge.api_package_name}->{edge.dependency_package_name}"
        for edge in violations
    )
    raise ApiDtoOwnershipViolation(
        "API DTO cutover still depends on module-owned API DTO package(s): "
        f"{details}"
    )


def _edge_sort_key(edge: ApiDependencyEdge) -> tuple[str, str, str]:
    return (
        edge.api_package_name,
        edge.dependency_package_name,
        edge.api_manifest_path,
    )


def _load_toml(path: Path) -> dict[str, object]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _is_authored_source_path(path: Path) -> bool:
    return not any(part.startswith(".") or part.startswith("_") for part in path.parts)


def _repo_path(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _required_str(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Expected non-empty string for {label}")
    return value


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
