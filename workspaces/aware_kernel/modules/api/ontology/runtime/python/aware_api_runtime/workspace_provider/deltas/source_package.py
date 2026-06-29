from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
)

from aware_code.semantic_contract_config import source_code_package_config_ref
from aware_api_runtime.workspace_provider.deltas.transport import (
    authored_aware_source_delta_paths,
    code_package_delta_from_provider_delta_request,
    delta_path_has_content,
)


def api_delta_source_package_payload(
    *,
    request: object,
    snapshot: object,
    manifest_path: Path,
    package_payload: Mapping[str, object],
) -> dict[str, object]:
    source_delta = api_delta_source_package_delta_from_request(request=request)
    package_name = api_delta_package_name(
        snapshot=snapshot,
        package_payload=package_payload,
    )
    workspace_root = api_delta_snapshot_repo_root(snapshot=snapshot)
    package_root = getattr(snapshot, "package_root")
    spec = getattr(snapshot, "spec")
    sources_root = (package_root / spec.build.sources_dir).resolve()
    config_ref = source_code_package_config_ref(
        manifest_kind="aware_api_toml",
        surface="api",
    )
    return {
        "source_update_strategy": "code_package_delta",
        "source_file_count": len(source_delta.paths),
        "source_delta_path_count": len(source_delta.paths),
        "source_delta_kind_counts": api_delta_source_package_delta_kind_counts(
            delta=source_delta,
        ),
        "code_package_build_arguments": {
            "code_package_config_id": str(config_ref.config_id),
            "package_name": package_name,
            "language": CodeLanguage.aware.value,
            "surface": "api",
            "manifest_relative_path": api_delta_relative_to(
                path=manifest_path,
                root=workspace_root,
            ),
            "package_root": api_delta_relative_to(
                path=package_root,
                root=workspace_root,
            ),
            "sources_root": api_delta_relative_to(
                path=sources_root,
                root=workspace_root,
            ),
            "fqn_prefix": _optional_text(getattr(spec.api, "fqn_prefix", None)),
        },
        "code_package_apply_delta_arguments": {
            "delta": source_delta.model_dump(mode="json"),
        },
    }


def api_delta_source_package_delta_from_request(
    *,
    request: object,
) -> CodePackageDelta:
    delta = code_package_delta_from_provider_delta_request(request=request)
    source_paths = authored_aware_source_delta_paths(delta=delta)
    if not source_paths:
        raise RuntimeError(
            "API provider-delta source package apply requires transported "
            "authored .aware CodePackageDelta paths."
        )
    delete_paths = tuple(
        path
        for path in source_paths
        if _enum_value(path.kind) == CodePackageDeltaKind.delete.value
    )
    if delete_paths:
        raise RuntimeError(
            "API provider-delta source package apply requires full rebuild for "
            "delete paths until API delete/stale semantic execution is wired."
        )
    missing_content_paths = tuple(
        path.relative_path for path in source_paths if not delta_path_has_content(path)
    )
    if missing_content_paths:
        raise RuntimeError(
            "API provider-delta source package apply requires content-backed "
            "create/update paths: " + ", ".join(sorted(missing_content_paths))
        )
    return CodePackageDelta(
        package_name=delta.package_name,
        package_root=delta.package_root,
        sources_root=delta.sources_root,
        manifest_relative_path=delta.manifest_relative_path,
        authority=delta.authority,
        authority_kind=delta.authority_kind,
        source_revision_id=delta.source_revision_id,
        production=delta.production,
        paths=list(source_paths),
        warnings=list(delta.warnings),
    )


def api_delta_source_package_delta_kind_counts(
    *,
    delta: CodePackageDelta,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in delta.paths:
        kind = _enum_value(path.kind)
        counts[kind] = counts.get(kind, 0) + 1
    return dict(sorted(counts.items()))


def api_delta_package_name(
    *,
    snapshot: object,
    package_payload: Mapping[str, object],
) -> str:
    package_name = _optional_text(package_payload.get("package_name"))
    if package_name is not None:
        return package_name
    spec = getattr(snapshot, "spec")
    package_name = _optional_text(getattr(spec.api, "package_name", None))
    if package_name is None:
        raise RuntimeError(
            "API provider-delta package operation requires package_name."
        )
    return package_name


def api_delta_snapshot_repo_root(*, snapshot: object) -> Path:
    repo_root = getattr(snapshot, "repo_root", None)
    if isinstance(repo_root, Path):
        return repo_root.resolve()
    return Path(str(repo_root)).resolve()


def api_delta_relative_to(*, path: Path, root: Path) -> str:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return resolved_path.as_posix()


def _enum_value(value: object) -> str:
    raw_value = getattr(value, "value", value)
    return str(raw_value or "").strip()


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "api_delta_package_name",
    "api_delta_relative_to",
    "api_delta_snapshot_repo_root",
    "api_delta_source_package_delta_from_request",
    "api_delta_source_package_delta_kind_counts",
    "api_delta_source_package_payload",
]
