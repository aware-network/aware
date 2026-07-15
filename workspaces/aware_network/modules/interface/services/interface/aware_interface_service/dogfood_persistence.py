from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aware_interface_service_dto.comms.models.interface_host_state import InterfaceHostState
from aware_utils.logging import logger


_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class InterfaceHostSnapshotRecord:
    namespace: str
    captured_at: str
    host_state: InterfaceHostState
    view_state_cursor: str | None
    view_state_digest: str | None
    environment_config_id: str | None
    interface_package_id: str | None
    interface_package_name: str | None


class InterfaceHostDogfoodStore:
    """Launch persistence for generated Interface Host boundary DTOs.

    This adapter intentionally stores DTO-shaped JSON. A later ORM-backed store
    should implement the same methods and persist the same DTO payload columns.
    """

    def __init__(self, *, state_home: Path) -> None:
        self._root = state_home.expanduser().resolve() / "interface-host"

    def save_host_state(
        self,
        host_state: InterfaceHostState,
        *,
        captured_at: str | None = None,
    ) -> InterfaceHostSnapshotRecord:
        record = self._snapshot_record(host_state, captured_at=captured_at)
        path = self._snapshot_path(host_state.namespace)
        self._write_json(path, self._snapshot_payload(record))
        return record

    def read_host_state(
        self,
        *,
        namespace: str,
    ) -> InterfaceHostState | None:
        record = self.read_snapshot(namespace=namespace)
        return record.host_state if record is not None else None

    def read_snapshot(
        self,
        *,
        namespace: str,
    ) -> InterfaceHostSnapshotRecord | None:
        path = self._snapshot_path(namespace)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise TypeError("snapshot payload must be a JSON object")
            raw_host_state = payload.get("host_state")
            if not isinstance(raw_host_state, dict):
                raise TypeError("snapshot payload is missing host_state")
            host_state = InterfaceHostState.model_validate(raw_host_state)
            return InterfaceHostSnapshotRecord(
                namespace=str(payload.get("namespace") or host_state.namespace),
                captured_at=str(payload.get("captured_at") or ""),
                host_state=host_state,
                view_state_cursor=_optional_str(payload.get("view_state_cursor")),
                view_state_digest=_optional_str(payload.get("view_state_digest")),
                environment_config_id=_optional_str(
                    payload.get("environment_config_id")
                ),
                interface_package_id=_optional_str(payload.get("interface_package_id")),
                interface_package_name=_optional_str(
                    payload.get("interface_package_name")
                ),
            )
        except Exception as exc:
            logger.warning(
                "aware_interface_service failed to read dogfood host snapshot %s: %s",
                path,
                exc,
            )
            return None

    def append_action_receipt(
        self,
        *,
        request_id: str | None,
        namespace: str,
        operation_kind: str,
        action_key: str,
        pane_ref: str | None = None,
        status: str,
        error: str | None = None,
        host_state: InterfaceHostState | None = None,
        service_status: str | None = None,
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
        captured_at: str | None = None,
    ) -> dict[str, Any]:
        timestamp = captured_at or _utc_now_isoformat()
        cursor = host_state.runtime.view_state_cursor if (
            host_state is not None and host_state.runtime is not None
        ) else None
        current_operation = (
            host_state.current_operation
            if host_state is not None
            else None
        )
        receipt: dict[str, Any] = {
            "schema_version": _SCHEMA_VERSION,
            "captured_at": timestamp,
            "request_id": request_id,
            "namespace": namespace,
            "operation_kind": operation_kind,
            "pane_ref": pane_ref,
            "action_key": action_key,
            "endpoint_ref": endpoint_ref,
            "discriminant": discriminant,
            "status": status,
            "service_status": service_status,
            "error": error,
            "view_state_cursor": cursor.cursor if cursor is not None else None,
            "view_state_digest": cursor.digest if cursor is not None else None,
            "current_operation": (
                current_operation.model_dump(mode="json", exclude_none=True)
                if current_operation is not None
                else None
            ),
        }
        self._append_jsonl(self._receipts_path(namespace), receipt)
        return receipt

    def read_action_receipts(self, *, namespace: str) -> tuple[dict[str, Any], ...]:
        path = self._receipts_path(namespace)
        if not path.exists():
            return ()
        receipts: list[dict[str, Any]] = []
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                payload = json.loads(stripped)
                if isinstance(payload, dict):
                    receipts.append(payload)
        except Exception as exc:
            logger.warning(
                "aware_interface_service failed to read dogfood action receipts %s: %s",
                path,
                exc,
            )
            return ()
        return tuple(receipts)

    def _snapshot_record(
        self,
        host_state: InterfaceHostState,
        *,
        captured_at: str | None,
    ) -> InterfaceHostSnapshotRecord:
        runtime = host_state.runtime
        cursor = runtime.view_state_cursor if runtime is not None else None
        resolved_view = runtime.resolved_view if runtime is not None else None
        return InterfaceHostSnapshotRecord(
            namespace=host_state.namespace,
            captured_at=captured_at or _utc_now_isoformat(),
            host_state=host_state,
            view_state_cursor=cursor.cursor if cursor is not None else None,
            view_state_digest=cursor.digest if cursor is not None else None,
            environment_config_id=(
                str(host_state.environment_config_id)
                if host_state.environment_config_id is not None
                else None
            ),
            interface_package_id=(
                str(resolved_view.interface_package_id)
                if resolved_view is not None
                and resolved_view.interface_package_id is not None
                else None
            ),
            interface_package_name=(
                resolved_view.interface_package_name
                if resolved_view is not None
                else None
            ),
        )

    def _snapshot_payload(
        self,
        record: InterfaceHostSnapshotRecord,
    ) -> dict[str, Any]:
        return {
            "schema_version": _SCHEMA_VERSION,
            "namespace": record.namespace,
            "captured_at": record.captured_at,
            "view_state_cursor": record.view_state_cursor,
            "view_state_digest": record.view_state_digest,
            "environment_config_id": record.environment_config_id,
            "interface_package_id": record.interface_package_id,
            "interface_package_name": record.interface_package_name,
            "host_state": record.host_state.model_dump(
                mode="json",
                exclude_none=True,
            ),
        }

    def _snapshot_path(self, namespace: str) -> Path:
        return self._root / "host-states" / f"{_namespace_file_stem(namespace)}.json"

    def _receipts_path(self, namespace: str) -> Path:
        return self._root / "action-receipts" / f"{_namespace_file_stem(namespace)}.jsonl"

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f".{path.name}.tmp")
        tmp_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp_path.replace(path)

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def _utc_now_isoformat() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _optional_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _namespace_file_stem(namespace: str) -> str:
    normalized = namespace.strip() or "default"
    prefix = "".join(
        item if item.isalnum() or item in {".", "_", "-"} else "_"
        for item in normalized
    ).strip("._-")
    if not prefix:
        prefix = "namespace"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return f"{prefix[:64]}-{digest}"
