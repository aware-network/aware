"""Small local consumer contract; the configured host owns execution authority.

This is not the remote facade command/witness protocol. A transport is supplied
by trusted application infrastructure, never discovered or selected by a call.
"""

import json
from dataclasses import dataclass
from typing import Any, Protocol, cast


class ScalarTransport(Protocol):
    async def exchange(self, request: bytes, /) -> bytes: ...


class ScalarInvocationError(RuntimeError):
    def __init__(self, code: str, recovery_ref: str | None = None) -> None:
        self.code = code
        self.recovery_ref = recovery_ref
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ScalarReceipt:
    invocation_ref: str
    attempt_ref: str
    receipt_digest: str
    outcome: str


@dataclass(frozen=True, slots=True)
class ScalarResult:
    value: bool | int | str | None
    receipt: ScalarReceipt


@dataclass(frozen=True, slots=True)
class ScalarInvocationStatus:
    """Journal observation, not a recovered result or worker-cleanup proof."""

    state: str
    journal_state: str | None
    revision: int | None
    invocation_ref: str | None
    recovery_ref: str | None
    backend_receipt: ScalarReceipt | None


def _text(value: object) -> bool:
    return type(value) is str and 0 < len(value.encode("utf-8")) <= 4096 and "\0" not in value


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ScalarInvocationError("scalar.invalid_response")
        result[key] = value
    return result


def _receipt(value: object) -> ScalarReceipt:
    if type(value) is not dict:
        raise ScalarInvocationError("scalar.invalid_response")
    receipt = cast(dict[str, Any], value)
    if (set(receipt) != {"invocation_ref", "attempt_ref", "receipt_digest", "outcome"}
        or not all(_text(receipt[key]) for key in receipt)
        or receipt["outcome"] != "no_op" or not receipt["receipt_digest"].startswith("sha256:")
        or len(receipt["receipt_digest"]) != 71
        or any(ch not in "0123456789abcdef" for ch in receipt["receipt_digest"][7:])):
        raise ScalarInvocationError("scalar.invalid_response")
    return ScalarReceipt(**receipt)


class LocalScalarClient:
    """Caller-bound client, provided by the host, with no runtime fallback."""

    def __init__(self, transport: ScalarTransport) -> None:
        self._transport = transport

    async def invocation_status(
        self, *, object_ref: str, action_ref: str, invocation_key: str,
        recovery_ref: str | None = None,
    ) -> ScalarInvocationStatus:
        """Observe this caller's operation/key without execution or recovery."""
        if (not all(_text(value) for value in (object_ref, action_ref, invocation_key))
            or recovery_ref is not None and not _text(recovery_ref)):
            raise ScalarInvocationError("scalar.invalid_request")
        request = {"contract": "aware.ontology.local-scalar.status-request.v1",
                   "object_ref": object_ref, "action_ref": action_ref,
                   "invocation_key": invocation_key, "recovery_ref": recovery_ref}
        response = await self._transport.exchange(json.dumps(
            request, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode())
        if type(response) is not bytes or len(response) > 65536:
            raise ScalarInvocationError("scalar.invalid_response")
        try:
            row = cast(dict[str, Any], json.loads(response, object_pairs_hook=_unique))
        except (ValueError, UnicodeError) as failure:
            raise ScalarInvocationError("scalar.invalid_response") from failure
        if (type(row) is not dict or set(row) != {
            "contract", "object_ref", "action_ref", "invocation_key", "state",
            "journal_state", "revision", "invocation_ref", "recovery_ref", "backend_receipt"}
            or row["contract"] != "aware.ontology.local-scalar.status.v1"
            or any(row[key] != request[key] for key in ("object_ref", "action_ref", "invocation_key"))):
            raise ScalarInvocationError("scalar.invalid_response")
        states = {"admitted": "pending", "prepared": "pending", "contact_authorized": "pending",
                  "executing": "pending", "recovery_required": "recovery_required",
                  "unavailable_before_contact": "unavailable", "verified_no_effect": "backend_settled"}
        if row["state"] == "not_found":
            if recovery_ref is not None or any(row[key] is not None for key in (
                "journal_state", "revision", "invocation_ref", "recovery_ref", "backend_receipt")):
                raise ScalarInvocationError("scalar.invalid_response")
        elif (type(row["journal_state"]) is not str
              or states.get(row["journal_state"]) != row["state"]
              or type(row["revision"]) is not int or not 1 <= row["revision"] <= 9007199254740991
              or not _text(row["invocation_ref"]) or not _text(row["recovery_ref"])
              or recovery_ref is not None and row["recovery_ref"] != recovery_ref):
            raise ScalarInvocationError("scalar.invalid_response")
        receipt: ScalarReceipt | None = None
        if row["state"] == "backend_settled":
            receipt = _receipt(row["backend_receipt"])
            if receipt.invocation_ref != row["invocation_ref"] or receipt.attempt_ref != row["recovery_ref"]:
                raise ScalarInvocationError("scalar.invalid_response")
        elif row["backend_receipt"] is not None:
            raise ScalarInvocationError("scalar.invalid_response")
        return ScalarInvocationStatus(row["state"], row["journal_state"], row["revision"],
            row["invocation_ref"], row["recovery_ref"], receipt)

    async def invoke_scalar(
        self, *, object_ref: str, action_ref: str, invocation_key: str,
    ) -> ScalarResult:
        if not all(_text(value) for value in (object_ref, action_ref, invocation_key)):
            raise ScalarInvocationError("scalar.invalid_request")
        request = {"contract": "aware.ontology.local-scalar.request.v1",
                   "object_ref": object_ref, "action_ref": action_ref,
                   "invocation_key": invocation_key}
        response = await self._transport.exchange(json.dumps(
            request, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode())
        if type(response) is not bytes or len(response) > 65536:
            raise ScalarInvocationError("scalar.invalid_response")
        try:
            row = cast(dict[str, Any], json.loads(response, object_pairs_hook=_unique))
        except (ValueError, UnicodeError) as failure:
            raise ScalarInvocationError("scalar.invalid_response") from failure
        if (type(row) is not dict
            or row.get("contract") != "aware.ontology.local-scalar.result.v1"
            or row.get("object_ref") != object_ref or row.get("action_ref") != action_ref
            or row.get("invocation_key") != invocation_key):
            raise ScalarInvocationError("scalar.invalid_response")
        if row.get("status") == "refused":
            if set(row) != {"contract", "object_ref", "action_ref", "invocation_key", "status", "code", "recovery_ref"} or not _text(row["code"]):
                raise ScalarInvocationError("scalar.invalid_response")
            if row["recovery_ref"] is not None and not _text(row["recovery_ref"]):
                raise ScalarInvocationError("scalar.invalid_response")
            raise ScalarInvocationError(row["code"], row["recovery_ref"])
        if (set(row) != {"contract", "object_ref", "action_ref", "invocation_key", "status", "value", "receipt", "settled", "worker_cleaned"}
            or row.get("status") != "complete" or row["settled"] is not True
            or row["worker_cleaned"] is not True or type(row["value"]) not in (bool, int, str, type(None))):
            raise ScalarInvocationError("scalar.invalid_response")
        return ScalarResult(row["value"], _receipt(row["receipt"]))
