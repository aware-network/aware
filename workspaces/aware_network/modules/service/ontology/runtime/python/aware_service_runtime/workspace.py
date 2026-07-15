from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
from aware_service_runtime.manifest.spec import (
    AwareServiceCompilationMode,
    AwareServiceDependencyKind,
    AwareServiceHostActivationMode,
    AwareServiceImplementationLanguage,
    AwareServiceImplementationRole,
    AwareServiceTomlBuildSpec,
    AwareServiceTomlDependencySpec,
    AwareServiceTomlHostSpec,
    AwareServiceTomlImplementationPackageSpec,
    AwareServiceTomlImplementationSpec,
    AwareServiceTomlPackageSpec,
    AwareServiceTomlRouteAuthoritySelectorSpec,
    AwareServiceTomlSpec,
)
from aware_service_ontology.service.service_package import ServicePackage


@dataclass(frozen=True, slots=True)
class ServiceWorkspaceSnapshot:
    repo_root: Path
    package_root: Path
    spec_path: Path
    spec: AwareServiceTomlSpec
    source_files: tuple[Path, ...]


class ServiceWorkspace:
    _spec_path: Path
    _package_root: Path
    _repo_root: Path

    def __init__(self, *, spec_path: str | Path, repo_root: str | Path | None = None):
        resolved_spec_path = Path(spec_path).resolve()
        if not resolved_spec_path.exists():
            raise FileNotFoundError(
                f"aware.service.toml not found: {resolved_spec_path}"
            )
        self._spec_path = resolved_spec_path
        self._package_root = resolved_spec_path.parent
        if repo_root is None:
            self._repo_root = _resolve_repo_root(start=self._package_root)
        else:
            self._repo_root = Path(repo_root).resolve()

    @classmethod
    def from_toml(
        cls, *, toml_path: str | Path, repo_root: str | Path | None = None
    ) -> ServiceWorkspace:
        return cls(spec_path=toml_path, repo_root=repo_root)

    @property
    def spec_path(self) -> Path:
        return self._spec_path

    @property
    def package_root(self) -> Path:
        return self._package_root

    @property
    def repo_root(self) -> Path:
        return self._repo_root

    def build_snapshot(self) -> ServiceWorkspaceSnapshot:
        spec = load_aware_service_toml_spec(toml_path=self._spec_path)

        sources_root = (self._package_root / spec.build.sources_dir).resolve()
        _assert_within(
            base=self._package_root, candidate=sources_root, label="[build].sources_dir"
        )
        if not sources_root.exists():
            raise FileNotFoundError(
                f"Service sources_dir does not exist: {sources_root} (from {self._spec_path})"
            )
        if not sources_root.is_dir():
            raise NotADirectoryError(
                f"Service sources_dir must be a directory: {sources_root}"
            )

        files_by_rel: dict[str, Path] = {}
        for include in spec.build.include_paths:
            pattern = (include or "").strip()
            if not pattern:
                continue
            for candidate in sources_root.glob(pattern):
                if not candidate.is_file():
                    continue
                resolved = candidate.resolve()
                _assert_within(
                    base=sources_root, candidate=resolved, label="include_paths"
                )
                rel_from_sources = resolved.relative_to(sources_root).as_posix()
                if _is_excluded(
                    rel_path=rel_from_sources, exclude_patterns=spec.build.exclude_paths
                ):
                    continue
                rel_from_package = resolved.relative_to(self._package_root).as_posix()
                files_by_rel[rel_from_package] = Path(rel_from_package)

        ordered_source_files = tuple(files_by_rel[key] for key in sorted(files_by_rel))

        return ServiceWorkspaceSnapshot(
            repo_root=self._repo_root,
            package_root=self._package_root,
            spec_path=self._spec_path,
            spec=spec,
            source_files=ordered_source_files,
        )


def build_service_workspace_snapshot_from_package(
    *,
    service_package: ServicePackage,
    materialized_workspace_root: str | Path,
) -> ServiceWorkspaceSnapshot:
    """Build a service compile snapshot from committed ServicePackage truth."""

    repo_root = Path(materialized_workspace_root).expanduser().resolve()
    package_root = _resolve_relative_root(
        root=repo_root,
        raw=service_package.package_root,
        label="ServicePackage.package_root",
    )
    sources_root = _resolve_service_sources_root(
        repo_root=repo_root,
        package_root=package_root,
        raw_sources_root=service_package.sources_root,
    )
    sources_dir = sources_root.relative_to(package_root).as_posix()
    spec = AwareServiceTomlSpec(
        aware_service=int(service_package.aware_service_version),
        service=AwareServiceTomlPackageSpec(
            package_name=service_package.name,
            fqn_prefix=service_package.fqn_prefix or "",
            version_number=int(service_package.version_number),
            title=service_package.title,
            description=service_package.description,
        ),
        build=AwareServiceTomlBuildSpec(
            sources_dir=sources_dir,
            include_paths=_string_list_or_default(
                service_package.include_paths,
                default=("**/*.aware",),
            ),
            exclude_paths=_string_list_or_default(
                service_package.exclude_paths,
                default=(),
            ),
            force_fresh_scan=bool(service_package.force_fresh_scan),
            compilation_mode=AwareServiceCompilationMode(
                service_package.compilation_mode
            ),
        ),
        host=AwareServiceTomlHostSpec(
            service_surface=service_package.service_surface,
            activation_mode=AwareServiceHostActivationMode(
                service_package.activation_mode
            ),
            materialize_on_start=bool(service_package.materialize_on_start),
        ),
        dependencies=[
            _dependency_spec_from_payload(item)
            for item in _json_object_list(service_package.dependencies)
        ],
        implementation=_implementation_spec_from_service_package(service_package),
    )
    return ServiceWorkspaceSnapshot(
        repo_root=repo_root,
        package_root=package_root,
        spec_path=_committed_service_package_spec_path(
            repo_root=repo_root,
            package_root=package_root,
            service_package=service_package,
        ),
        spec=spec,
        source_files=_resolve_source_files(
            package_root=package_root,
            sources_root=sources_root,
            include_paths=spec.build.include_paths,
            exclude_paths=spec.build.exclude_paths,
        ),
    )


def _resolve_repo_root(*, start: Path) -> Path:
    cursor = start.resolve()
    for candidate in [cursor, *cursor.parents]:
        if (candidate / "aware.workspace.toml").exists():
            return candidate
    for candidate in [cursor, *cursor.parents]:
        if _revision_filesystem_manifest_path(candidate).exists():
            return candidate
    for candidate in [cursor, *cursor.parents]:
        if (candidate / "aware.environment.toml").exists():
            return candidate
    return cursor


def _revision_filesystem_manifest_path(workspace_root: Path) -> Path:
    return workspace_root / ".aware" / "workspace" / "revision-filesystem.manifest.json"


def _resolve_relative_root(*, root: Path, raw: object, label: str) -> Path:
    token = str(raw or ".").strip() or "."
    path = Path(token).expanduser()
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve()
    _assert_within(base=root, candidate=resolved, label=label)
    if not resolved.exists():
        raise FileNotFoundError(f"{label} does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"{label} must be a directory: {resolved}")
    return resolved


def _resolve_service_sources_root(
    *,
    repo_root: Path,
    package_root: Path,
    raw_sources_root: object,
) -> Path:
    token = str(raw_sources_root or "services").strip() or "services"
    candidates: list[Path] = []
    path = Path(token).expanduser()
    if path.is_absolute():
        candidates.append(path)
    else:
        candidates.append(repo_root / path)
        candidates.append(package_root / path)
    for candidate in candidates:
        resolved = candidate.resolve()
        try:
            _assert_within(
                base=package_root,
                candidate=resolved,
                label="ServicePackage.sources_root",
            )
        except ValueError:
            continue
        if not resolved.exists():
            continue
        if not resolved.is_dir():
            raise NotADirectoryError(
                f"ServicePackage.sources_root must be a directory: {resolved}"
            )
        return resolved
    raise FileNotFoundError(
        "ServicePackage.sources_root does not resolve to an existing directory "
        f"inside package_root: package_root={package_root} sources_root={token!r}"
    )


def _committed_service_package_spec_path(
    *,
    repo_root: Path,
    package_root: Path,
    service_package: ServicePackage,
) -> Path:
    raw_manifest_path = str(service_package.manifest_relative_path or "").strip()
    if raw_manifest_path:
        path = Path(raw_manifest_path).expanduser()
        if not path.is_absolute():
            path = repo_root / path
        return path.resolve()
    return (package_root / "aware.service.toml").resolve()


def _resolve_source_files(
    *,
    package_root: Path,
    sources_root: Path,
    include_paths: list[str],
    exclude_paths: list[str],
) -> tuple[Path, ...]:
    files_by_rel: dict[str, Path] = {}
    for include in include_paths:
        pattern = (include or "").strip()
        if not pattern:
            continue
        for candidate in sources_root.glob(pattern):
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            _assert_within(
                base=sources_root,
                candidate=resolved,
                label="ServicePackage.include_paths",
            )
            rel_from_sources = resolved.relative_to(sources_root).as_posix()
            if _is_excluded(rel_path=rel_from_sources, exclude_patterns=exclude_paths):
                continue
            rel_from_package = resolved.relative_to(package_root).as_posix()
            files_by_rel[rel_from_package] = Path(rel_from_package)
    return tuple(files_by_rel[key] for key in sorted(files_by_rel))


def _string_list_or_default(value: object, *, default: tuple[str, ...]) -> list[str]:
    if not isinstance(value, list):
        return list(default)
    out = [str(item).strip() for item in value if str(item or "").strip()]
    return out or list(default)


def _json_object_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _dependency_spec_from_payload(
    payload: dict[str, object],
) -> AwareServiceTomlDependencySpec:
    package_name = str(payload.get("package_name") or "").strip()
    if not package_name:
        raise RuntimeError("ServicePackage dependency requires package_name.")
    kind = str(payload.get("kind") or AwareServiceDependencyKind.package.value).strip()
    version_number = payload.get("version_number")
    expected_hash_sha256 = payload.get("expected_hash_sha256")
    return AwareServiceTomlDependencySpec(
        package_name=package_name,
        version_number=(
            int(version_number)
            if isinstance(version_number, int)
            or (isinstance(version_number, str) and version_number.strip())
            else None
        ),
        kind=AwareServiceDependencyKind(kind),
        expected_hash_sha256=(
            str(expected_hash_sha256) if expected_hash_sha256 is not None else None
        ),
        route_authority_selector=_route_authority_selector_spec_from_payload(
            payload.get("route_authority_selector")
        ),
    )


def _route_authority_selector_spec_from_payload(
    payload: object,
) -> AwareServiceTomlRouteAuthoritySelectorSpec | None:
    if not isinstance(payload, dict):
        return None
    provider_set_id = payload.get("provider_set_id")
    workspace_revision_id = payload.get("workspace_revision_id")
    workspace_deployment_revision_id = payload.get("workspace_deployment_revision_id")
    workspace_deployment_channel = payload.get("workspace_deployment_channel")
    workspace_deployment_artifact_key = payload.get("workspace_deployment_artifact_key")
    selector = AwareServiceTomlRouteAuthoritySelectorSpec(
        provider_set_id=(
            str(provider_set_id).strip() if provider_set_id is not None else None
        ),
        workspace_revision_id=(
            str(workspace_revision_id).strip()
            if workspace_revision_id is not None
            else None
        ),
        workspace_deployment_revision_id=(
            str(workspace_deployment_revision_id).strip()
            if workspace_deployment_revision_id is not None
            else None
        ),
        workspace_deployment_channel=(
            str(workspace_deployment_channel).strip()
            if workspace_deployment_channel is not None
            else None
        ),
        workspace_deployment_artifact_key=(
            str(workspace_deployment_artifact_key).strip()
            if workspace_deployment_artifact_key is not None
            else None
        ),
    )
    return None if selector.is_empty else selector


def _implementation_spec_from_service_package(
    service_package: ServicePackage,
) -> AwareServiceTomlImplementationSpec:
    packages: list[AwareServiceTomlImplementationPackageSpec] = []
    service_package_root = str(service_package.package_root or ".").strip() or "."
    for package in service_package.implementation_packages:
        package_name = str(package.package_name or "").strip()
        language = _enum_value_text(package.language)
        import_root = str(package.import_root or "").strip()
        manifest_relative_path = str(package.manifest_relative_path or "").strip()
        if (
            not package_name
            or not language
            or not import_root
            or not manifest_relative_path
        ):
            raise RuntimeError(
                "Committed ServicePackage implementation package is missing "
                "required contract payload: "
                f"service_package_id={service_package.id} bridge_id={package.id}"
            )
        role = str(package.role or "service_bindings").strip() or "service_bindings"
        package_root = str(package.package_root or ".").strip() or "."
        packages.append(
            AwareServiceTomlImplementationPackageSpec(
                package_name=package_name,
                language=AwareServiceImplementationLanguage(language),
                import_root=import_root,
                manifest_path=_manifest_path_relative_to_package_root(
                    package_root=package_root,
                    manifest_relative_path=manifest_relative_path,
                ),
                package_root=_package_root_relative_to_service_package(
                    service_package_root=service_package_root,
                    implementation_package_root=package_root,
                ),
                entrypoint=(
                    str(package.entrypoint).strip() if package.entrypoint else None
                ),
                role=AwareServiceImplementationRole(role),
                include_paths=_string_list_or_default(
                    package.include_paths, default=()
                ),
                exclude_paths=_string_list_or_default(
                    package.exclude_paths, default=()
                ),
            )
        )
    return AwareServiceTomlImplementationSpec(packages=packages)


def _enum_value_text(value: object) -> str:
    raw_value = getattr(value, "value", value)
    return str(raw_value or "").strip()


def _manifest_path_relative_to_package_root(
    *,
    package_root: str,
    manifest_relative_path: str,
) -> str:
    package_root_path = PurePosixPath(package_root or ".")
    manifest_path = PurePosixPath(manifest_relative_path)
    try:
        return manifest_path.relative_to(package_root_path).as_posix()
    except ValueError:
        return manifest_path.as_posix()


def _package_root_relative_to_service_package(
    *,
    service_package_root: str,
    implementation_package_root: str,
) -> str:
    service_path = PurePosixPath(service_package_root or ".")
    implementation_path = PurePosixPath(implementation_package_root or ".")
    if implementation_path == service_path:
        return "."
    try:
        return implementation_path.relative_to(service_path).as_posix()
    except ValueError as exc:
        raise RuntimeError(
            "Committed ServicePackage implementation package_root must be within "
            "the ServicePackage package_root: "
            f"service_package_root={service_path.as_posix()!r} "
            f"implementation_package_root={implementation_path.as_posix()!r}"
        ) from exc


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}"
    )


def _is_excluded(*, rel_path: str, exclude_patterns: list[str]) -> bool:
    token = PurePosixPath(rel_path)
    for raw_pattern in exclude_patterns:
        pattern = (raw_pattern or "").strip()
        if pattern and token.match(pattern):
            return True
    return False


__all__ = [
    "ServiceWorkspace",
    "ServiceWorkspaceSnapshot",
    "build_service_workspace_snapshot_from_package",
]
