"""Physical source reads and selection of the original observation/receipt owners."""

from __future__ import annotations

import os
import stat
import unicodedata
from pathlib import Path, PurePosixPath

from aware_workspace_runtime.contracts import WorkspaceRepositoryBinding
from aware_workspace_runtime.observation import WorkspaceRepositoryObservationSession
from aware_workspace_runtime.provider import FileSystemIndexObservationProvider

from .repository_mutation_store import WorkspaceRepositoryMutationStore


def execution_identity():
    identities = [
        (provider, (os.environ.get(key) or "").strip())
        for provider, key in (
            ("codex", "CODEX_THREAD_ID"),
            ("claude_code", "CLAUDE_CODE_SESSION_ID"),
        )
    ]
    identities = [(provider, value) for provider, value in identities if value]
    if len(identities) != 1 or any(
        c.isspace() for _, value in identities for c in value
    ):
        raise ValueError("provider_execution_identity_unavailable")
    provider, value = identities[0]
    return f"{provider}-{value}"


def canonical_path(path):
    if type(path) is not str or not path or unicodedata.normalize("NFC", path) != path:
        raise ValueError("source_path_noncanonical")
    parsed = PurePosixPath(path)
    if (
        parsed.is_absolute()
        or str(parsed) != path
        or path == "."
        or ".." in parsed.parts
        or "\\" in path
        or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in path)
    ):
        raise ValueError("source_path_noncanonical")
    return path


class FilesystemSourceProjectionPort:
    def __init__(self, *, repository_root: Path, state_root: Path, execution_id: str):
        if not isinstance(repository_root, Path) or not repository_root.is_absolute():
            raise ValueError("absolute_repository_root_required")
        # Never silently select through a symlink or change the selected root.
        if repository_root.resolve() != repository_root or not repository_root.is_dir():
            raise ValueError("original_repository_root_required")
        if not isinstance(state_root, Path) or not state_root.is_absolute():
            raise ValueError("absolute_state_root_required")
        if state_root.resolve() != state_root or state_root.is_relative_to(
            repository_root
        ):
            raise ValueError("separate_original_state_root_required")
        self.root = repository_root
        self.state_root = state_root
        self.execution_id = execution_id
        self.check_execution()
        self.binding = WorkspaceRepositoryBinding(repository_root)
        self.root_identity = self._identity(os.stat(self.root, follow_symlinks=False))

    @staticmethod
    def _identity(value):
        return value.st_dev, value.st_ino

    def check_execution(self):
        if (
            type(self.execution_id) is not str
            or execution_identity() != self.execution_id
        ):
            raise ValueError("source_projection_execution_mismatch")

    def create_session(self):
        self.state_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        return WorkspaceRepositoryObservationSession(
            binding=self.binding,
            provider=FileSystemIndexObservationProvider(
                binding=self.binding, cache_dir=self.state_root / "observation"
            ),
            observation_mode="command",
        )

    def create_receipt_store(self):
        return WorkspaceRepositoryMutationStore(
            repository_binding_ref=self.binding.binding_key,
            state_root=self.state_root / "receipts",
        )

    def read_source(self, path):
        canonical_path(path)
        descriptors = []
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        try:
            directory = os.open(self.root, flags)
            descriptors.append(directory)
            root_identity = self._identity(os.fstat(directory))
            if root_identity != self.root_identity:
                raise ValueError("source_root_identity_changed")
            for part in PurePosixPath(path).parts[:-1]:
                directory = os.open(part, flags, dir_fd=directory)
                descriptors.append(directory)
            leaf = PurePosixPath(path).name
            prior = os.stat(leaf, dir_fd=directory, follow_symlinks=False)
            if not stat.S_ISREG(prior.st_mode) or prior.st_nlink != 1:
                raise ValueError("source_regular_single_link_required")
            descriptor = os.open(
                leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
            )
            descriptors.append(descriptor)
            before = os.fstat(descriptor)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_size > 4 * 1024 * 1024
                or self._identity(before) != self._identity(prior)
            ):
                raise ValueError("source_regular_bounded_authority_required")
            chunks = []
            remaining = 4 * 1024 * 1024 + 1
            while remaining:
                chunk = os.read(descriptor, min(remaining, 65536))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            body = b"".join(chunks)
            after = os.fstat(descriptor)
            identity = lambda value: (
                value.st_dev,
                value.st_ino,
                value.st_size,
                value.st_mtime_ns,
                value.st_ctime_ns,
                value.st_nlink,
            )
            if len(body) > 4 * 1024 * 1024 or identity(before) != identity(after):
                raise ValueError("source_changed_during_read")
            current = os.stat(leaf, dir_fd=directory, follow_symlinks=False)
            if identity(current) != identity(after):
                raise ValueError("source_changed_during_read")
            return body, root_identity, self._identity(after)
        finally:
            errors = []
            for descriptor in reversed(descriptors):
                try:
                    os.close(descriptor)
                except BaseException as error:  # noqa: BLE001 - release every acquired descriptor
                    errors.append(error)
            if errors:
                raise ValueError("source_read_cleanup_incomplete") from errors[0]
