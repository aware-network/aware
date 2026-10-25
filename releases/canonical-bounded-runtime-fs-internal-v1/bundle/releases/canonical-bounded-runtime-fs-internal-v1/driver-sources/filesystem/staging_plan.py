"""Bounded detached staging inputs; no custody, authorization or physical IO."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields

from .confined_mutation import _read_text, _relative_path

_MIB = 1024 * 1024
_CEILINGS = (10_000, 256 * _MIB, 256 * _MIB, 1024, 64, 4 * _MIB)
_EMPTY_DIGEST = "sha256:" + hashlib.sha256(b"").hexdigest()


@dataclass(frozen=True, slots=True)
class StagingDirectory:
    path: str
    mode: int


@dataclass(frozen=True, slots=True)
class StagingFile:
    """Declared final regular-file metadata, not temporary write permissions."""

    path: str
    mode: int
    size_bytes: int
    content_digest: str


@dataclass(frozen=True, slots=True)
class StagingPlanLimits:
    member_count: int
    file_bytes: int
    total_file_bytes: int
    path_bytes: int
    path_components: int
    encoded_bytes: int


@dataclass(frozen=True, slots=True)
class StagingPlan:
    limits: StagingPlanLimits
    members: tuple[StagingDirectory | StagingFile, ...]


@dataclass(frozen=True, slots=True)
class StagingPlanSummary:
    plan_digest: str
    member_count: int
    total_file_bytes: int
    encoded_bytes: int


def _integer(value: object, minimum: int, maximum: int, code: str) -> None:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(code)


def validate_staging_plan(plan: StagingPlan) -> StagingPlanSummary:
    """Revalidate original input before future owner admission, without IO.

    The summary is freely reconstructible detached data, never a permit or
    proof of namespace exclusion, written bytes or available backend capacity.
    """
    if type(plan) is not StagingPlan or type(plan.limits) is not StagingPlanLimits:
        raise TypeError("original_staging_plan_required")
    limits = plan.limits
    limit_values = tuple(getattr(limits, field.name) for field in fields(limits))
    for value, ceiling in zip(limit_values, _CEILINGS, strict=True):
        _integer(value, 1, ceiling, "invalid_staging_limit")
    if type(plan.members) is not tuple:
        raise TypeError("staging_members_tuple_required")
    if len(plan.members) > limits.member_count:
        raise ValueError("staging_member_limit")

    # All input collections and encoding allocations are bounded before IO.
    paths: dict[str, bool] = {}
    encoder = json.JSONEncoder(
        ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )
    hasher = hashlib.sha256()
    encoded_size = 0

    def emit(text):
        nonlocal encoded_size
        block = text.encode("utf-8")
        encoded_size += len(block)
        hasher.update(block)

    # Encode the original closed header with the original JSON encoder. The
    # member array is streamed one validated row at a time, not copied into a
    # second complete list while the preceding stage's evidence stays live.
    emit(encoder.encode(["aware.filesystem.staging-plan.v1", limit_values])[:-1])
    emit(",[")
    total_bytes = 0
    total_path_bytes = 0
    for member in plan.members:
        kind = type(member)
        if kind not in (StagingDirectory, StagingFile):
            raise TypeError("original_staging_member_required")
        if type(member.path) is not str:
            raise TypeError("staging_path_string_required")
        # Reject oversized scalars before Unicode normalization/encoding.
        if len(member.path) > limits.path_bytes:
            raise ValueError("staging_path_byte_limit")
        _read_text(member.path, limits.path_bytes)
        path = _relative_path(member.path)
        if path != member.path:
            raise ValueError("original_staging_path_changed")
        # The original validator requires already-normalized input. Keep that
        # exact immutable input text instead of retaining a duplicate string
        # produced by PurePosixPath for every path in the duplicate index.
        path = member.path
        if len(path.split("/")) > limits.path_components:
            raise ValueError("staging_path_depth_limit")
        total_path_bytes += len(path.encode("utf-8"))
        if total_path_bytes > limits.encoded_bytes:
            raise ValueError("staging_metadata_limit")
        if path in paths:
            raise ValueError("staging_duplicate_path")
        parent = path.rpartition("/")[0]
        if parent and not paths.get(parent, False):
            raise ValueError("staging_declared_parent_required")
        directory = kind is StagingDirectory
        modes = (
            (0o700, 0o755) if directory else (0o444, 0o555, 0o600, 0o644, 0o700, 0o755)
        )
        if type(member.mode) is not int or member.mode not in modes:
            raise ValueError("staging_mode_unsupported")
        if directory:
            row = ["directory", path, member.mode]
        else:
            _integer(member.size_bytes, 0, limits.file_bytes, "staging_file_limit")
            digest = member.content_digest
            if (
                type(digest) is not str
                or len(digest) != 71
                or not digest.startswith("sha256:")
                or any(c not in "0123456789abcdef" for c in digest[7:])
            ):
                raise ValueError("staging_digest_invalid")
            if member.size_bytes == 0 and digest != _EMPTY_DIGEST:
                raise ValueError("staging_empty_digest_mismatch")
            total_bytes += member.size_bytes
            if total_bytes > limits.total_file_bytes:
                raise ValueError("staging_total_file_limit")
            row = ["file", path, member.mode, member.size_bytes, digest]
        if paths:
            emit(",")
        # Policy bounds this individual row before encoding. The public
        # one-row encoder avoids a fresh mutually recursive streaming-engine
        # graph per row; no complete plan string or row list is materialized.
        emit(encoder.encode(row))
        paths[path] = directory

    emit("]]")
    # Retain the original validation order: all member-policy checks precede
    # the final complete-frame byte-limit check. No provisional digest escapes.
    if encoded_size > limits.encoded_bytes:
        raise ValueError("staging_metadata_limit")
    return StagingPlanSummary(
        "sha256:" + hasher.hexdigest(),
        len(plan.members),
        total_bytes,
        encoded_size,
    )
