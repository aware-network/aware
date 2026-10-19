"""Bounded stdin transport for original Issue read-result data, not authority."""

from __future__ import annotations

import hashlib
import json

from aware_issue_sdk import IssueReadProjectionResolveOutcome
from aware_issue_sdk.operation import (
    ISSUE_RESOLVE_READ_PROJECTION_PROVIDER_OPERATION_REF,
)
from aware_issue_sdk.operation_codec import decode_issue_result

MAX_BYTES = 786_432
MAX_CHUNK = 65_536
MAX_DEPTH = 32
MAX_NODES = 8192
MAX_ITEMS = 4096
MAX_STRING_BYTES = 262_144


def input_observation():
    return {
        "source": "stdin_issue_read_projection_v1",
        "selector": "/projection/source/digest",
        "byte_count": 0,
        "eof": False,
        "source_sha256": None,
        "result_validation_complete": False,
        "selected_issue_guard": None,
    }


class ObservationInputError(ValueError):
    def __init__(self, code, observation, cause, *, observed_outcome=None):
        super().__init__(code)
        self.code = code
        self.observation = dict(observation)
        self.observation.update(
            result_validation_complete=False, selected_issue_guard=None
        )
        self.original_cause = cause
        self.observed_outcome = observed_outcome
        self.interruption = code == "issue_observation_input_interrupted"
        self.output_cause = None
        self.output_retirement_cause = None


class _Fault(ValueError):
    def __init__(self, code, *, observed_outcome=None):
        super().__init__(code)
        self.code = "issue_observation_input_" + code
        self.observed_outcome = observed_outcome


def _pairs(rows):
    result = {}
    for key, value in rows:
        if key in result:
            raise _Fault("duplicate_key")
        result[key] = value
    return result


def _number(value):
    raise _Fault("invalid_json")


def _lexical_depth(text):
    # Bound nesting before json.loads can recurse. Root is SDK depth zero.
    quoted = escaped = False
    depth = 0
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH + 1:
                raise _Fault("structure_limit")
        elif char in "]}":
            depth -= 1


def _structure(value):
    nodes = 0
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if depth > MAX_DEPTH or nodes > MAX_NODES:
            raise _Fault("structure_limit")
        if type(item) is dict:
            for key, child in item.items():
                pending.append((key, depth + 1))
                pending.append((child, depth + 1))
        elif type(item) is list:
            if len(item) > MAX_ITEMS:
                raise _Fault("structure_limit")
            pending.extend((child, depth + 1) for child in item)
        elif (
            type(item) is str
            and len(item.encode("utf-8", errors="strict")) > MAX_STRING_BYTES
        ):
            raise _Fault("structure_limit")


def _relative_source(path):
    return (
        type(path) is str
        and bool(path)
        and not path.startswith("/")
        and "\\" not in path
        and "\x00" not in path
        and all(part not in {"", ".", ".."} for part in path.split("/"))
    )


def read_issue_guard(stream, *, issue_ref, actor_ref):
    """Borrow one binary stream, retaining only bounded data and typed evidence."""
    observation = input_observation()
    raw = bytearray()
    binary = chunk = None
    stage = "availability"
    try:
        if stream is None or not callable(getattr(stream, "isatty", None)):
            raise _Fault("unavailable")
        if stream.isatty():
            raise _Fault("interactive")
        binary = getattr(stream, "buffer", None)
        if (
            binary is None
            or not callable(getattr(binary, "read", None))
            or getattr(binary, "closed", False)
        ):
            raise _Fault("unavailable")
        stage = "read"
        while True:
            remaining = MAX_BYTES + 1 - len(raw)
            chunk = binary.read(min(MAX_CHUNK, remaining))
            if type(chunk) is not bytes:
                raise _Fault("read_failed")
            if not chunk:
                # Commit EOF and its source hash together; no hash for partial input.
                digest = "sha256:" + hashlib.sha256(raw).hexdigest()
                observation.update(eof=True, source_sha256=digest)
                break
            raw.extend(chunk[:remaining])
            observation["byte_count"] = len(raw)
            if len(raw) > MAX_BYTES or len(chunk) > remaining:
                raise _Fault("byte_limit")
        stage = "utf8"
        if raw.startswith(b"\xef\xbb\xbf"):
            raise _Fault("invalid_utf8")
        text = raw.decode("utf-8", errors="strict")
        stage = "json"
        _lexical_depth(text)
        frame = json.loads(
            text, object_pairs_hook=_pairs, parse_float=_number, parse_constant=_number
        )
        stage = "structure"
        _structure(frame)
        stage = "codec"
        result = decode_issue_result(
            ISSUE_RESOLVE_READ_PROJECTION_PROVIDER_OPERATION_REF, frame
        )
        if result.outcome is not IssueReadProjectionResolveOutcome.FOUND:
            raise _Fault("not_found", observed_outcome=result.outcome.value)
        projection = result.projection
        if projection is None:
            raise _Fault("invalid_result")
        if result.issue_ref != issue_ref or projection.issue_ref != issue_ref:
            raise _Fault("issue_mismatch")
        if projection.owner_ref != actor_ref:
            raise _Fault("actor_mismatch")
        if not _relative_source(projection.source_path):
            raise _Fault("path_invalid")
        guard = projection.source_digest
        observation.update(result_validation_complete=True, selected_issue_guard=guard)
        return guard, dict(observation)
    except BaseException as cause:
        code = (
            "issue_observation_input_interrupted"
            if not isinstance(cause, Exception)
            else cause.code
            if type(cause) is _Fault
            else "issue_observation_input_unavailable"
            if stage == "availability"
            else "issue_observation_input_read_failed"
            if stage == "read"
            else "issue_observation_input_invalid_utf8"
            if isinstance(cause, UnicodeError)
            else "issue_observation_input_invalid_result"
            if stage == "codec"
            else "issue_observation_input_structure_limit"
            if isinstance(cause, RecursionError)
            else "issue_observation_input_invalid_json"
        )
        raise ObservationInputError(
            code,
            observation,
            cause,
            observed_outcome=cause.observed_outcome if type(cause) is _Fault else None,
        ) from cause
    finally:
        stream = binary = chunk = None
