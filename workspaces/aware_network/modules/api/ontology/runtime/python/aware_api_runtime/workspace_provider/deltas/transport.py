from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)


def api_delta_unsupported_reason(*, request: object) -> str | None:
    raw_delta = getattr(request, "code_package_delta", None)
    if raw_delta is None:
        return "api_delta_code_package_delta_required"
    try:
        delta = code_package_delta_from_provider_delta_request(request=request)
    except Exception:
        return "api_delta_code_package_delta_invalid"
    if not delta.paths:
        return "api_delta_code_package_delta_paths_unavailable"
    source_paths = authored_aware_source_delta_paths(delta=delta)
    if not source_paths:
        return "api_delta_source_upsert_content_unavailable"
    for delta_path in source_paths:
        if _enum_value(delta_path.kind) == CodePackageDeltaKind.delete.value:
            return "api_delta_delete_requires_full_rebuild"
    if not any(delta_path_has_content(delta_path) for delta_path in source_paths):
        return "api_delta_source_upsert_content_unavailable"
    return None


def code_package_delta_from_provider_delta_request(
    *,
    request: object,
) -> CodePackageDelta:
    raw_delta = getattr(request, "code_package_delta", None)
    if raw_delta is None:
        raise ValueError("Provider-delta request requires code_package_delta")
    if isinstance(raw_delta, CodePackageDelta):
        return raw_delta
    return CodePackageDelta.model_validate(raw_delta)


def authored_aware_source_delta_paths(
    *,
    delta: CodePackageDelta,
) -> tuple[CodePackageDeltaPath, ...]:
    paths: list[CodePackageDeltaPath] = []
    manifest_relative_path = (
        Path(delta.manifest_relative_path).as_posix().strip("/")
        if delta.manifest_relative_path
        else ""
    )
    for delta_path in delta.paths:
        relative_path = Path(delta_path.relative_path).as_posix().strip("/")
        if not relative_path or relative_path == manifest_relative_path:
            continue
        path_role = _enum_value(getattr(delta_path, "path_role", None))
        if path_role and path_role != "authored_source":
            continue
        language = _enum_value(getattr(delta_path, "language", None))
        if language and language != CodeLanguage.aware.value:
            continue
        if relative_path.endswith(".aware") or language == CodeLanguage.aware.value:
            paths.append(delta_path)
    return tuple(paths)


def delta_path_has_content(delta_path: object) -> bool:
    if getattr(delta_path, "content_text", None) is not None:
        return True
    content_plan = getattr(delta_path, "content_plan", None)
    return getattr(content_plan, "content_text", None) is not None


def top_changed_path_payloads(*, request: object) -> tuple[dict[str, object], ...]:
    hints = getattr(request, "delta_cause_hints", None)
    raw_paths = getattr(hints, "top_changed_paths", ())
    if not isinstance(raw_paths, (list, tuple)):
        return ()
    return tuple(_model_payload(path) for path in raw_paths)


def _enum_value(value: object) -> str:
    raw_value = getattr(value, "value", value)
    return str(raw_value or "").strip()


def _model_payload(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="json")
        if isinstance(payload, Mapping):
            return {str(key): item for key, item in payload.items()}
    if hasattr(value, "__dict__"):
        return {str(key): item for key, item in vars(value).items()}
    return {}


__all__ = [
    "api_delta_unsupported_reason",
    "authored_aware_source_delta_paths",
    "code_package_delta_from_provider_delta_request",
    "delta_path_has_content",
    "top_changed_path_payloads",
]
