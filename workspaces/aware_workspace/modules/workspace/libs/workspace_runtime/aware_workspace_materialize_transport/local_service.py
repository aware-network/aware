"""Lightweight client for the existing Local Service serving protocol."""

from __future__ import annotations

import base64
import json
import os
import socket
import stat
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Protocol, cast
from uuid import uuid4

from .contracts import (
    WorkspaceMaterializeCommandProposalV2,
    WorkspaceMaterializeHostResultV2,
    WorkspaceMaterializeTransportContractError,
)

WORKSPACE_MATERIALIZE_LOCAL_SERVICE_CAPABILITY = "workspace.materialization"
WORKSPACE_MATERIALIZE_LOCAL_SERVICE_OPERATION = "materialize"
WORKSPACE_MATERIALIZE_ROUTE_ENV = "AWARE_WORKSPACE_LOCAL_SERVICE_ROUTE_PATH"
_DEVELOPMENT_ROUTE_ENV = "AWARE_DEV_LOCAL_SERVICE_ROUTE_PATH"
_SERVING_PROTOCOL = "aware.local_service.serving.v1"
_SERVING_PROTOCOL_VERSION = "1.1"
_MAX_FRAME_BYTES = 1_000_000


class _FrameClient(Protocol):
    def request(self, operation: str, parameters: dict[str, object]) -> object: ...

    def close(self) -> None: ...


class WorkspaceMaterializeLocalServiceTransport:
    """Command-specialized client over the one existing serving protocol."""

    def __init__(
        self,
        *,
        route_path: str | Path,
        client_key: str,
        admission_evidence: Mapping[str, object],
        request_timeout_seconds: float = 30.0,
        frame_client_factory: Callable[[Path, float], _FrameClient] | None = None,
    ) -> None:
        if not client_key or client_key.strip() != client_key:
            raise WorkspaceMaterializeTransportContractError(
                "client_key must be nonempty trimmed text"
            )
        if request_timeout_seconds <= 0:
            raise WorkspaceMaterializeTransportContractError(
                "request_timeout_seconds must be positive"
            )
        self._route_path = Path(route_path).expanduser().resolve()
        self._client_key = client_key
        self._admission_evidence = _json_object(dict(admission_evidence))
        self._request_timeout_seconds = request_timeout_seconds
        self._frame_client_factory = frame_client_factory or _UnixFrameClient

    def invoke(self, proposal_wire: bytes) -> WorkspaceMaterializeHostResultV2:
        proposal = WorkspaceMaterializeCommandProposalV2.from_wire(proposal_wire)
        socket_path = _read_unix_socket_path(self._route_path)
        client = self._frame_client_factory(socket_path, self._request_timeout_seconds)
        session_token: str | None = None
        error: BaseException | None = None
        call_result: object = None
        try:
            admission = _object(
                client.request(
                    "attach",
                    {
                        "client_key": self._client_key,
                        "admission_evidence": self._admission_evidence,
                    },
                ),
                "attach_result",
            )
            session_token = _text(admission.get("session_token"), "session_token")
            call_result = client.request(
                "call",
                {
                    "session_token": session_token,
                    "capability_key": WORKSPACE_MATERIALIZE_LOCAL_SERVICE_CAPABILITY,
                    "operation_key": WORKSPACE_MATERIALIZE_LOCAL_SERVICE_OPERATION,
                    "correlation_id": proposal.attempt_ref,
                    "payload": {
                        "proposal_wire_base64": base64.b64encode(proposal_wire).decode(
                            "ascii"
                        )
                    },
                    "idempotency_key": proposal.attempt_ref,
                    "deadline_at": None,
                    "cancellation_id": None,
                    "require_idempotency": True,
                },
            )
        except Exception as caught:  # noqa: BLE001 - total transport boundary
            error = caught
        finally:
            if session_token is not None:
                try:
                    client.request("detach", {"session_token": session_token})
                except Exception:  # noqa: BLE001, S110 - detach is best effort
                    pass
            try:
                client.close()
            except Exception as caught:  # noqa: BLE001 - close is transport evidence
                if error is None:
                    error = caught
        if error is not None:
            raise error
        result = _object(call_result, "call_result")
        if (
            _text(result.get("correlation_id"), "correlation_id")
            != proposal.attempt_ref
        ):
            raise WorkspaceMaterializeTransportContractError(
                "Local Service call correlation differs"
            )
        if result.get("status") != "succeeded":
            failure = _object(result.get("failure"), "failure")
            raise WorkspaceMaterializeTransportContractError(
                f"{_text(failure.get('code'), 'failure_code')}: "
                f"{_text(failure.get('message'), 'failure_message')}"
            )
        payload = _object(result.get("payload"), "result_payload")
        if set(payload) != {"result_wire_base64"}:
            raise WorkspaceMaterializeTransportContractError(
                "Local Service materialization result payload differs"
            )
        encoded = _text(payload["result_wire_base64"], "result_wire_base64")
        try:
            response_wire = base64.b64decode(encoded, validate=True)
        except ValueError as caught:
            raise WorkspaceMaterializeTransportContractError(
                "Local Service materialization result is not canonical base64"
            ) from caught
        if base64.b64encode(response_wire).decode("ascii") != encoded:
            raise WorkspaceMaterializeTransportContractError(
                "Local Service materialization result base64 differs"
            )
        return WorkspaceMaterializeHostResultV2.from_wire(
            response_wire, proposal=proposal
        )


class _UnixFrameClient:
    def __init__(self, socket_path: Path, timeout_seconds: float) -> None:
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.settimeout(timeout_seconds)
        self._socket.connect(str(socket_path))
        self._buffer = bytearray()

    def request(self, operation: str, parameters: dict[str, object]) -> object:
        request_id = str(uuid4())
        frame = {
            "id": request_id,
            "type": "request",
            "data": _SERVING_PROTOCOL,
            "payload": {
                "protocol_version": _SERVING_PROTOCOL_VERSION,
                "operation": operation,
                "parameters": parameters,
            },
            "request_id": None,
        }
        self._socket.sendall(_canonical_json(frame) + b"\n")
        response = _object(_decode_json(self._read_line()), "serving_response")
        if (
            response.get("request_id") != request_id
            or response.get("data") != _SERVING_PROTOCOL
        ):
            raise WorkspaceMaterializeTransportContractError(
                "Local Service serving response correlation differs"
            )
        payload = _object(response.get("payload"), "serving_payload")
        if response.get("type") == "error":
            raise WorkspaceMaterializeTransportContractError(
                f"{_text(payload.get('code'), 'serving_error_code')}: "
                f"{_text(payload.get('message'), 'serving_error_message')}"
            )
        if (
            response.get("type") != "response"
            or payload.get("protocol_version") != _SERVING_PROTOCOL_VERSION
            or payload.get("operation") != operation
        ):
            raise WorkspaceMaterializeTransportContractError(
                "Local Service serving response contract differs"
            )
        return payload.get("result")

    def close(self) -> None:
        self._socket.close()

    def _read_line(self) -> bytes:
        while True:
            newline = self._buffer.find(b"\n")
            if newline >= 0:
                line = bytes(self._buffer[:newline])
                del self._buffer[: newline + 1]
                if not line:
                    raise WorkspaceMaterializeTransportContractError(
                        "Local Service serving frame is empty"
                    )
                return line
            chunk = self._socket.recv(65536)
            if not chunk:
                raise WorkspaceMaterializeTransportContractError(
                    "Local Service serving socket closed"
                )
            self._buffer.extend(chunk)
            if len(self._buffer) > _MAX_FRAME_BYTES:
                raise WorkspaceMaterializeTransportContractError(
                    "Local Service serving frame exceeds the command boundary"
                )


def default_workspace_materialize_transport(
    *,
    env: Mapping[str, str] | None = None,
    request_timeout_seconds: float = 30.0,
) -> WorkspaceMaterializeLocalServiceTransport | None:
    """Resolve deployment coordinates only; never select semantic providers."""

    values = os.environ if env is None else env
    provider_key = (values.get("AWARE_INTERFACE_PROVIDER") or "").strip()
    provider_session_id = (
        values.get("AWARE_INTERFACE_PROVIDER_SESSION_ID") or ""
    ).strip()
    if not provider_key and not provider_session_id:
        codex_thread_id = (values.get("CODEX_THREAD_ID") or "").strip()
        if codex_thread_id:
            provider_key = "codex"
            provider_session_id = codex_thread_id
    if not provider_key or not provider_session_id:
        return None
    route_path = _route_path(values)
    if not route_path.is_file():
        return None
    return WorkspaceMaterializeLocalServiceTransport(
        route_path=route_path,
        client_key=f"workspace-materialize.{provider_key}.{provider_session_id}",
        admission_evidence={
            "actor_kind": "agent",
            "admission_kind": "agent_identity_bootstrap",
            "execution_id": f"{provider_key}-{provider_session_id}",
            "provider_key": provider_key,
            "provider_session_id": provider_session_id,
        },
        request_timeout_seconds=request_timeout_seconds,
    )


def _read_unix_socket_path(route_path: Path) -> Path:
    details = route_path.lstat()
    if (
        stat.S_ISLNK(details.st_mode)
        or not stat.S_ISREG(details.st_mode)
        or details.st_uid != os.getuid()
        or stat.S_IMODE(details.st_mode) & 0o077
    ):
        raise WorkspaceMaterializeTransportContractError(
            "Local Service route is not a private regular file"
        )
    root = _object(_decode_json(route_path.read_bytes()), "route")
    endpoints = root.get("endpoints")
    if type(endpoints) is not list:
        raise WorkspaceMaterializeTransportContractError(
            "Local Service route endpoints differ"
        )
    matches = [
        _object(item, "route_endpoint")
        for item in endpoints
        if isinstance(item, dict) and item.get("kind") == "unix"
    ]
    if len(matches) != 1:
        raise WorkspaceMaterializeTransportContractError(
            "Local Service route requires one Unix endpoint"
        )
    path = Path(_text(matches[0].get("address"), "socket_path"))
    if not path.is_absolute():
        raise WorkspaceMaterializeTransportContractError(
            "Local Service Unix endpoint must be absolute"
        )
    return path


def _route_path(env: Mapping[str, str]) -> Path:
    explicit = (
        env.get(WORKSPACE_MATERIALIZE_ROUTE_ENV)
        or env.get(_DEVELOPMENT_ROUTE_ENV)
        or ""
    ).strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    state_home = (env.get("XDG_STATE_HOME") or "").strip()
    root = Path(state_home).expanduser() if state_home else Path.home() / ".local/state"
    return (root / "aware/development/local-service/route.json").resolve()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def _decode_json(value: bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in items:
            if key in result:
                raise WorkspaceMaterializeTransportContractError(
                    "Local Service value contains a duplicate object key"
                )
            result[key] = item
        return result

    try:
        return json.loads(value.decode("utf-8"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as caught:
        raise WorkspaceMaterializeTransportContractError(
            "Local Service value is not JSON"
        ) from caught


def _json_object(value: dict[str, object]) -> dict[str, object]:
    return _object(_decode_json(_canonical_json(value)), "json_object")


def _object(value: object, field: str) -> dict[str, object]:
    if type(value) is not dict or not all(type(key) is str for key in value):
        raise WorkspaceMaterializeTransportContractError(
            f"{field} must be an exact JSON object"
        )
    return cast(dict[str, object], value)


def _text(value: object, field: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise WorkspaceMaterializeTransportContractError(
            f"{field} must be nonempty exact text"
        )
    return value


__all__ = [
    "WORKSPACE_MATERIALIZE_LOCAL_SERVICE_CAPABILITY",
    "WORKSPACE_MATERIALIZE_LOCAL_SERVICE_OPERATION",
    "WORKSPACE_MATERIALIZE_ROUTE_ENV",
    "WorkspaceMaterializeLocalServiceTransport",
    "default_workspace_materialize_transport",
]
