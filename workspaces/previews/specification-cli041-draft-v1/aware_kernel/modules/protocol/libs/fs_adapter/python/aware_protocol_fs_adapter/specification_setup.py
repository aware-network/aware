"""Protocol-owned SPEC-only candidate preparation. No source writer or Issue policy."""

from __future__ import annotations

import json
import os
import re
import stat
import tomllib
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from aware_protocol_runtime import ProtocolAdmissionOutcomeKind
from aware_protocol_sdk import (
    ProtocolSpecificationSetupError,
    ProtocolSpecificationSetupRequest,
)

from .goal_templates import canonical_relative_path
from .manifest import admit_protocol_manifest_bytes, resolve_repository_path_at_use
from .specification_selection import SPECIFICATION_PATH_TEMPLATE

_HEADER = re.compile(r"^[ \t]*\[[^\r\n]+\][ \t]*(?:#[^\r\n]*)?(?:\r?\n)?$")
_SPEC_HEADER = re.compile(
    r"^[ \t]*\[records\.specification\][ \t]*(?:#[^\r\n]*)?(?:\r?\n)?$"
)
_ROLE = re.compile(
    r"""^([ \t]*role[ \t]*=[ \t]*)(["'])unavailable\2([ \t]*(?:#[^\r\n]*)?)(\r?\n)?$"""
)


@dataclass(frozen=True, slots=True)
class SpecificationSetupCandidate:
    """Preview data only: consumption always obtains a fresh genuine Issue admission."""

    repository_root: Path
    manifest_path: Path
    relative_manifest_path: str
    preimage: bytes
    postimage: bytes

    @property
    def postimage_sha256(self) -> str:
        return "sha256:" + sha256(self.postimage).hexdigest()


def prepare_specification_setup(
    request: ProtocolSpecificationSetupRequest,
) -> SpecificationSetupCandidate:
    if type(request) is not ProtocolSpecificationSetupRequest:
        raise TypeError("Setup requires the exact SDK request")
    try:
        root = Path(request.repository_root).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise ProtocolSpecificationSetupError("setup_repository_unavailable")
        path = Path(request.manifest_path)
        path = path if path.is_absolute() else root / path
        relative = path.relative_to(root).as_posix()
        if not canonical_relative_path(relative) or path.name != "aware.protocol.toml":
            raise ProtocolSpecificationSetupError("setup_manifest_locator_invalid")
        resolution = resolve_repository_path_at_use(
            repository_root=root, relative_path=relative, field_name="setup.manifest"
        )
        if resolution.path is None:
            raise ProtocolSpecificationSetupError("setup_manifest_unconfined")
        source = _read_source(path)
        if "sha256:" + sha256(source).hexdigest() != request.expected_manifest_sha256:
            raise ProtocolSpecificationSetupError("setup_manifest_preimage_changed")
        before = admit_protocol_manifest_bytes(source=source, repository_root=root)
        if before.outcome is not ProtocolAdmissionOutcomeKind.CANONICAL_V1:
            raise ProtocolSpecificationSetupError(
                "setup_manifest_admission_refused:" + ":".join(before.diagnostics)
            )
        decoded = tomllib.loads(source.decode("utf-8"))
        if decoded["protocol"] != {
            "name": "aware.collaboration",
            "profile": "aware.collaboration.fs_v1",
            "semantic_version": 1,
        } or decoded["target"] != {
            "kind": "repository",
            "authority_mode": "filesystem",
        }:
            raise ProtocolSpecificationSetupError("setup_profile_unavailable")
        if not canonical_relative_path(request.specification_root) or any(
            not canonical_relative_path(p) for p in request.directory_paths
        ):
            raise ProtocolSpecificationSetupError("setup_root_noncanonical")
        # Directory preparation is limited to the selected root and its ancestors.
        if any(
            p != request.specification_root
            and not request.specification_root.startswith(p + "/")
            for p in request.directory_paths
        ):
            raise ProtocolSpecificationSetupError("setup_directory_not_root_ancestor")
        desired = {
            "profile": "specification_fs_v1",
            "role": "authority",
            "root": request.specification_root,
            "path_template": SPECIFICATION_PATH_TEMPLATE,
        }
        record = decoded["records"]["specification"]
        if record == desired:
            candidate = source
        elif record == {"profile": "specification_fs_v1", "role": "unavailable"}:
            candidate = _edit_explicit_table(source, request.specification_root)
        else:
            raise ProtocolSpecificationSetupError("setup_reconfiguration_unavailable")
        after = admit_protocol_manifest_bytes(source=candidate, repository_root=root)
        if after.outcome is not ProtocolAdmissionOutcomeKind.CANONICAL_V1:
            raise ProtocolSpecificationSetupError(
                "setup_candidate_admission_refused:" + ":".join(after.diagnostics)
            )
        expected = tomllib.loads(source.decode("utf-8"))
        expected["records"]["specification"] = desired
        if tomllib.loads(candidate.decode("utf-8")) != expected:
            raise ProtocolSpecificationSetupError("setup_candidate_delta_invalid")
        return SpecificationSetupCandidate(root, path, relative, source, candidate)
    except ProtocolSpecificationSetupError:
        raise
    except (OSError, RuntimeError, ValueError, UnicodeError) as error:
        raise ProtocolSpecificationSetupError("setup_source_unavailable") from error


def _read_source(path: Path) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size > 16 * 1024 * 1024
        ):
            raise ProtocolSpecificationSetupError(
                "setup_manifest_regular_bounded_required"
            )
        chunks = []
        remaining = 16 * 1024 * 1024 + 1
        while remaining:
            chunk = os.read(descriptor, min(remaining, 65536))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
        identity = lambda s: (
            s.st_dev,
            s.st_ino,
            s.st_size,
            s.st_mtime_ns,
            s.st_ctime_ns,
            s.st_mode,
            s.st_nlink,
        )
        source = b"".join(chunks)
        if identity(before) != identity(after) or len(source) > 16 * 1024 * 1024:
            raise ProtocolSpecificationSetupError("setup_manifest_changed_during_read")
        return source
    finally:
        os.close(descriptor)


def _edit_explicit_table(source: bytes, root: str) -> bytes:
    # This is a deliberately finite source form, not a general TOML formatter.
    # Canonical admission above/below owns semantics; unsupported spelling refuses.
    lines = source.decode("utf-8").splitlines(keepends=True)
    headers = [i for i, line in enumerate(lines) if _SPEC_HEADER.fullmatch(line)]
    if len(headers) != 1:
        raise ProtocolSpecificationSetupError("setup_source_form_unsupported")
    start = headers[0] + 1
    end = next(
        (i for i in range(start, len(lines)) if _HEADER.fullmatch(lines[i])), len(lines)
    )
    # Avoid interpreting apparent table/key lines inside multiline TOML strings.
    if any('"""' in line or "'''" in line for line in lines):
        raise ProtocolSpecificationSetupError("setup_source_form_unsupported")
    roles = [
        (i, _ROLE.fullmatch(lines[i]))
        for i in range(start, end)
        if _ROLE.fullmatch(lines[i])
    ]
    if len(roles) != 1:
        raise ProtocolSpecificationSetupError("setup_source_form_unsupported")
    index, match = roles[0]
    assert match is not None
    newline = match[4] or ("\r\n" if b"\r\n" in source else "\n")
    lines[index] = match[1] + match[2] + "authority" + match[2] + match[3] + newline
    lines.insert(
        index + 1,
        "root = "
        + json.dumps(root, ensure_ascii=False)
        + newline
        + "path_template = "
        + json.dumps(SPECIFICATION_PATH_TEMPLATE)
        + newline,
    )
    return "".join(lines).encode("utf-8")
