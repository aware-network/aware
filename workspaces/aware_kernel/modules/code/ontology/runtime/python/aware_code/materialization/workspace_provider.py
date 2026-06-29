from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from uuid import UUID

from aware_code.package.discovery import discover_packages_from_manifest_paths
from aware_code.package.schemas import CodePackageInfo
from aware_code.package.snapshot_commit import commit_code_package_text_snapshot
from aware_code.semantic_contract_config import source_code_package_config_ref
from aware_code.semantic_materialization import (
    SemanticPackageMaterializationBundle,
    SemanticPackageMaterializationRequest,
    SemanticPackageMaterializationResult,
)
from aware_code_ontology.code.code_plan import CodePackageDelta
from aware_code.setup_language_plugins import setup_code_plugins

_IGNORED_SOURCE_PARTS = frozenset(
    (
        ".aware",
        ".dart_tool",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
    )
)


async def materialize(
    request: SemanticPackageMaterializationRequest,
) -> SemanticPackageMaterializationResult:
    code_package = _selected_code_package(request=request)
    manifest_kind = _code_package_manifest_kind(code_package=code_package)
    config_ref = source_code_package_config_ref(
        manifest_kind=manifest_kind,
        surface="runtime",
    )
    source_texts = _source_texts_by_relative_path(
        workspace_root=request.workspace_root,
        code_package=code_package,
    )
    projection_hash = _projection_hash_for_name(
        index=request.index,
        projection_name="CodePackage",
    )
    source_root = _code_package_source_root(code_package=code_package)
    snapshot = await commit_code_package_text_snapshot(
        index=request.index,
        actor_id=request.actor_id,
        branch_id=request.branch_id,
        projection_hash=projection_hash,
        code_package_config_id=config_ref.config_id,
        package_name=code_package.name,
        language=code_package.language,
        surface="runtime",
        manifest_kind=manifest_kind,
        manifest_relative_path=code_package.manifest_path.as_posix(),
        package_root=code_package.root_path.as_posix(),
        sources_root=source_root,
        fqn_prefix=_optional_text(code_package.metadata.get("fqn_prefix")),
        source_texts_by_relative_path={},
        unparsed_texts_by_relative_path=source_texts,
    )
    details = {
        "source_code_package_id": str(snapshot.code_package.id),
        "code_package_id": str(snapshot.code_package.id),
        "code_package_config_id": str(config_ref.config_id),
        "code_package_config_key": config_ref.config_key,
        "code_package_commit_id": str(snapshot.commit_id),
        "code_package_head_commit_id": str(snapshot.head_commit_id),
        "code_package_object_instance_graph_commit_id": (
            str(snapshot.object_instance_graph_commit_id)
        ),
        "manifest_kind": manifest_kind,
        "manifest_relative_path": code_package.manifest_path.as_posix(),
        "package_name": code_package.name,
        "package_root": code_package.root_path.as_posix(),
        "source_root": source_root,
        "path_count": len(source_texts),
        "object_count": snapshot.object_count,
        "change_count": snapshot.change_count,
    }
    return SemanticPackageMaterializationResult(
        details=details,
        bundle_packages=(
            SemanticPackageMaterializationBundle(
                package_key=code_package.name,
                manifest_toml_path=code_package.manifest_path,
                semantic_package_id=snapshot.code_package.id,
                semantic_root_id=snapshot.code_package.id,
                semantic_branch_id=request.branch_id,
                semantic_head_commit_id=snapshot.head_commit_id,
                semantic_object_instance_graph_commit_id=(
                    snapshot.object_instance_graph_commit_id
                ),
                semantic_root_object_instance_graph_commit_id=(
                    snapshot.object_instance_graph_commit_id
                ),
                semantic_root_kind="code_package",
                semantic_projection_name="CodePackage",
                semantic_projection_hash=projection_hash,
                source_code_package_id=snapshot.code_package.id,
                source_object_instance_graph_commit_id=(
                    snapshot.object_instance_graph_commit_id
                ),
            ),
        ),
        commit_id=snapshot.commit_id,
        head_commit_id=snapshot.head_commit_id,
    )


async def materialize_delta(request: object) -> dict[str, object]:
    package_payload = _object_payload(getattr(request, "package", None))
    semantic_contract_payload = _object_payload(
        getattr(request, "semantic_contract", None)
    )
    if semantic_contract_payload.get("provider_key") != "aware_code":
        return _provider_delta_fallback_result(
            request=request,
            package_payload=package_payload,
            semantic_contract_payload=semantic_contract_payload,
            fallback_reason="code_delta_semantic_contract_unsupported",
            details={
                "provider_key": semantic_contract_payload.get("provider_key"),
            },
        )

    try:
        code_package_delta = CodePackageDelta.model_validate(
            getattr(request, "code_package_delta", None)
        )
    except Exception as exc:
        return _provider_delta_fallback_result(
            request=request,
            package_payload=package_payload,
            semantic_contract_payload=semantic_contract_payload,
            fallback_reason="code_delta_payload_invalid",
            details={"error": f"{type(exc).__name__}: {exc}"},
        )

    if getattr(request, "execute_provider_delta_materialization", False) is not True:
        preview_refs = _existing_commit_refs_from_request(request=request)
        if not _commit_refs_complete(commit_refs=preview_refs):
            return _provider_delta_fallback_result(
                request=request,
                package_payload=package_payload,
                semantic_contract_payload=semantic_contract_payload,
                fallback_reason="code_delta_execution_required",
                details={"mode": "preview"},
            )
        return _provider_delta_success_result(
            request=request,
            package_payload=package_payload,
            semantic_contract_payload=semantic_contract_payload,
            code_package_delta=code_package_delta,
            commit_refs=preview_refs,
            details={
                "provider_key": "aware_code",
                "mode": "preview",
                "path_count": len(code_package_delta.paths),
                "changed_path_count": len(code_package_delta.paths),
            },
        )

    try:
        result = await _materialize_code_package_delta_snapshot(
            request=request,
            package_payload=package_payload,
            semantic_contract_payload=semantic_contract_payload,
            code_package_delta=code_package_delta,
        )
    except Exception as exc:
        return _provider_delta_fallback_result(
            request=request,
            package_payload=package_payload,
            semantic_contract_payload=semantic_contract_payload,
            fallback_reason="code_delta_snapshot_materialization_failed",
            details={"error": f"{type(exc).__name__}: {exc}"},
        )
    return result


async def _materialize_code_package_delta_snapshot(
    *,
    request: object,
    package_payload: Mapping[str, object],
    semantic_contract_payload: Mapping[str, object],
    code_package_delta: CodePackageDelta,
) -> dict[str, object]:
    workspace_root = _required_path_value(
        getattr(request, "workspace_root", None),
        field_name="workspace_root",
    )
    index = getattr(request, "index", None)
    if index is None:
        raise RuntimeError("Code provider delta execution requires runtime index.")

    code_package = _selected_code_package_for_delta(
        request=request,
        workspace_root=workspace_root,
        package_payload=package_payload,
    )
    manifest_kind = _code_package_manifest_kind(code_package=code_package)
    config_ref = source_code_package_config_ref(
        manifest_kind=manifest_kind,
        surface="runtime",
    )
    projection_hash = _projection_hash_for_name(
        index=index,
        projection_name="CodePackage",
    )
    source_root = _code_package_source_root(code_package=code_package)
    source_texts = _source_texts_by_relative_path(
        workspace_root=workspace_root,
        code_package=code_package,
    )
    source_texts = _source_texts_with_delta_overlay(
        source_texts=source_texts,
        code_package_delta=code_package_delta,
    )
    branch_id = _semantic_branch_id_for_delta_request(request=request)
    snapshot = await commit_code_package_text_snapshot(
        index=index,
        actor_id=_optional_uuid_value(getattr(request, "actor_id", None)),
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_config_id=config_ref.config_id,
        package_name=code_package.name,
        language=code_package.language,
        surface="runtime",
        manifest_kind=manifest_kind,
        manifest_relative_path=code_package.manifest_path.as_posix(),
        package_root=code_package.root_path.as_posix(),
        sources_root=source_root,
        fqn_prefix=_optional_text(code_package.metadata.get("fqn_prefix")),
        source_texts_by_relative_path={},
        unparsed_texts_by_relative_path=source_texts,
    )
    commit_refs = {
        "package_key": code_package.name,
        "package_kind": "code",
        "manifest_toml_path": code_package.manifest_path.as_posix(),
        "semantic_owner_module": "aware_code",
        "semantic_package_kind": "code_package",
        "semantic_contract_module": semantic_contract_payload.get("module"),
        "semantic_contract_name": semantic_contract_payload.get("name"),
        "semantic_contract_role": semantic_contract_payload.get("role"),
        "semantic_contract_provider_key": semantic_contract_payload.get(
            "provider_key"
        ),
        "semantic_branch_id": str(branch_id),
        "semantic_projection_name": "CodePackage",
        "semantic_projection_hash": projection_hash,
        "semantic_package_id": str(snapshot.code_package.id),
        "semantic_root_kind": "code_package",
        "semantic_root_id": str(snapshot.code_package.id),
        "semantic_head_commit_id": str(snapshot.head_commit_id),
        "semantic_object_instance_graph_commit_id": (
            str(snapshot.object_instance_graph_commit_id)
        ),
        "semantic_root_object_instance_graph_commit_id": (
            str(snapshot.object_instance_graph_commit_id)
        ),
        "source_code_package_id": str(snapshot.code_package.id),
        "source_object_instance_graph_commit_id": (
            str(snapshot.object_instance_graph_commit_id)
        ),
    }
    details = {
        "provider_key": "aware_code",
        "mode": "delta",
        "source_code_package_id": str(snapshot.code_package.id),
        "code_package_id": str(snapshot.code_package.id),
        "code_package_config_id": str(config_ref.config_id),
        "code_package_config_key": config_ref.config_key,
        "code_package_commit_id": str(snapshot.commit_id),
        "code_package_head_commit_id": str(snapshot.head_commit_id),
        "code_package_object_instance_graph_commit_id": (
            str(snapshot.object_instance_graph_commit_id)
        ),
        "manifest_kind": manifest_kind,
        "manifest_relative_path": code_package.manifest_path.as_posix(),
        "package_name": code_package.name,
        "package_root": code_package.root_path.as_posix(),
        "source_root": source_root,
        "path_count": len(source_texts),
        "changed_path_count": len(code_package_delta.paths),
        "object_count": snapshot.object_count,
        "change_count": snapshot.change_count,
        "provider_delta_operation_execution": (
            _code_delta_operation_execution_receipt(
                commit_id=str(snapshot.commit_id),
                head_commit_id=str(snapshot.head_commit_id),
                object_instance_graph_commit_id=(
                    str(snapshot.object_instance_graph_commit_id)
                ),
            )
        ),
    }
    return _provider_delta_success_result(
        request=request,
        package_payload=package_payload,
        semantic_contract_payload=semantic_contract_payload,
        code_package_delta=code_package_delta,
        commit_refs=commit_refs,
        details=details,
    )


def _provider_delta_success_result(
    *,
    request: object,
    package_payload: Mapping[str, object],
    semantic_contract_payload: Mapping[str, object],
    code_package_delta: CodePackageDelta,
    commit_refs: Mapping[str, object],
    details: Mapping[str, object],
) -> dict[str, object]:
    bundle_package = {
        "package_key": commit_refs.get("package_key")
        or package_payload.get("package_name"),
        "manifest_toml_path": commit_refs.get("manifest_toml_path")
        or package_payload.get("manifest_path"),
        **dict(commit_refs),
    }
    current_delta_fingerprint = str(
        getattr(request, "current_delta_fingerprint", "") or ""
    )
    package_name = str(
        package_payload.get("package_name")
        or code_package_delta.package_name
        or commit_refs.get("package_key")
        or ""
    )
    return {
        "status": "succeeded",
        "package": dict(package_payload),
        "semantic_contract": dict(semantic_contract_payload),
        "current_delta_fingerprint": current_delta_fingerprint,
        "applied_semantic_keys": [package_name] if package_name else [],
        "skipped_semantic_keys": [],
        "stale_semantic_keys": [],
        "implementation_required": False,
        "implementation_work_items": [],
        "fallback_reason": None,
        "commit_ref_contract": dict(commit_refs),
        "bundle_package": bundle_package,
        "bundle_packages": [bundle_package],
        "details": dict(details),
        "error": None,
    }


def _provider_delta_fallback_result(
    *,
    request: object,
    package_payload: Mapping[str, object],
    semantic_contract_payload: Mapping[str, object],
    fallback_reason: str,
    details: Mapping[str, object],
) -> dict[str, object]:
    return {
        "status": "fallback_required",
        "package": dict(package_payload),
        "semantic_contract": dict(semantic_contract_payload),
        "current_delta_fingerprint": str(
            getattr(request, "current_delta_fingerprint", "") or ""
        ),
        "applied_semantic_keys": [],
        "skipped_semantic_keys": [],
        "stale_semantic_keys": [],
        "implementation_required": False,
        "implementation_work_items": [],
        "fallback_reason": fallback_reason,
        "commit_ref_contract": {},
        "bundle_package": {},
        "bundle_packages": [],
        "details": dict(details),
        "error": None,
    }


def _selected_code_package_for_delta(
    *,
    request: object,
    workspace_root: Path,
    package_payload: Mapping[str, object],
) -> CodePackageInfo:
    manifest_path = package_payload.get("manifest_path")
    if isinstance(manifest_path, str) and manifest_path.strip():
        return _selected_code_package(
            request=SemanticPackageMaterializationRequest(
                runtime=getattr(request, "runtime", None),
                index=getattr(request, "index", None),
                actor_id=_optional_uuid_value(getattr(request, "actor_id", None)),
                branch_id=_semantic_branch_id_for_delta_request(request=request),
                workspace_root=workspace_root,
                manifest_path=Path(manifest_path),
            )
        )
    code_package_delta = getattr(request, "code_package_delta", None)
    delta_payload = _object_payload(code_package_delta)
    delta_manifest_path = delta_payload.get("manifest_relative_path")
    if isinstance(delta_manifest_path, str) and delta_manifest_path.strip():
        return _selected_code_package(
            request=SemanticPackageMaterializationRequest(
                runtime=getattr(request, "runtime", None),
                index=getattr(request, "index", None),
                actor_id=_optional_uuid_value(getattr(request, "actor_id", None)),
                branch_id=_semantic_branch_id_for_delta_request(request=request),
                workspace_root=workspace_root,
                manifest_path=Path(delta_manifest_path),
            )
        )
    raise RuntimeError("Code provider delta request missing manifest path.")


def _source_texts_with_delta_overlay(
    *,
    source_texts: Mapping[str, str],
    code_package_delta: CodePackageDelta,
) -> dict[str, str]:
    texts_by_path = dict(source_texts)
    for path in code_package_delta.paths:
        relative_path = str(path.relative_path or "").strip().strip("/")
        if not relative_path:
            raise RuntimeError("Code provider delta path missing relative_path.")
        path_kind = getattr(path.kind, "value", str(path.kind))
        if path_kind == "delete":
            texts_by_path.pop(relative_path, None)
            continue
        content_text = path.content_text
        if content_text is None and path.content_plan is not None:
            content_text = path.content_plan.content_text
        if content_text is None:
            raise RuntimeError(
                "Code provider delta path requires content_text or content_plan: "
                f"{relative_path}"
            )
        texts_by_path[relative_path] = content_text
    return texts_by_path


def _existing_commit_refs_from_request(*, request: object) -> dict[str, object]:
    previous_evidence = _object_payload(
        getattr(request, "previous_materialization_evidence", None)
    )
    commit_refs = previous_evidence.get("commit_refs")
    if isinstance(commit_refs, Mapping):
        return {str(key): value for key, value in commit_refs.items()}
    baseline_ref = _object_payload(getattr(request, "baseline_ref", None))
    if not baseline_ref:
        baseline_ref = _object_payload(previous_evidence.get("baseline_ref"))
    refs: dict[str, object] = {}
    for field_name in (
        "source_code_package_id",
        "source_object_instance_graph_commit_id",
        "semantic_package_id",
        "semantic_branch_id",
        "semantic_head_commit_id",
        "semantic_projection_name",
        "semantic_projection_hash",
        "semantic_object_instance_graph_commit_id",
        "semantic_root_kind",
        "semantic_root_id",
        "semantic_root_object_instance_graph_commit_id",
    ):
        value = baseline_ref.get(field_name)
        if value is not None:
            refs[field_name] = value
    return refs


def _commit_refs_complete(*, commit_refs: Mapping[str, object]) -> bool:
    return all(
        str(commit_refs.get(field_name) or "").strip()
        for field_name in (
            "source_code_package_id",
            "source_object_instance_graph_commit_id",
            "semantic_package_id",
            "semantic_branch_id",
            "semantic_object_instance_graph_commit_id",
        )
    )


def _semantic_branch_id_for_delta_request(*, request: object) -> UUID:
    existing_commit_refs = _existing_commit_refs_from_request(request=request)
    for value in (
        existing_commit_refs.get("semantic_branch_id"),
        _object_payload(getattr(request, "provider_delta_lane_state", None)).get(
            "semantic_branch_id"
        ),
        getattr(request, "branch_id", None),
    ):
        branch_id = _optional_uuid_value(value)
        if branch_id is not None:
            return branch_id
    raise RuntimeError("Code provider delta request missing semantic branch id.")


def _code_delta_operation_execution_receipt(
    *,
    commit_id: str,
    head_commit_id: str,
    object_instance_graph_commit_id: str,
) -> dict[str, object]:
    semantic_execution = {
        "status": "executed",
        "status_counts": {
            "applied": 1,
            "blocked": 0,
            "failed": 0,
            "error": 0,
        },
        "commit_id": head_commit_id,
        "domain_commit_id": commit_id,
        "object_instance_graph_commit_id": object_instance_graph_commit_id,
        "invocation_receipts": [
            {
                "status": "succeeded",
                "commit_id": head_commit_id,
                "object_instance_graph_commit_id": object_instance_graph_commit_id,
            },
        ],
    }
    return {
        "execution_kind": "aware_code.provider_delta.code_package_snapshot",
        "status": "executed",
        "semantic_function_call_execution": semantic_execution,
    }


def _selected_code_package(
    *,
    request: SemanticPackageMaterializationRequest,
) -> CodePackageInfo:
    setup_code_plugins()
    manifest_path = _workspace_relative_path(
        workspace_root=request.workspace_root,
        path=request.manifest_path,
    )
    discovered_packages = discover_packages_from_manifest_paths(
        workspace_root=request.workspace_root,
        manifest_paths=(manifest_path,),
    )
    normalized_manifest_path = manifest_path.as_posix()
    for code_package in discovered_packages:
        if code_package.manifest_path.as_posix() == normalized_manifest_path:
            return code_package
    raise RuntimeError(
        "Code materialization request manifest was not resolved by Code "
        f"language discovery: {normalized_manifest_path}"
    )


def _workspace_relative_path(*, workspace_root: Path, path: Path) -> Path:
    resolved_path = (
        path.resolve() if path.is_absolute() else (workspace_root / path).resolve()
    )
    try:
        return resolved_path.relative_to(workspace_root.resolve())
    except ValueError:
        return path


def _code_package_manifest_kind(
    *,
    code_package: CodePackageInfo,
) -> str:
    raw_manifest_kind = code_package.metadata.get("manifest_kind")
    if not isinstance(raw_manifest_kind, str) or not raw_manifest_kind.strip():
        raise RuntimeError(
            "Code materialization requires language discovery manifest_kind: "
            f"{code_package.manifest_path.as_posix()}"
        )
    return raw_manifest_kind.strip()


def _source_texts_by_relative_path(
    *,
    workspace_root: Path,
    code_package: CodePackageInfo,
) -> dict[str, str]:
    package_root = (workspace_root / code_package.root_path).resolve()
    if not package_root.is_dir():
        raise RuntimeError(
            "Code materialization package root not found: "
            f"{code_package.root_path.as_posix()}"
        )
    texts_by_path: dict[str, str] = {}
    for path in sorted(package_root.rglob("*")):
        if not path.is_file():
            continue
        relative_package_path = path.relative_to(package_root)
        if _IGNORED_SOURCE_PARTS.intersection(relative_package_path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        texts_by_path[relative_package_path.as_posix()] = text
    return texts_by_path


def _projection_hash_for_name(*, index: object, projection_name: str) -> str:
    projection_hash_for_name = getattr(index, "projection_hash_for_name", None)
    if callable(projection_hash_for_name):
        value = projection_hash_for_name(projection_name)
        if isinstance(value, str) and value.strip():
            return value
    projection_hash_by_name = getattr(index, "projection_hash_by_name", None)
    if isinstance(projection_hash_by_name, dict):
        value = projection_hash_by_name.get(projection_name)
        if isinstance(value, str) and value.strip():
            return value
    opg_by_hash = getattr(index, "opg_by_hash", None)
    if isinstance(opg_by_hash, dict):
        for projection_hash, opg in sorted(opg_by_hash.items()):
            if _projection_name(opg) == projection_name:
                return str(projection_hash)
    raise RuntimeError(f"Missing projection hash for {projection_name!r}")


def _projection_name(opg: object) -> str | None:
    name = getattr(opg, "name", None)
    if isinstance(name, str) and name.strip():
        return name
    projection = getattr(opg, "projection_graph", None)
    projection_name = getattr(projection, "name", None)
    if isinstance(projection_name, str) and projection_name.strip():
        return projection_name
    return None


def _code_package_source_root(*, code_package: CodePackageInfo) -> str | None:
    source_root = _optional_text(code_package.metadata.get("source_root"))
    if source_root is not None:
        return source_root
    sources_root = _optional_text(code_package.metadata.get("sources_root"))
    if sources_root is not None:
        return sources_root
    return code_package.root_path.as_posix()


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _required_path_value(value: object, *, field_name: str) -> Path:
    if isinstance(value, Path):
        return value
    if isinstance(value, str) and value.strip():
        return Path(value)
    raise RuntimeError(f"Code provider delta request missing {field_name}.")


def _optional_uuid_value(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return UUID(value)
        except ValueError:
            return None
    return None


def _object_payload(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="json")
        if isinstance(payload, Mapping):
            return {str(key): item for key, item in payload.items()}
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


__all__ = ["materialize", "materialize_delta"]
