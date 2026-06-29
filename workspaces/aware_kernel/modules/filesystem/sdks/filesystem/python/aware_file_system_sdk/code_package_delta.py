from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import cast

from aware_file_system_service_dto.file_system.types import (
    FileSystemApplyPolicy,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemBackendKind,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemContentDigest,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemDeltaEntry,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemDeltaOperation,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemDeltaSet,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemDeltaTotals,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemRelativePath,
)
from aware_file_system_service_dto.file_system.types import FileSystemRootRef

from aware_file_system_sdk.client import (
    AwareFileSystemSdk,
    FileSystemSdkError,
    build_root_ref,
    default_apply_policy,
    normalize_relative_path,
)

@dataclass(frozen=True, slots=True)
class FileSystemCodePackageAppliedFile:
    package_name: str | None
    package_root: str | None
    relative_path: str
    root_relative_path: str
    operation: str
    before_exists: bool
    after_exists: bool
    after_sha256: str | None = None
    digest_verified: bool | None = None


@dataclass(frozen=True, slots=True)
class FileSystemCodePackageApplyResult:
    root_path: Path
    applied_files: tuple[FileSystemCodePackageAppliedFile, ...]
    file_system_apply_receipt: Mapping[str, object] | None = None
    evidence: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FileSystemCodePackageDeltaPlan:
    root: FileSystemRootRef
    delta_set: FileSystemDeltaSet
    planned_entries: tuple["_PlannedCodePackageDeltaEntry", ...]
    evidence: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class _PlannedCodePackageDeltaEntry:
    package_name: str | None
    package_root: str | None
    relative_path: str
    root_relative_path: str
    operation: str
    target: Path
    before_exists: bool
    expected_sha256: str | None
    file_system_entry: FileSystemDeltaEntry


@dataclass(frozen=True, slots=True)
class FileSystemCodePackageDeltaClient:
    file_system_sdk: AwareFileSystemSdk

    def plan(
        self,
        *,
        root_path: str | Path,
        code_package_deltas: Iterable[object],
        display_name: str = "filesystem-sdk-code-package-delta",
    ) -> FileSystemCodePackageDeltaPlan:
        root = Path(root_path).expanduser().resolve()
        if not root.is_dir():
            raise FileSystemSdkError(f"FileSystem SDK root is not a directory: {root}")
        deltas = tuple(code_package_deltas)
        root_ref = build_root_ref(root_path=root, display_name=display_name)
        planned_entries = tuple(
            entry
            for delta in deltas
            for entry in _planned_delta_entries(root=root, delta=delta)
        )
        delta_set = FileSystemDeltaSet(
            root=root_ref,
            entries=[entry.file_system_entry for entry in planned_entries],
            totals=_delta_totals(planned_entries),
        )
        return FileSystemCodePackageDeltaPlan(
            root=root_ref,
            delta_set=delta_set,
            planned_entries=planned_entries,
            evidence={
                "boundary": "filesystem.sdk.code_package_delta",
                "operation": "plan",
                "code_api_dto_package": "aware_code_service_api",
                "delta_count": len(deltas),
                "entry_count": len(planned_entries),
            },
        )

    async def apply(
        self,
        *,
        root_path: str | Path,
        code_package_deltas: Iterable[object],
        policy: FileSystemApplyPolicy | None = None,
        dry_run: bool = False,
        backend_kind: FileSystemBackendKind | None = None,
        display_name: str = "filesystem-sdk-code-package-delta-apply",
    ) -> FileSystemCodePackageApplyResult:
        deltas = tuple(code_package_deltas)
        plan = self.plan(
            root_path=root_path,
            code_package_deltas=deltas,
            display_name=display_name,
        )
        response = await self.file_system_sdk.apply_delta_set(
            root_path=plan.root.root_path,
            delta_set=plan.delta_set,
            policy=policy or default_apply_policy(),
            dry_run=dry_run,
            backend_kind=backend_kind,
            display_name=plan.root.display_name or display_name,
        )
        receipt = response.receipt
        if receipt is None:
            raise FileSystemSdkError(
                "FileSystem delta apply failed: missing apply receipt"
            )
        applied_files = tuple(
            _applied_file_from_plan(root=plan.root, planned=planned)
            for planned in plan.planned_entries
        )
        receipt_payload = _model_dump_json(receipt)
        return FileSystemCodePackageApplyResult(
            root_path=Path(plan.root.root_path),
            applied_files=applied_files,
            file_system_apply_receipt=receipt_payload,
            evidence={
                "boundary": "filesystem.delta.apply",
                "api_client": "aware_file_system_service_api",
                "code_api_dto_package": "aware_code_service_api",
                "backend_kind_requested": _enum_text(
                    backend_kind or self.file_system_sdk.backend_kind
                ),
                "dry_run": dry_run,
                "delta_count": len(deltas),
                "entry_count": len(plan.planned_entries),
                "receipt": receipt_payload,
                "backend_receipt": _model_dump_json(response.backend_receipt),
            },
        )


def build_code_package_delta_client(
    *,
    file_system_sdk: AwareFileSystemSdk,
) -> FileSystemCodePackageDeltaClient:
    return FileSystemCodePackageDeltaClient(file_system_sdk=file_system_sdk)


def _planned_delta_entries(
    *,
    root: Path,
    delta: object,
) -> tuple[_PlannedCodePackageDeltaEntry, ...]:
    package_root = _optional_relative_path(getattr(delta, "package_root", None))
    sources_root = _optional_relative_path(getattr(delta, "sources_root", None))
    if sources_root is None:
        sources_root = package_root
    entries: list[_PlannedCodePackageDeltaEntry] = []
    for path_delta in tuple(getattr(delta, "paths", ()) or ()):
        relative_path = _required_relative_path(
            getattr(path_delta, "relative_path", None),
            "CodePackageDelta path",
        )
        operation = _enum_text(getattr(path_delta, "kind", None))
        base = _materialized_delta_base_path(
            package_root=package_root,
            sources_root=sources_root,
            relative_path=relative_path,
        )
        root_relative_path = _join_relative_paths(base, relative_path)
        target = _safe_root_target(root=root, root_relative_path=root_relative_path)
        expected_sha256 = _expected_sha256(path_delta)
        file_system_entry = _file_system_delta_entry(
            path_delta=path_delta,
            operation=operation,
            root_relative_path=root_relative_path,
            expected_sha256=expected_sha256,
        )
        entries.append(
            _PlannedCodePackageDeltaEntry(
                package_name=_optional_str(getattr(delta, "package_name", None)),
                package_root=package_root,
                relative_path=relative_path,
                root_relative_path=root_relative_path,
                operation=operation,
                target=target,
                before_exists=target.exists(),
                expected_sha256=expected_sha256,
                file_system_entry=file_system_entry,
            )
        )
    return tuple(entries)


def _file_system_delta_entry(
    *,
    path_delta: object,
    operation: str,
    root_relative_path: str,
    expected_sha256: str | None,
) -> FileSystemDeltaEntry:
    if operation == "delete":
        return FileSystemDeltaEntry(
            operation=FileSystemDeltaOperation.delete,
            path=FileSystemRelativePath(relative_path=root_relative_path),
        )
    if operation not in {"create", "update"}:
        message = (
            f"Unsupported CodePackageDelta operation: "
            f"{operation or '<empty>'}"
        )
        raise FileSystemSdkError(message)
    content_text = getattr(path_delta, "content_text", None)
    if content_text is None:
        message = (
            f"CodePackageDelta {operation} requires inline content_text: "
            f"{root_relative_path}"
        )
        raise FileSystemSdkError(message)
    if not isinstance(content_text, str):
        message = (
            f"CodePackageDelta content_text must be a string: "
            f"{root_relative_path}"
        )
        raise FileSystemSdkError(message)
    content_bytes = content_text.encode("utf-8")
    _verify_expected_digest(
        content_bytes=content_bytes,
        expected_sha256=expected_sha256,
        root_relative_path=root_relative_path,
    )
    after_digest = (
        FileSystemContentDigest(hex=expected_sha256, byte_length=len(content_bytes))
        if expected_sha256 is not None
        else None
    )
    return FileSystemDeltaEntry(
        operation=FileSystemDeltaOperation(operation),
        path=FileSystemRelativePath(relative_path=root_relative_path),
        after_digest=after_digest,
        content_text=content_text,
    )


def _verify_expected_digest(
    *,
    content_bytes: bytes,
    expected_sha256: str | None,
    root_relative_path: str,
) -> None:
    if expected_sha256 is None:
        return
    actual = sha256(content_bytes).hexdigest()
    if actual != expected_sha256:
        message = (
            f"CodePackageDelta digest mismatch for {root_relative_path}: "
            f"expected {expected_sha256}, got {actual}"
        )
        raise FileSystemSdkError(message)


def _delta_totals(
    planned_entries: tuple[_PlannedCodePackageDeltaEntry, ...],
) -> FileSystemDeltaTotals:
    byte_count = 0
    digest_count = 0
    for planned in planned_entries:
        if planned.operation in {"create", "update"}:
            content = planned.file_system_entry.content_text or ""
            byte_count += len(content.encode("utf-8"))
        if planned.expected_sha256 is not None:
            digest_count += 1
    return FileSystemDeltaTotals(
        create_count=sum(
            1 for planned in planned_entries if planned.operation == "create"
        ),
        update_count=sum(
            1 for planned in planned_entries if planned.operation == "update"
        ),
        delete_count=sum(
            1 for planned in planned_entries if planned.operation == "delete"
        ),
        byte_count=byte_count,
        digest_count=digest_count,
    )


def _applied_file_from_plan(
    *,
    root: FileSystemRootRef,
    planned: _PlannedCodePackageDeltaEntry,
) -> FileSystemCodePackageAppliedFile:
    root_path = Path(root.root_path).expanduser().resolve()
    target = _safe_root_target(
        root=root_path,
        root_relative_path=planned.root_relative_path,
    )
    after_exists = target.exists()
    after_sha256 = _file_sha256(target) if target.is_file() else None
    return FileSystemCodePackageAppliedFile(
        package_name=planned.package_name,
        package_root=planned.package_root,
        relative_path=planned.relative_path,
        root_relative_path=planned.root_relative_path,
        operation=planned.operation,
        before_exists=planned.before_exists,
        after_exists=after_exists,
        after_sha256=after_sha256,
        digest_verified=planned.expected_sha256 is not None,
    )


def _materialized_delta_base_path(
    *,
    package_root: str | None,
    sources_root: str | None,
    relative_path: str,
) -> str:
    if package_root is None and sources_root is None:
        raise FileSystemSdkError(
            "CodePackageDelta requires package_root or sources_root."
        )
    if package_root is None:
        return sources_root or "."
    if sources_root is None or sources_root == package_root:
        return package_root
    if _relative_path_contains(parent=package_root, child=sources_root):
        source_suffix = _relative_path_suffix(parent=package_root, child=sources_root)
        if source_suffix is not None and _relative_path_contains(
            parent=source_suffix,
            child=relative_path,
        ):
            return package_root
        return sources_root
    return package_root


def _expected_sha256(path_delta: object) -> str | None:
    after_hash = _normalize_sha256_digest(getattr(path_delta, "after_hash", None))
    if after_hash is not None:
        return after_hash
    production: object | None = getattr(path_delta, "production", None)
    if production is None:
        return None
    return _normalize_sha256_digest(getattr(production, "output_digest", None))


def _normalize_sha256_digest(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if text.startswith("sha256:"):
        text = text.split(":", 1)[1]
    if len(text) != 64:
        return None
    if not all(ch in "0123456789abcdef" for ch in text):
        return None
    return text


def _safe_root_target(*, root: Path, root_relative_path: str) -> Path:
    target = (root / root_relative_path).resolve()
    if not _is_relative_to(path=target, root=root):
        message = (
            f"FileSystem SDK target escapes the filesystem root: "
            f"{root_relative_path}"
        )
        raise FileSystemSdkError(message)
    return target


def _is_relative_to(*, path: Path, root: Path) -> bool:
    try:
        _ = path.relative_to(root)
    except ValueError:
        return False
    return True


def _optional_relative_path(value: object) -> str | None:
    text = _optional_str(value)
    if text is None:
        return None
    return normalize_relative_path(text)


def _required_relative_path(value: object, context: str) -> str:
    path = _optional_relative_path(value)
    if path is None:
        raise FileSystemSdkError(f"{context} requires a relative path.")
    return path


def _join_relative_paths(base: str, relative: str) -> str:
    if base == ".":
        return relative
    if relative == ".":
        return base
    return f"{base.rstrip('/')}/{relative.lstrip('/')}"


def _relative_path_contains(*, parent: str, child: str) -> bool:
    normalized_parent = parent.rstrip("/")
    normalized_child = child.rstrip("/")
    if normalized_parent in {"", "."}:
        return True
    return (
        normalized_child == normalized_parent
        or normalized_child.startswith(f"{normalized_parent}/")
    )


def _relative_path_suffix(*, parent: str, child: str) -> str | None:
    normalized_parent = parent.rstrip("/")
    normalized_child = child.rstrip("/")
    if normalized_child == normalized_parent:
        return "."
    prefix = f"{normalized_parent}/"
    if normalized_child.startswith(prefix):
        return normalized_child[len(prefix) :]
    return None


def _optional_str(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _enum_text(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw or "").strip()


def _file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _model_dump_json(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return cast(dict[str, object], model_dump(mode="json"))
    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        return {str(key): item for key, item in mapping.items()}
    return None


__all__ = [
    "FileSystemCodePackageAppliedFile",
    "FileSystemCodePackageApplyResult",
    "FileSystemCodePackageDeltaClient",
    "FileSystemCodePackageDeltaPlan",
    "build_code_package_delta_client",
]
