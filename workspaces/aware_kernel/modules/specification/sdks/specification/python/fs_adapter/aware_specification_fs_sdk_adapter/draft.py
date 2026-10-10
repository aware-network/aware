"""Render explicit meaning; the existing strict adapter validates the result."""

import ctypes
import errno
import json
import os
import secrets

from aware_specification_fs_source_contract.values import (
    MAX_MEMBERS,
    MAX_TOTAL_BYTES,
    canonical_source_body,
)
from aware_specification_runtime import SpecificationSnapshot, invariant_ref, phase_ref
from aware_specification_sdk import (
    SpecificationDraftRequest,
    SpecificationOperationError,
)


def render_draft(request: SpecificationDraftRequest) -> dict[str, bytes]:
    request.__post_init__()
    definition = request.definition
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    invariant_paths = {
        value.invariant_key: f"invariants/{index:02d}-{value.invariant_key}/README.md"
        for index, value in enumerate(definition.invariants)
    }
    phase_paths = {
        value.phase_key: f"phases/{value.ordinal:02d}-{value.phase_key}/README.md"
        for value in definition.phases
    }
    files: dict[str, str] = {
        "SPEC.md": f"# {definition.title} — SPEC\n\nStatus: `draft`\nOwner: {request.author_ref}\n\n## Goal\n\n{definition.description}\n",
        "invariants/README.md": f"# {definition.title} — Invariants\n\n## Members\n\n| Invariant Ref | Path |\n| --- | --- |\n"
        + "".join(
            f"| `{invariant_ref(definition.key, value.invariant_key)}` | `{invariant_paths[value.invariant_key]}` |\n"
            for value in definition.invariants
        ),
        "PHASES.md": f"# {definition.title} — PHASES\n\nStatus: `draft`\nOwner: {request.author_ref}\n\n## Members\n\n| Phase Ref | Path |\n| --- | --- |\n"
        + "".join(
            f"| `{phase_ref(definition.key, value.phase_key)}` | `{phase_paths[value.phase_key]}` |\n"
            for value in definition.phases
        ),
    }
    manifest = [
        "aware = 1",
        "",
        "[specification]",
        'profile = "specification_fs_v1"',
        f"key = {quote(definition.key)}",
        f"semantic_version = {definition.version_number}",
        'entrypoint = "SPEC.md"',
        'invariant_index = "invariants/README.md"',
        'phase_index = "PHASES.md"',
    ]
    for index, value in enumerate(definition.invariants):
        path = invariant_paths[value.invariant_key]
        manifest += [
            "",
            "[[invariants]]",
            f"key = {quote(value.invariant_key)}",
            f"semantic_revision = {value.semantic_revision}",
            f"entrypoint = {quote(path)}",
        ]
        files[path] = (
            f"# Invariant {index:02d} — {value.invariant_key}\n\nStatus: `declared`\nOwner: {request.author_ref}\nSpec: SPEC.md\n\n## Statement\n\n{value.statement}\n"
        )
    for value in definition.phases:
        gate = value.gate
        manifest += [
            "",
            "[[phases]]",
            f"key = {quote(value.phase_key)}",
            f"ordinal = {value.ordinal}",
            f"entrypoint = {quote(phase_paths[value.phase_key])}",
            f"gate_key = {quote(gate.gate_key)}",
            f"gate_contract = {quote(gate.gate_contract)}",
            f"evidence_schema_ref = {quote(gate.evidence_schema_ref)}",
            "invariant_refs = ["
            + ", ".join(quote(ref) for ref in gate.invariant_refs)
            + "]",
        ]
        dependency_rows = []
        for dependency in value.dependencies:
            rationale = (
                (dependency.rationale or "")
                .replace("\\", "\\\\")
                .replace("|", "\\|")
                .replace("\n", "\\n")
            )
            dependency_rows.append(
                f"| `{dependency.dependency_key}` | `{dependency.kind.value}` | `{dependency.required_phase_ref}` | `{dependency.required_gate_digest}` | {rationale} |\n"
            )
        files[phase_paths[value.phase_key]] = (
            f"# Phase {value.ordinal:02d} — {value.title}\n\nState: `planned`\nOwner: {request.author_ref}\n\n"
            f"## Gate\n\n{gate.promise}\n\n## Goal\n\n{value.description}\n\n## Advances\n\n"
            + (
                "".join(f"- `{ref}`\n" for ref in gate.invariant_refs)
                or "No invariants.\n"
            )
            + "\n## Dependencies\n\n| Dependency Key | Kind | Required Phase Ref | Required Gate Digest | Rationale |\n| --- | --- | --- | --- | --- |\n"
            + "".join(dependency_rows)
            + "\n## Iterations\n\nNo iterations.\n"
        )
    dependencies = [
        (phase_ref(definition.key, p.phase_key), d)
        for p in definition.phases
        for d in p.dependencies
    ]
    if not dependencies:
        # Empty arrays are explicit when no array-of-table entries exist.
        manifest[2:2] = ["phase_dependencies = []", "iterations = []", ""]
    else:
        manifest[2:2] = ["iterations = []", ""]
        for owner, value in dependencies:
            manifest += [
                "",
                "[[phase_dependencies]]",
                f"key = {quote(value.dependency_key)}",
                f"owner_phase_ref = {quote(owner)}",
                f"kind = {quote(value.kind.value)}",
                f"required_phase_ref = {quote(value.required_phase_ref)}",
                f"required_gate_digest = {quote(value.required_gate_digest)}",
                f"rationale = {quote(value.rationale or '')}",
            ]
    files["aware.spec.toml"] = "\n".join(manifest) + "\n"
    encoded = {path: canonical_source_body(body)[1] for path, body in files.items()}
    if len(encoded) > MAX_MEMBERS or sum(map(len, encoded.values())) > MAX_TOTAL_BYTES:
        raise SpecificationOperationError("draft_size_exceeded")
    SpecificationSnapshot((definition,))
    return encoded


def render_specification_draft(
    request: SpecificationDraftRequest,
) -> tuple[tuple[str, bytes], ...]:
    """Return exact immutable draft members; no IO or publication authority."""
    if type(request) is not SpecificationDraftRequest:
        raise SpecificationOperationError("invalid_draft_request")
    try:
        return tuple(sorted(render_draft(request).items()))
    except SpecificationOperationError as error:
        # This pure preparation has performed no physical operation. Preserve
        # the original contract refusal, not physical-effect authority.
        raise SpecificationOperationError(error.code, effect="none") from error
    except (AttributeError, TypeError, ValueError) as error:
        raise SpecificationOperationError("invalid_draft_request") from error


def rename_no_replace(parent_fd: int, source: str, target: str) -> None:
    library = ctypes.CDLL(None, use_errno=True)
    try:
        operation = library.renameat2
    except AttributeError as error:
        raise SpecificationOperationError(
            "atomic_draft_publication_unavailable"
        ) from error
    operation.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    operation.restype = ctypes.c_int
    if operation(parent_fd, os.fsencode(source), parent_fd, os.fsencode(target), 1):
        number = ctypes.get_errno()
        if number in {errno.EEXIST, errno.ENOTEMPTY}:
            raise SpecificationOperationError("draft_target_exists")
        if number in {errno.ENOSYS, errno.EINVAL, errno.EOPNOTSUPP}:
            raise SpecificationOperationError("atomic_draft_publication_unavailable")
        raise OSError(number, os.strerror(number))


def stage_files(parent_fd: int, files: dict[str, bytes]) -> str:
    name = ".aware-spec-draft-" + secrets.token_hex(16)
    os.mkdir(name, mode=0o700, dir_fd=parent_fd)
    root = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
    try:
        for path, body in sorted(files.items()):
            directory = os.dup(root)
            try:
                for segment in path.split("/")[:-1]:
                    try:
                        os.mkdir(segment, mode=0o755, dir_fd=directory)
                    except FileExistsError:
                        pass
                    following = os.open(
                        segment,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=directory,
                    )
                    os.close(directory)
                    directory = following
                fd = os.open(
                    path.split("/")[-1],
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o644,
                    dir_fd=directory,
                )
                try:
                    pending = memoryview(body)
                    while pending:
                        written = os.write(fd, pending)
                        if written <= 0:
                            raise OSError("draft write made no progress")
                        pending = pending[written:]
                finally:
                    os.close(fd)
            finally:
                os.close(directory)
        return name
    except BaseException:
        cleanup_stage(parent_fd, name, files)
        raise
    finally:
        os.close(root)


def cleanup_stage(parent_fd: int, name: str, files: dict[str, bytes]) -> None:
    """Remove only this operation's known staged paths; never follow symlinks."""
    try:
        root = os.open(
            name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd
        )
    except OSError:
        return
    try:
        directories = set()
        for path in files:
            parts = path.split("/")
            for length in range(1, len(parts)):
                directories.add("/".join(parts[:length]))
            fd = os.dup(root)
            try:
                for part in parts[:-1]:
                    following = os.open(
                        part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                    )
                    os.close(fd)
                    fd = following
                try:
                    os.unlink(parts[-1], dir_fd=fd)
                except FileNotFoundError:
                    pass
            except OSError:
                pass
            finally:
                os.close(fd)
        for path in sorted(directories, key=lambda p: (p.count("/"), p), reverse=True):
            parts = path.split("/")
            fd = os.dup(root)
            try:
                for part in parts[:-1]:
                    following = os.open(
                        part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                    )
                    os.close(fd)
                    fd = following
                os.rmdir(parts[-1], dir_fd=fd)
            except OSError:
                pass
            finally:
                os.close(fd)
    finally:
        os.close(root)
    try:
        os.rmdir(name, dir_fd=parent_fd)
    except OSError:
        # Foreign additions or topology change remain visible; never broaden deletion.
        pass
