from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import tomllib

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_package import (
    SemanticPackageDescriptor,
    SemanticPackageProvider,
    SemanticPackageRegistry,
)

from .semantic_contract import AWARE_SDK_SEMANTIC_CONTRACT

SDK_WORKSPACE_MATERIALIZATION_ORDER = 250


class _SdkSemanticPackageProvider(SemanticPackageProvider):
    @property
    def provider_key(self) -> str:
        return "aware_sdk"

    def resolve(self, code_package: CodePackageInfo) -> tuple[SemanticPackageDescriptor, ...]:
        if code_package.metadata.get("manifest_kind") != "aware_sdk_toml":
            return ()
        metadata = dict(code_package.metadata)
        metadata.update(
            {
                "fqn_prefix": code_package.metadata.get("fqn_prefix"),
                "package_kind": code_package.metadata.get("package_kind"),
                "workspace_materialization_primary": True,
                "workspace_materialization_order": (
                    SDK_WORKSPACE_MATERIALIZATION_ORDER
                ),
                "workspace_materialization_branch": "semantic",
                "workspace_materialization_commit": True,
                "semantic_projection_name": "SdkPackage",
                "semantic_root_kind": "sdk_config",
            }
        )
        return (
            SemanticPackageDescriptor(
                provider_key=self.provider_key,
                family="sdk",
                semantic_kind="sdk_package",
                package_name=code_package.name,
                manifest_relative_path=code_package.manifest_path.as_posix(),
                metadata=metadata,
                semantic_scope_keys=AWARE_SDK_SEMANTIC_CONTRACT.semantic_scope_keys,
                capability_participation=AWARE_SDK_SEMANTIC_CONTRACT.capability_participation,
                capability_profiles=AWARE_SDK_SEMANTIC_CONTRACT.capability_profiles,
                capability_bundles=AWARE_SDK_SEMANTIC_CONTRACT.capability_bundles,
            ),
        )


def sdk_semantic_package_metadata(
    *,
    workspace_root: Path,
    package_root: Path,
    manifest_path: Path,
    manifest_spec: object,
    descriptor: object | None = None,
    metadata: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Derive SDK public code package declarations from `aware.sdk.toml`.

    The SDK manifest owns the public package target location, while the target
    package manager manifest owns the installable distribution name.
    """

    _ = (descriptor, metadata)
    sdk_root = _sdk_root_for_manifest(
        package_root=package_root,
        manifest_path=manifest_path,
    )
    targets: list[dict[str, object]] = []
    blockers: list[str] = []
    python_target = getattr(getattr(manifest_spec, "targets", None), "python", None)
    if python_target is not None:
        python_payload = _python_public_package_target_payload(
            workspace_root=workspace_root,
            sdk_root=sdk_root,
            manifest_path=manifest_path,
            manifest_spec=manifest_spec,
            target=python_target,
            blockers=blockers,
        )
        if python_payload is not None:
            targets.append(python_payload)

    result: dict[str, object] = {
        "package_root": _workspace_relative_path(
            workspace_root=workspace_root,
            path=sdk_root,
        ),
    }
    if targets:
        result["language_materialization_targets"] = targets
    if blockers:
        result["language_materialization_target_blockers"] = blockers
    return result


def _python_public_package_target_payload(
    *,
    workspace_root: Path,
    sdk_root: Path,
    manifest_path: Path,
    manifest_spec: object,
    target: object,
    blockers: list[str],
) -> dict[str, object] | None:
    language_root = sdk_root / (_target_text(target, "root_dir") or "python")
    public_package = getattr(target, "public_package", None)
    package_root = language_root / (_target_text(public_package, "root_dir") or ".")
    package_dir = (
        _target_text(public_package, "package_dir")
        or _target_text(getattr(manifest_spec, "sdk", None), "fqn_prefix")
    )
    if package_dir is None:
        blockers.append(
            _sdk_target_blocker(
                manifest_path=manifest_path,
                reason="targets.python.public_package.package_dir_missing",
            )
        )
        return None
    manifest = package_root / "pyproject.toml"
    if not manifest.is_file():
        blockers.append(
            _sdk_target_blocker(
                manifest_path=manifest_path,
                reason="targets.python.pyproject_toml_missing",
                path=manifest,
            )
        )
        return None
    sources_root = package_root / package_dir
    if not sources_root.is_dir():
        blockers.append(
            _sdk_target_blocker(
                manifest_path=manifest_path,
                reason="targets.python.public_package.package_dir_missing",
                path=sources_root,
            )
        )
        return None
    package_name = _pyproject_project_name(manifest)
    if package_name is None:
        blockers.append(
            _sdk_target_blocker(
                manifest_path=manifest_path,
                reason="targets.python.pyproject_name_missing",
                path=manifest,
            )
        )
        return None
    return {
        "role": "public_package",
        "language": "python",
        "output_dir": _workspace_relative_path(
            workspace_root=sdk_root,
            path=package_root,
        ),
        "import_root": package_dir.replace("/", "."),
        "package_name": package_name,
        "materialization_source": "sdk",
        "code_package_surface": "sdk",
    }


def _sdk_root_for_manifest(*, package_root: Path, manifest_path: Path) -> Path:
    resolved_manifest_parent = manifest_path.resolve().parent
    if resolved_manifest_parent.name == "aware":
        return resolved_manifest_parent.parent
    return package_root.resolve()


def _target_text(target: object | None, attribute_name: str) -> str | None:
    value = getattr(target, attribute_name, None)
    if not isinstance(value, str):
        return None
    normalized = value.strip().replace("\\", "/").strip("/")
    return normalized or None


def _pyproject_project_name(manifest_path: Path) -> str | None:
    try:
        payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    project = payload.get("project")
    if not isinstance(project, dict):
        return None
    name = project.get("name")
    if not isinstance(name, str):
        return None
    normalized = name.strip()
    return normalized or None


def _workspace_relative_path(*, workspace_root: Path, path: Path) -> str:
    return path.resolve().relative_to(workspace_root.resolve()).as_posix()


def _sdk_target_blocker(
    *,
    manifest_path: Path,
    reason: str,
    path: Path | None = None,
) -> str:
    if path is None:
        return f"{manifest_path.as_posix()}: {reason}"
    return f"{manifest_path.as_posix()}: {reason}: {path.as_posix()}"


_PROVIDER = _SdkSemanticPackageProvider()


def register_semantic_package_providers() -> None:
    SemanticPackageRegistry.register(_PROVIDER)


__all__ = [
    "AWARE_SDK_SEMANTIC_CONTRACT",
    "SDK_WORKSPACE_MATERIALIZATION_ORDER",
    "register_semantic_package_providers",
    "sdk_semantic_package_metadata",
]
