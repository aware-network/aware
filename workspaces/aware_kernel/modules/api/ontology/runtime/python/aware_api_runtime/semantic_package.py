from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import tomllib

from aware_api_runtime.semantic_contract import (
    API_DIAGNOSTICS_CAPABILITY_PARTICIPATION,
    API_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION,
)


API_WORKSPACE_MATERIALIZATION_ORDER = 100


def api_semantic_package_metadata(
    *,
    workspace_root: Path,
    package_root: Path,
    manifest_path: Path,
    manifest_spec: object,
    descriptor: object | None = None,
    metadata: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Derive API-generated Python package declarations from `aware.api.toml`."""

    _ = (descriptor, metadata)
    api_root = package_root.resolve()
    targets: list[dict[str, object]] = []
    blockers: list[str] = []
    python_target = getattr(getattr(manifest_spec, "targets", None), "python", None)
    if python_target is not None:
        for role, product_target, fallback_import_root in (
            (
                "public_package",
                getattr(python_target, "public_package", None),
                _api_fqn_prefix(manifest_spec=manifest_spec),
            ),
            (
                "service_protocol_package",
                getattr(python_target, "service_protocol", None),
                _service_protocol_import_root(
                    public_import_root=_api_fqn_prefix(manifest_spec=manifest_spec)
                ),
            ),
        ):
            payload = _python_product_package_target_payload(
                workspace_root=workspace_root,
                api_root=api_root,
                manifest_path=manifest_path,
                python_target=python_target,
                product_target=product_target,
                role=role,
                fallback_import_root=fallback_import_root,
                blockers=blockers,
            )
            if payload is not None:
                targets.append(payload)

    for export in getattr(manifest_spec, "semantic_package_exports", ()):
        payload = _python_semantic_export_package_target_payload(
            workspace_root=workspace_root,
            api_root=api_root,
            manifest_path=manifest_path,
            export=export,
            blockers=blockers,
        )
        if payload is not None:
            targets.append(payload)

    result: dict[str, object] = {
        "package_root": _workspace_relative_path(
            workspace_root=workspace_root,
            path=api_root,
        ),
    }
    if targets:
        result["language_materialization_targets"] = targets
    if blockers:
        result["language_materialization_target_blockers"] = blockers
    return result


def _python_product_package_target_payload(
    *,
    workspace_root: Path,
    api_root: Path,
    manifest_path: Path,
    python_target: object,
    product_target: object | None,
    role: str,
    fallback_import_root: str,
    blockers: list[str],
) -> dict[str, object] | None:
    language_root = _target_text(python_target, "root_dir") or "python"
    output_dir = _target_text(product_target, "root_dir")
    if output_dir is None:
        package_dir = _target_text(product_target, "package_dir") or fallback_import_root
        output_dir = _join_repo_path(language_root, package_dir)
    package_root = api_root / output_dir
    return _python_package_target_payload(
        workspace_root=workspace_root,
        package_root=package_root,
        output_dir=output_dir,
        import_root=_first_package_dir_component(package_root=package_root),
        role=role,
        materialization_source="api",
        code_package_surface="api",
        manifest_path=manifest_path,
        blockers=blockers,
    )


def _python_semantic_export_package_target_payload(
    *,
    workspace_root: Path,
    api_root: Path,
    manifest_path: Path,
    export: object,
    blockers: list[str],
) -> dict[str, object] | None:
    if str(getattr(export, "kind", "")).split(".")[-1] != "api_dto":
        return None
    export_manifest_path = _target_attr_text(export, "manifest_path")
    if export_manifest_path is None:
        blockers.append(
            _api_target_blocker(
                manifest_path=manifest_path,
                reason="semantic_package_exports.api_dto.manifest_path_missing",
            )
        )
        return None
    export_manifest = api_root / export_manifest_path
    dto_import_root = _aware_toml_fqn_prefix(export_manifest) or _package_name_token(
        _target_attr_text(export, "package_name")
    )
    if dto_import_root is None:
        blockers.append(
            _api_target_blocker(
                manifest_path=manifest_path,
                reason="semantic_package_exports.api_dto.fqn_prefix_missing",
                path=export_manifest,
            )
        )
        return None
    output_dir = _join_repo_path("python", dto_import_root)
    package_root = api_root / output_dir
    return _python_package_target_payload(
        workspace_root=workspace_root,
        package_root=package_root,
        output_dir=output_dir,
        import_root=dto_import_root,
        role="api_dto",
        materialization_source="api",
        code_package_surface="api",
        manifest_path=manifest_path,
        blockers=blockers,
    )


def _python_package_target_payload(
    *,
    workspace_root: Path,
    package_root: Path,
    output_dir: str,
    import_root: str | None,
    role: str,
    materialization_source: str,
    code_package_surface: str,
    manifest_path: Path,
    blockers: list[str],
) -> dict[str, object] | None:
    manifest = package_root / "pyproject.toml"
    if not manifest.is_file():
        blockers.append(
            _api_target_blocker(
                manifest_path=manifest_path,
                reason=f"{role}.pyproject_toml_missing",
                path=manifest,
            )
        )
        return None
    package_name = _pyproject_project_name(manifest)
    if package_name is None:
        blockers.append(
            _api_target_blocker(
                manifest_path=manifest_path,
                reason=f"{role}.pyproject_name_missing",
                path=manifest,
            )
        )
        return None
    resolved_import_root = import_root or _first_package_dir_component(
        package_root=package_root
    )
    if resolved_import_root is None:
        blockers.append(
            _api_target_blocker(
                manifest_path=manifest_path,
                reason=f"{role}.import_root_missing",
                path=package_root,
            )
        )
        return None
    return {
        "role": role,
        "language": "python",
        "output_dir": output_dir,
        "import_root": resolved_import_root.replace("/", "."),
        "package_name": package_name,
        "materialization_source": materialization_source,
        "code_package_surface": code_package_surface,
    }


def _api_fqn_prefix(*, manifest_spec: object) -> str:
    api = getattr(manifest_spec, "api", None)
    token = _target_attr_text(api, "fqn_prefix") or _target_attr_text(
        api, "package_name"
    )
    return _package_name_token(token) or "aware_api_public_package"


def _service_protocol_import_root(*, public_import_root: str) -> str:
    token = public_import_root
    if token.endswith("_api"):
        token = token[: -len("_api")]
    token = token.strip("_")
    return f"{token}_protocol" if token else "aware_api_protocol"


def _aware_toml_fqn_prefix(manifest: Path) -> str | None:
    try:
        payload = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    package = payload.get("package")
    if not isinstance(package, dict):
        return None
    return _target_text_from_mapping(package, "fqn_prefix")


def _pyproject_project_name(manifest: Path) -> str | None:
    try:
        payload = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    project = payload.get("project")
    if not isinstance(project, dict):
        return None
    return _target_text_from_mapping(project, "name")


def _first_package_dir_component(*, package_root: Path) -> str | None:
    for child in sorted(package_root.iterdir() if package_root.is_dir() else ()):
        if child.is_dir() and (child / "__init__.py").is_file():
            return child.name
    return None


def _target_text(target: object | None, attribute_name: str) -> str | None:
    if target is None:
        return None
    return _normalize_path_text(getattr(target, attribute_name, None))


def _target_attr_text(target: object | None, attribute_name: str) -> str | None:
    if target is None:
        return None
    value = getattr(target, attribute_name, None)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _target_text_from_mapping(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_path_text(value: object | None) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().replace("\\", "/").strip("/")
    return normalized or None


def _package_name_token(value: str | None) -> str | None:
    if value is None:
        return None
    token = value.strip().replace("-", "_").strip("_")
    return token or None


def _join_repo_path(*parts: str) -> str:
    normalized_parts = [
        part.strip().strip("/")
        for part in parts
        if part.strip().strip("/")
    ]
    return "/".join(normalized_parts) or "."


def _workspace_relative_path(*, workspace_root: Path, path: Path) -> str:
    return path.resolve().relative_to(workspace_root.resolve()).as_posix()


def _api_target_blocker(
    *,
    manifest_path: Path,
    reason: str,
    path: Path | None = None,
) -> str:
    if path is None:
        return f"{manifest_path.as_posix()}: {reason}"
    return f"{manifest_path.as_posix()}: {reason}: {path.as_posix()}"


__all__ = [
    "API_DIAGNOSTICS_CAPABILITY_PARTICIPATION",
    "API_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION",
    "API_WORKSPACE_MATERIALIZATION_ORDER",
    "api_semantic_package_metadata",
]
