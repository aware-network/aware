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

    def read_tree_entry(self, path: str, *, maximum_bytes: int = 16777216):
        """Additive C read profile; v0 read_source retains its 4 MiB contract."""
        from aware_workspace_sdk.repository_tree_projection_values import (
            WorkspaceTreeEntryPin,
            WorkspaceTreeTargetRead,
        )

        canonical_path(path)
        if (
            len(path.encode("utf-8")) > 1024
            or any(len(part.encode("utf-8")) > 255 for part in path.split("/"))
            or any(unicodedata.category(char).startswith("C") for char in path)
            or type(maximum_bytes) is not int
            or not 0 < maximum_bytes <= 16777216
        ):
            raise ValueError("tree_read_bounds_invalid")
        _TREE_EXECUTION_CHECK(self)
        descriptors = []
        chunks = []
        body = None
        error = None
        output = None
        try:
            root = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            descriptors.append(root)
            root_identity = (os.fstat(root).st_dev, os.fstat(root).st_ino)
            if root_identity != self.root_identity:
                raise ValueError("tree_root_identity_changed")
            directory = root
            parts = path.split("/")
            absent = False
            for part in parts[:-1]:
                try:
                    child = os.open(
                        part,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=directory,
                    )
                except FileNotFoundError:
                    absent = True
                    break
                # Deep paths retain only root + current + next, never one fd per depth.
                descriptors.append(child)
                if directory != root:
                    descriptors.remove(directory)
                    os.close(directory)
                directory = child
            before = None
            if not absent:
                try:
                    before = os.stat(parts[-1], dir_fd=directory, follow_symlinks=False)
                except FileNotFoundError:
                    absent = True
            if absent:
                entry = WorkspaceTreeEntryPin(False, *([None] * 8))
            elif stat.S_ISDIR(before.st_mode):
                descriptor = os.open(
                    parts[-1],
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory,
                )
                descriptors.append(descriptor)
                after = os.fstat(descriptor)
                if _tree_stat_pin(before) != _tree_stat_pin(after):
                    raise ValueError("tree_entry_changed_during_read")
                entry = _tree_entry_pin(after, None)
            elif stat.S_ISREG(before.st_mode) and before.st_nlink == 1:
                descriptor = os.open(
                    parts[-1],
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                    dir_fd=directory,
                )
                descriptors.append(descriptor)
                opened = os.fstat(descriptor)
                if (
                    _tree_stat_pin(before) != _tree_stat_pin(opened)
                    or opened.st_size > maximum_bytes
                ):
                    raise ValueError("tree_regular_bounded_preimage_required")
                remaining = maximum_bytes + 1
                while remaining:
                    chunk = os.read(descriptor, min(remaining, 65536))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                body = b"".join(chunks)
                after = os.fstat(descriptor)
                if len(body) > maximum_bytes or _tree_stat_pin(
                    opened
                ) != _tree_stat_pin(after):
                    raise ValueError("tree_entry_changed_during_read")
                import hashlib

                entry = _tree_entry_pin(
                    after, "sha256:" + hashlib.sha256(body).hexdigest()
                )
            else:
                raise ValueError("tree_regular_single_link_or_directory_required")
            if not absent:
                current = os.stat(parts[-1], dir_fd=directory, follow_symlinks=False)
                if _tree_stat_pin(current) != _tree_stat_pin(after):
                    raise ValueError("tree_entry_changed_during_read")
            current_root = os.stat(self.root, follow_symlinks=False)
            if (current_root.st_dev, current_root.st_ino) != root_identity:
                raise ValueError("tree_root_identity_changed")
            _TREE_EXECUTION_CHECK(self)
            output = WorkspaceTreeTargetRead(entry, root_identity, body)
        except BaseException as caught:  # noqa: BLE001 - preserve interrupts through cleanup
            error = caught
        finally:
            cleanup_errors = []
            for descriptor in reversed(descriptors):
                try:
                    os.close(descriptor)
                except BaseException as caught:  # noqa: BLE001 - all originals release once
                    cleanup_errors.append(caught)
            descriptors.clear()
            chunks.clear()
            body = None
            if cleanup_errors:
                cleanup = ValueError("tree_read_cleanup_unknown")
                if error is not None:
                    error.add_note("tree_read_cleanup_unknown")
                else:
                    error = cleanup
                    cleanup.__cause__ = cleanup_errors[0]
                output = None
            cleanup_errors.clear()
        if error is not None:
            raise error
        return output

    def retain_tree_preparation(self, request):
        # No local writer or substitute preparation when the supplier is absent.
        from aware_file_system.confined_mutation import ConfinedMutationProfile
        from aware_file_system.retained_tree_projection import (
            retain_confined_tree_projection,
        )

        _TREE_EXECUTION_CHECK(self)
        return retain_confined_tree_projection(
            root=self.root,
            request=request,
            confinement_profile=ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
        )

    def create_tree_session(self, binding):
        _TREE_EXECUTION_CHECK(self)
        if (
            type(binding) is not WorkspaceRepositoryBinding
            or binding.root_path != self.root
        ):
            raise ValueError("original_tree_repository_binding_required")
        return WorkspaceRepositoryObservationSession(
            binding=binding,
            provider=FileSystemIndexObservationProvider(
                binding=binding, cache_dir=self.state_root / "tree-observation"
            ),
            observation_mode="command",
        )

    def create_tree_receipt_store(self, binding, *, capacity):
        _TREE_EXECUTION_CHECK(self)
        if (
            type(binding) is not WorkspaceRepositoryBinding
            or binding.root_path != self.root
        ):
            raise ValueError("Original tree receipt repository binding required")
        return WorkspaceRepositoryMutationStore(
            repository_binding_ref=binding.binding_key,
            state_root=self.state_root / "receipts",
            capacity=capacity,
        )


_TREE_EXECUTION_CHECK = FilesystemSourceProjectionPort.check_execution


def _tree_stat_pin(value):
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
        value.st_mode,
        value.st_nlink,
    )


def _tree_entry_pin(value, digest):
    from aware_workspace_sdk.repository_tree_projection_values import (
        WorkspaceTreeEntryPin,
    )

    return WorkspaceTreeEntryPin(
        True,
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
        stat.S_IMODE(value.st_mode),
        value.st_nlink,
        digest,
    )
