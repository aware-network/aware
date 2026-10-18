"""Bounded explicit stdin framing only, never an SDK schema or authority."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterator
from typing import Any

MAX_FRAME_BYTES = 2_097_152
MAX_FRAME_DEPTH = 64
MAX_FRAME_NODES = 65_536


class ReferenceInputError(ValueError):
    """Fixed local transport reason; underlying errors retain their cause."""


def input_observation() -> dict[str, Any]:
    return {
        "source": "stdin_agent_result_v1",
        "selector": "/reference",
        "byte_count": 0,
        "eof": False,
        "source_sha256": None,
    }


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ReferenceInputError("reference_input_duplicate_key")
        value[key] = item
    return value


def _non_finite(_text: str) -> Any:
    raise ReferenceInputError("reference_input_non_finite")


def _children(value: Any, depth: int) -> Iterator[tuple[Any, int]]:
    if type(value) is dict:
        for key, item in value.items():
            yield key, depth + 1
            yield item, depth + 1
    elif type(value) is list:
        for item in value:
            yield item, depth + 1


def _validate_tree(value: Any) -> None:
    stack: list[Iterator[tuple[Any, int]]] = [iter(((value, 0),))]
    count = 0
    while stack:
        try:
            item, depth = next(stack[-1])
        except StopIteration:
            stack.pop()
            continue
        count += 1
        if count > MAX_FRAME_NODES:
            raise ReferenceInputError("reference_input_node_limit")
        if depth > MAX_FRAME_DEPTH:
            raise ReferenceInputError("reference_input_depth_limit")
        if type(item) is str:
            try:
                item.encode("utf-8")
            except UnicodeError as error:
                raise ReferenceInputError("reference_input_invalid_utf8") from error
        elif type(item) is float and not math.isfinite(item):
            raise ReferenceInputError("reference_input_non_finite")
        if type(item) in (dict, list):
            stack.append(_children(item, depth))


def read_result_reference(stdin: Any, observation: dict[str, Any]) -> Any:
    """Select one detached wire value. Caller invokes the original SDK codec."""
    try:
        try:
            interactive = stdin.isatty()
        except (OSError, ValueError, AttributeError) as error:
            raise ReferenceInputError("reference_input_read_failed") from error
        if interactive:
            raise ReferenceInputError("reference_input_interactive")
        buffer = getattr(stdin, "buffer", None)
        if buffer is None:
            raise ReferenceInputError("reference_input_unavailable")
        body = bytearray()
        while True:
            try:
                chunk = buffer.read(min(65_536, MAX_FRAME_BYTES + 1 - len(body)))
                if type(chunk) is not bytes:
                    raise TypeError("binary_stdin_read_required")
            except Exception as error:
                raise ReferenceInputError("reference_input_read_failed") from error
            body.extend(chunk)
            observation["byte_count"] = len(body)
            if len(body) > MAX_FRAME_BYTES:
                raise ReferenceInputError("reference_input_byte_limit")
            if not chunk:
                observation["eof"] = True
                observation["source_sha256"] = (
                    "sha256:" + hashlib.sha256(body).hexdigest()
                )
                break
        try:
            text = body.decode("utf-8")
        except UnicodeError as error:
            raise ReferenceInputError("reference_input_invalid_utf8") from error
        try:
            frame = json.loads(
                text, object_pairs_hook=_pairs, parse_constant=_non_finite
            )
        except ReferenceInputError:
            raise
        except RecursionError as error:
            raise ReferenceInputError("reference_input_depth_limit") from error
        except ValueError as error:
            raise ReferenceInputError("reference_input_invalid_json") from error
        _validate_tree(frame)
        if (
            type(frame) is not dict
            or frame.get("contract") != "aware.agent.workspace-review.v1"
        ):
            raise ReferenceInputError("reference_input_frame_required")
        if frame.get("reference") is None:
            raise ReferenceInputError("reference_input_reference_required")
        return frame["reference"]
    except BaseException as error:
        if not isinstance(error, Exception):
            BaseException.__setattr__(
                error, "reference_input_code", "reference_input_interrupted"
            )
        raise
