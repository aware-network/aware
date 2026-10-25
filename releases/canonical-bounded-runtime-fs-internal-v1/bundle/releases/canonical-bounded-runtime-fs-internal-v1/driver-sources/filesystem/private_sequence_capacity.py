"""Read-only original-owner private sequence capacity and detached wire values.

Module identity is captured at import, never by a forecasting operation. This
single-batch model does not reserve future terminal capacity or physical space.
"""

from __future__ import annotations

import hashlib
import json
import sys
import types
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .confined_mutation import ConfinedFileMutationRequest, ConfinedMutationProfile
    from .private_directory import (
        PrivateDirectoryBinding,
        PrivateDirectoryObservation,
        RetainedPrivateDirectory,
    )
    from .retained_file_sequence import ConfinedSequenceLimits

SCHEMA = "aware.filesystem.private-sequence-capacity.v1"
SCHEDULE = "release_receiving_single_batch_v1"
MAX_FORECAST_BYTES = 2097152
MAX_JSON_DEPTH = 32
MAX_JSON_TOKENS = 65536
MAX_REQUESTS = 9
MAX_REQUEST_BYTES = 1048576
MAX_TOTAL_REQUEST_BYTES = 8388608
MAX_MODEL_MODULES = 16
_VERSION = "0.3.10"
_MAX_INT = 2**63 - 1

type CapacityCode = Literal[
    "capacity_input_invalid",
    "capacity_original_parent_required",
    "capacity_binding_mismatch",
    "capacity_parent_unavailable",
    "capacity_model_mismatch",
    "capacity_schedule_unsupported",
    "capacity_model_unavailable",
    "capacity_forecast_invalid",
    "capacity_capture_interrupted",
]


@dataclass(frozen=True, slots=True)
class CapacityModelIdentity:
    distribution: Literal["aware-file-system"]
    version: str
    model: Literal["private_sequence_evidence_v1"]
    modules: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class CapacityBound:
    name: str
    used: int
    additional: int
    ceiling: int


@dataclass(frozen=True, slots=True)
class PrivateSequenceCapacityForecast:
    schema: Literal["aware.filesystem.private-sequence-capacity.v1"]
    model: CapacityModelIdentity
    schedule: Literal["release_receiving_single_batch_v1"]
    binding: PrivateDirectoryBinding
    observation: PrivateDirectoryObservation
    history_sha256: str
    request_sha256: str
    decision: Literal["within_model", "exceeds_model"]
    bounds: tuple[CapacityBound, ...]
    physical_validation: Literal["not_performed"]
    reservation: Literal["not_performed"]
    filesystem_effect: Literal["none"]
    grants_admission: Literal[False]
    permits_dispatch: Literal[False]
    authorizes_retry: Literal[False]
    future_terminal_capacity: Literal["not_established"]


class PrivateSequenceCapacityError(ValueError):
    code: CapacityCode
    stage: Literal["lookup", "input", "model", "capture", "encode", "decode"]
    original_inputs: object
    original_cause: BaseException
    historical_observation: PrivateDirectoryObservation | None
    original_forecast: object
    interruption: bool
    parent_mutation: Literal["none"]
    filesystem_effect: Literal["none"]
    physical_validation: Literal["not_performed"]
    grants_admission: Literal[False]
    permits_dispatch: Literal[False]
    authorizes_retry: Literal[False]
    permits_disposal_replay: Literal[False]

    def __init__(
        self,
        code,
        stage,
        original_inputs,
        original_cause,
        historical_observation=None,
        original_forecast=None,
    ):
        interruption = not isinstance(original_cause, Exception)
        if (
            type(original_cause) is _Fault
            and str(original_cause) == "capacity_original_parent_required"
        ):
            # Original lookup normalizes BaseException into a typed refusal.
            # Preserve that evidence without retrying lookup or following an
            # arbitrary exception graph. Both original wrappers stay intact.
            original = original_cause.__cause__
            owner = _owner()
            if type(original) is owner.PrivateDirectoryRefusal:
                evidence = getattr(original, "evidence", None)
                interruption = (
                    evidence is not None
                    and type(evidence) is owner.PrivateDirectoryRefusalEvidence
                    and type(evidence.primary_failure)
                    is owner.ConfinedSequencePrimaryFailure
                    and evidence.primary_failure.interruption is True
                )
                if interruption:
                    code = "capacity_capture_interrupted"
        super().__init__(code)
        self.code = code
        self.stage = stage
        self.original_inputs = original_inputs
        self.original_cause = original_cause
        self.historical_observation = historical_observation
        self.original_forecast = original_forecast
        self.interruption = interruption
        self.parent_mutation = "none"
        self.filesystem_effect = "none"
        self.physical_validation = "not_performed"
        self.grants_admission = False
        self.permits_dispatch = False
        self.authorizes_retry = False
        self.permits_disposal_replay = False


class _Fault(ValueError):
    pass


_MODEL = None
_MODEL_BYTES = None
_FUNCTIONS = ()
_CLASSES = ()
_METHODS = ()


def _owner():
    if type(__package__) is not str:
        raise _Fault("capacity_model_unavailable")
    return sys.modules[__package__ + ".private_directory"]


def _safe_data(value, active=None, depth=0):
    """Keep original data references, never rejected custody in an error graph."""
    active = set() if active is None else active
    try:
        kind = type(value)
        if kind in (str, bytes, int, bool, type(None)):
            return value, False
        owner = _owner()
        if kind in (
            owner.native.ConfinedMutationKind,
            owner.native.ConfinedMutationProfile,
        ):
            return value, False
        if depth > 32 or id(value) in active:
            return {"invalid_input": "cycle_or_depth"}, True
        active.add(id(value))
        try:
            if kind in (tuple, list):
                if len(value) > 16384:
                    return {"invalid_input": "too_many_items"}, True
                pairs = [_safe_data(item, active, depth + 1) for item in value]
                if not any(changed for _, changed in pairs):
                    return value, False
                return tuple(item for item, _ in pairs), True
            if (
                kind is dict
                and len(value) <= 16384
                and all(type(k) is str for k in value)
            ):
                pairs = {
                    key: _safe_data(item, active, depth + 1)
                    for key, item in value.items()
                }
                if not any(changed for _, changed in pairs.values()):
                    return value, False
                return {key: item for key, (item, _) in pairs.items()}, True
            schemas = {row[0]: row[-1] for row in _CLASSES}
            if kind in schemas:
                pairs = {}
                for name, slot in schemas[kind]:
                    if slot is None:
                        return {
                            "invalid_input": type.__getattribute__(kind, "__name__")
                        }, True
                    pairs[name] = _safe_data(
                        slot.__get__(value, kind), active, depth + 1
                    )
                if not any(changed for _, changed in pairs.values()):
                    return value, False
                return {
                    "invalid_input": type.__getattribute__(kind, "__name__"),
                    "fields": {key: item for key, (item, _) in pairs.items()},
                }, True
            return {"invalid_input": type.__getattribute__(kind, "__name__")}, True
        finally:
            active.discard(id(value))
    finally:
        value = None


def _initialize_model():
    """Import-time identity; no per-call filesystem or metadata discovery."""
    global _MODEL, _MODEL_BYTES, _FUNCTIONS, _CLASSES, _METHODS
    owner = _owner()
    globals().update(
        PrivateDirectoryBinding=owner.PrivateDirectoryBinding,
        PrivateDirectoryObservation=owner.PrivateDirectoryObservation,
        RetainedPrivateDirectory=owner.RetainedPrivateDirectory,
        ConfinedFileMutationRequest=owner.native.ConfinedFileMutationRequest,
        ConfinedMutationProfile=owner.native.ConfinedMutationProfile,
        ConfinedSequenceLimits=owner.sequence.ConfinedSequenceLimits,
    )
    modules = (owner, owner.sequence, owner.native, sys.modules[__name__])
    _MODEL = CapacityModelIdentity(
        "aware-file-system",
        _VERSION,
        "private_sequence_evidence_v1",
        tuple(
            sorted(
                (
                    "aware_file_system/" + _module_source_path(module).name,
                    hashlib.sha256(
                        _module_source_path(module).read_bytes()
                    ).hexdigest(),
                )
                for module in modules
            )
        ),
    )
    _FUNCTIONS = tuple(
        (module, name, value, value.__code__)
        for module in modules
        for name, value in vars(module).items()
        if type(value) is types.FunctionType and value.__module__ == module.__name__
    )
    _CLASSES = tuple(
        (
            cls,
            cls.__init__,
            cls.__init__.__code__,
            cls.__getattribute__,
            cls.__new__,
            sys.modules[cls.__module__],
            cls.__name__,
            tuple((f.name, vars(cls).get(f.name)) for f in fields(cls)),
        )
        for cls in (
            CapacityModelIdentity,
            CapacityBound,
            PrivateSequenceCapacityForecast,
            *owner._WIRES,
            owner.sequence._SequenceState,
            owner.native.ConfinedFileMutationRequest,
        )
    )
    _METHODS = tuple(
        (row[0], name, method, method.__code__)
        for row in _CLASSES
        for name, method in vars(row[0]).items()
        if type(method) is types.FunctionType
    )
    _MODEL_BYTES = _canonical(_model_payload(_MODEL))
    return _MODEL


def _module_source_path(module):
    source = module.__file__
    if type(source) is not str:
        raise ValueError("capacity model requires its original source members")
    return Path(source)


def _authenticate():
    if _MODEL is None or any(
        getattr(module, name, None) is not function or function.__code__ is not code
        for module, name, function, code in _FUNCTIONS
    ):
        raise _Fault("capacity_model_mismatch")
    for cls, init, code, getattribute, new, module, name, slots in _CLASSES:
        if (
            getattr(module, name, None) is not cls
            or cls.__new__ is not new
            or cls.__init__ is not init
            or init.__code__ is not code
            or cls.__getattribute__ is not getattribute
            or any(vars(cls).get(name) is not slot for name, slot in slots)
        ):
            raise _Fault("capacity_model_mismatch")
    if any(
        vars(cls).get(name) is not method or method.__code__ is not code
        for cls, name, method, code in _METHODS
    ):
        raise _Fault("capacity_model_mismatch")
    if _canonical(_model_payload(_MODEL)) != _MODEL_BYTES:
        raise _Fault("capacity_model_mismatch")


def _text(value, maximum):
    if type(value) is not str or not value or len(value) > maximum:
        raise ValueError("invalid text")
    if any(
        ord(c) < 32 or 0x7F <= ord(c) <= 0x9F or 0xD800 <= ord(c) <= 0xDFFF
        for c in value
    ):
        raise ValueError("invalid text")
    if len(value.encode("utf-8")) > maximum:
        raise ValueError("text too long")
    return value


def _digest(value):
    if (
        type(value) is not str
        or len(value) != 64
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise ValueError("invalid digest")
    return value


def _integer(value, *, positive=False):
    if type(value) is not int or not (1 if positive else 0) <= value <= _MAX_INT:
        raise ValueError("invalid integer")
    return value


def _canonical(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _model_payload(value):
    if type(value) is not CapacityModelIdentity:
        raise ValueError("original model value required")
    if (
        type(value.distribution) is not str
        or value.distribution != "aware-file-system"
        or type(value.model) is not str
        or value.model != "private_sequence_evidence_v1"
    ):
        raise ValueError("invalid model literals")
    _text(value.version, 128)
    if (
        type(value.modules) is not tuple
        or not 1 <= len(value.modules) <= MAX_MODEL_MODULES
    ):
        raise ValueError("invalid module closure")
    paths = []
    for row in value.modules:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError("invalid module row")
        path, digest = row
        _text(path, 4096)
        if (
            path.startswith("/")
            or "\\" in path
            or any(p in ("", ".", "..") for p in path.split("/"))
        ):
            raise ValueError("invalid module path")
        _digest(digest)
        paths.append(path)
    if paths != sorted(set(paths)):
        raise ValueError("unordered module closure")
    return {
        "distribution": value.distribution,
        "version": value.version,
        "model": value.model,
        "modules": [list(row) for row in value.modules],
    }


def _limits(count):
    return {
        "ancestor_guards": 1,
        "binding_metadata_bytes": 2097152,
        "created_ancestor_paths": 1,
        "file_bytes": 1048576,
        "file_transitions": count,
        "input_files": count,
        "path_components": 1,
        "path_utf8_bytes": 128,
        "physical_step_count": 128,
        "retained_before_and_after_bytes": 8388608,
        "scratch_paths": count,
        "simultaneous_live_scratch": 1,
        "simultaneous_owned_descriptors": 96,
    }


def _request_payload(binding, requests, limits, profile, schedule):
    owner = _owner()
    sequence, native = owner.sequence, owner.native
    if schedule != SCHEDULE or type(schedule) is not str:
        raise _Fault("capacity_schedule_unsupported")
    if (
        type(profile) is not native.ConfinedMutationProfile
        or profile is not native.ConfinedMutationProfile.DESCRIPTOR_WALK_V1
    ):
        raise _Fault("capacity_schedule_unsupported")
    if type(requests) is not tuple or not 1 <= len(requests) <= MAX_REQUESTS:
        raise ValueError("invalid requests")
    if type(limits) is not sequence.ConfinedSequenceLimits:
        raise ValueError("original limits required")
    actual_limits = {name: getattr(limits, name) for name in sequence._LIMIT_CAPS}
    if any(
        type(v) is not int for v in actual_limits.values()
    ) or actual_limits != _limits(len(requests)):
        raise _Fault("capacity_schedule_unsupported")
    if (
        native.ConfinedFileMutationRequest is not sequence._REQUEST_TYPE
        or sequence._REQUEST_TYPE.__init__ is not sequence._REQUEST_INIT[0]
        or sequence._REQUEST_INIT[0].__code__ is not sequence._REQUEST_INIT[1]
        or sequence._REQUEST_TYPE.__post_init__ is not sequence._REQUEST_POST[0]
        or sequence._REQUEST_POST[0].__code__ is not sequence._REQUEST_POST[1]
        or any(
            vars(sequence._REQUEST_TYPE).get(name) is not slot
            for name, slot in sequence._REQUEST_SLOTS
        )
    ):
        raise _Fault("capacity_model_mismatch")
    rows, paths, total = [], set(), 0
    for request in requests:
        if type(request) is not sequence._REQUEST_TYPE:
            raise ValueError("original request required")
        data = {
            name: slot.__get__(request, sequence._REQUEST_TYPE)
            for name, slot in sequence._REQUEST_SLOTS
        }
        path, body = data["path"], data["content"]
        _text(path, 128)
        sequence._path(path)
        if (
            "/" in path
            or path in paths
            or type(body) is not bytes
            or len(body) > MAX_REQUEST_BYTES
            or data["kind"] is not native.ConfinedMutationKind.CREATE
            or data["expected_exists"] is not False
            or data["expected_content_digest"] is not None
            or type(data["text_replacements"]) is not tuple
            or data["text_replacements"]
        ):
            raise ValueError("unsupported request")
        maximum = _integer(data["maximum_bytes"], positive=True)
        if len(body) > maximum or maximum > native.DEFAULT_CONFINED_MUTATION_MAX_BYTES:
            raise ValueError("invalid request maximum")
        paths.add(path)
        total += len(body)
        rows.append(
            {
                "kind": "create",
                "path": path,
                "expected_exists": False,
                "expected_content_digest": None,
                "content_sha256": hashlib.sha256(body).hexdigest(),
                "content_bytes": len(body),
                "maximum_bytes": maximum,
            }
        )
    if total > MAX_TOTAL_REQUEST_BYTES:
        raise ValueError("total content exceeds profile")
    return {
        "binding": owner.private_directory_value_to_payload(binding),
        "schedule": schedule,
        "confinement_profile": profile.value,
        "limits": actual_limits,
        "requests": rows,
    }


def _prospective_binding(binding, requests, limits):
    """Descriptive upper binding only; never enrolled in an owner registry."""
    s = _owner().sequence
    state = s._SequenceState(
        Path(binding.root_locator),
        (binding.device, binding.inode),
        requests,
        limits,
        "aware.filesystem.file-sequence.v1",
        "sequence-generation:" + "f" * 32,
        "sequence-preparation:" + "f" * 32,
        binding.process_id,
        binding.thread_id,
    )
    absent = s.ConfinedSequenceFileObservation(
        "observed", False, None, None, None, None, None, None, None
    )
    files, steps = [], []
    for index, request in enumerate(requests):
        scratch = s._sequence_scratch_path(state.root, state.root_identity, request)
        files.append(
            s.ConfinedSequenceFileBinding(
                index,
                "create",
                request.path,
                absent,
                "sha256:" + hashlib.sha256(request.content).hexdigest(),
                len(request.content),
                scratch,
                s._MODE,
            )
        )
        for kind in s._sequence_file_step_kinds(False, 0):
            steps.append(
                s._step_for(
                    state,
                    len(steps),
                    index,
                    kind,
                    scratch if kind.startswith("scratch_") else request.path,
                    (),
                    absent,
                    absent,
                    mode=0o666 if kind == "scratch_create" else None,
                )
            )
    return s.ConfinedSequenceBinding(
        state.provider_ref,
        state.generation,
        state.preparation_ref,
        str(state.root),
        state.root_identity,
        state.pid,
        state.thread,
        "descriptor_walk_v1",
        s._MODE,
        limits,
        tuple(files),
        (),
        tuple(steps),
        "sha256:" + "f" * 64,
    )


def _bounds(binding, observation, acquisitions, requests, limits):
    owner, count = _owner(), len(requests)
    # Uniform upper description: the longest allowed JSON-escaped leaf and
    # largest candidate size. No retained bodies or invented issued handles.
    # Recomputable from detached binding/count; codecs can check every charge.
    descriptive_requests = tuple(
        owner.native.ConfinedFileMutationRequest(
            owner.native.ConfinedMutationKind.CREATE,
            '"' * (128 - len(str(index))) + str(index),
            False,
            None,
            b"",
        )
        for index in range(count)
    )
    described = _prospective_binding(binding, descriptive_requests, limits)
    prospective = replace(
        described,
        files=tuple(
            replace(row, candidate_size_bytes=MAX_REQUEST_BYTES)
            for row in described.files
        ),
        ordered_steps=tuple(
            replace(row, candidate_size_bytes=MAX_REQUEST_BYTES)
            for row in described.ordered_steps
        ),
    )
    steps = len(prospective.ordered_steps)
    # Native preparation reads absent leaves/scratch and rechecks the leaves.
    # Include failed final reads and the extra per-dispatch guard in the whole
    # history reservation. This is an upper description, not extra capacity.
    resource_rows = 6 * count + 16
    reserved, validations = owner._private_sequence_reservation(
        Path(binding.root_locator),
        prospective,
        resource_rows,
        whole=True,
    )
    if resource_rows + 4 * count * steps + 12 * count + 8 > 16384:
        raise _Fault("capacity_model_unavailable")
    additional = {
        "ancestor_guards": 0,
        "binding_metadata_bytes": max(
            reserved, owner.sequence._sequence_metadata_reservation(steps, count)
        ),
        "created_ancestor_paths": 0,
        "file_bytes": MAX_REQUEST_BYTES,
        "file_transitions": count,
        "input_files": count,
        "path_components": 1,
        "path_utf8_bytes": 128,
        "physical_step_count": steps,
        "retained_before_and_after_bytes": MAX_TOTAL_REQUEST_BYTES,
        "scratch_paths": count,
        "simultaneous_live_scratch": 1,
        "simultaneous_owned_descriptors": 8,
        "private_acquisitions": 1,
        # The original whole-schedule validation charge is also reserved for
        # preparation/failure paths before the original whole check is reached.
        "private_validations": 2 * validations,
        "private_return_bytes": reserved,
    }
    ceilings = _limits(count) | {
        "private_acquisitions": 128,
        "private_validations": 65536,
        "private_return_bytes": 2097152,
    }
    usage = {
        "private_acquisitions": acquisitions,
        "private_validations": observation.validation_ordinal,
    }
    return tuple(
        CapacityBound(name, usage.get(name, 0), additional[name], ceilings[name])
        for name in sorted(ceilings)
    )


def _decision(bounds):
    return (
        "within_model"
        if all(
            row.used <= row.ceiling and row.additional <= row.ceiling - row.used
            for row in bounds
        )
        else "exceeds_model"
    )


def _forecast_payload(value):
    owner = _owner()
    if type(value) is not PrivateSequenceCapacityForecast:
        raise ValueError("original forecast value required")
    if (
        type(value.schema) is not str
        or value.schema != SCHEMA
        or type(value.schedule) is not str
        or value.schedule != SCHEDULE
    ):
        raise ValueError("invalid forecast schema/schedule")
    model = _model_payload(value.model)
    if model != _model_payload(_MODEL):
        raise _Fault("capacity_model_mismatch")
    binding = owner.private_directory_value_to_payload(value.binding)
    observation = owner.private_directory_value_to_payload(value.observation)
    if (
        type(value.binding) is not owner.PrivateDirectoryBinding
        or type(value.observation) is not owner.PrivateDirectoryObservation
        or value.observation.phase != "active"
        or value.observation.ledger_complete is not True
        or value.observation.active_sequence_ref is not None
        or owner.private_directory_value_to_payload(value.observation.binding)
        != binding
    ):
        raise ValueError("invalid historical observation")
    _digest(value.history_sha256)
    _digest(value.request_sha256)
    if type(value.bounds) is not tuple or len(value.bounds) != 16:
        raise ValueError("invalid bounds")
    names = tuple(
        sorted(
            _limits(1)
            | {
                "private_acquisitions": 128,
                "private_validations": 65536,
                "private_return_bytes": 2097152,
            }
        )
    )
    rows = {}
    for row in value.bounds:
        if type(row) is not CapacityBound:
            raise ValueError("original bound required")
        _text(row.name, 128)
        _integer(row.used)
        _integer(row.additional)
        _integer(row.ceiling, positive=True)
        rows[row.name] = row
    if tuple(row.name for row in value.bounds) != names:
        raise ValueError("invalid bound order/names")
    count = rows["file_transitions"].ceiling
    if not 1 <= count <= MAX_REQUESTS:
        raise ValueError("invalid request count")
    ceilings = _limits(count) | {
        "private_acquisitions": 128,
        "private_validations": 65536,
        "private_return_bytes": 2097152,
    }
    for name, row in rows.items():
        if row.ceiling != ceilings[name] or (
            name not in ("private_acquisitions", "private_validations")
            and row.used != 0
        ):
            raise ValueError("invalid capacity scope")
    if rows["private_validations"].used != value.observation.validation_ordinal:
        raise ValueError("history validation counter mismatch")
    expected_bounds = _bounds(
        value.binding,
        value.observation,
        rows["private_acquisitions"].used,
        (None,) * count,
        owner.sequence.ConfinedSequenceLimits(**_limits(count)),
    )
    if value.bounds != expected_bounds:
        raise ValueError("capacity model charges mismatch")
    if (
        _sha(
            {
                "observation": observation,
                "acquisitions": rows["private_acquisitions"].used,
            }
        )
        != value.history_sha256
    ):
        raise ValueError("history fingerprint mismatch")
    if type(value.decision) is not str or value.decision != _decision(value.bounds):
        raise ValueError("capacity decision mismatch")
    literals = {
        "physical_validation": "not_performed",
        "reservation": "not_performed",
        "filesystem_effect": "none",
        "grants_admission": False,
        "permits_dispatch": False,
        "authorizes_retry": False,
        "future_terminal_capacity": "not_established",
    }
    for name, expected in literals.items():
        actual = getattr(value, name)
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError("invalid authority qualification")
    return dict(
        schema=SCHEMA,
        model=model,
        schedule=SCHEDULE,
        binding=binding,
        observation=observation,
        history_sha256=value.history_sha256,
        request_sha256=value.request_sha256,
        decision=value.decision,
        bounds=[
            {
                "name": r.name,
                "used": r.used,
                "additional": r.additional,
                "ceiling": r.ceiling,
            }
            for r in value.bounds
        ],
        **literals,
    )


def forecast_private_file_sequence_capacity(
    directory: RetainedPrivateDirectory,
    *,
    expected_binding: PrivateDirectoryBinding,
    expected_model: CapacityModelIdentity,
    requests: tuple[ConfinedFileMutationRequest, ...],
    limits: ConfinedSequenceLimits,
    confinement_profile: ConfinedMutationProfile,
    schedule: Literal["release_receiving_single_batch_v1"],
) -> PrivateSequenceCapacityForecast:
    state = None
    observation = None
    stage = "lookup"
    inputs = None
    try:
        _authenticate()
        inputs, unsafe = _safe_data(
            {
                "expected_binding": expected_binding,
                "expected_model": expected_model,
                "requests": requests,
                "limits": limits,
                "confinement_profile": confinement_profile,
                "schedule": schedule,
            }
        )
        if unsafe:
            raise _Fault("capacity_input_invalid")
        _authenticate()
        try:
            state = _owner()._original_directory(directory)
        except _owner().PrivateDirectoryRefusal as cause:
            raise _Fault("capacity_original_parent_required") from cause
        with state.lock:
            stage = "capture"
            candidate = _owner()._directory_observation(state)
            _owner().private_directory_value_to_payload(candidate)
            observation = candidate
            candidate = None
            if (
                state.phase != "active"
                or state.close_attempted
                or state.fd is None
                or state.child is not None
                or state.native_sequence is not None
                or not state.complete
            ):
                raise _Fault("capacity_parent_unavailable")
            stage = "input"
            if type(expected_binding) is not _owner().PrivateDirectoryBinding:
                raise _Fault("capacity_binding_mismatch")
            if _owner().private_directory_value_to_payload(
                expected_binding
            ) != _owner().private_directory_value_to_payload(state.binding):
                raise _Fault("capacity_binding_mismatch")
            stage = "model"
            if _model_payload(expected_model) != _model_payload(_MODEL):
                raise _Fault("capacity_model_mismatch")
            stage = "input"
            request = _request_payload(
                state.binding, requests, limits, confinement_profile, schedule
            )
            stage = "model"
            bounds = _bounds(
                state.binding, observation, state.acquisitions, requests, limits
            )
            stage = "capture"
            model = _MODEL
            if model is None:
                raise _Fault("capacity_model_unavailable")
            result = PrivateSequenceCapacityForecast(
                SCHEMA,
                model,
                SCHEDULE,
                state.binding,
                observation,
                _sha(
                    {
                        "observation": _owner().private_directory_value_to_payload(
                            observation
                        ),
                        "acquisitions": state.acquisitions,
                    }
                ),
                _sha(request),
                _decision(bounds),
                bounds,
                "not_performed",
                "not_performed",
                "none",
                False,
                False,
                False,
                "not_established",
            )
            _forecast_payload(result)
            _authenticate()
            return result
    except BaseException as cause:
        code = (
            str(cause)
            if type(cause) is _Fault
            else "capacity_capture_interrupted"
            if not isinstance(cause, Exception)
            else "capacity_input_invalid"
            if stage == "input"
            else "capacity_model_unavailable"
        )
        raise PrivateSequenceCapacityError(
            code, stage, inputs, cause, observation
        ) from cause
    finally:
        state = None
        del directory
        del (
            expected_binding,
            expected_model,
            requests,
            limits,
            confinement_profile,
            schedule,
        )


def encode_private_sequence_capacity_forecast(
    value: PrivateSequenceCapacityForecast,
) -> bytes:
    original = None
    try:
        _authenticate()
        original, unsafe = _safe_data(value)
        if unsafe:
            raise ValueError("non-data forecast input")
        _authenticate()
        result = _canonical(_forecast_payload(value))
        _lexical(result)
        _authenticate()
        return result
    except BaseException as cause:
        code = (
            str(cause)
            if type(cause) is _Fault
            else "capacity_capture_interrupted"
            if not isinstance(cause, Exception)
            else "capacity_forecast_invalid"
        )
        raise PrivateSequenceCapacityError(
            code, "encode", {"value": original}, cause, original_forecast=original
        ) from cause
    finally:
        del value


def _lexical(value):
    """Bound UTF-8 bytes, lexical depth and tokens before JSON allocation."""
    if type(value) is not bytes or len(value) > MAX_FORECAST_BYTES:
        raise ValueError("invalid forecast bytes")
    text = value.decode("utf-8", errors="strict")
    depth = tokens = 0
    string = escaped = atom = False
    for char in text:
        if string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                string = False
            continue
        if char in " \r\n\t,:":
            atom = False
            continue
        if char == '"':
            tokens += 1
            string, atom = True, False
        elif char in "[{":
            tokens += 1
            depth += 1
            atom = False
        elif char in "]}":
            tokens += 1
            depth -= 1
            atom = False
        elif not atom:
            tokens += 1
            atom = True
        if tokens > MAX_JSON_TOKENS or not 0 <= depth <= MAX_JSON_DEPTH:
            raise ValueError("forecast lexical capacity")
    if string or depth != 0:
        raise ValueError("invalid JSON structure")
    return text


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _keys(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError("invalid fields")
    return value


def decode_private_sequence_capacity_forecast(
    value: bytes,
    *,
    expected_model: CapacityModelIdentity,
    expected_binding: PrivateDirectoryBinding,
    expected_request_sha256: str,
    expected_history_sha256: str,
) -> PrivateSequenceCapacityForecast:
    inputs = None
    try:
        _authenticate()
        inputs, unsafe = _safe_data(
            {
                "value": value,
                "expected_model": expected_model,
                "expected_binding": expected_binding,
                "expected_request_sha256": expected_request_sha256,
                "expected_history_sha256": expected_history_sha256,
            }
        )
        if unsafe:
            raise ValueError("non-data decode inputs")
        _authenticate()
        text = _lexical(value)

        def invalid_constant(value):
            raise ValueError("nonfinite JSON")

        data = json.loads(
            text, object_pairs_hook=_object, parse_constant=invalid_constant
        )
        _keys(data, (f.name for f in fields(PrivateSequenceCapacityForecast)))
        model = _keys(data["model"], (f.name for f in fields(CapacityModelIdentity)))
        if (
            type(model["modules"]) is not list
            or len(model["modules"]) > MAX_MODEL_MODULES
        ):
            raise ValueError("invalid module rows")
        modules = []
        for row in model["modules"]:
            if type(row) is not list or len(row) != 2:
                raise ValueError("invalid module row")
            modules.append(tuple(row))
        identity = CapacityModelIdentity(
            model["distribution"], model["version"], model["model"], tuple(modules)
        )
        if type(data["bounds"]) is not list or len(data["bounds"]) != 16:
            raise ValueError("invalid bound rows")
        bounds = tuple(
            CapacityBound(**_keys(row, (f.name for f in fields(CapacityBound))))
            for row in data["bounds"]
        )
        owner = _owner()
        binding = owner.private_directory_value_from_payload(
            owner.PrivateDirectoryBinding, data["binding"]
        )
        observation = owner.private_directory_value_from_payload(
            owner.PrivateDirectoryObservation, data["observation"]
        )
        arguments = data | {
            "model": identity,
            "binding": binding,
            "observation": observation,
            "bounds": bounds,
        }
        result = PrivateSequenceCapacityForecast(**arguments)
        payload = _forecast_payload(result)
        if (
            _model_payload(expected_model) != payload["model"]
            or owner.private_directory_value_to_payload(expected_binding)
            != payload["binding"]
            or _digest(expected_request_sha256) != result.request_sha256
            or _digest(expected_history_sha256) != result.history_sha256
            or _canonical(payload) != value
        ):
            raise ValueError("forecast expected-coordinate/canonical mismatch")
        _authenticate()
        return result
    except BaseException as cause:
        code = (
            str(cause)
            if type(cause) is _Fault
            else "capacity_capture_interrupted"
            if not isinstance(cause, Exception)
            else "capacity_forecast_invalid"
        )
        raise PrivateSequenceCapacityError(code, "decode", inputs, cause) from cause
    finally:
        del (
            value,
            expected_model,
            expected_binding,
            expected_request_sha256,
            expected_history_sha256,
        )
