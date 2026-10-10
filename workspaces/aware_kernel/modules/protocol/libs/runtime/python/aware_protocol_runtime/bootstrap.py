"""Neutral bootstrap values and lifecycle. Physical observations belong to FS.

Harness correlation is not authenticated actor issuance. Decoded evidence never
constructs a plan, admission or physical claim.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import threading
import uuid
from dataclasses import dataclass, field, fields, replace
from types import UnionType
from typing import Any, Literal, cast, get_args, get_origin, get_type_hints
from weakref import WeakKeyDictionary, WeakSet

OPERATION_REF = "protocol_sdk.initialize_profile"


@dataclass(frozen=True, slots=True)
class ProtocolBootstrapRequest:
    repository_root: str
    manifest_path: str = "aware.protocol.toml"
    issue_root: str = "docs/issues"
    directory_paths: tuple[str, ...] = ()
    install_agent_contract: bool = True
    dry_run: bool = True


@dataclass(frozen=True, slots=True)
class ProtocolBootstrapFile:
    path: str
    content_utf8: str
    source_sha256: str
    mode: int


@dataclass(frozen=True, slots=True)
class ProtocolBootstrapInput:
    request: ProtocolBootstrapRequest
    files: tuple[ProtocolBootstrapFile, ...]
    input_sha256: str
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProtocolBootstrapEffect:
    path: str
    kind: str
    state: Literal["none", "applied", "unknown"]
    durability_confirmed: bool
    before_sha256: str | None
    after_sha256: str | None
    after_device: int | None
    after_inode: int | None
    mode: int | None


@dataclass(frozen=True, slots=True)
class ProtocolBootstrapPlanObservation:
    request: ProtocolBootstrapRequest
    plan_ref: str
    plan_sha256: str
    input_sha256: str
    execution_id: str
    phase: str
    ordered_effect_paths: tuple[str, ...]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProtocolBootstrapResult:
    contract: str = field(default="aware.protocol.bootstrap-result.v1", kw_only=True)
    operation_ref: str = field(default=OPERATION_REF, kw_only=True)
    request: ProtocolBootstrapRequest
    outcome: Literal["initialized", "planned", "refused"]
    diagnostics: tuple[str, ...]
    execution_id: str
    attempt_ref: str | None
    manifest_source_sha256: str | None
    manifest_semantic_digest: str | None
    effects: tuple[ProtocolBootstrapEffect, ...]
    cleanup_state: Literal["not_attempted", "completed", "incomplete", "unknown"]
    ledger_complete: bool
    provider_invoked: bool
    authorizes_retry: bool = False


@dataclass(frozen=True, slots=True)
class ProtocolBootstrapErrorEvidence:
    contract: str = field(default="aware.protocol.bootstrap-error.v1", kw_only=True)
    operation_ref: str = field(default=OPERATION_REF, kw_only=True)
    request: ProtocolBootstrapRequest
    code: str
    phase: str
    execution_id: str
    attempt_ref: str | None
    effects: tuple[ProtocolBootstrapEffect, ...]
    cleanup_state: Literal["not_attempted", "completed", "incomplete", "unknown"]
    ledger_complete: bool
    provider_invoked: bool
    reported_result: object
    evidence_grade: str = field(default="unvalidated_provider_report", kw_only=True)
    diagnostics: tuple[str, ...]
    authorizes_retry: bool = False


class ProtocolBootstrapValueError(ValueError):
    pass


class ProtocolBootstrapError(RuntimeError):
    def __init__(self, *, evidence: ProtocolBootstrapErrorEvidence):
        super().__init__(evidence.code)
        self.evidence = evidence


_VALUES = (
    ProtocolBootstrapRequest,
    ProtocolBootstrapFile,
    ProtocolBootstrapInput,
    ProtocolBootstrapEffect,
    ProtocolBootstrapPlanObservation,
    ProtocolBootstrapResult,
    ProtocolBootstrapErrorEvidence,
)


def digest(source: bytes) -> str:
    return "sha256:" + hashlib.sha256(source).hexdigest()


def _root_type(value: object) -> bool:
    return any(value is declared for declared in _VALUES)


def _json(value: Any) -> Any:
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) is list:
        return [_json(item) for item in value]
    if type(value) is dict and all(type(key) is str for key in value):
        return {key: _json(item) for key, item in value.items()}
    raise ProtocolBootstrapValueError("bootstrap_json_value_required")


def unvalidated_report(value: Any, *, _seen=None, _depth=0) -> Any:
    seen = set() if _seen is None else _seen
    if id(value) in seen or _depth >= 32:
        return {
            "unvalidated_type": "cycle_or_depth_bound",
            "reason": "cycle_or_depth_bound",
        }

    def child(item):
        return unvalidated_report(item, _seen=seen | {id(value)}, _depth=_depth + 1)

    if _root_type(type(value)):
        result = {}
        for item in fields(value):
            try:
                member = object.__getattribute__(value, item.name)
            except AttributeError:
                result[item.name] = {"unvalidated_missing_field": True}
            else:
                result[item.name] = child(member)
        return result
    if type(value) in (tuple, list):
        return [child(item) for item in value]
    if type(value) is dict and all(type(key) is str for key in value):
        return {key: child(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    return {"unvalidated_type": "unsupported"}


def _convert(annotation, value, *, decode):
    origin, arguments = get_origin(annotation), get_args(annotation)
    if origin is UnionType:
        for member in arguments:
            try:
                return _convert(member, value, decode=decode)
            except ProtocolBootstrapValueError:
                pass
        raise ProtocolBootstrapValueError("bootstrap_union_value_required")
    if annotation is type(None) and value is None:
        return None
    if annotation is object:
        return _json(value)
    if origin is Literal:
        if any(type(value) is type(item) and value == item for item in arguments):
            return value
    elif origin is tuple:
        if type(value) is (list if decode else tuple):
            return (
                tuple(_convert(arguments[0], item, decode=decode) for item in value)
                if decode
                else [_convert(arguments[0], item, decode=decode) for item in value]
            )
    elif _root_type(annotation):
        if decode:
            return protocol_bootstrap_value_from_payload(annotation, value)
        if type(value) is annotation:
            return protocol_bootstrap_value_to_payload(value)
    elif annotation in (str, bool, int) and type(value) is annotation:
        return value
    raise ProtocolBootstrapValueError("bootstrap_exact_value_required")


def _semantic(value: Any) -> None:
    for item in fields(value):
        if "sha256" in item.name or item.name == "manifest_semantic_digest":
            observed = getattr(value, item.name)
            if (
                observed is not None
                and re.fullmatch(r"sha256:[0-9a-f]{64}", observed) is None
            ):
                raise ProtocolBootstrapValueError("bootstrap_digest_invalid")
    if type(value) is ProtocolBootstrapRequest and (
        not value.repository_root
        or "\x00" in value.repository_root
        or len(value.directory_paths) > 64
    ):
        raise ProtocolBootstrapValueError("bootstrap_request_invalid")
    if type(value) is ProtocolBootstrapFile and (
        value.mode != 0o644
        or digest(value.content_utf8.encode()) != value.source_sha256
    ):
        raise ProtocolBootstrapValueError("bootstrap_file_invalid")
    if type(value) in (ProtocolBootstrapResult, ProtocolBootstrapErrorEvidence):
        carrier = cast(ProtocolBootstrapResult | ProtocolBootstrapErrorEvidence, value)
        expected = (
            "aware.protocol.bootstrap-result.v1"
            if type(value) is ProtocolBootstrapResult
            else "aware.protocol.bootstrap-error.v1"
        )
        if (
            carrier.contract != expected
            or carrier.operation_ref != OPERATION_REF
            or carrier.authorizes_retry
        ):
            raise ProtocolBootstrapValueError("bootstrap_result_identity_invalid")
        if (
            type(value) is ProtocolBootstrapResult
            and value.outcome == "refused"
            and not any(text.strip() for text in value.diagnostics)
        ):
            raise ProtocolBootstrapValueError("bootstrap_refusal_diagnostics_required")


def protocol_bootstrap_value_to_payload(value):
    if not _root_type(type(value)):
        raise ProtocolBootstrapValueError("bootstrap_original_value_required")
    hints = get_type_hints(type(value))
    payload = {
        item.name: _convert(hints[item.name], getattr(value, item.name), decode=False)
        for item in fields(value)
    }
    _semantic(value)
    return payload


def protocol_bootstrap_value_from_payload(root, payload):
    if (
        not _root_type(root)
        or type(payload) is not dict
        or set(payload) != {item.name for item in fields(root)}
    ):
        raise ProtocolBootstrapValueError("bootstrap_exact_fields_required")
    hints = get_type_hints(root)
    value = root(
        **{
            name: _convert(hints[name], item, decode=True)
            for name, item in payload.items()
        }
    )
    _semantic(value)
    return value


def protocol_bootstrap_value_to_json(value):
    return json.dumps(
        protocol_bootstrap_value_to_payload(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def protocol_bootstrap_value_from_json(root, source):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ProtocolBootstrapValueError("bootstrap_duplicate_json_key")
            result[key] = value
        return result

    return protocol_bootstrap_value_from_payload(
        root, json.loads(source, object_pairs_hook=pairs)
    )


def detached(value):
    return protocol_bootstrap_value_from_payload(
        type(value), protocol_bootstrap_value_to_payload(value)
    )


def _execution():
    identities = [
        prefix + os.environ[name].strip()
        for name, prefix in (
            ("CODEX_THREAD_ID", "codex-"),
            ("CLAUDE_CODE_SESSION_ID", "claude_code-"),
        )
        if os.environ.get(name, "").strip()
    ]
    if len(identities) != 1 or any(character.isspace() for character in identities[0]):
        raise ValueError("unambiguous_provider_execution_required")
    return identities[0]


_PHYSICAL_TYPES = set()
_SELECTED = WeakSet()
_OWNERS = WeakKeyDictionary()
_CLAIMS = WeakKeyDictionary()
_CLAIM_LOCK = threading.Lock()


class _Handle:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable] -- initialized by Python

    def __new__(cls):
        raise TypeError("original_bootstrap_issuer_required")

    def __copy__(self):
        raise TypeError("bootstrap_handle_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("bootstrap_handle_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("bootstrap_handle_not_serializable")


def _owner(handle):
    if (
        type(handle) is not ProtocolBootstrapPlan
        and type(handle) is not ProtocolBootstrapAdmission
    ):
        raise ValueError("original_bootstrap_handle_required")
    owner = _OWNERS.get(handle)
    if owner is None:
        raise ValueError("original_bootstrap_handle_required")
    return owner


class ProtocolBootstrapPlan(_Handle):
    __slots__ = ()

    def observe(self):
        return _owner(self).observe_plan(self)

    def release(self):
        _owner(self).release_plan(self)

    def __enter__(self):
        self.observe()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.release()
        return False

    def __del__(self):
        try:
            self.release()
        except BaseException:  # noqa: BLE001 -- finalizer preserves the active exception
            return  # Fallback disposal is not completion evidence.


class ProtocolBootstrapAdmission(_Handle):
    __slots__ = ()

    def release(self):
        _owner(self).release_admission(self)

    def __del__(self):
        try:
            self.release()
        except BaseException:  # noqa: BLE001 -- finalizer is not completion evidence
            return


class _Claim(_Handle):
    __slots__ = ()

    def release(self):
        with _CLAIM_LOCK:
            _CLAIMS.pop(self, None)


def _consume_claim(claim, physical):
    with _CLAIM_LOCK:
        record = _CLAIMS.get(claim) if type(claim) is _Claim else None
        if record is None or record[0] is not physical:
            raise ValueError("original_bootstrap_claim_required")
        del _CLAIMS[claim]
    if record[1] != os.getpid() or record[2] != _execution():
        raise ValueError("bootstrap_claim_execution_changed")


@dataclass
class _State:
    request: ProtocolBootstrapRequest
    rendered: ProtocolBootstrapInput
    physical: Any
    plan_ref: str
    plan_sha256: str
    phase: str = "planned"
    attempt_ref: str | None = None
    provider_invoked: bool = False


class _BootstrapRuntime:
    """Original lifecycle. Physical port types register through owning FS only."""

    def __init__(self, *, physical, repository_root, execution_id):
        if not any(type(physical) is declared for declared in _PHYSICAL_TYPES):
            raise TypeError("original_bootstrap_physical_owner_required")
        if execution_id != _execution():
            raise ValueError("bootstrap_execution_mismatch")
        self.physical = physical
        self.repository_root = repository_root
        self.execution_id = execution_id
        self.pid = os.getpid()
        self.lock = threading.RLock()
        self.plans = WeakKeyDictionary()
        self.admissions = WeakKeyDictionary()
        self.generation = uuid.uuid4().hex
        self.last_evidence = None
        self.last_original_result = None

    def _current(self):
        if self.pid != os.getpid() or self.execution_id != _execution():
            raise ValueError("bootstrap_execution_changed")

    def _request(self, request):
        request = detached(request)
        if (
            type(request) is not ProtocolBootstrapRequest
            or request.repository_root != self.repository_root
        ):
            raise ValueError("bootstrap_request_root_mismatch")
        return request

    def _issue(self, kind):
        if self not in _SELECTED:
            raise ValueError("original_bootstrap_client_selection_required")
        handle = object.__new__(kind)
        _OWNERS[handle] = self
        return handle

    def _error(self, request, code, phase, state=None, report=None):
        evidence = ProtocolBootstrapErrorEvidence(
            state.request if state is not None else request,
            code,
            phase,
            self.execution_id,
            state.attempt_ref if state else None,
            state.physical.effects if state else (),
            state.physical.cleanup_state if state else "not_attempted",
            False,
            state.provider_invoked if state else False,
            report,
            (code,),
        )
        self.last_evidence = detached(evidence)
        return ProtocolBootstrapError(evidence=detached(evidence))

    def render(self, request):
        request = self._request(request)
        self._current()
        return detached(self.physical.render(request))

    def plan_initialization(self, request):
        request = self._request(request)
        with self.lock:
            physical = None
            state = None
            rendered = None
            try:
                self._current()
                rendered = self.render(request)
                physical = self.physical.retain(rendered)
                payload = {
                    "input": protocol_bootstrap_value_to_payload(rendered),
                    "topology": physical.plan_digest(),
                    "execution": self.execution_id,
                    "generation": self.generation,
                }
                state = _State(
                    request,
                    rendered,
                    physical,
                    "protocol-plan:" + uuid.uuid4().hex,
                    digest(
                        json.dumps(
                            payload, sort_keys=True, separators=(",", ":")
                        ).encode()
                    ),
                )
                plan = self._issue(ProtocolBootstrapPlan)
                self.plans[plan] = state
                return plan
            except BaseException as error:
                if physical is not None and rendered is not None:
                    if state is None:
                        state = _State(
                            request, rendered, physical, "", rendered.input_sha256
                        )
                    state.phase = "retired"
                    try:
                        physical.release()
                    except BaseException:  # noqa: BLE001 -- original failure and cleanup uncertainty both survive
                        state.phase = "retired"
                raise self._error(
                    request, "protocol_bootstrap_plan_refused", "plan", state
                ) from error

    def _retire(self, state):
        state.phase = "retired"
        state.physical.release()

    def observe_plan(self, plan):
        if type(plan) is not ProtocolBootstrapPlan:
            raise ValueError("original_bootstrap_plan_required")
        with self.lock:
            state = self.plans.get(plan)
            if state is None:
                raise ValueError("original_bootstrap_plan_required")
            if state.phase not in ("consumed", "retired"):
                try:
                    self._current()
                    state.physical.validate_current()
                except BaseException as error:  # noqa: BLE001 -- interruption terminally retires custody
                    try:
                        self._retire(state)
                    finally:
                        raise self._error(
                            state.request,
                            "protocol_bootstrap_plan_stale",
                            "observation",
                            state,
                        ) from error
            return detached(
                ProtocolBootstrapPlanObservation(
                    state.request,
                    state.plan_ref,
                    state.plan_sha256,
                    state.rendered.input_sha256,
                    self.execution_id,
                    state.phase,
                    (
                        *state.request.directory_paths,
                        *(item.path for item in state.rendered.files),
                    ),
                    state.rendered.diagnostics,
                )
            )

    def release_plan(self, plan):
        if type(plan) is not ProtocolBootstrapPlan:
            raise ValueError("original_bootstrap_plan_required")
        with self.lock:
            state = self.plans.get(plan)
            if state is not None and state.phase != "consumed":
                try:
                    self._retire(state)
                except BaseException as error:
                    raise self._error(
                        state.request,
                        "protocol_bootstrap_cleanup_unverified",
                        "cleanup",
                        state,
                    ) from error

    def release_admission(self, admission):
        if type(admission) is not ProtocolBootstrapAdmission:
            raise ValueError("original_bootstrap_admission_required")
        with self.lock:
            plan = self.admissions.pop(admission, None)
            if plan is not None:
                self.release_plan(plan)

    def admit_initialization(self, plan):
        if type(plan) is not ProtocolBootstrapPlan:
            raise ValueError("original_bootstrap_plan_required")
        with self.lock:
            state = self.plans.get(plan)
            if state is None:
                raise ValueError("original_bootstrap_plan_required")
            try:
                self._current()
                if state.phase != "planned" or state.request.dry_run:
                    raise ValueError("bootstrap_plan_not_admittable")
                state.physical.validate_current()
                admission = self._issue(ProtocolBootstrapAdmission)
                self.admissions[admission] = plan
                state.phase = "admitted"
                return admission
            except BaseException as error:  # noqa: BLE001 -- interrupted admission must retire
                try:
                    self._retire(state)
                finally:
                    raise self._error(
                        state.request,
                        "protocol_bootstrap_admission_refused",
                        "admission",
                        state,
                    ) from error

    def snapshot_failure(self, request, *, admission=None):
        """Retire only this owner's admission, without invoking an operation.

        The selected-root context is used only if no genuine retained request
        exists; diagnostics mark it as context, never a substitute dispatch.
        """
        with self.lock:
            self.last_evidence = self.last_original_result = None
            plan = (
                self.admissions.pop(admission, None)
                if type(admission) is ProtocolBootstrapAdmission
                else None
            )
            state = self.plans.get(plan) if plan is not None else None
            if state is not None:
                try:
                    self._retire(state)
                except BaseException:  # noqa: BLE001 -- preserve original cleanup uncertainty, never retry
                    state.phase = "retired"
            context = (
                state.request
                if state is not None
                else ProtocolBootstrapRequest(self.repository_root)
            )
            error = self._error(
                context,
                "protocol_bootstrap_request_snapshot_failed",
                "snapshot",
                state,
                unvalidated_report(request),
            )
            if state is None:
                error = ProtocolBootstrapError(
                    evidence=detached(
                        replace(
                            error.evidence,
                            diagnostics=(
                                error.evidence.code,
                                "request_is_selected_root_context_not_invocation",
                            ),
                        )
                    )
                )
                self.last_evidence = detached(error.evidence)
            return error

    def initialize_profile(self, request, *, admission=None):
        with self.lock:
            self.last_evidence = self.last_original_result = None
            plan = (
                self.admissions.pop(admission, None)
                if type(admission) is ProtocolBootstrapAdmission
                else None
            )
            state = self.plans.get(plan) if plan is not None else None
            if admission is not None and state is None:
                raise self._error(
                    request, "original_bootstrap_admission_required", "admission"
                )
            previous = state.phase if state else None
            if state:
                state.phase = "spent"
                state.attempt_ref = "protocol-attempt:" + uuid.uuid4().hex
            try:
                request = self._request(request)
                self._current()
                if request.dry_run:
                    if admission is not None:
                        raise ValueError("bootstrap_preview_admission_refused")
                    plan = self.plan_initialization(request)
                    state = self.plans[plan]
                    state.phase = "spent"
                elif (
                    state is None or previous != "admitted" or state.request != request
                ):
                    raise ValueError("bootstrap_apply_admission_required")
                state.physical.validate_current()
                source, semantic = None, None
                if not request.dry_run:
                    state.provider_invoked = True
                    claim = object.__new__(_Claim)
                    with _CLAIM_LOCK:
                        _CLAIMS[claim] = (state.physical, self.pid, self.execution_id)
                    try:
                        source, semantic = state.physical.apply(claim=claim)
                    finally:
                        claim.release()
                state.physical.release()
                if state.physical.cleanup_state != "completed":
                    raise ValueError("bootstrap_cleanup_unverified")
                self._current()
                result = ProtocolBootstrapResult(
                    request,
                    "planned" if request.dry_run else "initialized",
                    state.rendered.diagnostics,
                    self.execution_id,
                    state.attempt_ref,
                    source,
                    semantic,
                    state.physical.effects,
                    "completed",
                    True,
                    state.provider_invoked,
                )
                self.last_evidence = detached(
                    ProtocolBootstrapErrorEvidence(
                        state.request,
                        "protocol_bootstrap_result_invalid",
                        "result",
                        self.execution_id,
                        state.attempt_ref,
                        state.physical.effects,
                        "completed",
                        False,
                        state.provider_invoked,
                        None,
                        ("protocol_bootstrap_result_invalid",),
                    )
                )
                self.last_original_result = detached(result)
                state.phase = "consumed"
                return detached(result)
            except BaseException as error:
                if state is not None:
                    try:
                        self._retire(state)
                    except BaseException:  # noqa: BLE001 -- retain original failure and unknown cleanup
                        state.phase = "retired"
                if isinstance(error, ProtocolBootstrapError):
                    raise
                raise self._error(
                    request, "protocol_bootstrap_failed", "initialize", state
                ) from error

    def result_failure(self, request, report):
        with self.lock:
            evidence = self.last_evidence
            if evidence is None:
                evidence = self._error(
                    request, "protocol_bootstrap_result_invalid", "result"
                ).evidence
            return ProtocolBootstrapError(
                evidence=detached(
                    replace(
                        evidence,
                        code="protocol_bootstrap_result_invalid",
                        phase="result",
                        reported_result=report,
                        ledger_complete=False,
                    )
                )
            )
